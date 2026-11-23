#!/usr/bin/env python3
"""news-image-20261123: one 1024x1024 newspaper page summing up the world's
news of Monday 23 November 2026.

Standard library only. Reads the fresh bitmap font atlases in fonts/ (built
this session by tools/gen_font.py from system DejaVu TTFs), draws the whole
page procedurally, and writes a deterministic PNG to /output/entry.png
(or $MAKEFUN_OUTPUT_DIR/entry.png).

ALL content lives in the data lists at the top of this file (HEROES, GRID,
NUMBERS, BRIEFS, DATECHECK). A content patch is a text edit to those lists.
"""

import binascii
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024

# --------------------------------------------------------------------------
# CONTENT (wave 1, verified 23 Nov 2026 by the coordinator; see
# news-brief-20261123.md). Only verified items are included: every brief
# flagged [VERIFY wave 2] in the brief is deliberately absent from v1.
# --------------------------------------------------------------------------

MASTHEAD = "THE WORLD IN ONE PAGE"
DATE_LINE = "MONDAY, 23 NOVEMBER 2026"

# Heroes: num, region, kicker, headline, body, art key, pin (lon, lat).
HEROES = [
    {
        "num": 1, "region": "WORLD",
        "kicker": "CLIMATE \u00b7 ANTALYA + SYDNEY",
        "headline": "COP31 failed. The fallout begins",
        "body": ("Albanese blames 'difficult geopolitical times'. The draft "
                 "never named fossil fuels, so the EU rejected it \u2014 the "
                 "first collapse since 2009."),
        "art": "globe", "pin": (30.7, 36.9),
    },
    {
        "num": 2, "region": "ASIA-PACIFIC",
        "kicker": "MARKETS \u00b7 ASIA",
        "headline": "Asia steadies after Friday's rout",
        "body": ("Kospi fell 2.8% at the open as Seoul readied a "
                 "stabilisation fund; the ASX erased early losses. US "
                 "futures rebounded; gold rose to $3,577."),
        "art": "chart", "pin": (151.2, -33.9),
    },
    {
        "num": 3, "region": "ASIA-PACIFIC",
        "kicker": "NORTH KOREA \u00b7 PYONGYANG",
        "headline": "'Security, not supremacy,' says Kim",
        "body": ("KCNA: Kim's first credentials ceremony in 30 years \u2014 "
                 "ten new ambassadors, Russia and Sweden among them. No "
                 "mention of the US."),
        "art": "podium", "pin": (125.8, 39.0),
    },
]

# Grid: num, region, kicker, headline, body, art key, pin (lon, lat).
GRID = [
    {
        "num": 4, "region": "ASIA-PACIFIC", "kicker": "NEPAL\u2013INDIA",
        "headline": "Shah meets Modi in New Delhi",
        "body": ("Nepal's PM holds delegation talks in Delhi; MoUs and a "
                 "$2bn aid ask."),
        "art": "flags", "pin": (77.2, 28.6),
    },
    {
        "num": 5, "region": "ASIA-PACIFIC", "kicker": "INDONESIA",
        "headline": "Search goes on at candy factory",
        "body": ("Teams sift the gutted Milkita plant in Cikande: 7 dead, "
                 "~50 unaccounted for."),
        "art": "flame", "pin": (106.3, -6.0),
    },
    {
        "num": 6, "region": "EUROPE", "kicker": "FINLAND",
        "headline": "Russian ship burns off Finland",
        "body": ("The sanctioned Sparta II still burns after a weekend drone "
                 "strike; crew evacuated."),
        "art": "ship", "pin": (26.0, 60.0),
    },
    {
        "num": 7, "region": "EUROPE", "kicker": "UKRAINE",
        "headline": "14 still missing in Dymer",
        "body": ("Search goes on at a collapsed block north of Kyiv; "
                 "3 killed, 14 still missing."),
        "art": "building", "pin": (30.2, 50.8),
    },
    {
        "num": 8, "region": "AMERICAS", "kicker": "USA",
        "headline": "Fury at Sea-Tac ICE arrests",
        "body": ("A senator-elect calls 'outrageous' the detention of a "
                 "father and daughter."),
        "art": "plane", "pin": (-122.3, 47.6),
    },
    {
        "num": 9, "region": "AMERICAS", "kicker": "USA",
        "headline": "FBI incident confirmed",
        "body": ("Intelligence chief Clayton confirms a Sunday incident at "
                 "the FBI; urges upgrades."),
        "art": "fbi", "pin": (-77.0, 38.9),
    },
    {
        "num": 10, "region": "AFRICA", "kicker": "LIBYA",
        "headline": "UN urges Benghazi probe",
        "body": ("The UN wants an inquiry into Benghazi attacks, incl. a "
                 "blast on a Russian ship."),
        "art": "flag", "pin": (20.1, 32.1),
    },
    {
        "num": 11, "region": "EUROPE", "kicker": "OBITUARY",
        "headline": "Paolo Bulgari dies, 89",
        "body": ("The Italian jeweller and businessman has died aged 89, "
                 "the BBC reports."),
        "art": "diamond", "pin": (12.5, 41.9),
    },
    {
        "num": 12, "region": "ASIA-PACIFIC", "kicker": "BUSINESS",
        "headline": "Hello Kitty bets on games",
        "body": ("Sanrio turns to games to expand Hello Kitty's global "
                 "reach, Nikkei Asia reports."),
        "art": "kitty", "pin": (139.7, 35.7),
    },
    {
        "num": 13, "region": "OCEANIA", "kicker": "CRICKET",
        "headline": "India close in Wellington",
        "body": ("New Zealand, 119/2 and 233 behind, bat to save the Test "
                 "on the final day."),
        "art": "cricket", "pin": (174.8, -41.3),
    },
]

