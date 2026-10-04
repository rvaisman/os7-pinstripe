#!/usr/bin/env python3
"""Render README preview images from the generated SVGs, without touching KDE.

Needs PySide6 (`sudo dnf install python3-pyside6`) and, for the title font,
ChicagoFLF installed. Run generate.py first.

    python3 generate.py && python3 tools/render_previews.py

The window layout mimics Aurorae v2 with the default "Normal" border size.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
OUT = ROOT / "docs" / "screenshots"
FONT_PT = {1: 13, 2: 18, 3: 26}


class Deco:
    def __init__(self, scale):
        self.s = scale
        name = "OS7Pinstripe" if scale == 1 else f"OS7Pinstripe-{scale}x"
        d = BUILD / "aurorae" / name
        self.frame = QSvgRenderer(str(d / "decoration.svg"))
        self.btn = {k: QSvgRenderer(str(d / f"{k}.svg")) for k in ("close", "maximize", "minimize")}

    def piece(self, painter, prefix, name, rect):
        self.frame.render(painter, f"{prefix}-{name}", rect)

    def draw(self, painter, x, y, cw, ch, title, active=True, pressed_close=False):
        """Draw a window whose client area is cw x ch at (x, y); return outer rect."""
        s = self.s
        # Aurorae v2 clamps side borders to the "Normal" border size range (4-6 px)
        bl, br, bb = (min(max(v, 4), 6) for v in (1 * s, 2 * s, 2 * s))
        bt = 19 * s
        w, h = cw + bl + br, ch + bt + bb
        prefix = "decoration" if active else "decoration-inactive"
        el = lambda n: self.frame.boundsOnElement(f"{prefix}-{n}")
        L, R = el("left").width(), el("right").width()
        T, Bo = el("top").height(), el("bottom").height()
        # nine-slice frame (stretched pieces), the center covers the whole inside
        self.piece(painter, prefix, "center", QRectF(x + L, y + T, w - L - R, h - T - Bo))
        self.piece(painter, prefix, "topleft", QRectF(x, y, L, T))
        self.piece(painter, prefix, "top", QRectF(x + L, y, w - L - R, T))
        self.piece(painter, prefix, "topright", QRectF(x + w - R, y, R, T))
        self.piece(painter, prefix, "left", QRectF(x, y + T, L, h - T - Bo))
        self.piece(painter, prefix, "right", QRectF(x + w - R, y + T, R, h - T - Bo))
        self.piece(painter, prefix, "bottomleft", QRectF(x, y + h - Bo, L, Bo))
        self.piece(painter, prefix, "bottom", QRectF(x + L, y + h - Bo, w - L - R, Bo))
        self.piece(painter, prefix, "bottomright", QRectF(x + w - R, y + h - Bo, R, Bo))
        # buttons
        bs, by = 13 * s, y + 3 * s
        state = "active" if active else "inactive"
        close_state = "pressed" if (active and pressed_close) else state
        left_end = x + 7 * s + bs
        self.btn["close"].render(painter, f"{close_state}-center", QRectF(x + 7 * s, by, bs, bs))
        rx = x + w - 7 * s - bs
        self.btn["minimize"].render(painter, f"{state}-center", QRectF(rx, by, bs, bs))
        rx -= 3 * s + bs
        self.btn["maximize"].render(painter, f"{state}-center", QRectF(rx, by, bs, bs))
        # centered caption
        font = QFont("ChicagoFLF")
        font.setPixelSize(round(FONT_PT[s] * 96 / 72))
        painter.setFont(font)
        painter.setPen(QColor(0, 0, 0) if active else QColor(128, 128, 128))
        cap = QRectF(left_end + 6 * s, y + s, rx - left_end - 12 * s, 17 * s)
        text = QFontMetrics(font).elidedText(title, Qt.ElideMiddle, int(cap.width()))
        painter.drawText(cap, Qt.AlignCenter, text)
        # a little client content
        body = QFont("Noto Sans")
        body.setPixelSize(13 * s)
        painter.setFont(body)
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(QRectF(x + bl + 10 * s, y + bt + 8 * s, cw - 20 * s, ch - 16 * s),
                         Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                         "The quick brown fox.")
        return QRectF(x, y, w, h)


def wallpaper(painter, rect, scale=1):
    tile = QPixmap(str(BUILD / "wallpapers" / "pattern-gray.png"))
    if tile.isNull():
        painter.fillRect(rect, QColor(150, 150, 150))
    else:
        painter.drawTiledPixmap(rect, tile)


def scales_image():
    """Each scale drawn at its real pixel size; windows grow with the scale,
    as they would on a screen that needs that scale."""
    width = 1240
    rows = [(s, 34 + 14 * s + 19 * s + 64 * s + 30) for s in (1, 2, 3)]
    height = sum(h for _, h in rows) + 20
    img = QImage(width, height, QImage.Format_RGB32)
    p = QPainter(img)
    wallpaper(p, QRectF(0, 0, width, height))
    y = 20
    for s, h in rows:
        d = Deco(s)
        p.setFont(QFont("Noto Sans", 11, QFont.Bold))
        p.fillRect(QRectF(20, y, 270, 24), QColor(255, 255, 255))
        p.setPen(QColor(0, 0, 0))
        p.drawRect(QRectF(20, y, 270, 24))
        p.drawText(QRectF(28, y, 260, 24), Qt.AlignVCenter, f"--scale {s}  ·  title bar {19 * s} px")
        top = y + 34
        aw = 340 * s
        d.draw(p, 40, top + 14 * s, int(aw * 0.75), 40 * s, "Notes", active=False)
        d.draw(p, width - 40 - aw, top, aw, 40 * s, "Untitled — Editor", active=True)
        y += h
    p.end()
    img.save(str(OUT / "scales.png"))


def buttons_image():
    """The title bar widgets, magnified 8x."""
    s, z = 1, 8
    d = Deco(s)
    cell = 13 * z
    labels = [("close", "active", "Close"), ("close", "pressed", "Close (pressed)"),
              ("maximize", "active", "Zoom (maximize)"), ("minimize", "active", "Collapse (minimize)")]
    img = QImage(len(labels) * (cell + 60) + 40, cell + 70, QImage.Format_RGB32)
    img.fill(QColor(255, 255, 255))
    p = QPainter(img)
    small = QImage(13, 13, QImage.Format_ARGB32)
    x = 30
    for btn, state, text in labels:
        small.fill(Qt.transparent)
        sp = QPainter(small)
        d.btn[btn].render(sp, f"{state}-center", QRectF(0, 0, 13, 13))
        sp.end()
        big = small.scaled(cell, cell, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        p.drawImage(x, 20, big)
        p.setPen(QColor(0, 0, 0))
        p.setFont(QFont("Noto Sans", 10))
        p.drawText(QRectF(x - 20, 25 + cell, cell + 40, 30), Qt.AlignCenter, text)
        x += cell + 60
    p.end()
    img.save(str(OUT / "buttons.png"))


def titlebar_zoom_image():
    """A 1x title bar magnified 4x, to show the pixel pattern."""
    s, z = 1, 4
    d = Deco(s)
    img = QImage(300, 50, QImage.Format_ARGB32)
    img.fill(QColor(255, 255, 255))
    p = QPainter(img)
    d.draw(p, 0, 0, 294, 25, "Untitled", active=True)
    p.end()
    img = img.copy(0, 0, 300, 24).scaled(1200, 96, Qt.IgnoreAspectRatio, Qt.FastTransformation)
    img.save(str(OUT / "titlebar-zoom.png"))


if __name__ == "__main__":
    if not (BUILD / "aurorae").exists():
        sys.exit("Run generate.py first.")
    app = QGuiApplication(sys.argv)
    OUT.mkdir(parents=True, exist_ok=True)
    scales_image()
    buttons_image()
    titlebar_zoom_image()
    print(f"Previews written to {OUT}")
