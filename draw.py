"""DON'T BLINK — deterministic, original procedural space poster.

Run: python3 draw.py
Only math, struct and zlib are used. Pixels, vector rasterization, the
bitmap lettering and PNG encoding are all implemented here from scratch.
"""

import math
import struct
import zlib


W = H = 1024
CX, CY = 512.0, 402.0
IRIS, PUPIL = 244.0, 102.0
SEED = 1101
TAU = math.tau
pixels = bytearray(W * H * 3)


def rand():
    global SEED
    SEED = (1664525 * SEED + 1013904223) & 0xffffffff
    return SEED / 4294967296.0


def mix(a, b, t):
    return a + (b - a) * t


def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def hash2(x, y):
    n = (x * 374761393 + y * 668265263 + 17011) & 0xffffffff
    n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
    return (n ^ (n >> 16)) / 4294967295.0


def noise(x, y):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    return mix(mix(hash2(ix, iy), hash2(ix + 1, iy), fx),
               mix(hash2(ix, iy + 1), hash2(ix + 1, iy + 1), fx), fy)


def put(x, y, color, alpha=1.0, add=False):
    x, y = int(x), int(y)
    if not (0 <= x < W and 0 <= y < H):
        return
    i = (y * W + x) * 3
    alpha = max(0.0, min(1.0, alpha))
    for c in range(3):
        value = pixels[i + c] + color[c] * alpha if add else mix(pixels[i + c], color[c], alpha)
        pixels[i + c] = max(0, min(255, int(value)))


def disc(x, y, radius, color, alpha=1.0, glow=False):
    for yy in range(max(0, int(y - radius - 1)), min(H, int(y + radius + 2))):
        for xx in range(max(0, int(x - radius - 1)), min(W, int(x + radius + 2))):
            d = math.hypot(xx - x, yy - y)
            if d <= radius + 0.8:
                a = max(0.0, 1.0 - d / radius) ** 2 if glow else min(1.0, max(0.0, radius + 0.7 - d))
                put(xx, yy, color, alpha * a, glow)


def line(x1, y1, x2, y2, color, width=1.0, alpha=1.0):
    length = math.hypot(x2 - x1, y2 - y1)
    steps = max(1, int(length * 1.4))
    for i in range(steps + 1):
        t = i / steps
        disc(mix(x1, x2, t), mix(y1, y2, t), width * 0.5, color, alpha)


def polygon(points, color):
    for y in range(max(0, int(min(p[1] for p in points))), min(H, int(max(p[1] for p in points)) + 1)):
        hits = []
        for i, (x1, y1) in enumerate(points):
            x2, y2 = points[(i + 1) % len(points)]
            if min(y1, y2) <= y + 0.5 < max(y1, y2):
                hits.append(x1 + (y + 0.5 - y1) * (x2 - x1) / (y2 - y1))
        hits.sort()
        for i in range(0, len(hits) - 1, 2):
            for x in range(max(0, int(hits[i])), min(W, int(hits[i + 1]) + 1)):
                put(x, y, color)


def aperture(x):
    q = abs((x - CX) / 475.0)
    return 230.0 * max(0.0, 1.0 - q * q) ** 0.72


def background():
    # Smooth, low frequency dust rather than high entropy pixel noise.
    field = []
    for gy in range(257):
        row = []
        for gx in range(257):
            x, y = gx * 4, gy * 4
            n = (noise(x / 140, y / 140) * 0.60
                 + noise(x / 62 + 8, y / 62) * 0.27
                 + noise(x / 25, y / 25 + 13) * 0.13)
            ridge = y - (180 + 0.48 * x + 90 * math.sin(x / 250) + 140 * (n - 0.5))
            cloud = math.exp(-(ridge / 155) ** 2) * max(0, n - 0.27)
            # A second cloud bank curls behind the lower lid. Domain-warped
            # ridges and dark dust lanes prevent a flat airbrush appearance.
            billow = noise(x / 48 + 5 * n, y / 48 - 3 * n)
            lower = math.exp(-((y - 675 - 85 * math.sin(x / 210) - 120 * n) / 105) ** 2)
            lower *= max(0, n + 0.24 * billow - 0.39)
            dust = (0.35 + 0.65 * smooth(0.24, 0.66, billow))
            cloud *= dust
            violet = math.exp(-((x - 160) / 490) ** 2 - ((y - 400) / 440) ** 2)
            blue = math.exp(-((x - 920) / 400) ** 2 - ((y - 480) / 540) ** 2)
            fade = 1.0 - 0.80 * smooth(795, 1020, y)
            row.append(((5 + 145 * cloud * violet + 115 * lower * violet + 12 * violet) * fade,
                        (7 + 38 * cloud + 110 * lower * blue + 17 * blue) * fade,
                        (18 + 165 * cloud + 145 * lower + 22 * violet + 24 * blue) * fade))
        field.append(row)
    for y in range(H):
        gy, fy = y // 4, (y % 4) / 4
        for x in range(W):
            gx, fx = x // 4, (x % 4) / 4
            i = (y * W + x) * 3
            vignette = max(0.35, 1 - 0.36 * (((x - 512) / 690) ** 2 + ((y - 450) / 760) ** 2))
            for c in range(3):
                v = mix(mix(field[gy][gx][c], field[gy][gx + 1][c], fx),
                        mix(field[gy + 1][gx][c], field[gy + 1][gx + 1][c], fx), fy)
                pixels[i + c] = int(v * vignette)


