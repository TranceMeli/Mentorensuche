"""Erzeugt mentor_gesucht.svg: Variante B als animiertes SVG fuer GitHub-READMEs.

Schrift (Inconsolata, auf benutzte Zeichen reduziert) und Bild werden
eingebettet, weil GitHub in SVGs nichts von aussen nachlaedt.

Aufruf:  python tools/build_svg.py
"""
import base64
import io
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ROOT / "mentor_gesucht.svg"

# --- Layout ---------------------------------------------------------------
W = 560
TITLE_H = 40
IMG_H = round(W * 9 / 16)          # 315
FONT = 16
CHAR_W = FONT * 0.5                 # Inconsolata: 500/1000 em
LINE_H = 26
GUTTER = 52                         # Platz fuer Zeilennummern
PAD_TOP = 16
BLOCK_GAP = 10
STATUS_H = 24

# Farben (VS-Code-Dark)
C = dict(kw="#569cd6", fn="#dcdcaa", cls="#4ec9b0", str="#ce9178", com="#6a9955",
         var="#9cdcfe", txt="#d4d4d4", num="#5a5a5a")

# --- Inhalt: Bloecke aus Zeilen aus Segmenten (text, farbe, stil) ----------
BLOCKS = [
    ("hsl(51,100%,50%)", "hsla(51,100%,50%,0.06)", [
        [("def ", "kw"), ("mentor_gesucht", "fn", "b"), ("():", "txt")],
        [('    """Eine erfahrene Person, die ihr Fach-', "str")],
        [('    und Erfahrungswissen weitergibt."""', "str")],
    ]),
    ("hsl(190,100%,45%)", "hsla(190,100%,45%,0.06)", [
        [("class ", "kw"), ("FIAE", "cls", "b"), (":", "txt")],
        [("    # Fachinformatikerin Anwendungsentwicklung", "com", "i")],
        [("    ", "txt"), ("name", "var"), ("      = ", "txt"), ('"Melanie Schadl"', "str")],
        [("    ", "txt"), ("abschluss", "var"), (" = ", "txt"), ('"23.06.2026"', "str")],
    ]),
    ("#9a9a9a", "rgba(255,255,255,0.04)", [
        [("start", "var"), ("        = ", "txt"), ('"ab sofort!"', "str")],
        [("standort", "var"), ("     = ", "txt"), ('"Karlsruhe und Umgebung"', "str")],
        [("remote", "var"), ("       = ", "txt"), ("True", "kw")],
        [("umzugsbereit", "var"), (" = ", "txt"), ("True", "kw")],
    ]),
]

# Animation
CHAR_T = 0.022      # Sekunden pro Zeichen
LINE_PAUSE = 0.12   # Pause nach jeder Zeile
START = 0.6         # Verzoegerung vor dem Tippen


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def font_b64(name: str, text: str) -> str:
    font = TTFont(ASSETS / name)
    opts = subset.Options()
    opts.layout_features = []
    opts.name_IDs = []
    sub = subset.Subsetter(opts)
    sub.populate(text=text)
    sub.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def image_b64() -> str:
    img = Image.open(ASSETS / "medieval-knight-grey.jpg").convert("RGB")
    tw, th = W * 2, IMG_H * 2                     # 2x fuer scharfe Anzeige
    scale = max(tw / img.width, th / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    top = round((img.height - th) * 0.22)         # wie object-position: center 22%
    left = (img.width - tw) // 2
    img = img.crop((left, top, left + tw, top + th))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=78, optimize=True, progressive=True)
    return base64.b64encode(buf.getvalue()).decode()


