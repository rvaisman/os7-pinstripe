#!/usr/bin/env python3
"""Generate the OS7 Pinstripe theme for KDE Plasma 6.

Produces, under ./build:
  kwin-decorations/os7pinstripe{,-2x,-3x}  QML window decorations (default engine)
  aurorae/OS7Pinstripe{,-2x,-3x}           SVG window decorations (fallback engine)
  color-schemes/OS7Pinstripe.colors
  desktoptheme/OS7Pinstripe        Plasma Style (panel, popups, tooltips)
  wallpapers/*.png                 tiled desktop patterns

Usage:  python3 generate.py [--scale N]

--scale (1-3) sets the size of the Plasma Style and wallpaper patterns.
The window decorations are always generated in all three sizes. Scales are integers so
1-px lines stay crisp.

Only the Python standard library is needed.
"""
import argparse
import json
import shutil
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "build"
QML_SRC = ROOT / "src" / "decoration"

THEME_ID = "OS7Pinstripe"
THEME_NAME = "OS7 Pinstripe"
VERSION = "1.1.0"

S = 1  # integer scale factor, set per build step

B = "#000000"
W = "#ffffff"

# Title bar geometry (unscaled px): 1 outline + 17 interior + 1 separator = 19
TOP_H = 19
STRIPE_ROWS = [4, 6, 8, 10, 12, 14]   # the six classic pinstripes
TOP_NOMINAL_W = 400                    # nominal width of the stretched "top" element
GAP = (0.30, 0.70)                     # white gap behind the centered title (fraction)


def svg(w, h, body):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * S}" height="{h * S}" '
            f'viewBox="0 0 {w * S} {h * S}" shape-rendering="crispEdges">\n{body}</svg>\n')


def rect(id_, x, y, w, h, fill):
    x, y, w, h = x * S, y * S, w * S, h * S
    idattr = f' id="{id_}"' if id_ else ""
    if fill is None:  # invisible rect, used to give an element its size
        return f'<rect{idattr} x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>\n'
    return f'<rect{idattr} x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>\n'


def group(id_, parts):
    return f'<g id="{id_}">\n' + "".join(parts) + "</g>\n"


# ---------------------------------------------------------------------------
# Aurorae window decoration
# ---------------------------------------------------------------------------
def top_element(ox, oy, prefix, striped):
    w = TOP_NOMINAL_W
    p = [rect(None, ox, oy, w, TOP_H, W),
         rect(None, ox, oy, w, 1, B),                 # top outline
         rect(None, ox, oy + TOP_H - 1, w, 1, B)]     # title / content separator
    if striped:
        a, b = int(w * GAP[0]), int(w * GAP[1])
        for r in STRIPE_ROWS:
            p.append(rect(None, ox, oy + r, a, 1, B))
            p.append(rect(None, ox + b, oy + r, w - b, 1, B))
    return group(f"{prefix}-top", p)


def frame_elements(prefix, striped, oy):
    """Lay out the nine frame pieces on one row of the SVG, at y=oy."""
    x = 0
    parts = []
    # topleft 1x19: left outline
    parts.append(group(f"{prefix}-topleft", [rect(None, x, oy, 1, TOP_H, B)])); x += 10
    parts.append(top_element(x, oy, prefix, striped)); x += TOP_NOMINAL_W + 10
    # topright 2x19: outline + drop shadow (shadow starts 1px down)
    parts.append(group(f"{prefix}-topright", [
        rect(None, x, oy, 2, TOP_H, None),
        rect(None, x, oy, 1, TOP_H, B),
        rect(None, x + 1, oy + 1, 1, TOP_H - 1, B)])); x += 10
    parts.append(group(f"{prefix}-left", [rect(None, x, oy, 1, 20, B)])); x += 10
    parts.append(group(f"{prefix}-center", [rect(None, x, oy, 20, 20, W)])); x += 30
    # right 2x20: outline + shadow
    parts.append(group(f"{prefix}-right", [rect(None, x, oy, 2, 20, B)])); x += 10
    # bottomleft 1x2: outline; offset shadow leaves the bottom-left pixel clear
    parts.append(group(f"{prefix}-bottomleft", [
        rect(None, x, oy, 1, 2, None), rect(None, x, oy, 1, 1, B)])); x += 10
    parts.append(group(f"{prefix}-bottom", [rect(None, x, oy, 20, 2, B)])); x += 30
    parts.append(group(f"{prefix}-bottomright", [rect(None, x, oy, 2, 2, B)]))
    return "".join(parts)