# Number strip: (big value, small label).
NUMBERS = [
    ("$150M", "AUSTRALIA'S COP31 SPEND, FOR NO DEAL"),
    ("0", "FOSSIL-FUEL MENTIONS IN THE FINAL DRAFT"),
    ("\u22125.3%", "NASDAQ, FRIDAY"),
    ("+2.8%", "NASDAQ 100 FUTURES, MONDAY"),
    ("$3,577", "GOLD AN OUNCE, MONDAY (+1.1%)"),
]

# Briefs: (kicker, text, region). Verified Monday items only.
BRIEFS = [
    ("OKINAWA", "Restored castle to reopen with extensive fire safety measures.",
     "ASIA-PACIFIC"),
    ("JAPAN", "Decarbonization agency invests in a US metal recycling startup.",
     "ASIA-PACIFIC"),
    ("ISRAEL", "Ben-Gvir increases funding for four new firefighting helicopters.",
     "MIDDLE EAST"),
    ("INDIA", "Tata Sons to decide on going public this week.", "ASIA-PACIFIC"),
    ("INDIA\u2013NETHERLANDS",
     "Jaishankar and Dutch FM Berendsen review strategic partnership roadmap.",
     "ASIA-PACIFIC"),
    ("INDIA", "JEE Main 2027 Session 1 registration closes today.", "ASIA-PACIFIC"),
    ("USA", "El-Sayed and Van Hollen press a curb on Iran war funding.", "AMERICAS"),
    ("USA", "Ex-White House chief of staff urges Democrats to repeal tariff rises.",
     "AMERICAS"),
    ("MISS UNIVERSE", "116 women compete; the 75th pageant is in San Juan on Tuesday.",
     "AMERICAS"),
]

# DATE CHECK: real stories deliberately left out because they are NOT 23 Nov.
DATECHECK = [
    "COP31 collapse (Sun)",
    "Houthi Rabigh claim (Sun)",
    "Dymer strike (Sun)",
    "'El Chapo Isidro' captured (Fri)",
    "California concert shooting (Sat)",
    "ICE detention, Seattle (Sat)",
    "UN 'killer robots' talks (Sat)",
    "South Sudan, 24 killed (Sat\u2013Sun)",
    "India 720/9 declared (Sun)",
    "FIDE opening ceremony (Sun)",
    "S. Korea education minister quits (Sun)",
    "Netanyahu\u2013Eisenkot talks fail (Sun)",
    "Two tankers struck, Hormuz (Sat)",
    "Democrats' House majority (3 Nov)",
]

SOURCES = ("Sources: AFP \u00b7 BBC \u00b7 IANS \u00b7 KCNA via AFP \u00b7 MarketIndex "
           "\u00b7 Nikkei Asia \u00b7 Jerusalem Post \u00b7 Arab News \u00b7 Reuters "
           "\u00b7 ISW \u00b7 CricketNews")

REGION_COLORS = {
    "EUROPE": (30, 90, 180),
    "AMERICAS": (190, 40, 40),
    "ASIA-PACIFIC": (30, 140, 80),
    "MIDDLE EAST": (130, 60, 160),
    "AFRICA": (0, 150, 150),
    "OCEANIA": (30, 120, 60),
    "WORLD": (90, 90, 90),
}

# Badge offsets (dx, dy) for map pins whose true spots would collide.
PIN_OFFSETS = {6: (-13, -9), 7: (11, 9), 11: (-11, -8)}

