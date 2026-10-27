"""Parser y comparacion de lineas TRACE (contrato C3)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class TraceParseError(ValueError):
    def __init__(self, line_no: int, message: str):
        super().__init__(f"line {line_no}: {message}")
        self.line_no = line_no


@dataclass
class TraceEvent:
    seq: int
    frame: int
    ev: str
    fields: dict = None

    def __post_init__(self):
        if self.fields is None:
            self.fields = {}


@dataclass
class CompareResult:
    equal: bool
    index: Optional[int]
    actual: Optional[TraceEvent]
    reference: Optional[TraceEvent]
    message: str
    verdict: str
    scenario: Optional[str] = None


def parse_line(line: str, line_no: int = 1) -> Optional[TraceEvent]:
    """Parsea una linea TRACE. Devuelve None si no empieza con ``T|`` (se ignora)."""
    s = line.strip()
    if s == "" or not s.startswith("T|"):
        return None
    parts = s[2:].split("|", 3)
    if len(parts) < 3:
        raise TraceParseError(line_no, "malformed trace line: expected seq|frame|EV")
    seq_str, frame_str, ev = parts[0], parts[1], parts[2]
    if ev == "":
        raise TraceParseError(line_no, "empty event name")
    try:
        seq = int(seq_str)
    except ValueError:
        raise TraceParseError(line_no, f"invalid seq: {seq_str!r}")
    try:
        frame = int(frame_str)
    except ValueError:
        raise TraceParseError(line_no, f"invalid frame: {frame_str!r}")
    fields: dict = {}
    if len(parts) == 4:
        field_str = parts[3]
        if field_str != "":
            for pair in field_str.split(";"):
                if "=" not in pair:
                    raise TraceParseError(line_no, f"malformed field: {pair!r}")
                key, value = pair.split("=", 1)
                if key == "":
                    raise TraceParseError(line_no, "empty field name")
                fields[key] = value
    return TraceEvent(seq=seq, frame=frame, ev=ev, fields=fields)


def parse_trace(text: str) -> list[TraceEvent]:
    events: list[TraceEvent] = []
    for i, line in enumerate(text.splitlines(), 1):
        ev = parse_line(line, i)
        if ev is not None:
            events.append(ev)
    return events


def parse_file(path) -> list[TraceEvent]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    return parse_trace(text)


def _filter_events(events, allowed):
    if not allowed:
        return list(events)
    allowed_set = set(allowed)
    return [e for e in events if e.ev in allowed_set]


def _events_equal(a, b, tolerance_frames=0):
    if a.ev != b.ev:
        return False
    if a.fields != b.fields:
        return False
    if abs(a.frame - b.frame) > tolerance_frames:
        return False
    return True


def compare_events(actual, reference, allowed_events=None, tolerance_frames=0) -> CompareResult:
    fa = _filter_events(actual, allowed_events)
    fr = _filter_events(reference, allowed_events)
    n = min(len(fa), len(fr))
    for i in range(n):
        if not _events_equal(fa[i], fr[i], tolerance_frames):
            return CompareResult(
                equal=False,
                index=i,
                actual=fa[i],
                reference=fr[i],
                message=f"first divergent at index {i}: actual {fa[i].ev} vs reference {fr[i].ev}",
                verdict="FAIL",
            )
    if len(fa) != len(fr):
        i = n
        a = fa[i] if i < len(fa) else None
        r = fr[i] if i < len(fr) else None
        return CompareResult(
            equal=False,
            index=i,
            actual=a,
            reference=r,
            message=f"length mismatch: actual {len(fa)} vs reference {len(fr)} events",
            verdict="FAIL",
        )
    return CompareResult(
        equal=True,
        index=None,
        actual=None,
        reference=None,
        message="traces match",
        verdict="PASS",
    )


def _lookup_speaker(snoot_map, index):
    speakers = (snoot_map or {}).get("speakers", {})
    if index in speakers:
        return speakers[index]
    try:
        i = int(index)
    except (TypeError, ValueError):
        return ""
    if i in speakers:
        return speakers[i]
    if str(i) in speakers:
        return speakers[str(i)]
    return ""


def _lookup_text(snoot_map, gid):
    text_map = (snoot_map or {}).get("text", {})
    if gid in text_map:
        return text_map[gid]
    try:
        i = int(gid)
    except (TypeError, ValueError):
        return None
    if i in text_map:
        return text_map[i]
    if str(i) in text_map:
        return text_map[str(i)]
    return None


def normalize_engine(events, snoot_map) -> list:
    """Traduce una traza del motor a la forma comun (SAY who=<nombre>;id=<tid>, CHOICE i=<n>)."""
    out: list = []
    for e in events:
        if e.ev == "SAY":
            who_raw = e.fields.get("who", "")
            try:
                who_idx = int(who_raw) if who_raw not in ("", None) else 0
            except (TypeError, ValueError):
                who_idx = 0
            name = _lookup_speaker(snoot_map, who_idx)
            tid = _lookup_text(snoot_map, e.fields.get("text"))
            if tid is None:
                tid = ""
            out.append(TraceEvent(seq=e.seq, frame=e.frame, ev="SAY",
                                 fields={"who": name, "id": tid}))
        elif e.ev == "CHOICE":
            out.append(TraceEvent(seq=e.seq, frame=e.frame, ev="CHOICE",
                                 fields={"i": e.fields.get("i", "")}))
    return out


def normalize_renpy(events) -> list:
    """Deja solo SAY (who, id) y CHOICE (i) de una traza de Ren'Py."""
    out: list = []
    for e in events:
        if e.ev == "SAY":
            out.append(TraceEvent(seq=e.seq, frame=e.frame, ev="SAY",
                                 fields={"who": e.fields.get("who", ""),
                                         "id": e.fields.get("id", "")}))
        elif e.ev == "CHOICE":
            out.append(TraceEvent(seq=e.seq, frame=e.frame, ev="CHOICE",
                                 fields={"i": e.fields.get("i", "")}))
    return out


