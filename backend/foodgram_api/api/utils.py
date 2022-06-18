import io
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate

from foodgram_api.settings import STATIC_ROOT

pdfmetrics.registerFont(TTFont(
    'DejaVuSans',
    os.path.join(os.path.join(STATIC_ROOT, 'fonts'), 'DejaVuSans.ttf')
))


def ingredients_to_pdf(ingredients):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )
    style = getSampleStyleSheet()['Normal']
    style.fontName = 'DejaVuSans'
    story = []
    for ingredient in ingredients:
        story.append(Paragraph(ingredient, style, bulletText=u'\u2022'))
    doc.build(story)
    buffer.seek(io.SEEK_SET)
    return buffer
