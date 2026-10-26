"""Parser y comparacion de lineas TRACE (contrato C3)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional


class TraceParseError(ValueError):
    def __init__(self, line_no: int, message: str):
        super().__init__(f"line {line_no}: {message}")
        self.line_no = line_no


@dataclass(init=False)
class TraceEvent:
    seq: int
    frame: int
    ev: str
    fields: dict

    def __init__(self, seq, frame, ev, fields=None, campos=None):
        self.seq = seq
        self.frame = frame
        self.ev = ev
        if fields is None and campos is not None:
            fields = campos
        self.fields = fields if fields is not None else {}

    @property
    def campos(self):
        return self.fields

    def __eq__(self, other):
        if not isinstance(other, TraceEvent):
            return NotImplemented
        return (
            self.seq == other.seq
            and self.frame == other.frame
            and self.ev == other.ev
            and self.fields == other.fields
        )


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


def parse_trace_file(path):
    return parse_file(path)


def filter_events(events: Iterable[TraceEvent], allowed) -> list[TraceEvent]:
    if not allowed:
        return list(events)
    allowed_set = set(allowed)
    return [e for e in events if e.ev in allowed_set]


def events_equal(a: TraceEvent, b: TraceEvent, tolerance_frames: int = 0) -> bool:
    if a.ev != b.ev:
        return False
    if a.fields != b.fields:
        return False
    if abs(a.frame - b.frame) > tolerance_frames:
        return False
    return True


@dataclass
class CompareResult:
    equal: bool
    index: Optional[int]
    actual: Optional[TraceEvent]
    reference: Optional[TraceEvent]
    message: str
    verdict: str
    scenario: Optional[str] = None


def compare_events(actual, reference, allowed_events=None, tolerance_frames: int = 0) -> CompareResult:
    fa = filter_events(actual, allowed_events)
    fr = filter_events(reference, allowed_events)
    n = min(len(fa), len(fr))
    for i in range(n):
        if not events_equal(fa[i], fr[i], tolerance_frames):
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


def resolve_scenario_path(p, base=None) -> Path:
    pp = Path(p)
    if pp.is_absolute():
        return pp
    if base is not None:
        base_path = Path(base)
        cand_base = base_path.parent if base_path.is_file() else base_path
        cand = cand_base / pp
        if cand.exists():
            return cand
    cand = Path.cwd() / pp
    if cand.exists():
        return cand
    return pp


def compare_scenario(scenario, trace_path, root=None) -> CompareResult:
    from .scenario import Scenario  # noqa: F401

    ref_path = resolve_scenario_path(scenario.reference, getattr(scenario, "source", None))
    ref_events = parse_file(ref_path)
    actual_events = parse_file(trace_path)
    allowed = getattr(scenario.compare, "events", None) if hasattr(scenario, "compare") else None
    if allowed is None and isinstance(scenario.compare, dict):
        allowed = scenario.compare.get("events")
    tol = getattr(scenario.compare, "tolerance", {}) if hasattr(scenario, "compare") else {}
    if isinstance(tol, dict):
        tol_frames = tol.get("frames", 0)
    else:
        tol_frames = getattr(tol, "frames", 0) or 0
    result = compare_events(actual_events, ref_events, allowed, tol_frames)
    result.scenario = getattr(scenario, "id", None)
    return result


TraceError = TraceParseError


def compare(*args, **kwargs):
    """Comparacion flexible: escenario+traza o dos trazas (rutas o listas de eventos)."""
    scenario = kwargs.pop("scenario", None)
    trace = kwargs.pop("trace", None)
    if scenario is not None and trace is not None:
        scen = scenario
        if isinstance(scen, (str, Path)):
            from .scenario import load_scenario

            scen = load_scenario(scen)
        return compare_scenario(scen, trace)
    if len(args) == 1 and isinstance(args[0], (str, Path)) and str(args[0]).endswith((".yaml", ".yml")):
        # compare(scenario_path, trace_path) handled below? fallback
        pass
    if len(args) >= 2:
        a, b = args[0], args[1]
        # scenario + trace
        if hasattr(a, "compare") or (isinstance(a, (str, Path)) and str(a).endswith((".yaml", ".yml"))):
            scen = a
            if isinstance(scen, (str, Path)):
                from .scenario import load_scenario

                scen = load_scenario(scen)
            return compare_scenario(scen, b)
        # two traces
        ae = a if not isinstance(a, (str, Path)) else parse_file(a)
        re = b if not isinstance(b, (str, Path)) else parse_file(b)
        allowed = kwargs.get("allowed_events", kwargs.get("events"))
        tol = kwargs.get("tolerance_frames", kwargs.get("tolerance", 0))
        if isinstance(tol, dict):
            tol = tol.get("frames", 0)
        return compare_events(ae, re, allowed, tol)
    if len(args) == 1:
        return args[0]
    return None


def compare_traces(actual, reference, allowed_events=None, tolerance_frames=0):
    ae = actual if not isinstance(actual, (str, Path)) else parse_file(actual)
    re = reference if not isinstance(reference, (str, Path)) else parse_file(reference)
    return compare_events(ae, re, allowed_events, tolerance_frames)