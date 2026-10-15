"""Compose 320x200 screens from a WAD's own patches, fonts and flats,
keeping every pixel a palette index."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wad import Wad
from PIL import Image

W, H = 320, 200


class Screen:
    def __init__(self, wad, fill=0):
        self.wad = wad
        self.pal = wad.palette()
        self.px = bytearray([fill]) * (W * H)
        cm = wad.lump("COLORMAP")
        self.colormap = [cm[i * 256:(i + 1) * 256] for i in range(len(cm) // 256)]
        names = wad.names()
        self.fonta = names.index("FONTA_S") + 1
        self.fontb = names.index("FONTB_S") + 1
        self.black = min(range(256), key=lambda i: sum(self.pal[i]))
        self.custom = self._brackets()

    def _brackets(self):
        """FONTA has no [ or ]: build them from the strokes of its I."""
        names = self.wad.names()
        _, _, _, _, I = self.wad.patch(names[self.fonta + ord("I") - 33])
        k = I[0][1]
        rows = [[k, k, k, k, None],
                [k, I[1][2], I[1][1], I[1][3], k],
                [k, I[2][2], k, k, None],
                [k, I[3][2], k, None, None],
                [k, I[4][2], k, None, None],
                [k, I[5][2], k, k, None],
                [k, I[6][2], I[6][1], I[6][3], k],
                [k, k, k, k, None]]
        mirror = [list(reversed(r)) for r in rows]
        return {"[": (5, 8, 0, 0, rows), "]": (5, 8, 0, 0, mirror)}

    # -- pixels
    def put(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.px[y * W + x] = c

    def get(self, x, y):
        return self.px[y * W + x]

    def image(self, im, x=0, y=0):
        """Paste a palette image (PLAYPAL indices) or another Screen."""
        if isinstance(im, Screen):
            src, w, h = im.px, W, H
        else:
            src, (w, h) = im.tobytes(), im.size
        for j in range(h):
            for i in range(w):
                self.put(x + i, y + j, src[j * w + i])

    def flat(self, name, light=0, x0=0, y0=0, x1=W, y1=H):
        f = self.wad.lump(name)
        cm = self.colormap[light]
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.px[y * W + x] = cm[f[(y & 63) * 64 + (x & 63)]]

    def darken(self, light, x0=0, y0=0, x1=W, y1=H):
        cm = self.colormap[light]
        for y in range(max(0, y0), min(H, y1)):
            for x in range(max(0, x0), min(W, x1)):
                self.px[y * W + x] = cm[self.px[y * W + x]]

    def box(self, x0, y0, x1, y1, c):
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.put(x, y, c)

    # -- patches
    def patch(self, name, x, y, offsets=True, remap=None, scale=1):
        w, h, lo, to, rows = self.wad.patch(name) if isinstance(name, str) else name
        if offsets:
            x -= lo * scale; y -= to * scale
        for j in range(h * scale):
            for i in range(w * scale):
                c = rows[j // scale][i // scale]
                if c is not None:
                    self.put(x + i, y + j, remap[c] if remap else c)
        return w * scale, h * scale

    def patch_size(self, name):
        w, h, lo, to, rows = self.wad.patch(name)
        return w, h

    # -- text, spaced as MN_DrTextA / MN_DrTextB
    def _glyphs(self, s, base):
        out = []
        for ch in s.upper():
            c = ord(ch)
            if base == self.fonta and ch in self.custom:
                out.append(self.custom[ch])
            else:
                out.append(None if c < 33 else self.wad.lumps[base + c - 33][0])
        return out

    def text_width(self, s, big=False):
        base, space = (self.fontb, 8) if big else (self.fonta, 5)
        x = 0
        for g in self._glyphs(s, base):
            x += space if g is None else (g[0] if isinstance(g, tuple) else self.patch_size(g)[0]) - 1
        return x

    def text(self, s, x, y, big=False, shadow=True, remap=None, center=False):
        base, space = (self.fontb, 8) if big else (self.fonta, 5)
        if center:
            x = (W - self.text_width(s, big)) // 2 if center is True else center - self.text_width(s, big) // 2
        if shadow:
            sh = [self.black] * 256
            self.text(s, x + 1, y + 1, big, False, sh)
        for g in self._glyphs(s, base):
            if g is None:
                x += space
            else:
                w, h = self.patch(g, x, y, offsets=False, remap=remap)
                x += w - 1
        return x

    def ramp(self, target):
        """Remap a glyph's greys onto a colour: index -> nearest palette
        entry to target scaled by the grey's brightness."""
        out = []
        for c in self.pal:
            v = sum(c) / (3 * 255)
            want = tuple(min(255, int(t * v * 1.25)) for t in target)
            out.append(self.nearest(want))
        return out

    def nearest(self, rgb):
        return min(range(256), key=lambda i: sum((a - b) ** 2 for a, b in zip(self.pal[i], rgb)))

    def save(self, path):
        im = Image.frombytes("P", (W, H), bytes(self.px))
        im.putpalette([b for c in self.pal for b in c])
        im.save(path)
        return im