def build() -> str:
    all_text = "mentor_gesucht.py Python 3 main UTF-8 · 0123456789"
    for _, _, lines in BLOCKS:
        for line in lines:
            all_text += "".join(seg[0] for seg in line)

    parts, defs = [], []
    y = TITLE_H + IMG_H + PAD_TOP
    t = START
    ln = 0
    cursor = None

    for bi, (accent, bg, lines) in enumerate(BLOCKS):
        bh = len(lines) * LINE_H + 8
        parts.append(f'<rect x="0" y="{y}" width="{W}" height="{bh}" fill="{bg}"/>')
        parts.append(f'<rect x="0" y="{y}" width="4" height="{bh}" fill="{accent}"/>')
        ly = y + 4
        for line in lines:
            ln += 1
            text = "".join(seg[0] for seg in line)
            n = len(text)
            base = ly + LINE_H * 0.7
            x0 = GUTTER + 14
            # Zeilennummer
            parts.append(f'<text x="{GUTTER - 6}" y="{base}" class="n">{ln}</text>')
            # Tipp-Effekt: Clip-Rechteck waechst Zeichen fuer Zeichen
            cid = f"c{ln}"
            dur = max(n * CHAR_T, 0.05)
            vals = ";".join(f"{i * CHAR_W:g}" for i in range(n + 1))
            defs.append(
                f'<clipPath id="{cid}"><rect x="{x0}" y="{ly}" width="0" height="{LINE_H}">'
                f'<animate attributeName="width" values="{vals}" begin="{t:.2f}s" dur="{dur:.2f}s" '
                f'calcMode="discrete" fill="freeze"/></rect></clipPath>'
            )
            spans = []
            for seg in line:
                txt, col = seg[0], seg[1]
                cls = (" b" if "b" in seg[2:] else "") + (" i" if "i" in seg[2:] else "")
                spans.append(f'<tspan fill="{C[col]}" class="{cls.strip()}">{esc(txt)}</tspan>')
            parts.append(f'<text x="{x0}" y="{base}" clip-path="url(#{cid})">{"".join(spans)}</text>')
            # Tipp-Cursor wandert mit
            parts.append(
                f'<rect x="{x0}" y="{ly + 4}" width="{CHAR_W:g}" height="{LINE_H - 8}" fill="#d4d4d4" opacity="0">'
                f'<set attributeName="opacity" to="1" begin="{t:.2f}s" dur="{dur + LINE_PAUSE:.2f}s"/>'
                f'<animate attributeName="x" values="{";".join(f"{x0 + i * CHAR_W:g}" for i in range(n + 1))}" '
                f'begin="{t:.2f}s" dur="{dur:.2f}s" calcMode="discrete" fill="freeze"/></rect>'
            )
            cursor = (x0 + n * CHAR_W, ly + 4)
            t += dur + LINE_PAUSE
            ly += LINE_H
        y += bh + (BLOCK_GAP if bi < len(BLOCKS) - 1 else 0)

    # Blinkender Cursor am Ende
    cx, cy = cursor
    parts.append(
        f'<rect x="{cx:g}" y="{cy}" width="{CHAR_W:g}" height="{LINE_H - 8}" fill="#d4d4d4" opacity="0">'
        f'<animate attributeName="opacity" values="1;0" begin="{t:.2f}s" dur="1s" '
        f'calcMode="discrete" repeatCount="indefinite"/></rect>'
    )

    code_bottom = y + PAD_TOP
    H = code_bottom + STATUS_H

    reg = font_b64("Inconsolata-Regular.ttf", all_text)
    bold = font_b64("Inconsolata-Bold.ttf", all_text)
    img = image_b64()

    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">Mentor gesucht</title>
<desc id="d">Angehende Fachinformatikerin Anwendungsentwicklung (Abschluss 23.06.2026) sucht Mentor:in. Ab sofort, Karlsruhe und Umgebung, remote moeglich, umzugsbereit.</desc>
<style>
@font-face {{ font-family: "Incon"; font-weight: 400; src: url(data:font/ttf;base64,{reg}) format("truetype"); }}
@font-face {{ font-family: "Incon"; font-weight: 700; src: url(data:font/ttf;base64,{bold}) format("truetype"); }}
text {{ font-family: "Incon", Consolas, "Courier New", monospace; font-size: {FONT}px; white-space: pre; }}
.n {{ fill: {C["num"]}; text-anchor: end; }}
.b {{ font-weight: 700; }}
.i {{ font-style: italic; }}
.s {{ font-size: 13px; fill: #fff; }}
.f {{ font-size: 14px; fill: #bbb; }}
</style>
<defs>
<clipPath id="win"><rect width="{W}" height="{H}" rx="12"/></clipPath>
{"".join(defs)}
</defs>
<g clip-path="url(#win)" xml:space="preserve">
<rect width="{W}" height="{H}" fill="#1e1e1e"/>
<rect width="{W}" height="{TITLE_H}" fill="#3a3a3a"/>
<circle cx="20" cy="20" r="6" fill="#ff5f57"/><circle cx="40" cy="20" r="6" fill="#febc2e"/><circle cx="60" cy="20" r="6" fill="#28c840"/>
<text x="82" y="25" class="f">mentor_gesucht.py</text>
<text x="{W - 14}" y="25" class="f" text-anchor="end" fill="#888">Python 3</text>
<image x="0" y="{TITLE_H}" width="{W}" height="{IMG_H}" preserveAspectRatio="xMidYMid slice" href="data:image/jpeg;base64,{img}" xlink:href="data:image/jpeg;base64,{img}"/>
{"".join(parts)}
<rect x="0" y="{H - STATUS_H}" width="{W}" height="{STATUS_H}" fill="hsl(190,100%,30%)"/>
<text x="14" y="{H - 7}" class="s">main</text>
<text x="{W - 14}" y="{H - 7}" class="s" text-anchor="end">UTF-8 · Python</text>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="#555"/>
</svg>
'''


if __name__ == "__main__":
    svg = build()
    OUT.write_text(svg, encoding="utf-8")
    print(f"{OUT.name}: {len(svg.encode()) / 1024:.0f} KB")
