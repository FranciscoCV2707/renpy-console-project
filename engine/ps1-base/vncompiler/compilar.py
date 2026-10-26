"""Compilador compartido guion.json -> VNB1: texto, menus, expresiones y flujo entre paquetes.

Lo que todavia no compila (imagenes, audio, camara, pantallas, Python) se cuenta en el reporte: no se inventa su
efecto. Los capitulos se compilan de su etiqueta `chapter_*` hasta el final de su bloque.
"""
import struct
from collections import Counter

from . import formatos
from . import guion as g
from . import texto as t
from .operadores import OP_CODE

OP_SAY, OP_SAYX, OP_PAUSE, OP_MENU, OP_JUMP, OP_JIF, OP_SET, OP_ADD = 0x01, 0x02, 0x30, 0x40, 0x41, 0x42, 0x50, 0x51
OP_PUSH_VAR, OP_PUSH_CONST, OP_OP, OP_END = 0x52, 0x53, 0x54, 0x46
OP_CALL, OP_RETURN, OP_LOAD_CHAPTER, OP_STORE_VAR, OP_HALT = 0x43, 0x44, 0x45, 0x55, 0xFF
VISUAL = {"show", "scene", "hide", "with", "camera", "show_layer", "window", "play", "stop", "queue", "voice"}
NO_SOPORTADO = {"python", "statement", "screen", "while", "unknown"}


def constante(expr):
    """Valor de una expresion del guion si es una constante (`{"py", "tree": {"const": v}}`), o None."""
    if not isinstance(expr, dict):
        return None
    arbol = expr.get("tree", expr)
    return arbol.get("const") if isinstance(arbol, dict) and "const" in arbol else None


