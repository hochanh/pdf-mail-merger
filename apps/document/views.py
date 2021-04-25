import json
import logging
from io import BytesIO

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.contrib.staticfiles import finders
from django.core.files import File
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.templatetags.static import static
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import generic
from reportlab.lib import pagesizes
from reportlab.pdfgen import canvas

from apps.account.models import TRIAL_LIMIT
from apps.common.views import PAGINATE_BY, AccountView
from apps.document.models import DEFAULT_BACKGROUND, Document
from apps.document.output import PdfDocumentOutput
from apps.document.renderer import Renderer
from apps.pdf.models import CachedFile
from apps.pdf.views import BaseEditorView

logger = logging.getLogger(__name__)


class DownloadView(LoginRequiredMixin, BaseEditorView):
    title = _('PDF download')

    def get_output(self, *args, **kwargs):
        return PdfDocumentOutput(*args, **kwargs)

    def get_layout_settings_key(self):
        return 'pdf_layout'

    def get_background_settings_key(self):
        return 'pdf_background'

    def get_default_background(self):
        return static(DEFAULT_BACKGROUND)

    def generate(self, rows, override_layout=None, override_background=None, variables=None):
        prov = self.get_output(
            override_layout=override_layout,
            override_background=override_background,
            variables=variables,
        )
        fname, mimet, data = prov.generate(rows)
        return fname, mimet, data

    def get_current_layout(self):
        prov = self.get_output()
        return prov._default_layout()

    def get(self, request, *args, **kwargs):
        document = get_object_or_404(Document, pk=kwargs.get('pk'),
                                     account=request.user.account)
        return self.pdf_by_document(document)

    def pdf_by_document(self, document: Document):
        limit = document.account.plan_limit if not document.account.plan_expired else TRIAL_LIMIT

        fname, mimet, data = self.generate(
            document.load_data().dict[:limit],
            document.layout,
            document.background,
            document.get_variables(),
        )
        ftype = fname.split(".")[-1]
        resp = HttpResponse(data, content_type='application/octet-stream')
        resp['Content-Disposition'] = 'attachment; filename="{}.{}"'.format(document.name, ftype)
        return resp


class EditorView(LoginRequiredMixin, BaseEditorView):

    @cached_property
    def document(self):
        return get_object_or_404(Document, id=self.kwargs['pk'],
                                 account=self.request.user.account)

    @property
    def title(self):
        return _('PDFs layout for: {}').format(self.document)

    def get_variables(self):
        return self.document.get_variables()

    def save_layout(self):
        self.document.layout = json.loads(self.request.POST.get("data"))
        self.document.save(update_fields=['layout'])

    def get_preview_data(self):
        return self.document.first_row

    def get_default_background(self):
        return static(DEFAULT_BACKGROUND)

    def generate(self, row, override_layout=None, override_background=None):
        Renderer._register_fonts()

        buffer = BytesIO()
        if override_background:
            bgf = default_storage.open(override_background.name, "rb")
        elif isinstance(self.document.background, File) and self.document.background.name:
            bgf = default_storage.open(self.document.background.name, "rb")
        else:
            bgf = open(finders.find(DEFAULT_BACKGROUND), "rb")

        r = Renderer(
            override_layout or self.get_current_layout(),
            bgf,
            self.get_variables(),
        )

        p = canvas.Canvas(buffer, pagesize=pagesizes.A4)
        r.draw_page(p, row)
        p.save()
        outbuffer = r.render_background(buffer, 'Document')
        return 'out.pdf', 'application/pdf', outbuffer.read()

    def get_current_layout(self):
        return self.document.layout

    def get_current_background(self):
        return self.document.background.url \
            if self.document.background else self.get_default_background()

    def save_background(self, f: CachedFile):
        if self.document.background:
            self.document.background.delete()
        self.document.background.save('background.pdf', f.file)


class IndexView(PermissionRequiredMixin, AccountView, generic.ListView):
    model = Document
    context_object_name = 'documents'
    template_name = 'document/index.html'
    permission_required = 'document.view_document'
    ordering = '-updated_at'
    paginate_by = PAGINATE_BY


class DocumentForm(forms.ModelForm):

    file = forms.FileField(widget=forms.FileInput(attrs={
        'accept': '.csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel'
    }))

    class Meta:
        model = Document
        fields = ('name', 'file')


class CreateView(PermissionRequiredMixin, generic.CreateView):
    model = Document
    template_name = 'document/detail.html'
    permission_required = 'document.add_document'

    def get(self, *args, **kwargs):
        form = DocumentForm()
        return render(self.request, self.template_name, {'form': form})

    @transaction.atomic
    def post(self, *args, **kwargs):
        form = DocumentForm(self.request.POST, self.request.FILES)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.account = self.request.user.account
            instance.user = self.request.user
            instance.save()

            try:
                instance.populate_data()
                messages.add_message(self.request, messages.INFO, 'Create document success!')
            except Exception as e:
                messages.add_message(self.request, messages.ERROR, str(e))
            return redirect(reverse("document:detail", kwargs={'pk': instance.id}))

        messages.add_message(self.request, messages.ERROR, 'Create document failure.')
        return render(self.request, self.template_name, {'form': form})


class DetailView(PermissionRequiredMixin, AccountView, generic.DetailView):
    model = Document
    template_name = 'document/detail.html'
    permission_required = ('document.view_document', 'document.change_document')

    def get(self, *args, **kwargs):
        document = self.get_object()
        form = DocumentForm(instance=document)

        return render(self.request, self.template_name, {'form': form})

    @transaction.atomic
    def post(self, *args, **kwargs):
        document = self.get_object()
        form = DocumentForm(self.request.POST, self.request.FILES, instance=document)

        if form.is_valid():
            instance = form.save(commit=False)
            if not instance.account:
                instance.account = self.request.user.account
            if not instance.user:
                instance.user = self.request.user
            instance.save()

            try:
                instance.populate_data()
                messages.add_message(self.request, messages.INFO, 'Create document success!')
            except Exception as e:
                messages.add_message(self.request, messages.ERROR, str(e))
            return redirect(reverse("document:detail", kwargs={'pk': instance.id}))

        messages.add_message(self.request, messages.ERROR, 'Update document failure.')
        return render(self.request, self.template_name, {'form': form})


class DeleteView(PermissionRequiredMixin, AccountView, generic.DetailView):
    model = Document
    template_name = 'document/delete.html'
    permission_required = 'document.delete_document'

    def get(self, *args, **kwargs):
        document = self.get_object()
        return render(self.request, self.template_name, {'document': document})

    def post(self, *args, **kwargs):
        document = self.get_object()
        document.file.delete()
        document.delete()

        messages.add_message(self.request, messages.INFO, 'Delete document success.')
        return redirect(reverse("document:index"))
