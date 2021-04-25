import copy
import logging
import uuid
from io import BytesIO

from arabic_reshaper import ArabicReshaper
from bidi.algorithm import get_display
from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils.html import conditional_escape
from django.utils.translation import gettext_lazy as _
from PyPDF2 import PdfFileReader
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import getAscentDescent
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

logger = logging.getLogger(__name__)


class Renderer(object):

    def __init__(self, layout, background, variables):
        self.layout = layout
        self.background = background
        self.variables = variables

        if self.background:
            self.bg_bytes = self.background.read()
            self.bg_pdf = PdfFileReader(BytesIO(self.bg_bytes), strict=False)
        else:
            self.bg_bytes = None
            self.bg_pdf = None

    @classmethod
    def _register_fonts(cls):
        pdfmetrics.registerFont(TTFont('Arial', finders.find('fonts/Arial.ttf')))
        pdfmetrics.registerFont(TTFont('Arial I', finders.find('fonts/Arial Italic.ttf')))
        pdfmetrics.registerFont(TTFont('Arial B', finders.find('fonts/Arial Bold.ttf')))
        pdfmetrics.registerFont(TTFont('Arial B I', finders.find('fonts/Arial Bold Italic.ttf')))

    def _draw_barcodearea(self, canvas: Canvas, o: dict, row: dict):
        content = row.get("qrcode", "Missing qrcode column")

        level = 'H'
        if len(content) > 32:
            level = 'M'
        if len(content) > 128:
            level = 'L'

        reqs = float(o['size']) * mm
        qrw = QrCodeWidget(content, barLevel=level,
                           barHeight=reqs, barWidth=reqs)
        d = Drawing(reqs, reqs)
        d.add(qrw)
        qr_x = float(o['left']) * mm
        qr_y = float(o['bottom']) * mm
        renderPDF.draw(d, canvas, qr_x, qr_y)

    def _get_text_content(self, o: dict, row: dict, inner=False):
        if not o['content']:
            return '(error)'

        if o['content'] == 'other':
            return o['text']

        if o['content'] in self.variables:
            return row.get(o['content'], '')

        return ''

    def _draw_textarea(self, canvas: Canvas, o: dict, row: dict):
        font = o['fontfamily'] or 'Arial'
        if o['bold']:
            font += ' B'
        if o['italic']:
            font += ' I'

        align_map = {
            'left': TA_LEFT,
            'center': TA_CENTER,
            'right': TA_RIGHT
        }
        style = ParagraphStyle(
            name=uuid.uuid4().hex,
            fontName=font,
            fontSize=float(o['fontsize']),
            leading=float(o['fontsize']),
            autoLeading="max",
            textColor=Color(o['color'][0] / 255, o['color']
                            [1] / 255, o['color'][2] / 255),
            alignment=align_map[o['align']]
        )
        text = conditional_escape(
            self._get_text_content(o, row) or "",
        ).replace("\n", "<br/>\n")

        # reportlab does not support RTL, ligature-heavy scripts like Arabic. Therefore, we use ArabicReshaper
        # to resolve all ligatures and python-bidi to switch RTL texts.
        configuration = {
            'delete_harakat': True,
            'support_ligatures': False,
        }
        reshaper = ArabicReshaper(configuration=configuration)
        text = "<br/>".join(get_display(reshaper.reshape(line))
                            for line in text.split("<br/>"))

        p = Paragraph(text, style=style)
        w, h = p.wrapOn(canvas, float(o['width']) * mm, 1000 * mm)
        ad = getAscentDescent(font, float(o['fontsize']))
        canvas.saveState()
        # The ascent/descent offsets here are not really proven to be correct, they're just empirical values to get
        # reportlab render similarly to browser canvas.
        if o.get('downward', False):
            canvas.translate(float(o['left']) * mm, float(o['bottom']) * mm)
            canvas.rotate(o.get('rotation', 0) * -1)
            p.drawOn(canvas, 0, -h - ad[1] / 2)
        else:
            canvas.translate(float(o['left']) * mm,
                             float(o['bottom']) * mm + h)
            canvas.rotate(o.get('rotation', 0) * -1)
            p.drawOn(canvas, 0, -h - ad[1])
        canvas.restoreState()

    def draw_page(self, canvas: Canvas, row: dict, show_page=True):
        for o in self.layout:
            if o['type'] == "barcodearea":
                self._draw_barcodearea(canvas, o, row)
            elif o['type'] == "textarea":
                self._draw_textarea(canvas, o, row)

            if self.bg_pdf:
                canvas.setPageSize((self.bg_pdf.getPage(0).mediaBox[2],
                                    self.bg_pdf.getPage(0).mediaBox[3]))
        if show_page:
            canvas.showPage()

    def render_background(self, buffer, title=_('Document')):
        from PyPDF2 import PdfFileReader, PdfFileWriter
        buffer.seek(0)
        new_pdf = PdfFileReader(buffer)
        output = PdfFileWriter()

        for page in new_pdf.pages:
            bg_page = copy.copy(self.bg_pdf.getPage(0))
            bg_page.mergePage(page)
            output.addPage(bg_page)

        output.addMetadata({
            '/Title': str(title),
            '/Creator': settings.APP_NAME,
        })
        outbuffer = BytesIO()
        output.write(outbuffer)
        outbuffer.seek(0)
        return outbuffer
