from io import BytesIO

from django.contrib.staticfiles import finders
from django.core.files.storage import default_storage
from django.http import HttpRequest
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from apps.document.models import DEFAULT_BACKGROUND
from apps.document.renderer import Renderer


class PdfDocumentOutput:
    identifier = 'pdf'
    verbose_name = _('PDF output')
    download_button_text = _('PDF')
    multi_download_button_text = _('Download PDF')
    long_download_button_text = _('Download PDF')

    def __init__(self, override_layout=None, override_background=None, variables=None):
        self.override_layout = override_layout
        self.override_background = override_background
        self.variables = variables
        super().__init__()

    def _register_fonts(self):
        Renderer._register_fonts()

    def _draw_page(self, rows):
        buffer = BytesIO()
        objs = self.override_layout

        if self.override_background:
            bgf = default_storage.open(self.override_background.name, "rb")
        else:
            bgf = self._get_default_background()

        p = self._create_canvas(buffer)
        renderer = Renderer(objs, bgf, self.variables)

        for row in rows:
            renderer.draw_page(p, row, True)

        p.save()
        return renderer.render_background(buffer, _('Document'))

    def generate(self, rows):
        outbuffer = self._draw_page(rows)
        return '%s.pdf' % ("random",), 'application/pdf', outbuffer.read()

    def _create_canvas(self, buffer):
        from reportlab.lib import pagesizes
        from reportlab.pdfgen import canvas

        self._register_fonts()
        return canvas.Canvas(buffer, pagesize=pagesizes.A4)

    def _get_default_background(self):
        return open(finders.find(DEFAULT_BACKGROUND), "rb")

    def settings_content_render(self, request: HttpRequest) -> str:
        template = get_template('pdf/output/form.html')
        return template.render({
            'request': request
        })
