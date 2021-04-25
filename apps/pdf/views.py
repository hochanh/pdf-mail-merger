import json
import logging
import mimetypes
from datetime import timedelta
from io import BytesIO

from PyPDF2 import PdfFileWriter
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import (FileResponse, HttpResponse, HttpResponseBadRequest,
                         JsonResponse)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from reportlab.lib.units import mm

from apps.pdf.models import CachedFile

logger = logging.getLogger(__name__)


class BaseEditorView(TemplateView):
    template_name = 'pdf/editor.html'
    accepted_formats = (
        'application/pdf',
    )
    maxfilesize = 1024 * 1024 * 10
    minfilesize = 10
    title = None
    settings = {}

    def get(self, request, *args, **kwargs):
        resp = super().get(request, *args, **kwargs)
        return resp

    def process_upload(self):
        f = self.request.FILES.get('background')
        error = False
        if f.size > self.maxfilesize:
            error = _('The uploaded PDF file is to large.')
        if f.size < self.minfilesize:
            error = _('The uploaded PDF file is to small.')
        if mimetypes.guess_type(f.name)[0] not in self.accepted_formats:
            error = _('Please only upload PDF files.')
        # if there was an error, add error message to response_data and return
        if error:
            return error, None
        return None, f

    def get_preview_data(self):
        raise NotImplementedError()

    def generate(self, row, override_layout=None, override_background=None):
        raise NotImplementedError()

    def get_layout_settings_key(self):
        raise NotImplementedError()

    def get_background_settings_key(self):
        raise NotImplementedError()

    def get_default_background(self):
        raise NotImplementedError()

    def get_current_background(self):
        return self.get_default_background()

    def get_current_layout(self):
        raise NotImplementedError()

    def get_variables(self):
        raise NotImplementedError()

    def save_layout(self):
        raise NotImplementedError()

    def save_background(self, f: CachedFile):
        fexisting = settings.get(self.get_background_settings_key())
        if fexisting:
            try:
                default_storage.delete(fexisting.name)
            except OSError:  # pragma: no cover
                logger.error('Deleting file %s failed.' % fexisting.name)

        # Create new file
        nonce = get_random_string(length=8)
        fname = 'pub/%s/%s.%s' % (self.get_layout_settings_key(), nonce, 'pdf')
        newname = default_storage.save(fname, f.file)
        settings.set[self.get_background_settings_key()] = 'file://' + newname

    def post(self, request, *args, **kwargs):
        if "emptybackground" in request.POST:
            p = PdfFileWriter()
            try:
                p.addBlankPage(
                    width=float(request.POST.get('width')) * mm,
                    height=float(request.POST.get('height')) * mm,
                )
            except ValueError:
                return JsonResponse({
                    "status": "error",
                    "error": "Invalid height/width given."
                })
            buffer = BytesIO()
            p.write(buffer)
            buffer.seek(0)
            c = CachedFile()
            c.expires = now() + timedelta(days=7)
            c.date = now()
            c.filename = 'background_preview.pdf'
            c.type = 'application/pdf'
            c.save()
            c.file.save('empty.pdf', ContentFile(buffer.read()))
            c.refresh_from_db()
            return JsonResponse({
                "status": "ok",
                "id": c.id,
                "url": reverse('pdf:background', kwargs={
                    'filename': str(c.id)
                })
            })

        if "background" in request.FILES:
            error, fileobj = self.process_upload()
            if error:
                return JsonResponse({
                    "status": "error",
                    "error": error
                })
            c = CachedFile()
            c.expires = now() + timedelta(days=7)
            c.date = now()
            c.filename = 'background_preview.pdf'
            c.type = 'application/pdf'
            c.file = fileobj
            c.save()
            c.refresh_from_db()
            return JsonResponse({
                "status": "ok",
                "id": c.id,
                "url": reverse('pdf:background', kwargs={
                    'filename': str(c.id)
                })
            })

        cf = None
        if request.POST.get("background", "").strip():
            try:
                cf = CachedFile.objects.get(id=request.POST.get("background"))
            except CachedFile.DoesNotExist:
                pass

        if "preview" in request.POST:
            row = self.get_preview_data()
            fname, mimet, data = self.generate(
                row,
                override_layout=(json.loads(self.request.POST.get("data"))
                                 if self.request.POST.get("data")
                                 else None),
                override_background=cf.file if cf else None
            )

            resp = HttpResponse(data, content_type=mimet)
            ftype = fname.split(".")[-1]
            resp['Content-Disposition'] = 'attachment; filename="pdf-preview.{}"'.format(
                ftype)
            return resp
        elif "data" in request.POST:
            if cf:
                self.save_background(cf)
            self.save_layout()
            return JsonResponse({'status': 'ok'})
        return HttpResponseBadRequest()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pdf'] = self.get_current_background()
        ctx['variables'] = self.get_variables()
        ctx['layout'] = json.dumps(self.get_current_layout())
        ctx['title'] = self.title
        return ctx


class PdfView(TemplateView):
    def get(self, request, *args, **kwargs):
        cf = get_object_or_404(CachedFile, id=kwargs.get("filename"),
                               filename="background_preview.pdf")
        resp = FileResponse(cf.file, content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(cf.filename)
        return resp
