"""Conversione degli sprite Pokémon Essentials (Gen 9 Pack) nel formato DS di pokeplatinum, in Python puro."""
import struct, zlib
from collections import Counter

import pngpix

BG = (0, 168, 0)   # colore di sfondo (indice 0, trasparente)


def read_rgba(path):
    """PNG 8 bit, tipi colore 2/3/6 (anche 1/2/4 bit con palette) -> (w, h, righe di (r,g,b,a))."""
    data = open(path, 'rb').read()
    i, chunks = 8, []
    while i < len(data):
        n = struct.unpack('>I', data[i:i + 4])[0]
        chunks.append((data[i + 4:i + 8], data[i + 8:i + 8 + n]))
        i += 12 + n
    w, h, bd, ct, _, _, il = struct.unpack('>IIBBBBB', [b for t, b in chunks if t == b'IHDR'][0])
    assert il == 0, 'interlacciato non supportato'
    plte = [b for t, b in chunks if t == b'PLTE']
    trns = [b for t, b in chunks if t == b'tRNS']
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    bpp = max(1, channels * bd // 8)
    stride = (w * channels * bd + 7) // 8
    raw = zlib.decompress(b''.join(b for t, b in chunks if t == b'IDAT'))
    prev = bytearray(stride)
    rows, pos = [], 0
    for _ in range(h):
        f = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4: line[x] = (line[x] + pngpix.paeth(a, b, c)) & 255
        prev = line
        row = []
        if ct == 6:
            row = [tuple(line[x * 4:x * 4 + 4]) for x in range(w)]
        elif ct == 2:
            row = [tuple(line[x * 3:x * 3 + 3]) + (255,) for x in range(w)]
        elif ct == 4:
            row = [(line[x * 2],) * 3 + (line[x * 2 + 1],) for x in range(w)]
        elif ct in (0, 3):
            if bd == 8:
                idx = list(line[:w])
            else:
                per, mask = 8 // bd, (1 << bd) - 1
                idx = [(byte >> (8 - bd * (k + 1))) & mask for byte in line for k in range(per)][:w]
            if ct == 3:
                pal = [tuple(plte[0][j:j + 3]) for j in range(0, len(plte[0]), 3)]
                alpha = list(trns[0]) if trns else []
                row = [pal[v] + ((alpha[v] if v < len(alpha) else 255),) for v in idx]
            else:
                row = [(v * 255 // ((1 << bd) - 1),) * 3 + (255,) for v in idx]
        rows.append(row)
    return w, h, rows


def halve(w, h, rows):
    """Le immagini di Essentials sono ingrandite 2x: prende un pixel ogni due."""
    return w // 2, h // 2, [r[::2] for r in rows[::2]]


def opaque(px):
    return px[3] >= 128


def bbox(w, h, rows):
    xs = [x for y in range(h) for x in range(w) if opaque(rows[y][x])]
    ys = [y for y in range(h) for x in range(w) if opaque(rows[y][x])]
    if not xs:
        return 0, 0, 1, 1
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def fit80(w, h, rows):
    """Porta l'immagine in 80x80: centrata in orizzontale, appoggiata in basso; ridotta se più grande."""
    x0, y0, x1, y1 = bbox(w, h, rows)
    bw, bh = x1 - x0, y1 - y0
    scale = min(1.0, 80 / bw, 80 / bh)
    nw, nh = max(1, int(bw * scale)), max(1, int(bh * scale))
    out = [[(0, 0, 0, 0)] * 80 for _ in range(80)]
    ox = (80 - nw) // 2
    oy = 80 - nh - (0 if nh >= 78 else 2)
    for y in range(nh):
        sy = y0 + min(bh - 1, int(y / scale))
        for x in range(nw):
            sx = x0 + min(bw - 1, int(x / scale))
            out[oy + y][ox + x] = rows[sy][sx]
    return out


def dist(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def quantize(images, n=15):
    """Palette comune di n colori per le immagini (liste di righe RGBA) -> (palette, immagini di indici 0..n, 0 = trasparente)."""
    counts = Counter(px[:3] for img in images for row in img for px in row if opaque(px))
    colors = [[c, k] for c, k in counts.items()]
    while len(colors) > n:
        best = None
        for i in range(len(colors)):
            for j in range(i + 1, len(colors)):
                d = dist(colors[i][0], colors[j][0]) * min(colors[i][1], colors[j][1])
                if best is None or d < best[0]:
                    best = (d, i, j)
        _, i, j = best
        (ci, ki), (cj, kj) = colors[i], colors[j]
        merged = tuple((ci[t] * ki + cj[t] * kj) // (ki + kj) for t in range(3))
        colors[i] = [merged, ki + kj]
        del colors[j]
    palette = [BG] + [c for c, _ in colors]
    cache = {}
    def index(px):
        if not opaque(px):
            return 0
        c = px[:3]
        if c not in cache:
            cache[c] = 1 + min(range(len(colors)), key=lambda k: dist(c, colors[k][0]))
        return cache[c]
    return palette, [[[index(px) for px in row] for row in img] for img in images]


def shiny_palette(palette, index_imgs, shiny_imgs):
    """Per ogni indice, il colore più frequente nelle stesse posizioni delle immagini shiny."""
    votes = [Counter() for _ in palette]
    for idx, sh in zip(index_imgs, shiny_imgs):
        for y in range(80):
            for x in range(80):
                v = idx[y][x]
                if v and opaque(sh[y][x]):
                    votes[v][sh[y][x][:3]] += 1
    return [BG] + [votes[v].most_common(1)[0][0] if votes[v] else palette[v] for v in range(1, len(palette))]


def two_frames(idx):
    """160x80: lo stesso fotogramma due volte."""
    return [row + row for row in idx]


def write_sprite(path, idx_rows, palette):
    pal = palette + [(0, 0, 0)] * (16 - len(palette))
    pngpix.write(path, 160, 80, two_frames(idx_rows), pal, bd=4)


def write_pal(path, palette):
    pal = palette + [(0, 0, 0)] * (16 - len(palette))
    with open(path, 'w', newline='\r\n') as f:
        f.write('JASC-PAL\n0100\n16\n')
        for r, g, b in pal:
            f.write(f'{r} {g} {b}\n')


def convert_mon(front, back, front_shiny, back_shiny):
    imgs = []
    for p in [front, back, front_shiny, back_shiny]:
        w, h, rows = read_rgba(p)
        if w >= 160:
            w, h, rows = halve(w, h, rows)
        imgs.append(fit80(w, h, rows))
    palette, (fi, bi) = quantize(imgs[:2])
    shiny = shiny_palette(palette, [fi, bi], imgs[2:])
    return palette, shiny, fi, bi


def convert_icon(path, icon_palettes):
    """Icona Essentials 128x64 (2 fotogrammi 64x64, ingranditi 2x) -> 32x64 su una delle palette condivise."""
    w, h, rows = read_rgba(path)
    w, h, rows = halve(w, h, rows)       # 64x32
    frames = [[row[f * 32:(f + 1) * 32] for row in rows] for f in range(2)]
    if w < 64:                           # icona con un solo fotogramma
        frames = [[row[:32] for row in rows]] * 2
    pixels = [px[:3] for fr in frames for row in fr for px in row if opaque(px)]
    best = None
    for p, pal in enumerate(icon_palettes):
        err = sum(min(dist(c, q) for q in pal[1:]) for c in set(pixels))
        if best is None or err < best[0]:
            best = (err, p)
    p = best[1]
    pal = icon_palettes[p]
    cache = {}
    def index(px):
        if not opaque(px):
            return 0
        c = px[:3]
        if c not in cache:
            cache[c] = 1 + min(range(15), key=lambda k: dist(c, pal[k + 1]))
        return cache[c]
    out = [[index(px) for px in row] for fr in frames for row in fr]
    return p, out