# Schematic dotted world map: land spans per row. Row r covers latitude
# 77.5 - 5*r (centre); column c covers longitude -177.5 + 5*c (centre).
# Each tuple is (row, first col, last col) of land, authored from a world map.
MAP_SPANS = [
    (0, 11, 16), (0, 26, 30), (0, 48, 52), (0, 60, 66),
    (1, 3, 8), (1, 11, 19), (1, 25, 32), (1, 48, 71),
    (2, 3, 8), (2, 8, 24), (2, 27, 30), (2, 39, 42), (2, 44, 71),
    (3, 3, 25), (3, 31, 33), (3, 37, 42), (3, 42, 71),
    (4, 9, 25), (4, 35, 36), (4, 37, 42), (4, 42, 71),
    (5, 11, 25), (5, 35, 44), (5, 44, 64), (5, 67, 68),
    (6, 11, 22), (6, 35, 44), (6, 45, 63),
    (7, 11, 22), (7, 34, 42), (7, 42, 53), (7, 53, 62), (7, 64, 65),
    (8, 12, 21), (8, 34, 43), (8, 43, 48), (8, 51, 60), (8, 61, 64),
    (9, 12, 20), (9, 34, 43), (9, 43, 48), (9, 48, 54), (9, 54, 60), (9, 62, 64),
    (10, 13, 18), (10, 32, 43), (10, 43, 47), (10, 49, 53), (10, 55, 57),
    (10, 60, 60),
    (11, 15, 18), (11, 32, 42), (11, 44, 47), (11, 50, 53), (11, 55, 57),
    (11, 57, 60),
    (12, 17, 19), (12, 32, 43), (12, 44, 47), (12, 50, 52), (12, 55, 57),
    (13, 17, 20), (13, 20, 26), (13, 32, 44), (13, 51, 51), (13, 55, 57),
    (13, 60, 60),
    (14, 20, 29), (14, 33, 45), (14, 55, 60), (14, 62, 65),
    (15, 20, 29), (15, 34, 45), (15, 55, 64), (15, 62, 66),
    (16, 20, 29), (16, 34, 44), (16, 56, 64), (16, 63, 66),
    (17, 20, 29), (17, 37, 44), (17, 57, 63), (17, 62, 64),
    (18, 20, 28), (18, 38, 44), (18, 44, 46), (18, 58, 65),
    (19, 21, 28), (19, 38, 43), (19, 44, 46), (19, 58, 66),
    (20, 21, 27), (20, 38, 42), (20, 58, 66),
    (21, 22, 26), (21, 39, 42), (21, 59, 66),
    (22, 21, 25), (22, 39, 42), (22, 59, 66), (22, 69, 71),
    (23, 21, 24), (23, 64, 66), (23, 69, 71),
    (24, 21, 24), (24, 65, 65), (24, 69, 70),
    (25, 21, 23),
    (26, 21, 23),
    (27, 22, 23),
]

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------
PAPER = (250, 248, 242)
INK = (22, 22, 22)
RED = (178, 34, 34)
DARKRED = (140, 25, 25)
BLUE = (30, 70, 140)
GREY = (110, 108, 100)
HAIR = (200, 196, 186)
BANNER_DARK = (26, 38, 58)
MAP_BG = (226, 236, 244)
MAP_DOT = (150, 160, 140)
WHITE = (255, 255, 255)

# --------------------------------------------------------------------------
# Bitmap fonts (BFN1 format, written by tools/gen_font.py)
# --------------------------------------------------------------------------


class Font:
    def __init__(self, stem):
        path = os.path.join(HERE, "fonts", stem + ".bin")
        with open(path, "rb") as fh:
            data = fh.read()
        assert data[:4] == b"BFN1", path
        size, ascent, descent, count = struct.unpack_from("<HHHH", data, 4)
        self.size = size
        self.ascent = ascent
        self.descent = descent
        self.glyphs = {}
        off = 12
        entries = []
        for _ in range(count):
            cp, adv, ox, oy, w, h = struct.unpack_from("<I H h h H H", data, off)
            off += 14
            entries.append((cp, adv, ox, oy, w, h))
        for cp, adv, ox, oy, w, h in entries:
            n = w * h
            self.glyphs[cp] = (adv, ox, oy, w, h, data[off:off + n])
            off += n

    def glyph(self, ch):
        g = self.glyphs.get(ord(ch))
        if g is None:
            g = self.glyphs[ord("?")]
        return g

    def width(self, text):
        return sum(self.glyph(ch)[0] for ch in text)

    def wrap(self, text, max_w):
        """Greedy word wrap; returns a list of lines."""
        lines = []
        for para in text.split("\n"):
            words = para.split(" ")
            cur = ""
            for word in words:
                trial = word if not cur else cur + " " + word
                if self.width(trial) <= max_w:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    # Hard-split a single overlong word.
                    while self.width(word) > max_w and len(word) > 1:
                        cut = len(word) - 1
                        while cut > 1 and self.width(word[:cut]) > max_w:
                            cut -= 1
                        lines.append(word[:cut])
                        word = word[cut:]
                    cur = word
            if cur or not lines:
                lines.append(cur)
        return lines


FONTS = {}


def F(stem):
    if stem not in FONTS:
        FONTS[stem] = Font(stem)
    return FONTS[stem]


