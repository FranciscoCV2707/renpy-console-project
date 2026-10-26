"""Ajuste y paginacion con las metricas de la fuente FNT1 usada por la consola."""
import struct


class TextLayout:
    def __init__(self, font, dialogue_width=304, menu_width=280, dialogue_height=54):
        if len(font) < 8 or font[:4] != b"FNT1" or not font[4]:
            raise ValueError("fuente FNT1 invalida")
        count = struct.unpack_from("<H", font, 6)[0]
        if len(font) < 8 + count * 10:
            raise ValueError("tabla FNT1 truncada")
        self.metrics = {}
        for index in range(count):
            code, style, _, _, width, _, xoff, _, advance = struct.unpack_from("<HBBBBBbbB", font, 8 + index * 10)
            self.metrics[code, style] = (advance, max(advance, xoff + width + (style == 2)))
        self.dialogue_width = dialogue_width
        self.menu_width = menu_width
        self.rows = dialogue_height // font[4]
        if min(dialogue_width, menu_width, self.rows) < 1:
            raise ValueError("caja de texto invalida")

    def __call__(self, data, menu=False):
        tokens = []
        position = 0
        while position < len(data):
            value = data[position]
            size = 2 if value in (1, 2, 3, 6) else 1 if value < 128 else 2 if value < 224 else 3 if value < 240 else 4
            token = data[position:position + size]
            if len(token) != size:
                raise ValueError("texto truncado")
            position += size
            if menu and value < 32 and value != 10:
                continue
            tokens.append(token)
        width = self.menu_width if menu else self.dialogue_width
        output = bytearray()
        line = []
        row = 1
        style = 0

        def measure(parts):
            advance = extent = 0
            current = style
            for token in parts:
                if token[0] == 1:
                    current = token[1]
                elif token[0] >= 32:
                    code = ord(token.decode("utf-8"))
                    step, ink = self.metrics.get((code, int(current == 1)), (0, 0))
                    extent = max(extent, advance + ink + int(current == 2))
                    advance += step
            return extent

        def flush(force_page=False):
            nonlocal line, row, style
            for token in line:
                output.extend(token)
                if token[0] == 1:
                    style = token[1]
            page = not menu and (force_page or row >= self.rows)
            output.append(11 if page else 10)
            row = 1 if page else row + 1
            if page and style:
                output.extend((1, style))
            line = []

        word = []

        def append_word():
            nonlocal line, word
            if not word:
                return
            spacer = [b" "] if line else []
            if line and measure(line + spacer + word) > width:
                flush()
                spacer = []
            line += spacer
            for token in word:
                if token[0] >= 32 and measure(line + [token]) > width:
                    flush()
                line.append(token)
            word = []

        for token in tokens:
            if token in (b" ", b"\n", b"\x0b"):
                append_word()
                if token != b" ":
                    flush(token == b"\x0b")
            else:
                word.append(token)
        append_word()
        for token in line:
            output.extend(token)
        return bytes(output)