def compare_cross(actual, reference) -> CompareResult:
    """Alinea dos secuencias ya normalizadas y reporta el primer evento divergente."""
    fa = list(actual)
    fr = list(reference)
    n = min(len(fa), len(fr))
    for i in range(n):
        a, b = fa[i], fr[i]
        if a.ev != b.ev or a.fields != b.fields:
            return CompareResult(
                equal=False,
                index=i,
                actual=a,
                reference=b,
                message=f"first divergent at index {i}: actual {a.ev} vs reference {b.ev}",
                verdict="FAIL",
            )
    if len(fa) != len(fr):
        i = n
        a = fa[i] if i < len(fa) else None
        r = fr[i] if i < len(fr) else None
        return CompareResult(
            equal=False,
            index=i,
            actual=a,
            reference=r,
            message=f"length mismatch: actual {len(fa)} vs reference {len(fr)} events",
            verdict="FAIL",
        )
    return CompareResult(
        equal=True,
        index=None,
        actual=None,
        reference=None,
        message="traces match",
        verdict="PASS",
    )


def compare_scenario(scenario, trace_path) -> CompareResult:
    ref_path = Path(scenario.reference)
    if not ref_path.is_absolute():
        base = scenario.source
        if base is not None:
            base_path = Path(base)
            cand_base = base_path.parent if base_path.is_file() else base_path
            cand = cand_base / ref_path
            if cand.exists():
                ref_path = cand
            else:
                cand2 = Path.cwd() / ref_path
                if cand2.exists():
                    ref_path = cand2
        else:
            cand = Path.cwd() / ref_path
            if cand.exists():
                ref_path = cand
    ref_events = parse_file(ref_path)
    actual_events = parse_file(trace_path)
    mode = getattr(scenario.compare, "mode", "same")
    if mode == "renpy":
        try:
            from .snoot_map import load_map
            snoot_map = load_map()
        except (RuntimeError, OSError, ValueError, ImportError):
            snoot_map = None
        norm_actual = normalize_engine(actual_events, snoot_map)
        norm_ref = normalize_renpy(ref_events)
        result = compare_cross(norm_actual, norm_ref)
        result.scenario = scenario.id
        return result
    allowed = scenario.compare.events
    tol_frames = scenario.compare.tolerance.get("frames", 0)
    result = compare_events(actual_events, ref_events, allowed, tol_frames)
    result.scenario = scenario.id
    return result
