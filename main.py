#!/usr/bin/env python3
"""VELMARA — travel poster for a place that isn't there.

Pure-stdlib renderer: retro poster into a pixel buffer, hand-rolled PNG
encoder, writes /output/entry.png (1024x1024). No network, deterministic.
"""
import math
import os
import random
import struct
import zlib

W = H = 1024
buf = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i:i + 3] = bytes(c)


def blend(x, y, c, a):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        for k in range(3):
            buf[i + k] = int(buf[i + k] * (1 - a) + c[k] * a)


def rect(x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1)):
        row = y * W * 3
        for x in range(max(0, x0), min(W, x1)):
            i = row + x * 3
            buf[i:i + 3] = bytes(c)


def circle(cx, cy, r, c):
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        dx = int(math.sqrt(max(0, r * r - (y - cy) ** 2)))
        rect(cx - dx, y, cx + dx + 1, y + 1, c)


def ring(cx, cy, r, wdt, c):
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        for x in range(max(0, cx - r), min(W, cx + r + 1)):
            d = math.hypot(x - cx, y - cy)
            if r - wdt <= d <= r:
                px(x, y, c)


def poly(points, c):
    ys = [p[1] for p in points]
    for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
        nodes = []
        n = len(points)
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            if y1 == y2:
                continue
            if min(y1, y2) <= y < max(y1, y2):
                nodes.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        nodes.sort()
        for i in range(0, len(nodes) - 1, 2):
            rect(int(nodes[i]), y, int(nodes[i + 1]) + 1, y + 1, c)


def line(x1, y1, x2, y2, c, wdt=2):
    steps = max(abs(x2 - x1), abs(y2 - y1), 1)
    for s in range(steps + 1):
        x = int(x1 + (x2 - x1) * s / steps)
        y = int(y1 + (y2 - y1) * s / steps)
        for dy in range(-wdt // 2, wdt // 2 + 1):
            for dx in range(-wdt // 2, wdt // 2 + 1):
                px(x + dx, y + dy, c)


def lerp(a, b, t):
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))


FONT = {
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
}