def stars():
    for _ in range(1500):
        x, y = rand() * W, rand() * 845
        b = rand()
        color = (int(100 + 150 * rand()), int(140 + 110 * rand()), 245)
        if b > 0.984:
            disc(x, y, 14, color, 0.7, True)
            line(x - 4, y, x + 4, y, color, 0.8, 0.7)
            line(x, y - 6, x, y + 6, color, 0.8, 0.7)
        disc(x, y, 0.45 + b * b * 0.8, color, 0.3 + b * 0.6)


def eye():
    # Almond silhouette; the iris is a polar interference field with
    # hundreds of independently warped radial filaments and crypts.
    for y in range(124, 682):
        for x in range(26, 999):
            dx, dy = x - CX, y - CY
            edge = aperture(x)
            d = math.hypot(dx, dy)
            theta = math.atan2(dy, dx)
            border = abs(dy) - edge
            halo = math.exp(-abs(border) / 14.0) * 0.46
            if halo > 0.012:
                put(x, y, (74, 71, 141) if dy < 0 else (17, 114, 134), halo, True)
            if border > 0:
                continue
            edgefade = smooth(0, 28, -border)
            if d > IRIS:
                smoke = 0.5 + 0.5 * math.sin(d * 0.055 + 6 * theta)
                light = math.exp(-((d - IRIS) / 95) ** 2)
                vein = noise(x / 71 + smoke, y / 55) * smoke
                put(x, y, (8 + 20 * light + 13 * vein, 13 + 32 * light * smoke,
                           29 + 48 * light + 18 * vein), edgefade)
                continue
            if d < PUPIL:
                put(x, y, (2, 3, 9))
                continue
            t = (d - PUPIL) / (IRIS - PUPIL)
            warp = theta + 0.019 * math.sin(d * 0.061 + theta * 11) + 0.006 * math.sin(d * 0.17 - theta * 17)
            threads = (0.50 + 0.24 * math.sin(warp * 287 + 1.8 * math.sin(warp * 43))
                       + 0.15 * math.sin(warp * 513 + d * 0.035)
                       + 0.11 * math.sin(warp * 827 - d * 0.06))
            crypt = 0.62 + 0.38 * math.sin(theta * 71 + 2 * math.sin(theta * 19) + d * 0.035)
            body = (0.38 + 0.62 * threads) * (0.72 + 0.28 * crypt)
            body *= (0.4 + 0.6 * math.sin(math.pi * t) ** 0.35)
            sectors = 0.80 + 0.20 * math.sin(theta * 7 + math.sin(theta * 13))
            body *= sectors
            # Jagged collarette, the folded gold boundary of a real iris.
            collar = 0.24 + 0.045 * math.sin(theta * 31) + 0.024 * math.sin(theta * 79)
            gold = math.exp(-((t - collar) / 0.035) ** 2) * (0.55 + 0.45 * crypt)
            warm = math.exp(-((t - 0.08) / 0.31) ** 2)
            outer = smooth(0.98, 0.82, t)
            ring = 0.6 + 0.4 * math.sin(d * 0.18 + math.sin(theta * 23) * 1.6)
            r = (18 + 135 * warm + 12 * ring) * body + 68 * gold
            g = (110 + 80 * (1 - warm) + 22 * ring) * body + 42 * gold
            b = (154 + 54 * (1 - warm)) * body + 5 * gold
            put(x, y, (r * outer, g * outer, b * outer), edgefade)
    # Thin rim arcs tie the eye into the surrounding nebula.
    for side in (-1, 1):
        last = None
        for x in range(39, 986):
            yy = CY + side * aperture(x)
            strength = math.sin(math.pi * (x - 37) / 950) ** 0.55
            color = (112, 82, 158) if side < 0 else (39, 144, 162)
            if last:
                line(last[0], last[1], x, yy, color, 1.6, strength * 0.8)
            last = (x, yy)
    # Broken, close-spaced specular arcs make the eyelids feel enormous.
    for side, start, end in ((-1, 175, 534), (1, 543, 907)):
        for x in range(start, end):
            fall = math.sin(math.pi * (x - start) / (end - start)) ** 2
            y = CY + side * (aperture(x) + 3.0)
            disc(x, y, 2.0, (137, 118, 199) if side < 0 else (89, 208, 218), 0.58 * fall)
            disc(x, y, 8, (104, 75, 160) if side < 0 else (33, 122, 154), 0.19 * fall, True)


