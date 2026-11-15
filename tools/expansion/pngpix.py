"""Legge un PNG indicizzato (1/2/4/8 bit, senza interlacciamento): dimensioni, indici dei pixel, palette."""
import struct, zlib


def chunks(path):
    d = open(path, 'rb').read()
    i = 8
    while i < len(d):
        n = struct.unpack('>I', d[i:i + 4])[0]
        yield d[i + 4:i + 8], d[i + 8:i + 8 + n]
        i += 12 + n


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def read(path):
    ch = list(chunks(path))
    w, h, bd, ct = struct.unpack('>IIBB', [b for t, b in ch if t == b'IHDR'][0][:10])
    plte = [b for t, b in ch if t == b'PLTE']
    pal = [tuple(plte[0][j:j + 3]) for j in range(0, len(plte[0]), 3)] if plte else []
    raw = zlib.decompress(b''.join(b for t, b in ch if t == b'IDAT'))
    stride = (w * bd + 7) // 8
    bpp = 1
    rows, prev, pos = [], bytearray(stride), 0
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
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4: line[x] = (line[x] + paeth(a, b, c)) & 255
        prev = line
        px = []
        if bd == 8:
            px = list(line)
        else:
            per = 8 // bd
            mask = (1 << bd) - 1
            for byte in line:
                for k in range(per):
                    px.append((byte >> (8 - bd * (k + 1))) & mask)
            px = px[:w]
        rows.append(px)
    return w, h, bd, rows, pal


def write(path, w, h, rows, pal, bd=8):
    raw = bytearray()
    for r in rows:
        raw.append(0)
        if bd == 8:
            raw += bytes(r)
        else:
            per = 8 // bd
            for x in range(0, w, per):
                v = 0
                for k in range(per):
                    v |= (r[x + k] if x + k < w else 0) << (8 - bd * (k + 1))
                raw.append(v)
    def chunk(t, b):
        return struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff)
    out = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, bd, 3, 0, 0, 0))
    out += chunk(b'PLTE', bytes(c for rgb in pal for c in rgb))
    out += chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')
    open(path, 'wb').write(out)
