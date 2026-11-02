"""Apply the requested monochrome palette to source styles and document design."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def gray_hex(value):
    raw = value.lstrip('#')
    if len(raw) in (3, 4): raw = ''.join(c * 2 for c in raw)
    r, g, b = [int(raw[i:i+2], 16) for i in (0, 2, 4)]
    shade = round(.2126 * r + .7152 * g + .0722 * b)
    return f'#{shade:02X}{shade:02X}{shade:02X}' + raw[6:].upper()

def gray_rgba(match):
    r, g, b = map(float, match.group(1, 2, 3))
    shade = round(.2126 * r + .7152 * g + .0722 * b)
    return f'rgba({shade}, {shade}, {shade}, {match.group(4)})'

tokens = {'green':'primary', 'mint':'surface', 'cream':'background', 'gold':'secondaryText', 'red':'error'}
palette = {'173C35':'171717', '19664F':'111111', 'D8E9E0':'E5E5E5', 'E4EBE6':'F1F1F1', 'CBD9D0':'D5D5D5', '576F64':'626262', 'BC8543':'494949', 'B74038':'252525'}
files = list((ROOT/'mobile/src').rglob('*.tsx')) + [ROOT/'mobile/app.json', ROOT/'mobile/assets/raiz.svg']
for path in files:
    content = path.read_text(encoding='utf-8-sig')
    for old, new in tokens.items(): content = re.sub(r'\bC\.'+old+r'\b', 'C.'+new, content)
    if path.name == 'ui.tsx':
        for old, new in tokens.items(): content = re.sub(r'(?m)^  '+old+r':', '  '+new+':', content)
    for old, new in palette.items(): content = re.sub('#'+old, '#'+new, content, flags=re.I)
    content = re.sub(r'#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3,4}\b', lambda m: gray_hex(m.group()), content)
    content = re.sub(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)', gray_rgba, content)
    path.write_text(content, encoding='utf-8')

path = ROOT/'scripts/build_report.py'
content = path.read_text(encoding='utf-8')
content = re.sub(r'#[0-9a-fA-F]{6}\b', lambda m: gray_hex(m.group()), content)
content = re.sub(r"'([0-9A-Fa-f]{6})'", lambda m: "'" + gray_hex(m.group(1))[1:] + "'", content)
content = content.replace("RGBColor.from_string('515151')", "RGBColor.from_string('111111')")
content = content.replace('una paleta verde, fondos suaves y acentos tierra', 'una paleta de blanco y negro, con grises para distinguir superficies')
content = content.replace('# Use neutral green table accents instead of the Word theme default blue.', '# Use monochrome table accents and grayscale diagrams throughout the report.')
if "doc.save(OUT/'Informe_Raiz_Blanco_Negro.docx')" not in content:
    content = content.replace("doc.save(OUT/'Informe_Raiz_Movil.docx')", "doc.save(OUT/'Informe_Raiz_Movil.docx')\ndoc.save(OUT/'Informe_Raiz_Blanco_Negro.docx')")
path.write_text(content, encoding='utf-8')
print('Monochrome palette applied to app styles, logo, configuration and report generator.')