def eclipse():
    # Long, irregular coronal streamers, with directional solar wind.
    jets = ((-2.72, 0.10, 0.70), (-2.35, 0.17, 0.40), (-1.65, 0.09, 0.54),
            (-0.64, 0.13, 1.0), (-0.18, 0.075, 0.80), (0.61, 0.15, 0.53),
            (1.27, 0.12, 0.78), (2.14, 0.10, 0.55), (2.83, 0.07, 0.56))
    for y in range(188, 617):
        for x in range(298, 727):
            d = math.hypot(x - CX, y - CY)
            if d < PUPIL - 1:
                continue
            a = math.atan2(y - CY, x - CX)
            delta = d - PUPIL
            ray = 0.5 + 0.5 * math.sin(a * 71 + 1.3 * math.sin(a * 19) + delta * 0.012)
            lobes = 0.0
            for direction, spread, power in jets:
                da = (a - direction + math.pi) % TAU - math.pi
                lobes += power * math.exp(-(da / spread) ** 2)
            halo = math.exp(-max(0, delta) / (10 + lobes * 47))
            stream = halo * (0.38 + 0.62 * ray) * (0.30 + 0.7 * min(1, lobes + 0.2))
            fine = math.exp(-max(0, delta) / 8) * (0.65 + 0.35 * ray)
            core = math.exp(-(delta / 1.55) ** 2)
            put(x, y, (255, 129, 46), stream * 0.87, True)
            put(x, y, (255, 213, 134), fine * 0.72, True)
            put(x, y, (255, 250, 222), core, True)
    # Red magnetic prominences loop above the moon's eastern limb.
    for center, extent, height in ((-0.48, 0.17, 21), (1.02, 0.12, 14), (-2.70, 0.10, 12)):
        last = None
        for i in range(91):
            t = i / 90
            a = center + (t - 0.5) * extent * 2
            r = PUPIL + 2 + height * math.sin(math.pi * t) ** 0.8
            x, y = CX + r * math.cos(a), CY + r * math.sin(a)
            disc(x, y, 6, (255, 58, 38), 0.14, True)
            if last:
                line(last[0], last[1], x, y, (255, 111, 65), 1.1, 0.82)
            last = (x, y)
    # The occluding moon stays truly dark, making the corona legible.
    disc(CX, CY, PUPIL - 1.7, (2, 3, 9))
    # One sharp diamond-ring glint breaks the eclipse's symmetry.
    a = -0.62
    x, y = CX + PUPIL * math.cos(a), CY + PUPIL * math.sin(a)
    disc(x, y, 45, (255, 131, 61), 0.62, True)
    disc(x, y, 18, (255, 206, 121), 0.95, True)
    line(x - 13, y + 6, x + 13, y - 6, (255, 232, 182), 0.9, 0.7)
    disc(x, y, 3.4, (255, 253, 231))


