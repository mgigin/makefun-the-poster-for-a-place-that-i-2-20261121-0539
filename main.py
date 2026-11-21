#!/usr/bin/env python3
# Velmara: a vintage travel poster for a coastline that never existed.
# Standard library only. Renders into an RGB buffer, encodes PNG by hand,
# saves /output/entry.png at 1024x1024. Same output on every run.
import math
import os
import random
import struct
import zlib

SIZE = 1024
canvas = bytearray(SIZE * SIZE * 3)


def plot(x, y, rgb):
    if 0 <= x < SIZE and 0 <= y < SIZE:
        off = (y * SIZE + x) * 3
        canvas[off:off + 3] = bytes(rgb)


def mix_pixel(x, y, rgb, alpha):
    if 0 <= x < SIZE and 0 <= y < SIZE:
        off = (y * SIZE + x) * 3
        for ch in range(3):
            canvas[off + ch] = int(canvas[off + ch] * (1 - alpha) + rgb[ch] * alpha)


def box(x0, y0, x1, y1, rgb):
    for yy in range(max(0, y0), min(SIZE, y1)):
        base = yy * SIZE * 3
        for xx in range(max(0, x0), min(SIZE, x1)):
            off = base + xx * 3
            canvas[off:off + 3] = bytes(rgb)


def disc(cx, cy, radius, rgb):
    for yy in range(max(0, cy - radius), min(SIZE, cy + radius + 1)):
        half = int(math.sqrt(max(0, radius * radius - (yy - cy) ** 2)))
        box(cx - half, yy, cx + half + 1, yy + 1, rgb)


def halo(cx, cy, radius, thickness, rgb):
    for yy in range(max(0, cy - radius), min(SIZE, cy + radius + 1)):
        for xx in range(max(0, cx - radius), min(SIZE, cx + radius + 1)):
            dist = math.hypot(xx - cx, yy - cy)
            if radius - thickness <= dist <= radius:
                plot(xx, yy, rgb)


def shape(points, rgb):
    ys = [p[1] for p in points]
    for yy in range(max(0, min(ys)), min(SIZE, max(ys) + 1)):
        crossings = []
        count = len(points)
        for idx in range(count):
            ax, ay = points[idx]
            bx, by = points[(idx + 1) % count]
            if ay == by:
                continue
            if min(ay, by) <= yy < max(ay, by):
                crossings.append(ax + (yy - ay) * (bx - ax) / (by - ay))
        crossings.sort()
        for idx in range(0, len(crossings) - 1, 2):
            box(int(crossings[idx]), yy, int(crossings[idx + 1]) + 1, yy + 1, rgb)


