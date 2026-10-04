#!/usr/bin/env python3
"""Render README preview images from the generated theme, without touching KDE.

Needs PySide6 (`sudo dnf install python3-pyside6`) and, for the title font,
ChicagoFLF installed. Run generate.py first.

    python3 generate.py && python3 tools/render_previews.py

Windows are drawn with the same geometry as src/decoration/main.qml (the QML
engine); the boxes come from the generated button SVGs, which are identical.
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
        self.btn = {k: QSvgRenderer(str(d / f"{k}.svg")) for k in ("close", "maximize", "minimize")}

    def draw(self, painter, x, y, cw, ch, title, active=True, pressed_close=False):
        """Draw a window whose client area is cw x ch at (x, y), like main.qml."""
        u = self.s
        black, white = QColor(0, 0, 0), QColor(255, 255, 255)
        bl, br, bb, bt = u, 2 * u, 2 * u, 19 * u
        w, h = cw + bl + br, ch + bt + bb
        fw, fh = w - u, h - u                      # frame without the drop shadow
        painter.fillRect(QRectF(x + u, y + u, w - u, h - u), black)      # shadow
        painter.fillRect(QRectF(x, y, fw, fh), black)                     # outline
        painter.fillRect(QRectF(x + u, y + u, fw - 2 * u, fh - 2 * u), white)
        painter.fillRect(QRectF(x, y + bt - u, fw, u), black)            # separator
        tx, ty, tw, th = x, y + u, fw, 17 * u                             # title bar
        if active:
            for i in range(6):
                painter.fillRect(QRectF(tx + 2 * u, ty + (3 + 2 * i) * u, tw - 4 * u, u), black)
        # boxes: close on the left; zoom + collapse on the right
        bs, by = 13 * u, ty + 2 * u
        lx = tx + 7 * u
        right_w = 2 * bs + 3 * u
        rx = tx + tw - 6 * u - right_w
        if active:
            self.btn["close"].render(painter, "pressed-center" if pressed_close else "active-center",
                                     QRectF(lx, by, bs, bs))
            self.btn["maximize"].render(painter, "active-center", QRectF(rx, by, bs, bs))
            self.btn["minimize"].render(painter, "active-center", QRectF(rx + bs + 3 * u, by, bs, bs))
        # caption: centered, kept clear of the boxes, on a plate as wide as the text
        font = QFont("ChicagoFLF")
        font.setPixelSize(round(FONT_PT[u] * 96 / 72))
        fm = QFontMetrics(font)
        left_limit, right_limit = lx + bs + 8 * u, rx - 8 * u
        avail = max(0, right_limit - left_limit)
        text = fm.elidedText(title, Qt.ElideMiddle, int(avail))
        text_w = min(fm.horizontalAdvance(text), avail)
        cx = round(max(left_limit, min(right_limit - text_w, tx + (tw - text_w) / 2)))
        if active:
            painter.fillRect(QRectF(cx - 6 * u, ty, text_w + 12 * u, th), white)
        painter.setFont(font)
        painter.setPen(black if active else QColor(128, 128, 128))
        painter.drawText(QRectF(cx, ty, text_w, th), Qt.AlignLeft | Qt.AlignVCenter, text)
        # a little client content
        body = QFont("Noto Sans")
        body.setPixelSize(13 * u)
        painter.setFont(body)
        painter.setPen(black)
        painter.drawText(QRectF(x + bl + 10 * u, y + bt + 8 * u, cw - 20 * u, ch - 16 * u),
                         Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, "The quick brown fox.")
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


def long_title_image():
    """The same long title in a wide and in a narrow window (scale 2)."""
    d = Deco(2)
    img = QImage(1000, 260, QImage.Format_RGB32)
    p = QPainter(img)
    wallpaper(p, QRectF(0, 0, 1000, 260))
    title = "user@host:~/projects/os7-pinstripe — a rather long window title"
    d.draw(p, 30, 20, 930, 60, title)
    d.draw(p, 30, 140, 420, 60, title)
    p.end()
    img.save(str(OUT / "long-title.png"))


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
    long_title_image()
    print(f"Previews written to {OUT}")