def rocket():
    rx, ry = 648.0, 694.0
    length = math.hypot(CX - rx, CY - ry)
    ux, uy = (CX - rx) / length, (CY - ry) / length
    vx, vy = -uy, ux

    def pt(u, v):
        return (rx + u * ux + v * vx, ry + u * uy + v * vy)

    # Every exhaust point is behind a ship pointing exactly at the pupil.
    # A diffuse red envelope, a gold flame and a white-hot engine core.
    for s in range(146, 0, -1):
        x, y = pt(-20 - s, 1.5 * math.sin(s * 0.17) * s / 146)
        width = 3 + 13 * (s / 146)
        fade = (1 - s / 150) ** 0.65
        disc(x, y, width * 2.9, (245, 65, 41), fade * 0.065, True)
        disc(x, y, width, (255, 86, 39), fade * 0.28, True)
        disc(x, y, width * 0.31, (255, 178, 68), fade * 0.85)
        if s < 72:
            disc(x, y, 2.5 * (1 - s / 80), (255, 247, 190), 0.9)
    x, y = pt(-25, 0)
    disc(x, y, 25, (255, 174, 66), 0.9, True)
    for _ in range(110):
        s = rand() * 146
        x, y = pt(-27 - s, (rand() - 0.5) * (7 + s * 0.15))
        disc(x, y, 0.5 + rand() * 1.0, (255, 139 + int(rand() * 80), 87), 1 - s / 180)

    def shape(points, color):
        polygon([pt(u, v) for u, v in points], color)

    shape([(-21, -9), (-29, -18), (-2, -13), (7, 0), (-2, 13), (-29, 18), (-21, 9)], (8, 13, 24))
    shape([(-20, -8), (-26, -16), (-3, -11), (3, -6)], (225, 65, 65))
    shape([(-20, 8), (-26, 16), (-3, 11), (3, 6)], (155, 35, 55))
    shape([(33, 0), (19, -8), (-15, -9), (-23, -5), (-23, 5), (-15, 9), (19, 8)], (12, 22, 34))
    shape([(30, 0), (17, -6), (-15, -7), (-20, -4), (-20, 4), (-15, 7), (17, 6)], (221, 225, 212))
    shape([(30, 0), (17, -6), (13, -6), (13, 6), (17, 6)], (248, 83, 70))
    shape([(-18, 1), (13, 2), (17, 6), (-15, 7), (-20, 4)], (112, 148, 156))
    shape([(-22, -5), (-18, -5), (-18, 5), (-22, 5)], (237, 90, 63))
    x, y = pt(3, 0)
    disc(x, y, 6, (21, 40, 55))
    disc(x, y, 4.2, (47, 188, 208))
    disc(x - 1, y - 1, 1.5, (218, 255, 240))
    x1, y1 = pt(-12, -5)
    x2, y2 = pt(10, -4)
    line(x1, y1, x2, y2, (255, 250, 219), 1)


FONT = {
    'D': ('11110', '10001', '10001', '10001', '10001', '10001', '11110'),
    'O': ('01110', '11011', '10001', '10001', '10001', '11011', '01110'),
    'N': ('10001', '11001', '11001', '10101', '10011', '10011', '10001'),
    "'": ('11', '11', '01', '10', '00', '00', '00'),
    'T': ('11111', '00100', '00100', '00100', '00100', '00100', '00100'),
    'B': ('11110', '10001', '10001', '11110', '10001', '10001', '11110'),
    'L': ('10000', '10000', '10000', '10000', '10000', '10000', '11111'),
    'I': ('111', '010', '010', '010', '010', '010', '111'),
    'K': ('10001', '10010', '10100', '11000', '10100', '10010', '10001'),
    ' ': ('000',) * 7,
}


def title():
    text, scale = "DON'T BLINK", 13
    total = sum(len(FONT[c][0]) + 1 for c in text) - 1
    left, top = (W - total * scale) // 2, 862
    for ox, oy, col in ((4, 6, (99, 32, 63)), (0, 0, (255, 232, 182))):
        x = left + ox
        for char in text:
            glyph = FONT[char]
            for row, bits in enumerate(glyph):
                for column, bit in enumerate(bits):
                    if bit == '1':
                        for yy in range(top + oy + row * scale, top + oy + (row + 1) * scale):
                            for xx in range(x + column * scale, x + (column + 1) * scale):
                                put(xx, yy, col)
            x += (len(glyph[0]) + 1) * scale
    line(450, 986, 492, 986, (66, 144, 156), 1)
    disc(512, 986, 2.5, (239, 139, 92))
    line(532, 986, 574, 986, (66, 144, 156), 1)


def chunk(tag, data):
    return struct.pack('!I', len(data)) + tag + data + struct.pack('!I', zlib.crc32(tag + data) & 0xffffffff)


def save():
    header = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', W, H, 8, 2, 0, 0, 0))
    # Predictive row filters retain smooth gradients at a small file size.
    # Use the finest channel precision that fits the competition's cap.
    for quantum in (1, 2, 3, 4, 6, 8):
        raw = bytearray()
        previous = bytearray(W * 3)
        for y in range(H):
            start = y * W * 3
            row = bytearray((v // quantum) * quantum for v in pixels[start:start + W * 3])
            sub = bytearray((v - (row[i - 3] if i >= 3 else 0)) & 255 for i, v in enumerate(row))
            up = bytearray((v - previous[i]) & 255 for i, v in enumerate(row))
            sub_cost = sum(min(v, 256 - v) for v in sub)
            up_cost = sum(min(v, 256 - v) for v in up)
            raw.append(1 if sub_cost < up_cost else 2)
            raw.extend(sub if sub_cost < up_cost else up)
            previous = row
        result = header + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
        if len(result) <= 1024 * 1024:
            with open('entry.png', 'wb') as f:
                f.write(result)
            print('entry.png: %d x %d, %d bytes, channel quantum %d' % (W, H, len(result), quantum))
            return
    raise RuntimeError('PNG exceeds 1 MiB')


if __name__ == '__main__':
    background()
    stars()
    eye()
    eclipse()
    rocket()
    title()
    save()
