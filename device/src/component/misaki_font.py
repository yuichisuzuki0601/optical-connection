"""Read Misaki glyphs from flash without loading the whole font into RAM."""


_KANA_H2Z = (
    0x02, 0x0c, 0x0d, 0x01, 0xfb, 0xf2, 0xa1, 0xa3,
    0xa5, 0xa7, 0xa9, 0xe3, 0xe5, 0xe7, 0xc3, 0xfc,
    0xa2, 0xa4, 0xa6, 0xa8, 0xaa, 0xab, 0xad, 0xaf,
    0xb1, 0xb3, 0xb5, 0xb7, 0xb9, 0xbb, 0xbd, 0xbf,
    0xc1, 0xc4, 0xc6, 0xc8, 0xca, 0xcb, 0xcc, 0xcd,
    0xce, 0xcf, 0xd2, 0xd5, 0xd8, 0xdb, 0xde, 0xdf,
    0xe0, 0xe1, 0xe2, 0xe4, 0xe6, 0xe8, 0xe9, 0xea,
    0xeb, 0xec, 0xed, 0xef, 0xf3, 0x9b, 0x9c,
)
_LATIN_H2Z = {0xa2: 0xffe0, 0xa3: 0xffe1, 0xa5: 0xffe5,
              0xa6: 0xffe4, 0xac: 0xffe2, 0xaf: 0xffe3}


class MisakiFont:
    FONT_LEN = 7
    FONT_TOFU = 0x25a1

    def __init__(self):
        self._data = open('asset/font/misaki/misaki_font_data.bin', 'rb')
        self._table = open('asset/font/misaki/misaki_font_table.bin', 'rb')
        self._table.seek(0, 2)
        self._table_size = self._table.tell() // 2

    def find(self, code):
        low = 0
        high = self._table_size - 1
        while low <= high:
            pos = low + ((high - low + 1) >> 1)
            self._table.seek(pos * 2)
            value = self._table.read(2)
            current = value[0] | (value[1] << 8)
            if current == code:
                return pos
            if current < code:
                low = pos + 1
            else:
                high = pos - 1
        return -1

    def font(self, code, flgz=True):
        if flgz:
            if code == 0x20:
                code = 0x3000
            elif 0x20 <= code <= 0x7e:
                code = code - 0x20 + 0xff00
            elif 0xa1 <= code <= 0xff:
                code = _LATIN_H2Z.get(code, code)
            elif 0xff61 <= code <= 0xff9f:
                code = _KANA_H2Z[code - 0xff61] + 0x3000

        index = self.find(code)
        if index < 0:
            index = self.find(self.FONT_TOFU)
        self._data.seek(index * self.FONT_LEN)
        return tuple(self._data.read(self.FONT_LEN)) + (0,)
