"""Simulacion determinista del flujo VNB1 para contrastarlo con core/vm.c."""
import struct


FORMATS = {0x00: "", 0x01: "BH", 0x02: "BH", 0x03: "B", 0x10: "HH", 0x11: "BHBbBH",
           0x12: "B", 0x13: "BHHH", 0x14: "BHBB", 0x15: "H", 0x16: "HhhHB", 0x17: "H", 0x1B: "HhB", 0x1C: "BhB",
           0x18: "BBB", 0x20: "HBB", 0x21: "B", 0x22: "BHB", 0x23: "BB", 0x24: "H",
           0x25: "B", 0x26: "BBB", 0x27: "H", 0x30: "HB", 0x31: "B", 0x41: "I",
           0x42: "I", 0x43: "I", 0x44: "", 0x45: "HIB", 0x46: "", 0x50: "Bh", 0x51: "Bh",
           0x52: "B", 0x53: "h", 0x54: "B", 0x55: "B", 0x60: "H", 0x61: "B", 0x62: "B",
           0xFE: "H", 0xFF: ""}


def signed(value):
    return (value + 32768) % 65536 - 32768


def simulate(chapters, start=0, choices=(), max_steps=1000000, initial_variables=None):
    variables = [0] * 64 if initial_variables is None else list(initial_variables)
    if len(variables) != 64:
        raise ValueError("se requieren 64 variables")
    queue = iter(choices)
    chapter, pc = start, 0
    stack, calls, trace = [], [], []

    def read(fmt):
        nonlocal pc
        size = struct.calcsize("<" + fmt)
        if pc + size > len(code):
            raise ValueError("instruccion truncada")
        fields = struct.unpack_from("<" + fmt, code, pc)
        pc += size
        return fields

    for _ in range(max_steps):
        if chapter not in chapters:
            raise ValueError(f"capitulo no disponible: {chapter}")
        data = chapters[chapter]
        if len(data) < 32 or data[:4] != b"VNB1":
            raise ValueError("cabecera VNB1 invalida")
        size, text_base, text_count = struct.unpack_from("<IIH", data, 8)
        if size > len(data) - 32:
            raise ValueError("codigo VNB1 truncado")
        code = data[32:32 + size]
        if pc >= len(code):
            raise ValueError("pc fuera de rango")
        opcode = code[pc]
        pc += 1
        if opcode == 0x40:
            flags, count = read("BB")
            if not 1 <= count <= 16:
                raise ValueError("cantidad de opciones invalida")
            options = [read("HI") for _ in range(count)]
            if any(text >= text_count for text, _ in options):
                raise ValueError("texto de menu fuera de rango")
            trace.append("MENU " + " ".join(map(str, [count] + [text for text, _ in options])))
            choice = next(queue, 0)
            if not 0 <= choice < count:
                raise ValueError("opcion de menu invalida")
            pc = options[choice][1]
            continue
        if opcode not in FORMATS:
            raise ValueError(f"opcode sin soporte: {opcode:02x}")
        fields = read(FORMATS[opcode])
        required = 0
        if opcode in (0x42, 0x55):
            required = 1
        elif opcode == 0x54:
            required = 1 if fields[0] == 8 else 2
        if len(stack) < required:
            raise ValueError("pila vacia")
        if opcode in (0x01, 0x02):
            speaker, text = fields
            if text >= text_count:
                raise ValueError("texto fuera de rango")
            trace.append(f"SAY {chapter} {text} {text_base + text} {speaker}")
        elif opcode == 0x41:
            pc = fields[0]
        elif opcode == 0x42:
            if not stack.pop():
                pc = fields[0]
        elif opcode == 0x43:
            if len(calls) >= 8:
                raise ValueError("pila de CALL desbordada")
            calls.append((chapter, pc))
            pc = fields[0]
        elif opcode == 0x44:
            if not calls:
                break
            chapter, pc = calls.pop()
        elif opcode == 0x45:
            if fields[2] == 0:
                if len(calls) >= 8:
                    raise ValueError("pila de CALL desbordada")
                calls.append((chapter, pc))
            chapter, pc = fields[:2]
        elif opcode == 0x46:
            break
        elif opcode in (0x50, 0x51, 0x52, 0x55):
            index = fields[0]
            if index >= 64:
                raise ValueError("variable fuera de rango")
            if opcode == 0x50:
                variables[index] = fields[1]
            elif opcode == 0x51:
                variables[index] = signed(variables[index] + fields[1])
            elif opcode == 0x52:
                stack.append(variables[index])
            else:
                variables[index] = stack.pop()
        elif opcode == 0x53:
            stack.append(fields[0])
        elif opcode == 0x54:
            operator = fields[0]
            right = stack.pop()
            if operator == 8:
                stack.append(int(not right))
            else:
                left = stack.pop()
                operations = {0: lambda: left == right, 1: lambda: left != right,
                              2: lambda: left < right, 3: lambda: left <= right,
                              4: lambda: left > right, 5: lambda: left >= right,
                              6: lambda: bool(left and right), 7: lambda: bool(left or right),
                              9: lambda: left + right, 10: lambda: left - right, 11: lambda: left * right}
                if operator not in operations:
                    raise ValueError("operador invalido")
                stack.append(signed(int(operations[operator]())))
        elif opcode == 0xFF:
            raise ValueError(f"HALT en capitulo {chapter}, offset {pc - 1}")
        if len(stack) > 16:
            raise ValueError("pila de expresiones desbordada")
    else:
        raise ValueError("limite de pasos de simulacion")
    trace += ["END", "VARS " + ",".join(map(str, variables))]
    return trace
