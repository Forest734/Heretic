"""Read lumps and patches from a WAD, in its own palette."""
import struct


class Wad:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        kind, n, off = struct.unpack_from("<4sii", self.data, 0)
        self.lumps = []
        for i in range(n):
            pos, size, name = struct.unpack_from("<ii8s", self.data, off + 16 * i)
            self.lumps.append((name.rstrip(b"\0").decode("ascii").upper(), pos, size))

    def names(self):
        return [n for n, _, _ in self.lumps]

    def lump(self, name):
        # last one wins, as in the engine
        for n, pos, size in reversed(self.lumps):
            if n == name.upper():
                return self.data[pos:pos + size]
        raise KeyError(name)

    def palette(self, name="PLAYPAL"):
        p = self.lump(name)[:768]
        return [tuple(p[i:i + 3]) for i in range(0, 768, 3)]

    def patch(self, name):
        """(width, height, leftoffset, topoffset, rows) with None where transparent."""
        d = self.lump(name)
        w, h, lo, to = struct.unpack_from("<hhhh", d, 0)
        rows = [[None] * w for _ in range(h)]
        for x in range(w):
            (col,) = struct.unpack_from("<I", d, 8 + 4 * x)
            top = -1
            while d[col] != 0xFF:
                delta, length = d[col], d[col + 1]
                # tall patches: a delta not above the last one is relative
                top = delta if delta > top else top + delta
                for i in range(length):
                    if 0 <= top + i < h:
                        rows[top + i][x] = d[col + 3 + i]
                col += length + 4
        return w, h, lo, to, rows