def draw_text(text, cx, y, scale, c, shadow=None):
    gw = 5 * scale
    gap = 2 * scale
    total = len(text) * gw + (len(text) - 1) * gap
    x = cx - total // 2
    for ch in text:
        g = FONT[ch]
        for row in range(7):
            for col in range(5):
                if g[row][col] == "1":
                    if shadow:
                        rect(x + col * scale + scale // 2, y + row * scale + scale // 2,
                             x + (col + 1) * scale + scale // 2, y + (row + 1) * scale + scale // 2, shadow)
                    rect(x + col * scale, y + row * scale,
                         x + (col + 1) * scale, y + (row + 1) * scale, c)
        x += gw + gap


def main():
    top = (16, 74, 92)
    mid = (64, 145, 155)
    low = (240, 178, 110)
    horizon_y = 640
    bands = 28
    for b in range(bands):
        t = b / (bands - 1)
        c = lerp(top, mid, t * 2) if t < 0.5 else lerp(mid, low, (t - 0.5) * 2)
        y0 = int(b * horizon_y / bands)
        y1 = int((b + 1) * horizon_y / bands)
        rect(0, y0, W, y1, c)

    circle(740, 300, 150, (250, 214, 140))
    circle(740, 300, 118, (253, 231, 170))
    ring(740, 300, 168, 4, (250, 214, 140))
    ring(740, 300, 188, 2, (250, 214, 140))

    poly([(0, 640), (0, 520), (140, 430), (300, 540), (430, 460), (560, 560),
          (700, 470), (850, 560), (1024, 500), (1024, 640)], (88, 80, 130))
    poly([(0, 640), (0, 570), (180, 500), (360, 580), (520, 530), (680, 600),
          (1024, 580), (1024, 640)], (36, 96, 110))

    rect(0, horizon_y, W, H, (24, 110, 128))
    for i in range(26):
        y = horizon_y + 10 + i * 14
        c = lerp((60, 160, 165), (18, 84, 104), i / 25)
        rect(0, y, W, y + 5, c)
    rng = random.Random(20261121)
    for _ in range(220):
        x = rng.randrange(0, W - 40)
        y = rng.randrange(horizon_y + 16, H - 30)
        wdt = rng.randrange(10, 42)
        c = (190, 230, 220) if rng.random() < 0.7 else (250, 214, 140)
        rect(x, y, x + wdt, y + 3, c)

    poly([(0, 1024), (0, 660), (90, 610), (210, 640), (300, 720), (330, 850),
          (300, 1024)], (24, 52, 66))
    poly([(0, 1024), (0, 760), (120, 720), (240, 780), (270, 900), (250, 1024)],
         (16, 38, 50))

    lx, base_y = 150, 640
    tower_h, tower_w = 230, 64
    for i in range(tower_h):
        t = i / tower_h
        wdt = int(tower_w * (1 - 0.35 * t))
        band = int(i / 38) % 2
        c = (245, 238, 220) if band == 0 else (206, 64, 54)
        rect(lx - wdt // 2, base_y - i, lx + wdt // 2, base_y - i + 1, c)
    rect(lx - 30, base_y - tower_h - 16, lx + 30, base_y - tower_h, (24, 52, 66))
    rect(lx - 16, base_y - tower_h - 46, lx + 16, base_y - tower_h - 16, (253, 231, 170))
    poly([(lx - 24, base_y - tower_h - 46), (lx + 24, base_y - tower_h - 46),
          (lx, base_y - tower_h - 78)], (206, 64, 54))
    lamp_y = base_y - tower_h - 31
    for x in range(lx + 16, 760):
        t = (x - lx) / 610
        spread = int(6 + 70 * t)
        for y in range(lamp_y - spread, lamp_y + spread):
            blend(x, y, (253, 231, 170), 0.20 * (1 - t))

    for (bx, by, s) in [(430, 270, 16), (480, 305, 12), (390, 320, 10), (540, 250, 13)]:
        line(bx - s, by, bx, by - s // 2, (20, 40, 52), 3)
        line(bx, by - s // 2, bx + s, by, (20, 40, 52), 3)

    for (cx, cy, cw) in [(250, 330, 150), (330, 352, 110), (880, 140, 120)]:
        rect(cx - cw // 2, cy, cx + cw // 2, cy + 16, (240, 230, 205))
        rect(cx - cw // 3, cy - 14, cx + cw // 3, cy, (240, 230, 205))

    for _ in range(90):
        y = rng.randrange(horizon_y + 20, H - 40)
        spread = int(30 + (y - horizon_y) * 0.35)
        x = 740 + rng.randrange(-spread, spread)
        rect(x, y, x + rng.randrange(14, 46), y + 4, (250, 214, 140))

    poly([(660, 800), (760, 800), (735, 830), (680, 830)], (24, 52, 66))
    line(708, 800, 708, 720, (24, 52, 66), 3)
    poly([(708, 725), (708, 795), (752, 795)], (245, 238, 220))
    poly([(704, 735), (704, 795), (672, 795)], (206, 64, 54))

    rect(0, 0, W, 14, (16, 38, 50))
    rect(0, H - 14, W, H, (16, 38, 50))
    rect(0, 0, 14, H, (16, 38, 50))
    rect(W - 14, 0, W, H, (16, 38, 50))

    draw_text("VELMARA", W // 2, 70, 17, (253, 240, 205), shadow=(16, 38, 50))
    rect(257, 215, 767, 219, (253, 240, 205))
    # Small crescent moon, upper left — Velmara's second light
    circle(120, 150, 34, (253, 240, 205))
    circle(136, 140, 30, (30, 100, 118))

    for _ in range(9000):
        x = rng.randrange(0, W)
        y = rng.randrange(0, H)
        i = (y * W + x) * 3
        d = rng.choice((-10, -6, 6, 10))
        for k in range(3):
            buf[i + k] = max(0, min(255, buf[i + k] + d))

    out_dir = "/output" if os.path.isdir("/output") else "."
    path = os.path.join(out_dir, "entry.png")
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += buf[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    print(f"wrote {path}: {len(png)} bytes, {W}x{H}")


if __name__ == "__main__":
    main()
