"""Carga y validacion de escenarios del Test Lab (contrato C4)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


class ScenarioError(ValueError):
    def __init__(self, field_name: str, message: str):
        super().__init__(f"{field_name}: {message}")
        self.field = field_name


@dataclass
class CompareSpec:
    events: list[str]
    tolerance: dict = field(default_factory=dict)
    mode: str = "same"


@dataclass
class LimitsSpec:
    max_seconds: object = 0


@dataclass
class Scenario:
    id: str
    reference: str
    inputs: list
    expect: list
    compare: CompareSpec
    limits: LimitsSpec
    source: Optional[Path] = None

    @classmethod
    def from_dict(cls, data, source=None):
        if not isinstance(data, dict):
            raise ScenarioError("root", "scenario must be a mapping")
        for req in ("id", "reference", "inputs", "expect", "compare", "limits"):
            if req not in data:
                raise ScenarioError(req, "required field missing")
        sid = data["id"]
        if not isinstance(sid, str) or sid.strip() == "":
            raise ScenarioError("id", "must be a non-empty string")
        ref = data["reference"]
        if not isinstance(ref, str) or ref.strip() == "":
            raise ScenarioError("reference", "must be a non-empty string")
        inputs = data["inputs"]
        if not isinstance(inputs, list):
            raise ScenarioError("inputs", "must be a list")
        for i, item in enumerate(inputs):
            if not isinstance(item, dict):
                raise ScenarioError(f"inputs[{i}]", "must be a mapping")
        expect = data["expect"]
        if not isinstance(expect, list):
            raise ScenarioError("expect", "must be a list")
        for i, item in enumerate(expect):
            if not isinstance(item, dict):
                raise ScenarioError(f"expect[{i}]", "must be a mapping")
            if "ev" not in item:
                raise ScenarioError(f"expect[{i}].ev", "required")
            if not isinstance(item["ev"], str):
                raise ScenarioError(f"expect[{i}].ev", "must be a string")
        cmp_data = data["compare"]
        if not isinstance(cmp_data, dict):
            raise ScenarioError("compare", "must be a mapping")
        if "events" not in cmp_data:
            raise ScenarioError("compare.events", "required")
        events = cmp_data["events"]
        if not isinstance(events, list) or not all(isinstance(e, str) for e in events):
            raise ScenarioError("compare.events", "must be a list of strings")
        tolerance = cmp_data.get("tolerance", {})
        if not isinstance(tolerance, dict):
            raise ScenarioError("compare.tolerance", "must be a mapping")
        mode = cmp_data.get("mode", "same")
        if mode not in ("same", "renpy"):
            raise ScenarioError("compare.mode", "must be same or renpy")
        compare = CompareSpec(events=events, tolerance=tolerance, mode=mode)
        lim_data = data["limits"]
        if not isinstance(lim_data, dict):
            raise ScenarioError("limits", "must be a mapping")
        if "max_seconds" not in lim_data:
            raise ScenarioError("limits.max_seconds", "required")
        max_seconds = lim_data["max_seconds"]
        if isinstance(max_seconds, bool) or not isinstance(max_seconds, (int, float)):
            raise ScenarioError("limits.max_seconds", "must be a number")
        limits = LimitsSpec(max_seconds=max_seconds)
        return cls(
            id=sid,
            reference=ref,
            inputs=inputs,
            expect=expect,
            compare=compare,
            limits=limits,
            source=Path(source) if source is not None else None,
        )


def load_scenario(path):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return Scenario.from_dict(data, source=p)