def decoration_svg():
    body = rect("hint-stretch-borders", 0, 0, 1, 1, None)
    body += frame_elements("decoration", True, 10)
    body += frame_elements("decoration-inactive", False, 40)
    return svg(700, 70, body)


BTN = 13  # 13x13 button: 11x11 box plus a 1px white margin that clears the stripes


def box(ox, oy, filled=False):
    p = [rect(None, ox, oy, BTN, BTN, W),
         rect(None, ox + 1, oy + 1, 11, 11, B)]
    if not filled:
        p.append(rect(None, ox + 2, oy + 2, 9, 9, W))
    return p


def starburst(ox, oy):
    """The burst drawn while the close box is held down."""
    p = box(ox, oy)
    cx, cy = ox + 6, oy + 6
    pts = [(0, -3), (0, -2), (0, 2), (0, 3), (-3, 0), (-2, 0), (2, 0), (3, 0),
           (-3, -3), (-2, -2), (2, 2), (3, 3), (3, -3), (2, -2), (-2, 2), (-3, 3)]
    for dx, dy in pts:
        p.append(rect(None, cx + dx, cy + dy, 1, 1, B))
    return p


def zoom_glyph(ox, oy):
    # small square in the top-left corner (zoom box)
    return [rect(None, ox + 1, oy + 1, 7, 7, B), rect(None, ox + 2, oy + 2, 5, 5, W)]


def collapse_glyph(ox, oy):
    # double horizontal line (collapse / window-shade box)
    return [rect(None, ox + 1, oy + 5, 11, 1, B), rect(None, ox + 1, oy + 7, 11, 1, B)]


def button_svg(glyph=None, pressed="starburst"):
    x = 0
    body = ""
    for state in ("active", "hover", "pressed", "inactive", "deactivated"):
        ox, oy = x, 0
        if state in ("active", "hover"):
            parts = box(ox, oy) + (glyph(ox, oy) if glyph else [])
        elif state == "pressed":
            parts = starburst(ox, oy) if pressed == "starburst" else box(ox, oy, filled=True)
        else:  # inactive windows show no boxes, as on the original
            parts = [rect(None, ox, oy, BTN, BTN, None)]
        body += group(f"{state}-center", parts)
        x += BTN + 5
    return svg(x, BTN, body)


def aurorae_rc():
    return f"""[General]
TitleAlignment=Center
TitleVerticalAlignment=Center
Animation=0
ActiveTextColor=0,0,0,255
InactiveTextColor=128,128,128,255
UseTextShadow=false
HaloActive=false
HaloInactive=false
LeftButtons=X
RightButtons=AI
Shadow=false
DecorationPosition=0

[Layout]
BorderLeft={1 * S}
BorderRight={2 * S}
BorderBottom={2 * S}
TitleEdgeTop={1 * S}
TitleEdgeBottom={1 * S}
TitleEdgeLeft={7 * S}
TitleEdgeRight={7 * S}
TitleEdgeTopMaximized={1 * S}
TitleEdgeBottomMaximized={1 * S}
TitleEdgeLeftMaximized={7 * S}
TitleEdgeRightMaximized={7 * S}
TitleBorderLeft={6 * S}
TitleBorderRight={6 * S}
TitleHeight={(TOP_H - 2) * S}
ButtonWidth={BTN * S}
ButtonHeight={BTN * S}
ButtonSpacing={3 * S}
ButtonMarginTop={2 * S}
ButtonMarginTopMaximized={2 * S}
ExplicitButtonSpacer={8 * S}
PaddingTop=0
PaddingBottom=0
PaddingLeft=0
PaddingRight=0
"""


def aurorae_id(scale):
    return THEME_ID if scale == 1 else f"{THEME_ID}-{scale}x"


def aurorae_meta(scale):
    label = f"{THEME_NAME} SVG" if scale == 1 else f"{THEME_NAME} SVG ×{scale}"
    return f"""[Desktop Entry]
Name={label}
Comment=Black-and-white pinstriped window decoration inspired by early-1990s desktops
X-KDE-PluginInfo-Name={aurorae_id(scale)}
X-KDE-PluginInfo-Author=OS7 Pinstripe contributors
X-KDE-PluginInfo-Version={VERSION}
X-KDE-PluginInfo-License=GPL-3.0
"""


