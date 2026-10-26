"""Texto de Ren'Py a los codigos de control del motor (docs/bytecode.md, seccion 6).

Las etiquetas que el motor entiende se convierten en codigos; las demas se quitan y se cuentan en el reporte, para
revisarlas a mano (no se adivina su efecto).
"""
import re
import struct

TAG = re.compile(r"\{(/?)([a-z_]+)(?:=([^}]*))?\}")
SIMPLE = {
    ("i", False): b"\x01\x01", ("i", True): b"\x01\x00",
    ("b", False): b"\x01\x02", ("b", True): b"\x01\x00",
    ("nw", False): b"\x04",
    ("fast", False): b"\x05",
    ("sh", False): b"\x07", ("sh", True): b"\x08",
    ("sc", False): b"\x0e", ("sc", True): b"\x0f",
    ("cps", True): b"\x03\x00",          # cps 0 = velocidad por defecto (core/text.c)
}


def convertir(texto):
    """Texto en espanol -> (bytes UTF-8 con codigos, lista de etiquetas no soportadas)."""
    out = bytearray()
    sin_soporte = []
    pos = 0
    for m in TAG.finditer(texto):
        out += texto[pos:m.start()].replace("\n", "\x0a").encode("utf-8")
        pos = m.end()
        cierre, nombre, valor = m.group(1) == "/", m.group(2), m.group(3)
        try:
            if (nombre, cierre) in SIMPLE and valor is None:
                out += SIMPLE[(nombre, cierre)]
            elif nombre == "w" and valor and not cierre:
                out += b"\x02" + bytes([min(255, round(float(valor) * 10))])
            elif nombre == "cps" and valor and not cierre:
                out += b"\x03" + bytes([min(255, int(valor) // 5)])
            elif nombre == "size" and valor and not cierre:
                out += b"\x06" + struct.pack("b", max(-2, min(2, int(valor))))
            else:
                sin_soporte.append(m.group(0))
        except ValueError:                    # valores relativos como {cps=*1.5}: no se adivinan
            sin_soporte.append(m.group(0))
    out += texto[pos:].replace("\n", "\x0a").encode("utf-8")
    return bytes(out), sin_soporte