def stroke(x1, y1, x2, y2, rgb, width=2):
    steps = max(abs(x2 - x1), abs(y2 - y1), 1)
    for step in range(steps + 1):
        xx = int(x1 + (x2 - x1) * step / steps)
        yy = int(y1 + (y2 - y1) * step / steps)
        for dy in range(-width // 2, width // 2 + 1):
            for dx in range(-width // 2, width // 2 + 1):
                plot(xx + dx, yy + dy, rgb)


def blend_rgb(a, b, t):
    return tuple(int(a[ch] + (b[ch] - a[ch]) * t) for ch in range(3))


GLYPHS = {
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
}


def headline(word, center_x, top_y, scale, rgb, shadow=None):
    glyph_w = 5 * scale
    spacing = 2 * scale
    total_w = len(word) * glyph_w + (len(word) - 1) * spacing
    cursor = center_x - total_w // 2
    for letter in word:
        rows = GLYPHS[letter]
        for r in range(7):
            for c in range(5):
                if rows[r][c] == "1":
                    if shadow:
                        box(cursor + c * scale + scale // 2, top_y + r * scale + scale // 2,
                            cursor + (c + 1) * scale + scale // 2, top_y + (r + 1) * scale + scale // 2, shadow)
                    box(cursor + c * scale, top_y + r * scale,
                        cursor + (c + 1) * scale, top_y + (r + 1) * scale, rgb)
        cursor += glyph_w + spacing


def render():
    sky_top = (16, 74, 92)
    sky_mid = (64, 145, 155)
    sky_low = (240, 178, 110)
    horizon = 640
    band_count = 28
    for band in range(band_count):
        frac = band / (band_count - 1)
        colour = blend_rgb(sky_top, sky_mid, frac * 2) if frac < 0.5 else blend_rgb(sky_mid, sky_low, (frac - 0.5) * 2)
        box(0, int(band * horizon / band_count), SIZE, int((band + 1) * horizon / band_count), colour)

    disc(740, 300, 150, (250, 214, 140))
    disc(740, 300, 118, (253, 231, 170))
    halo(740, 300, 168, 4, (250, 214, 140))
    halo(740, 300, 188, 2, (250, 214, 140))

    shape([(0, 640), (0, 520), (140, 430), (300, 540), (430, 460), (560, 560),
           (700, 470), (850, 560), (1024, 500), (1024, 640)], (88, 80, 130))
    shape([(0, 640), (0, 570), (180, 500), (360, 580), (520, 530), (680, 600),
           (1024, 580), (1024, 640)], (36, 96, 110))

    box(0, horizon, SIZE, SIZE, (24, 110, 128))
    for idx in range(26):
        yy = horizon + 10 + idx * 14
        box(0, yy, SIZE, yy + 5, blend_rgb((60, 160, 165), (18, 84, 104), idx / 25))
    dice = random.Random(20261121)
    for _ in range(220):
        xx = dice.randrange(0, SIZE - 40)
        yy = dice.randrange(horizon + 16, SIZE - 30)
        box(xx, yy, xx + dice.randrange(10, 42), yy + 3,
            (190, 230, 220) if dice.random() < 0.7 else (250, 214, 140))

    shape([(0, 1024), (0, 660), (90, 610), (210, 640), (300, 720), (330, 850),
           (300, 1024)], (24, 52, 66))
    shape([(0, 1024), (0, 760), (120, 720), (240, 780), (270, 900), (250, 1024)],
          (16, 38, 50))

    tower_x, tower_base = 150, 640
    tower_height, tower_width = 230, 64
    for step in range(tower_height):
        frac = step / tower_height
        width = int(tower_width * (1 - 0.35 * frac))
        stripe = int(step / 38) % 2
        colour = (245, 238, 220) if stripe == 0 else (206, 64, 54)
        box(tower_x - width // 2, tower_base - step, tower_x + width // 2, tower_base - step + 1, colour)
    box(tower_x - 30, tower_base - tower_height - 16, tower_x + 30, tower_base - tower_height, (24, 52, 66))
    box(tower_x - 16, tower_base - tower_height - 46, tower_x + 16, tower_base - tower_height - 16, (253, 231, 170))
    shape([(tower_x - 24, tower_base - tower_height - 46), (tower_x + 24, tower_base - tower_height - 46),
           (tower_x, tower_base - tower_height - 78)], (206, 64, 54))
    lamp_y = tower_base - tower_height - 31
    for xx in range(tower_x + 16, 760):
        frac = (xx - tower_x) / 610
        spread = int(6 + 70 * frac)
        for yy in range(lamp_y - spread, lamp_y + spread):
            mix_pixel(xx, yy, (253, 231, 170), 0.20 * (1 - frac))

    for (bx, by, bs) in [(430, 270, 16), (480, 305, 12), (390, 320, 10), (540, 250, 13)]:
        stroke(bx - bs, by, bx, by - bs // 2, (20, 40, 52), 3)
        stroke(bx, by - bs // 2, bx + bs, by, (20, 40, 52), 3)

    for (cx, cy, cw) in [(250, 330, 150), (330, 352, 110), (880, 140, 120)]:
        box(cx - cw // 2, cy, cx + cw // 2, cy + 16, (240, 230, 205))
        box(cx - cw // 3, cy - 14, cx + cw // 3, cy, (240, 230, 205))

    for _ in range(90):
        yy = dice.randrange(horizon + 20, SIZE - 40)
        spread = int(30 + (yy - horizon) * 0.35)
        xx = 740 + dice.randrange(-spread, spread)
        box(xx, yy, xx + dice.randrange(14, 46), yy + 4, (250, 214, 140))

    shape([(660, 800), (760, 800), (735, 830), (680, 830)], (24, 52, 66))
    stroke(708, 800, 708, 720, (24, 52, 66), 3)
    shape([(708, 725), (708, 795), (752, 795)], (245, 238, 220))
    shape([(704, 735), (704, 795), (672, 795)], (206, 64, 54))

    box(0, 0, SIZE, 14, (16, 38, 50))
    box(0, SIZE - 14, SIZE, SIZE, (16, 38, 50))
    box(0, 0, 14, SIZE, (16, 38, 50))
    box(SIZE - 14, 0, SIZE, SIZE, (16, 38, 50))

    headline("VELMARA", SIZE // 2, 70, 17, (253, 240, 205), shadow=(16, 38, 50))
    box(257, 215, 767, 219, (253, 240, 205))
    disc(120, 150, 34, (253, 240, 205))
    disc(136, 140, 30, (30, 100, 118))
    # Two tiny stars near the moon
    plot(180, 110, (253, 240, 205))
    plot(200, 180, (253, 240, 205))

    for _ in range(9000):
        xx = dice.randrange(0, SIZE)
        yy = dice.randrange(0, SIZE)
        off = (yy * SIZE + xx) * 3
        delta = dice.choice((-10, -6, 6, 10))
        for ch in range(3):
            canvas[off + ch] = max(0, min(255, canvas[off + ch] + delta))

    folder = "/output" if os.path.isdir("/output") else "."
    target = os.path.join(folder, "entry.png")
    scanlines = bytearray()
    row_bytes = SIZE * 3
    for yy in range(SIZE):
        scanlines.append(0)
        scanlines += canvas[yy * row_bytes:(yy + 1) * row_bytes]

    def make_chunk(tag, payload):
        body = struct.pack(">I", len(payload)) + tag + payload
        return body + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    png_bytes = b"\x89PNG\r\n\x1a\n"
    png_bytes += make_chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
    png_bytes += make_chunk(b"IDAT", zlib.compress(bytes(scanlines), 9))
    png_bytes += make_chunk(b"IEND", b"")
    with open(target, "wb") as handle:
        handle.write(png_bytes)
    print(f"wrote {target}: {len(png_bytes)} bytes, {SIZE}x{SIZE}")


if __name__ == "__main__":
    render()