def build_aurorae():
    # One theme per scale: KWin caches each theme's geometry in memory, so
    # switching size means switching theme (no logout needed).
    d = OUT / "aurorae" / aurorae_id(S)
    d.mkdir(parents=True)
    (d / "decoration.svg").write_text(decoration_svg())
    (d / "close.svg").write_text(button_svg(None, "starburst"))
    (d / "maximize.svg").write_text(button_svg(zoom_glyph, "fill"))
    (d / "restore.svg").write_text(button_svg(zoom_glyph, "fill"))
    (d / "minimize.svg").write_text(button_svg(collapse_glyph, "fill"))
    (d / "shade.svg").write_text(button_svg(collapse_glyph, "fill"))
    # Aurorae looks for "<theme id>rc"
    (d / f"{aurorae_id(S)}rc").write_text(aurorae_rc())
    (d / "metadata.desktop").write_text(aurorae_meta(S))


# ---------------------------------------------------------------------------
# QML window decoration (Aurorae QML engine): the title plate fits the text
# ---------------------------------------------------------------------------
def qml_id(scale):
    return "os7pinstripe" if scale == 1 else f"os7pinstripe-{scale}x"


def build_qml_decoration():
    d = OUT / "kwin-decorations" / qml_id(S)
    ui = d / "contents" / "ui"
    ui.mkdir(parents=True)
    main = (QML_SRC / "main.qml").read_text().replace("@UNIT@", str(S))
    (ui / "main.qml").write_text(main)
    shutil.copy(QML_SRC / "PinstripeButton.qml", ui / "PinstripeButton.qml")
    label = THEME_NAME if S == 1 else f"{THEME_NAME} ×{S}"
    meta = {
        "KPackageStructure": "KWin/Decoration",
        "KPlugin": {
            "Id": qml_id(S),
            "Name": label,
            "Description": "Black-and-white pinstriped window decoration inspired by early-1990s desktops",
            "Authors": [{"Name": "OS7 Pinstripe contributors"}],
            "License": "GPL-3.0",
            "Version": VERSION,
        },
    }
    (d / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Color scheme (black and white)
# ---------------------------------------------------------------------------
def color_section(name, bg, alt, fg, inactive="128,128,128", active="0,0,0", focus="0,0,0"):
    return f"""[Colors:{name}]
BackgroundAlternate={alt}
BackgroundNormal={bg}
DecorationFocus={focus}
DecorationHover=0,0,0
ForegroundActive={active}
ForegroundInactive={inactive}
ForegroundLink=0,0,204
ForegroundNegative=170,0,0
ForegroundNeutral=153,102,0
ForegroundNormal={fg}
ForegroundPositive=0,119,0
ForegroundVisited=102,0,153

"""


def colors_file(name):
    s = """[ColorEffects:Disabled]
Color=255,255,255
ColorAmount=0
ColorEffect=0
ContrastAmount=0.55
ContrastEffect=1
IntensityAmount=0
IntensityEffect=0

[ColorEffects:Inactive]
ChangeSelectionColor=false
Enable=false

"""
    s += color_section("Button", "255,255,255", "238,238,238", "0,0,0")
    s += color_section("Complementary", "0,0,0", "34,34,34", "255,255,255", "170,170,170")
    s += color_section("Header", "255,255,255", "238,238,238", "0,0,0")
    s += color_section("Selection", "0,0,0", "51,51,51", "255,255,255", "204,204,204",
                       active="255,255,255", focus="255,255,255")
    s += color_section("Tooltip", "255,255,255", "238,238,238", "0,0,0")
    s += color_section("View", "255,255,255", "242,242,242", "0,0,0")
    s += color_section("Window", "255,255,255", "238,238,238", "0,0,0")
    s += f"""[General]
ColorScheme={THEME_ID}
Name={name}
shadeSortColumn=true

[KDE]
contrast=10

[WM]
activeBackground=255,255,255
activeBlend=0,0,0
activeForeground=0,0,0
inactiveBackground=255,255,255
inactiveBlend=128,128,128
inactiveForeground=128,128,128
"""
    return s


def build_colors():
    d = OUT / "color-schemes"
    d.mkdir(parents=True)
    (d / f"{THEME_ID}.colors").write_text(colors_file(THEME_NAME))


# ---------------------------------------------------------------------------
# Plasma Style: menu-bar-like panel, popups with a 1px drop shadow
# ---------------------------------------------------------------------------
def frame_svg(border=1, shadow=0, margin=None):
    """Nine-piece frame with a black outline and an optional offset drop shadow."""
    n = 10  # nominal size of the stretchable pieces
    L = T = border
    R = Bo = border + shadow
    pieces = [
        ("topleft", L, T, [rect(None, 0, 0, L, T, B)]),
        ("top", n, T, [rect(None, 0, 0, n, T, B)]),
        # the offset shadow leaves topright's shadow column clear
        ("topright", R, T, [rect(None, 0, 0, border, T, B)]),
        ("left", L, n, [rect(None, 0, 0, L, n, B)]),
        ("center", n, n, [rect(None, 0, 0, n, n, W)]),
        ("right", R, n, [rect(None, 0, 0, R, n, B)]),
        # ...and bottomleft's shadow row clear
        ("bottomleft", L, Bo, [rect(None, 0, 0, L, border, B)]),
        ("bottom", n, Bo, [rect(None, 0, 0, n, Bo, B)]),
        ("bottomright", R, Bo, [rect(None, 0, 0, R, Bo, B)]),
    ]
    body = ""
    x = 0
    for name, w, h, parts in pieces:
        body += f'<g id="{name}" transform="translate({x * S},0)">\n'
        body += rect(None, 0, 0, w, h, None) + "".join(parts) + "</g>\n"
        x += max(w, n) + 4
    if margin is not None:
        for edge in ("left", "right"):
            body += f'<g id="hint-{edge}-margin" transform="translate({x * S},0)">{rect(None, 0, 0, margin, 1, None)}</g>\n'
            x += margin + 4
        for edge in ("top", "bottom"):
            body += f'<g id="hint-{edge}-margin" transform="translate({x * S},0)">{rect(None, 0, 0, 1, margin, None)}</g>\n'
            x += 6
    return svg(x, n, body)


def build_plasma_style():
    d = OUT / "desktoptheme" / THEME_ID
    (d / "widgets").mkdir(parents=True)
    (d / "dialogs").mkdir()
    meta = {
        "KPlugin": {
            "Id": THEME_ID,
            "Name": THEME_NAME,
            "Description": "Black-and-white Plasma Style with 1px outlines and drop shadows",
            "Authors": [{"Name": "OS7 Pinstripe contributors"}],
            "License": "GPL-3.0",
            "Version": VERSION,
            "Category": "",
        },
        "X-Plasma-API-Minimum-Version": "6.0",
    }
    (d / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    (d / "plasmarc").write_text("[Settings]\nFallbackTheme=default\n")
    (d / "colors").write_text(colors_file(f"{THEME_NAME} (Plasma)"))
    # Panel: white with a black edge (a top panel only shows the bottom edge)
    (d / "widgets" / "panel-background.svg").write_text(frame_svg(1, 0, margin=2))
    # Menus, popups, tooltips, desktop widgets: outline + 1px drop shadow
    (d / "dialogs" / "background.svg").write_text(frame_svg(1, 1, margin=6))
    (d / "widgets" / "tooltip.svg").write_text(frame_svg(1, 1, margin=5))
    (d / "widgets" / "background.svg").write_text(frame_svg(1, 1, margin=8))


# ---------------------------------------------------------------------------
# Wallpapers: tiled checkerboard patterns
# ---------------------------------------------------------------------------
def write_png(path, rows):
    """Write an RGB PNG from a list of rows of (r, g, b) tuples (stdlib only)."""
    h, w = len(rows), len(rows[0])
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in rows)

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def checker(a, b):
    """8x8 checkerboard tile, each cell S x S pixels."""
    n = 8 * S
    return [[a if ((x // S) + (y // S)) % 2 == 0 else b for x in range(n)] for y in range(n)]


def build_wallpapers():
    d = OUT / "wallpapers"
    d.mkdir(parents=True)
    write_png(d / "pattern-bw.png", checker((255, 255, 255), (0, 0, 0)))          # classic 50% dither
    write_png(d / "pattern-gray.png", checker((170, 170, 170), (119, 119, 119)))  # softer gray
    write_png(d / "pattern-violet.png", checker((119, 119, 187), (85, 85, 153)))  # mid-90s color desktop


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scale", type=int, default=1, choices=range(1, 4),
                    help="size of the Plasma Style and wallpapers (default: 1)")
    scale = ap.parse_args().scale
    if OUT.exists():
        shutil.rmtree(OUT)
    for S in (1, 2, 3):
        build_qml_decoration()
        build_aurorae()
    S = scale
    build_colors()
    build_plasma_style()
    build_wallpapers()
    print(f"Theme generated in {OUT}")