class Capitulo:
    """Estado de la compilacion de un capitulo: codigo, textos, etiquetas, variables y reporte."""

    def __init__(self, nombre, hablantes, guion, variables=None, destinations=None, chapter=0, text_layout=None):
        self.text_layout = text_layout
        self.nombre = nombre
        self.hablantes = hablantes
        self.guion = guion
        self.codigo = bytearray()
        self.textos = []
        self.line_ids = {}
        self.animations = []
        self.etiquetas = {}
        self.saltos = []                 # (posicion, etiqueta o ('abs', desplazamiento))
        self.variables = variables if variables is not None else {}
        self.destinations = destinations
        self.chapter = chapter
        self.links = []
        self.diagnostics = []
        label = g.buscar_etiqueta(guion, nombre) or {}
        self.parameters = {parameter["name"]: f"{nombre}:{parameter['name']}"
                           for parameter in label.get("parameters", [])}
        self.ultimo_hablante = 0
        self.reporte = Counter()
        self.avisos = []

    # ---- emision
    def _emit(self, *partes):
        for p in partes:
            self.codigo += p if isinstance(p, (bytes, bytearray)) else bytes([p])

    def _destino(self, clave):
        """Reserva 4 bytes para un destino u32; se rellena al final."""
        self.saltos.append((len(self.codigo), clave))
        self.codigo += b"\x00\x00\x00\x00"

    def _texto(self, texto_bytes):
        self.textos.append(texto_bytes)
        return len(self.textos) - 1

    def _variable(self, nombre):
        if nombre not in self.variables:
            if len(self.variables) >= 64:
                raise ValueError(f"mas de 64 variables en {self.nombre}")
            self.variables[nombre] = len(self.variables)
        return self.variables[nombre]

    def _hablante(self, who):
        if who is None:
            return 0
        if who not in self.hablantes:
            self.avisos.append(f"hablante desconocido: {who}")
            return 0
        return self.hablantes[who]

    def _decir(self, node):
        texto = g.texto_es(node)
        if texto is None:
            self.reporte["linea sin traducir"] += 1
            texto = node.get("text") or ""
        codigo, sin_soporte = t.convertir(texto)
        if self.text_layout:
            codigo = self.text_layout(codigo)
        for etiqueta in sin_soporte:
            self.reporte[f"etiqueta sin soporte {etiqueta}"] += 1
        indice = self._texto(codigo)
        if node.get("id"):
            self.line_ids[indice] = node["id"]
        if node.get("who") == "extend":           # `extend "..."`: sigue en la caja del hablante anterior
            self._emit(OP_SAYX, struct.pack("<BH", self.ultimo_hablante, indice))
            self.reporte["SAYX"] += 1
            return
        self.ultimo_hablante = self._hablante(node.get("who"))
        self._emit(OP_SAY, struct.pack("<BH", self.ultimo_hablante, indice))
        self.reporte["SAY"] += 1

    def _expression(self, expr):
        if not isinstance(expr, dict):
            return False
        tree = expr.get("tree", expr)
        if not isinstance(tree, dict):
            return False
        if "const" in tree:
            value = tree["const"]
            if not isinstance(value, (int, bool)) or not -32768 <= value <= 32767:
                return False
            self._emit(OP_PUSH_CONST, struct.pack("<h", value))
        elif "var" in tree:
            name = tree["var"]
            self._emit(OP_PUSH_VAR, self._variable(self.parameters.get(name, name)))
        elif "not" in tree:
            if not self._expression(tree["not"]):
                return False
            self._emit(OP_OP, OP_CODE["not"])
        elif "neg" in tree:
            self._emit(OP_PUSH_CONST, struct.pack("<h", 0))
            if not self._expression(tree["neg"]):
                return False
            self._emit(OP_OP, OP_CODE["-"])
        elif "and" in tree or "or" in tree:
            operator = "and" if "and" in tree else "or"
            operands = tree[operator]
            if not operands or not self._expression(operands[0]):
                return False
            for operand in operands[1:]:
                if not self._expression(operand):
                    return False
                self._emit(OP_OP, OP_CODE[operator])
        elif "bin" in tree and tree["bin"] in ("+", "-", "*"):
            if not self._expression(tree["l"]) or not self._expression(tree["r"]):
                return False
            self._emit(OP_OP, OP_CODE[tree["bin"]])
        elif "cmp" in tree:
            comparisons = tree["cmp"]
            rights = tree.get("r", [])
            if len(comparisons) != len(rights) or not comparisons:
                return False
            left = tree["l"]
            for index, (operator, right) in enumerate(zip(comparisons, rights)):
                if operator not in ("==", "!=", "<", "<=", ">", ">="):
                    return False
                if not self._expression(left) or not self._expression(right):
                    return False
                self._emit(OP_OP, OP_CODE[operator])
                if index:
                    self._emit(OP_OP, OP_CODE["and"])
                left = right
        else:
            return False
        return True

    def _condicion(self, expr):
        position = len(self.codigo)
        variables = dict(self.variables)
        if self._expression(expr):
            return True
        del self.codigo[position:]
        self.variables.clear()
        self.variables.update(variables)
        return False

    def _unsupported(self, node, reason):
        self.reporte[reason] += 1
        self.diagnostics.append({"where": node.get("where", self.nombre), "reason": reason,
                                 "op": node.get("op")})
        self._emit(OP_HALT)

    # ---- nodos
    def compilar(self, nodos):
        for node in nodos:
            self._nodo(node)

    def _nodo(self, node):
        op = node.get("op")
        if op == "say":
            self._decir(node)
        elif op in ("ps1_scene", "ps1_show", "ps1_hide"):
            self._visual_resolved(node)
        elif op == "ps1_audio":
            from .audio import encode_audio
            opcode, payload, name = encode_audio(node)
            self._emit(opcode, payload)
            self.reporte[name] += 1
        elif op == "ps1_special":
            special = node.get("special")
            if type(special) is not int or not 0 <= special <= 255:
                raise ValueError("id SPECIAL fuera de rango")
            self._emit(0x31, special)
            self.reporte["SPECIAL"] += 1
        elif op == "ps1_perspective":
            z11, zc, on = node.get("z11", 1000), node.get("zc", 0), node.get("on", 1)
            if type(z11) is not int or not 1 <= z11 <= 65535 or type(zc) is not int or not -32768 <= zc <= 32767 or on not in (0, 1):
                raise ValueError("ps1_perspective fuera de rango")
            self._emit(0x1B, struct.pack("<HhB", z11, zc, on))
            self.reporte["PERSPECTIVE"] += 1
        elif op == "ps1_depth":
            tag, z, zzoom = node.get("tag", 0), node.get("z", 0), node.get("zzoom", 0)
            if type(tag) is not int or not 0 <= tag <= 255 or type(z) is not int or not -32768 <= z <= 32767 or zzoom not in (0, 1):
                raise ValueError("ps1_depth fuera de rango")
            self._emit(0x1C, struct.pack("<BhB", tag, z, zzoom))
            self.reporte["DEPTH"] += 1
        elif op == "ps1_order":
            # ORDER (core/vm.c scene_order): pone `tag` justo encima (above 1) o debajo (above 0) de `ref`
            values = [node.get(key) for key in ("tag", "ref", "above")]
            if any(type(value) is not int or not 0 <= value <= 255 for value in values) or values[2] not in (0, 1):
                raise ValueError("ps1_order fuera de rango")
            self._emit(0x18, struct.pack("<BBB", *values))
            self.reporte["ORDER"] += 1
        elif op in ("ps1_transition", "ps1_camera"):
            fields = (("type", 0, 0, 6), ("a", 0, 0, 65535), ("b", 0, 0, 65535), ("c", 0, 0, 65535)) if op == "ps1_transition" else (
                ("zoom", 256, 1, 65535), ("x", 0, -32768, 32767), ("y", 0, -32768, 32767),
                ("frames", 0, 0, 65535), ("curve", 0, 0, 3))
            values = []
            for key, default, minimum, maximum in fields:
                value = node.get(key, default)
                if type(value) is not int or not minimum <= value <= maximum:
                    raise ValueError(f"{op}: {key} fuera de rango")
                values.append(value)
            self._emit(0x13 if op == "ps1_transition" else 0x16,
                       struct.pack("<BHHH" if op == "ps1_transition" else "<HhhHB", *values))
            self.reporte[op.removeprefix("ps1_").upper()] += 1
        elif op == "label":
            self.etiquetas[node["name"]] = len(self.codigo)
            self.compilar(node.get("body") or [])
        elif op == "menu":
            self._menu(node)
        elif op == "jump":
            self._salto(node)
        elif op == "call":
            self._salto(node, call=True)
        elif op == "return":
            if node.get("value") is not None:
                if not self._condicion(node["value"]):
                    self._unsupported(node, "sin soporte: valor de retorno")
                    return
                self._emit(OP_STORE_VAR, self._variable("_return"))
            self._emit(OP_RETURN)
            self.reporte["RETURN"] += 1
        elif op == "sequence":
            self.compilar(node.get("body") or [])
        elif op == "if":
            self._si(node)
        elif op == "set":
            self._asignar(node)
        elif op == "pause":
            segundos = constante(node.get("seconds"))
            if segundos is not None:
                self._emit(OP_PAUSE, struct.pack("<HB", int(round(float(segundos) * 60)), 0))
                self.reporte["PAUSE"] += 1
            else:
                self.reporte["pausa hasta clic (lo hace el SAY)"] += 1
        elif op in VISUAL:
            self.reporte[f"pendiente imagen/audio: {op}"] += 1
        elif op in NO_SOPORTADO:
            self.reporte[f"sin soporte: {op}"] += 1
            self.diagnostics.append({"where": node.get("where", self.nombre), "reason": f"sin soporte: {op}", "op": op})
        else:
            self.reporte[f"desconocido: {op}"] += 1

    def _visual_resolved(self, node):
        def integer(name, default, minimum, maximum):
            value = node.get(name, default)
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f"{node['op']}: {name} fuera de rango")
            return value

        op = node["op"]
        anim = integer("anim", 0, 0, 65535)
        if "keyframes" in node:
            if op == "ps1_hide" or anim:
                raise ValueError("keyframes incompatibles con hide o anim explicito")
            blob = formatos.animation(node["keyframes"], node.get("loop", False), node.get("events", ()),
                                      node.get("loop_start", 0))
            if blob not in self.animations:
                self.animations.append(blob)
            anim = self.animations.index(blob) + 1
        if op == "ps1_scene":
            fields = (integer("image", 0, 0, 65535), anim)
            self._emit(0x10, struct.pack("<HH", *fields))
        elif op == "ps1_show":
            fields = (integer("tag", None, 0, 255), integer("image", None, 1, 65535),
                      integer("position", 255, 0, 255), integer("z", -128, -128, 127),
                      integer("flags", 0, 0, 255), anim)
            self._emit(0x11, struct.pack("<BHBbBH", *fields))
        else:
            self._emit(0x12, integer("tag", None, 0, 255))
        self.reporte[op.removeprefix("ps1_").upper()] += 1

    def _menu(self, node):
        if node.get("say"):
            self._decir(node["say"])
        opciones = [c for c in node.get("choices", []) if not c.get("caption_only")]
        if len(opciones) > 16:
            raise ValueError(f"mas de 16 opciones en {self.nombre}")
        conditional = [index for index, choice in enumerate(opciones) if choice.get("if") is not None]
        if len(conditional) > 4:
            self._unsupported(node, "sin soporte: mas de 4 opciones condicionadas")
            return
        texts = []
        for c in opciones:
            texto = (c.get("tl") or {}).get("es") or c.get("text") or ""
            codigo, sin_soporte = t.convertir(texto)
            if self.text_layout:
                codigo = self.text_layout(codigo, menu=True)
            for etiqueta in sin_soporte:
                self.reporte[f"etiqueta sin soporte {etiqueta}"] += 1
            texts.append(self._texto(codigo))
        destinos = [[] for _ in opciones]
        fin_saltos = []

        def emit_menu(remaining, visible):
            if remaining:
                index = remaining[0]
                if not self._condicion(opciones[index]["if"]):
                    self._unsupported(node, "sin soporte: condicion de menu")
                    return
                self._emit(OP_JIF)
                position = len(self.codigo)
                self.codigo += bytes(4)
                emit_menu(remaining[1:], sorted(visible + [index]))
                struct.pack_into("<I", self.codigo, position, len(self.codigo))
                emit_menu(remaining[1:], visible)
            elif visible:
                self._emit(OP_MENU, bytes([0, len(visible)]))
                for index in visible:
                    self.codigo += struct.pack("<H", texts[index])
                    destinos[index].append(len(self.codigo))
                    self.codigo += bytes(4)
            else:
                fin_saltos.append(len(self.codigo))
                self._emit(OP_JUMP, bytes(4))

        emit_menu(conditional, [index for index in range(len(opciones)) if index not in conditional])
        for i, c in enumerate(opciones):
            for position in destinos[i]:
                struct.pack_into("<I", self.codigo, position, len(self.codigo))
            self.compilar(c.get("body") or [])
            fin_saltos.append(len(self.codigo))
            self._emit(OP_JUMP)
            self.codigo += b"\x00\x00\x00\x00"
        fin = len(self.codigo)
        for pos in fin_saltos:
            struct.pack_into("<I", self.codigo, pos + 1, fin)
        self.reporte["MENU"] += 1

    def _salto(self, node, call=False):
        destino = node.get("label")
        if destino is None:
            self._unsupported(node, "sin soporte: salto calculado o argumentos de llamada")
            return
        label = g.buscar_etiqueta(self.guion, destino)
        parameters = (label or {}).get("parameters", [])
        arguments = node.get("args") or []
        if parameters or arguments:
            bindings = {}
            position = 0
            for argument in arguments:
                if argument.get("kind") == "keyword":
                    name = argument["name"]
                elif argument.get("kind") == "positional" and position < len(parameters):
                    name = parameters[position]["name"]
                    position += 1
                else:
                    self._unsupported(node, "sin soporte: argumentos de llamada")
                    return
                if name in bindings or name not in {parameter["name"] for parameter in parameters}:
                    raise ValueError(f"argumento invalido: {name} en {destino}")
                bindings[name] = argument["value"]
            for parameter in parameters:
                value = bindings.get(parameter["name"], parameter.get("default"))
                if not call or not self._condicion(value):
                    self._unsupported(node, "sin soporte: argumentos de llamada")
                    return
                self._emit(OP_STORE_VAR, self._variable(f"{destino}:{parameter['name']}"))
        target = self.destinations.get(destino) if self.destinations is not None else None
        if target is not None and target[0] != self.chapter:
            self._emit(OP_LOAD_CHAPTER, struct.pack("<H", target[0]))
            self.links.append((len(self.codigo), destino))
            self.codigo += bytes(4)
            self._emit(0 if call else 1)
            self.reporte["LOAD_CHAPTER"] += 1
        else:
            self._emit(OP_CALL if call else OP_JUMP)
            self._destino(destino)
            self.reporte["CALL" if call else "JUMP"] += 1

    def _si(self, node):
        fin = []
        for rama in node.get("branches", []):
            if rama.get("if") is None:
                self.compilar(rama.get("body") or [])
                continue
            if not self._condicion(rama["if"]):
                self._unsupported(node, "sin soporte: condicion")
                return
            self._emit(OP_JIF)
            siguiente = len(self.codigo)
            self.codigo += b"\x00\x00\x00\x00"
            self.compilar(rama.get("body") or [])
            fin.append(len(self.codigo))
            self._emit(OP_JUMP)
            self.codigo += b"\x00\x00\x00\x00"
            struct.pack_into("<I", self.codigo, siguiente, len(self.codigo))
        for pos in fin:
            struct.pack_into("<I", self.codigo, pos + 1, len(self.codigo))
        self.reporte["IF"] += 1

    def _asignar(self, node):
        valor = constante(node.get("value"))
        if isinstance(valor, bool):
            valor = int(valor)
        if node.get("aug") not in (None, "+", "-", "*"):
            self._unsupported(node, "sin soporte: operador de asignacion")
            return
        if isinstance(valor, int) and -32768 <= valor <= 32767 and node.get("aug") in (None, "+"):
            var = self._variable(self.parameters.get(node["var"], node["var"]))
            if node.get("aug") == "+":
                self._emit(OP_ADD, bytes([var]), struct.pack("<h", valor))
            else:
                self._emit(OP_SET, bytes([var]), struct.pack("<h", valor))
            self.reporte["SET_VAR"] += 1
            return
        expression = node.get("value")
        if node.get("aug"):
            expression = {"bin": node["aug"], "l": {"var": node["var"]},
                          "r": expression.get("tree", expression)}
        if not self._condicion(expression):
            self._unsupported(node, "sin soporte: asignacion")
            return
        self._emit(OP_STORE_VAR, self._variable(self.parameters.get(node["var"], node["var"])))
        self.reporte["SET_VAR"] += 1

    # ---- cierre
    def terminar(self):
        self._emit(OP_RETURN if self.destinations is not None else OP_END)
        for pos, clave in self.saltos:
            if clave not in self.etiquetas:
                raise ValueError(f"etiqueta sin resolver en {self.nombre}: {clave}")
            else:
                destino = self.etiquetas[clave]
            struct.pack_into("<I", self.codigo, pos, destino)
        for position, label in self.links:
            target = self.destinations[label]
            if target[1] is None:
                raise ValueError(f"etiqueta sin enlazar: {label}")
            struct.pack_into("<I", self.codigo, position, target[1])
        return bytes(self.codigo)


def compilar_capitulo(guion, nombre, hablantes=None):
    """Compila la etiqueta `nombre` del guion. Devuelve (codigo VNB1, bloque de textos, Capitulo)."""
    nodo = g.buscar_etiqueta(guion, nombre)
    if nodo is None:
        raise ValueError(f"no existe la etiqueta {nombre}")
    cap = Capitulo(nombre, hablantes if hablantes is not None else g.hablantes(guion), guion)
    cap.compilar(nodo.get("body") or [])
    codigo = cap.terminar()
    bloque = formatos.bloque_texto(cap.textos)
    vnb = formatos.vnb(codigo, text_count=len(cap.textos), chapter=0, animations=cap.animations)
    formatos.check_chapter_size(nombre, vnb, bloque)
    return vnb, bloque, cap