# --------------------------------------------------------------------------
# Canvas: RGB bytearray + drawing primitives + text
# --------------------------------------------------------------------------


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.rect(0, 0, w, h, bg)

    def _idx(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._idx(x, y)
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = self._idx(x0, yy)
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if thick <= 1:
                self.set(x0, y0, color)
            else:
                r = thick // 2
                self.rect(x0 - r, y0 - r, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=True):
        if r <= 0:
            return
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, color)
                else:
                    if r * r - 2 * r <= d2 <= r * r:
                        self.set(xx, yy, color)

    def triangle(self, p0, p1, p2, color):
        """Filled triangle via scanline fill."""
        pts = sorted([p0, p1, p2], key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts
        if y0 == y2:
            return
        for y in range(y0, y2 + 1):
            if y < y1:
                t1 = 0 if y1 == y0 else (y - y0) / (y1 - y0)
                xa = x0 + (x1 - x0) * t1
            else:
                t1 = 0 if y2 == y1 else (y - y1) / (y2 - y1)
                xa = x1 + (x2 - x1) * t1
            t2 = (y - y0) / (y2 - y0)
            xb = x0 + (x2 - x0) * t2
            xa, xb = sorted((int(round(xa)), int(round(xb))))
            for x in range(xa, xb + 1):
                self.set(x, y, color)

    def polyline(self, pts, color, thick=1):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], color, thick)

    def text(self, font, x, y_baseline, s, color):
        """Draw text with pen at (x, baseline y). Returns end x."""
        pen = x
        for ch in s:
            adv, ox, oy, w, h, bmp = font.glyph(ch)
            if w and h:
                gx, gy = pen + ox, y_baseline + oy
                for yy in range(h):
                    py = gy + yy
                    if py < 0 or py >= self.h:
                        continue
                    row = yy * w
                    for xx in range(w):
                        a = bmp[row + xx]
                        if a == 0:
                            continue
                        px = gx + xx
                        if px < 0 or px >= self.w:
                            continue
                        i = self._idx(px, py)
                        if a == 255:
                            self.px[i] = color[0]
                            self.px[i + 1] = color[1]
                            self.px[i + 2] = color[2]
                        else:
                            self.px[i] = (color[0] * a + self.px[i] * (255 - a)) // 255
                            self.px[i + 1] = (color[1] * a + self.px[i + 1] * (255 - a)) // 255
                            self.px[i + 2] = (color[2] * a + self.px[i + 2] * (255 - a)) // 255
            pen += adv
        return pen

    def text_center(self, font, cx, y_baseline, s, color):
        self.text(font, cx - font.width(s) // 2, y_baseline, s, color)

    def text_right(self, font, x_right, y_baseline, s, color):
        self.text(font, x_right - font.width(s), y_baseline, s, color)


# --------------------------------------------------------------------------
# PNG writer (stdlib zlib; filter 0 scanlines; deterministic)
# --------------------------------------------------------------------------


def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


# --------------------------------------------------------------------------
# Procedural banner art
# --------------------------------------------------------------------------


def art_globe(cv, x, y, w, h):
    """COP31: a cracked globe under a NO DEAL tag."""
    cv.rect(x, y, w, h, BANNER_DARK)
    cx, cy, r = x + 44, y + h // 2 + 2, 20
    cv.circle(cx, cy, r, (96, 160, 220))
    cv.circle(cx - 6, cy - 5, 6, (120, 190, 130))
    cv.circle(cx + 7, cy + 7, 5, (120, 190, 130))
    cv.circle(cx + 4, cy - 9, 3, (120, 190, 130))
    cv.line(cx - r, cy, cx + r, cy, (70, 130, 190))
    cv.line(cx, cy - r, cx, cy + r, (70, 130, 190))
    # Crack.
    cv.polyline([(cx - 12, cy - 18), (cx - 4, cy - 6), (cx - 9, cy + 4),
                 (cx + 2, cy + 12), (cx - 2, cy + 19)], (220, 60, 60), 2)
    # NO DEAL tag.
    tag = "NO DEAL"
    f = F("sans-bold-14")
    tw = f.width(tag)
    tx = x + w - tw - 28
    ty = y + h // 2 - 11
    cv.rect(tx - 8, ty - 2, tw + 16, 24, RED)
    cv.text(f, tx, ty + 15, tag, WHITE)
    # Empty chairs row along the bottom.
    for i in range(7):
        sx = x + 96 + i * 16
        cv.rect(sx, y + h - 12, 10, 8, (70, 90, 120))
        cv.rect(sx + 1, y + h - 18, 8, 6, (70, 90, 120))


def art_chart(cv, x, y, w, h):
    """Markets: Friday cliff, then a Monday recovery line."""
    cv.rect(x, y, w, h, (24, 28, 34))
    # Grid.
    for gy in (y + 12, y + 26, y + 40):
        cv.hline(x + 8, gy, w - 16, (52, 58, 66))
    pts_down = [(x + 10, y + 10), (x + 60, y + 14), (x + 110, y + 18),
                (x + 150, y + 34), (x + 185, y + 44)]
    pts_up = [(x + 185, y + 44), (x + 225, y + 38), (x + 265, y + 36),
              (x + 305, y + 30)]
    cv.polyline(pts_down, (220, 70, 70), 3)
    cv.polyline(pts_up, (90, 200, 120), 3)
    cv.circle(pts_down[-1][0], pts_down[-1][1], 3, (220, 70, 70))
    cv.circle(pts_up[-1][0], pts_up[-1][1], 3, (90, 200, 120))
    f = F("sans-bold-11")
    cv.text(f, x + 26, y + 24, "FRI", (220, 120, 120))
    cv.text(f, x + 250, y + 24, "MON", (140, 220, 160))
    # Down arrow then up arrow.
    cv.triangle((x + 168, y + 16), (x + 178, y + 16), (x + 173, y + 24),
                (220, 70, 70))
    cv.triangle((x + 282, y + 24), (x + 292, y + 24), (x + 287, y + 16),
                (90, 200, 120))


def art_podium(cv, x, y, w, h):
    """Kim: a row of flags over a podium."""
    cv.rect(x, y, w, h, (58, 28, 34))
    flag_colors = [(200, 40, 40), (40, 90, 200), (220, 180, 40),
                   (40, 160, 80), (200, 120, 40), (140, 60, 180)]
    for i, fc in enumerate(flag_colors):
        fx = x + 18 + i * 48
        cv.vline(fx, y + 6, 20, (200, 200, 200), 2)
        cv.rect(fx + 2, y + 6, 26, 13, fc)
    # Podium.
    px, py = x + w // 2, y + h - 4
    cv.triangle((px - 46, py), (px + 46, py), (px - 30, y + 30), (120, 100, 80))
    cv.triangle((px + 46, py), (px - 30, y + 30), (px + 30, y + 30),
                (120, 100, 80))
    cv.rect(px - 34, y + 28, 68, 5, (150, 130, 100))
    cv.line(px - 8, y + 28, px - 14, y + 18, (220, 220, 220), 2)
    cv.circle(px - 15, y + 16, 3, (220, 220, 220))


def art_flags(cv, x, y, w, h):
    """Nepal + India flags."""
    cv.rect(x, y, w, h, (238, 238, 230))
    # Nepal (crimson pennant pair, simplified as a triangle).
    cv.triangle((x + 52, y + 3), (x + 52, y + h - 3), (x + 78, y + h // 2 - 2),
                (200, 40, 60))
    cv.triangle((x + 52, y + 3), (x + 52, y + h - 3), (x + 78, y + h // 2 + 4),
                (200, 40, 60))
    cv.circle(x + 60, y + 9, 3, WHITE)
    # India tricolour.
    ix = x + 108
    cv.rect(ix, y + 3, 34, 6, (230, 140, 40))
    cv.rect(ix, y + 9, 34, 6, WHITE)
    cv.rect(ix, y + 15, 34, 6, (30, 140, 60))
    cv.circle(ix + 17, y + 12, 3, (30, 70, 160))


def art_flame(cv, x, y, w, h):
    """Factory fire: flames over a dark building."""
    cv.rect(x, y, w, h, (40, 30, 26))
    cv.rect(x + 20, y + 12, w - 40, h - 12, (70, 60, 55))
    for wx in range(x + 30, x + w - 30, 18):
        cv.rect(wx, y + 16, 8, 7, (230, 180, 60))
    cx = x + w // 2
    cv.triangle((cx - 16, y + 16), (cx + 16, y + 16), (cx, y + 1),
                (240, 120, 30))
    cv.triangle((cx - 9, y + 16), (cx + 9, y + 16), (cx, y + 6),
                (250, 210, 80))
    cv.triangle((cx - 34, y + 16), (cx - 20, y + 16), (cx - 27, y + 5),
                (240, 120, 30))
    cv.triangle((cx + 20, y + 16), (cx + 34, y + 16), (cx + 27, y + 5),
                (240, 120, 30))


def art_ship(cv, x, y, w, h):
    """Burning cargo ship at sea."""
    cv.rect(x, y, w, h, (70, 100, 130))
    cv.rect(x, y + h - 8, w, 8, (30, 70, 110))
    # Hull.
    cv.triangle((x + 30, y + 14), (x + w - 30, y + 14), (x + 44, y + h - 6),
                (40, 40, 44))
    cv.triangle((x + w - 30, y + 14), (x + 44, y + h - 6),
                (x + w - 44, y + h - 6), (40, 40, 44))
    # Containers + bridge.
    cv.rect(x + 60, y + 6, 26, 8, (200, 80, 50))
    cv.rect(x + 90, y + 6, 26, 8, (60, 160, 90))
    cv.rect(x + 130, y + 4, 12, 10, (220, 220, 220))
    # Fire + smoke.
    cv.triangle((x + 66, y + 8), (x + 80, y + 8), (x + 73, y - 1),
                (250, 160, 40))
    cv.circle(x + 150, y + 2, 4, (120, 120, 120))
    cv.circle(x + 158, y + 5, 5, (140, 140, 140))


def art_building(cv, x, y, w, h):
    """Collapsed apartment block, smoke rising."""
    cv.rect(x, y, w, h, (200, 205, 210))
    bx, bw = x + 55, 80
    cv.rect(bx, y + 8, bw, h - 8, (120, 125, 135))
    # Jagged broken top.
    cv.polyline([(bx, y + 10), (bx + 16, y + 4), (bx + 30, y + 11),
                 (bx + 46, y + 5), (bx + 62, y + 12), (bx + bw, y + 6)],
                (90, 95, 105), 2)
    for wy in (y + 14, y + 20):
        for wx in range(bx + 8, bx + bw - 8, 16):
            cv.rect(wx, wy, 8, 5, (60, 65, 75))
    # Smoke.
    cv.circle(x + 150, y + 4, 4, (150, 150, 150))
    cv.circle(x + 158, y + 8, 5, (160, 160, 160))
    cv.circle(x + 142, y + 8, 3, (150, 150, 150))


def art_plane(cv, x, y, w, h):
    """Airliner on a jet bridge."""
    cv.rect(x, y, w, h, (150, 195, 230))
    cv.rect(x, y + h - 6, w, 6, (120, 125, 130))
    cx, cy = x + w // 2, y + h // 2 - 1
    # Fuselage + wings + tail.
    cv.line(cx - 52, cy, cx + 52, cy, WHITE, 4)
    cv.line(cx - 10, cy - 12, cx + 14, cy + 10, WHITE, 4)
    cv.line(cx + 40, cy - 10, cx + 52, cy, WHITE, 3)
    cv.line(cx + 40, cy + 8, cx + 52, cy, WHITE, 3)
    # Jet bridge.
    cv.rect(x + 8, y + h - 14, 26, 5, (90, 95, 105))
    cv.vline(x + 30, y + h - 14, 8, (90, 95, 105), 3)


def art_fbi(cv, x, y, w, h):
    """Headquarters building + magnifier."""
    cv.rect(x, y, w, h, (36, 54, 96))
    cv.rect(x + 45, y + 8, 90, h - 8, (210, 210, 200))
    cv.triangle((x + 40, y + 9), (x + 140, y + 9), (x + 90, y + 1),
                (180, 180, 170))
    for px in range(x + 55, x + 130, 16):
        cv.vline(px, y + 13, h - 15, (120, 120, 115), 3)
    cv.circle(x + 160, y + 9, 6, (250, 210, 80), fill=False)
    cv.line(x + 165, y + 14, x + 172, y + 21, (250, 210, 80), 2)


def art_flag(cv, x, y, w, h):
    """UN-style flag + alert."""
    cv.rect(x, y, w, h, (232, 222, 190))
    cv.vline(x + 60, y + 2, h - 2, (120, 110, 90), 2)
    cv.rect(x + 62, y + 3, 52, 15, (90, 150, 210))
    cv.circle(x + 88, y + 10, 5, WHITE)
    cv.circle(x + 88, y + 10, 2, (90, 150, 210))
    f = F("sans-bold-14")
    cv.text(f, x + 128, y + 17, "?", DARKRED)
    cv.text(f, x + 142, y + 17, "!", DARKRED)


def art_diamond(cv, x, y, w, h):
    """Jeweller's diamond on black."""
    cv.rect(x, y, w, h, (24, 24, 28))
    cx, cy = x + w // 2, y + h // 2
    cv.polyline([(cx - 22, cy - 2), (cx - 12, cy - 10), (cx + 12, cy - 10),
                 (cx + 22, cy - 2), (cx, cy + 12), (cx - 22, cy - 2)],
                (220, 230, 240), 2)
    cv.line(cx - 22, cy - 2, cx + 22, cy - 2, (220, 230, 240), 2)
    cv.line(cx - 12, cy - 10, cx - 6, cy - 2, (180, 190, 200))
    cv.line(cx + 12, cy - 10, cx + 6, cy - 2, (180, 190, 200))
    cv.line(cx, cy - 10, cx, cy + 12, (180, 190, 200))
    cv.circle(cx - 34, cy - 8, 2, (250, 240, 180))
    cv.circle(cx + 36, cy + 6, 2, (250, 240, 180))


def art_kitty(cv, x, y, w, h):
    """Hello Kitty head + game controller."""
    cv.rect(x, y, w, h, (245, 200, 215))
    cx, cy = x + 70, y + h // 2 + 2
    cv.triangle((cx - 18, cy - 6), (cx - 8, cy - 6), (cx - 16, cy - 16), WHITE)
    cv.triangle((cx + 8, cy - 6), (cx + 18, cy - 6), (cx + 16, cy - 16), WHITE)
    cv.circle(cx, cy, 13, WHITE)
    cv.circle(cx - 5, cy - 1, 2, INK)
    cv.circle(cx + 5, cy - 1, 2, INK)
    cv.triangle((cx + 8, cy - 12), (cx + 16, cy - 16), (cx + 16, cy - 8), RED)
    cv.triangle((cx + 8, cy - 12), (cx + 16, cy - 8), (cx + 8, cy - 4), RED)
    # Controller.
    cv.rect(x + 118, y + 9, 40, 14, (60, 60, 70))
    cv.circle(x + 128, y + 16, 3, (250, 210, 80))
    cv.circle(x + 148, y + 16, 3, (120, 200, 240))
    cv.rect(x + 134, y + 14, 8, 4, WHITE)


def art_cricket(cv, x, y, w, h):
    """Bat, ball and stumps on green."""
    cv.rect(x, y, w, h, (60, 140, 80))
    cv.rect(x, y + h - 6, w, 6, (200, 190, 150))
    # Stumps.
    for i in range(3):
        cv.vline(x + 52 + i * 7, y + 8, 12, (240, 220, 120), 3)
    # Bat (leaning).
    cv.line(x + 100, y + 20, x + 124, y + 2, (220, 190, 140), 5)
    cv.line(x + 124, y + 2, x + 130, y - 2, (120, 90, 60), 3)
    # Ball.
    cv.circle(x + 152, y + 9, 6, (190, 40, 40))
    cv.line(x + 148, y + 5, x + 156, y + 13, WHITE)


ART = {
    "globe": art_globe, "chart": art_chart, "podium": art_podium,
    "flags": art_flags, "flame": art_flame, "ship": art_ship,
    "building": art_building, "plane": art_plane, "fbi": art_fbi,
    "flag": art_flag, "diamond": art_diamond, "kitty": art_kitty,
    "cricket": art_cricket,
}


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

X0 = 18
CW = 988  # content width; right edge 1006
WARN = []


def warn(msg):
    WARN.append(msg)
    print("WARN: " + msg, file=sys.stderr)


def story_count():
    return len(HEROES) + len(GRID) + len(BRIEFS)


def region_counts():
    counts = {}
    for s in HEROES + GRID:
        counts[s["region"]] = counts.get(s["region"], 0) + 1
    for _, _, region in BRIEFS:
        counts[region] = counts.get(region, 0) + 1
    return counts


def draw_masthead(cv, y):
    f_title = F("serif-bold-54")
    cv.text_center(f_title, 512, y + 52, MASTHEAD, INK)
    f_date = F("sans-bold-22")
    cv.text_center(f_date, 512, y + 80, DATE_LINE, DARKRED)
    counts = region_counts()
    sub = ("%d STORIES \u00b7 %d REGIONS \u00b7 EVERY EVENT HAPPENED OR WAS "
           "FIRST REPORTED ON THIS DAY" % (story_count(), len(counts)))
    f_sub = F("sans-12")
    cv.text_center(f_sub, 512, y + 97, sub, GREY)
    cv.hline(X0, y + 104, CW, INK, 3)
    cv.hline(X0, y + 108, CW, INK, 1)
    return y + 112


def draw_numbers(cv, y):
    n = len(NUMBERS)
    cell = CW // n
    f_num = F("sans-bold-34")
    f_lab = F("sans-bold-11")
    for i, (val, lab) in enumerate(NUMBERS):
        cx = X0 + i * cell + cell // 2
        cv.text_center(f_num, cx, y + 28, val, BLUE)
        lines = f_lab.wrap(lab, cell - 16)
        if len(lines) > 2:
            warn("number label too long: %r" % lab)
            lines = lines[:2]
        for j, ln in enumerate(lines):
            cv.text_center(f_lab, cx, y + 43 + j * 13, ln, INK)
        if i:
            cv.vline(X0 + i * cell, y + 4, 52, HAIR)
    cv.hline(X0, y + 59, CW, HAIR, 1)
    return y + 64


def draw_heroes(cv, y):
    n = len(HEROES)
    gap = 10
    col_w = (CW - gap * (n - 1)) // n
    f_kick = F("sans-bold-14")
    f_head = F("serif-bold-26")
    f_body = F("sans-15")
    f_num = F("sans-bold-14")
    for i, hero in enumerate(HEROES):
        x = X0 + i * (col_w + gap)
        ART[hero["art"]](cv, x, y, col_w, 52)
        # Number badge.
        cv.rect(x, y, 20, 20, RED)
        num = str(hero["num"])
        cv.text(f_num, x + 10 - f_num.width(num) // 2, y + 15, num, WHITE)
        yy = y + 52
        cv.text(f_kick, x, yy + 15, hero["kicker"], RED)
        lines = f_head.wrap(hero["headline"], col_w)
        if len(lines) > 2:
            warn("hero headline too long: %r" % hero["headline"])
            lines = lines[:2]
        for j, ln in enumerate(lines):
            cv.text(f_head, x, yy + 42 + j * 29, ln, INK)
        body = f_body.wrap(hero["body"], col_w)
        if len(body) > 4:
            warn("hero body too long (%d lines): %r" % (len(body), hero["body"]))
            body = body[:4]
        for j, ln in enumerate(body):
            cv.text(f_body, x, yy + 92 + j * 18, ln, INK)
    return y + 52 + 150 + 6


def draw_grid(cv, y):
    cols, rows = 5, 2
    gap_x, gap_y = 8, 6
    cell_w = (CW - gap_x * (cols - 1)) // cols
    cell_h = 112
    f_head = F("serif-bold-19")
    f_body = F("sans-12")
    f_num = F("sans-bold-11")
    for idx, story in enumerate(GRID):
        r, c = divmod(idx, cols)
        x = X0 + c * (cell_w + gap_x)
        yy = y + r * (cell_h + gap_y)
        ART[story["art"]](cv, x, yy, cell_w, 24)
        cv.rect(x, yy, 16, 16, RED)
        num = str(story["num"])
        cv.text(f_num, x + 8 - f_num.width(num) // 2, yy + 12, num, WHITE)
        lines = f_head.wrap(story["headline"], cell_w)
        if len(lines) > 2:
            warn("grid headline too long: %r" % story["headline"])
            lines = lines[:2]
        for j, ln in enumerate(lines):
            cv.text(f_head, x, yy + 45 + j * 21, ln, INK)
        body = f_body.wrap(story["body"], cell_w)
        if len(body) > 3:
            warn("grid body too long (%d lines): %r" % (len(body), story["body"]))
            body = body[:3]
        for j, ln in enumerate(body):
            cv.text(f_body, x, yy + 81 + j * 14, ln, INK)
    return y + rows * cell_h + gap_y


def draw_map(cv, y):
    f_title = F("sans-bold-14")
    title = "WHERE IT HAPPENED \u2014 THE TOP %d STORIES" % (
        len(HEROES) + len(GRID))
    cv.text(f_title, X0, y + 14, title, INK)
    # Region counts, right-aligned, each in its region colour.
    counts = region_counts()
    order = ["ASIA-PACIFIC", "EUROPE", "AMERICAS", "AFRICA", "MIDDLE EAST",
             "OCEANIA", "WORLD"]
    segs = [(r, "%s %d" % (r, counts[r])) for r in order if r in counts]
    f_cnt = F("sans-12")
    total = sum(f_cnt.width(" \u00b7 ".join(s for _, s in segs)) for _ in [0])
    # Draw segments right-aligned with middot separators.
    x = X0 + CW
    for i in range(len(segs) - 1, -1, -1):
        region, s = segs[i]
        wseg = f_cnt.width(s)
        x -= wseg
        cv.text(f_cnt, x, y + 14, s, REGION_COLORS[region])
        if i:
            x -= f_cnt.width(" \u00b7 ")
            cv.text(f_cnt, x, y + 14, " \u00b7 ", GREY)
    map_y = y + 18
    map_h = 60
    cv.rect(X0, map_y, CW, map_h, MAP_BG)
    # Dotted continents.
    for row, c0, c1 in MAP_SPANS:
        lat_c = 77.5 - row * 5
        py = map_y + int((80 - lat_c) / 140 * map_h)
        for col in range(c0, c1 + 1):
            lon_c = -177.5 + col * 5
            px = X0 + int((lon_c + 180) / 360 * CW)
            cv.circle(px, py, 1, MAP_DOT)
            # Stipple: a second dot half a row down, alternating sideways.
            dx = 3 if (row + col) % 2 else -3
            cv.circle(px + dx, py + 1, 1, MAP_DOT)
    # Pins.
    f_pin = F("sans-bold-11")
    for story in HEROES + GRID:
        lon, lat = story["pin"]
        px = X0 + int((lon + 180) / 360 * CW)
        py = map_y + int((80 - lat) / 140 * map_h)
        dx, dy = PIN_OFFSETS.get(story["num"], (0, 0))
        bx, by = px + dx, py + dy
        col = REGION_COLORS[story["region"]]
        if (dx, dy) != (0, 0):
            cv.line(px, py, bx, by, col, 1)
            cv.circle(px, py, 2, col)
        cv.circle(bx, by, 8, WHITE)
        cv.circle(bx, by, 8, col, fill=False)
        cv.circle(bx, by, 7, col, fill=False)
        num = str(story["num"])
        cv.text(f_pin, bx - f_pin.width(num) // 2, by + 4, num, col)
    return map_y + map_h + 4


def draw_briefs(cv, y):
    f_title = F("sans-bold-14")
    title = "IN BRIEF \u2014 %d MORE STORIES" % len(BRIEFS)
    cv.text(f_title, X0, y + 13, title, INK)
    f_note = F("sans-12")
    cv.text_right(f_note, X0 + CW, y + 13,
                  "EVERY ITEM VERIFIED FOR 23 NOVEMBER 2026", RED)
    cv.hline(X0, y + 17, CW, INK, 2)
    n = len(BRIEFS)
    if n <= 12:
        cols, f_kick, f_body, lh, gap = 2, F("sans-bold-14"), F("sans-14"), 16, 24
    else:
        cols, f_kick, f_body, lh, gap = 3, F("sans-bold-12"), F("sans-12"), 15, 18
    col_w = (CW - gap * (cols - 1)) // cols
    per_col = (n + cols - 1) // cols
    yy = y + 32
    max_y = yy
    for c in range(cols):
        cx = X0 + c * (col_w + gap)
        by = yy
        for item in BRIEFS[c * per_col:(c + 1) * per_col]:
            kick, text, _region = item
            head = kick + " \u2014 "
            # Wrap with the kicker on the first line.
            first_w = col_w - f_kick.width(head)
            words = text.split(" ")
            lines = []
            cur = ""
            limit = first_w
            for word in words:
                trial = word if not cur else cur + " " + word
                if f_body.width(trial) <= limit:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = word
                    limit = col_w
            if cur:
                lines.append(cur)
            cv.text(f_kick, cx, by, head, INK)
            cv.text(f_body, cx + f_kick.width(head), by, lines[0], INK)
            for j, ln in enumerate(lines[1:]):
                cv.text(f_body, cx, by + (j + 1) * lh, ln, INK)
            by += len(lines) * lh + 4
        max_y = max(max_y, by)
    return max_y


def draw_datecheck(cv, y):
    f_title = F("sans-bold-14")
    cv.text(f_title, X0, y + 13,
            "DATE CHECK \u2014 DELIBERATELY LEFT OUT: NOT 23 NOVEMBER", RED)
    cv.hline(X0, y + 17, CW, RED, 1)
    f_body = F("sans-12")
    joined = " \u00b7 ".join(DATECHECK)
    lines = f_body.wrap(joined, CW)
    if len(lines) > 3:
        warn("date check too long (%d lines)" % len(lines))
        lines = lines[:3]
    for j, ln in enumerate(lines):
        cv.text(f_body, X0, y + 30 + j * 14, ln, INK)
    return y + 30 + len(lines) * 14


def draw_sources(cv, y):
    f_src = F("sans-10")
    cv.text(f_src, X0, y, SOURCES, GREY)
    return y


def build():
    cv = Canvas(W, H, PAPER)
    y = 8
    y = draw_masthead(cv, y)
    y = draw_numbers(cv, y + 4)
    y = draw_heroes(cv, y + 6)
    y = draw_grid(cv, y + 6)
    y = draw_map(cv, y + 6)
    y = draw_briefs(cv, y + 6)
    y = draw_datecheck(cv, y + 4)
    y = draw_sources(cv, y + 12)
    if y > H - 4:
        warn("layout overflows by %d px" % (y - (H - 4)))
    print("layout ends at y=%d (canvas %d)" % (y, H), file=sys.stderr)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    path = os.path.join(outdir, "entry.png")
    size = write_png(cv, path)
    print("wrote %s (%d bytes)" % (path, size))
    if WARN:
        print("%d warnings" % len(WARN), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
