from dataclasses import dataclass, field

import pytest

from vncompiler.programa import compile_program
from vncompiler.temporal import animation_from_timeline, transition_from_spec


@dataclass
class Timeline:
    duration: float = 1
    loop_start: float | None = None
    diagnostics: list = field(default_factory=list)

    def sample(self, seconds):
        alignment = min(1, seconds) ** 2
        return {"xpos": 1920 * alignment, "xanchor": 6000 * alignment,
                "ypos": 1080, "yanchor": 1080, "zoom": 1, "alpha": 1}


def test_timeline_samples_curves_into_existing_animation_keys():
    result = animation_from_timeline(Timeline(), (1920, 1080), (6000, 1080), tolerance=6)
    assert result["keyframes"][0]["x"] == 0
    assert result["keyframes"][-1]["x"] == 256
    assert 2 < len(result["keyframes"]) <= 64
    assert result["sampling"]["fps"] == 60
    script = {"script": {"test": [{"op": "label", "name": "start", "body": [
        {"op": "ps1_scene", "image": 1, "keyframes": result["keyframes"]},
        {"op": "ps1_transition", "type": 1, "a": 60},
        {"op": "ps1_camera", "zoom": 300, "frames": 60}, {"op": "return"}]}]}}
    chapter = compile_program(script, ["start"]).chapters[0][2]
    assert len(chapter.animations) == 1
    assert chapter.reporte["TRANSITION"] == chapter.reporte["CAMERA"] == 1


@pytest.mark.parametrize("timeline", [Timeline(diagnostics=["unknown"]), Timeline(loop_start=0.5),
                                     Timeline(duration=2000)])
def test_unrepresentable_timeline_is_not_silently_accepted(timeline):
    with pytest.raises(ValueError):
        animation_from_timeline(timeline, (1920, 1080), (6000, 1080))


def test_key_budget_failure_is_explicit():
    with pytest.raises(ValueError, match="presupuesto"):
        animation_from_timeline(Timeline(), (1920, 1080), (6000, 1080), max_keys=2)


def test_inherited_clock_cannot_be_silently_dropped():
    timeline = Timeline()
    timeline.clock_offset = .25
    with pytest.raises(ValueError, match="reloj de fase"):
        animation_from_timeline(timeline, (1920, 1080), (6000, 1080))


@dataclass
class CycleTimeline:
    """Mimics the kit contract: clock_offset shifts the clock, later laps use cycle_tracks."""
    first: object
    steady: object
    clock_offset: float = 0.0
    cycle: bool = True
    duration: float = 1
    loop_start: float | None = 0
    diagnostics: list = field(default_factory=list)

    @property
    def cycle_tracks(self):
        return [] if self.cycle else None

    def sample(self, seconds):
        seconds += self.clock_offset
        curve = self.first
        if seconds >= self.duration:
            seconds %= self.duration
            curve = self.steady if self.cycle else self.first
        alignment = curve(seconds)
        return {"xpos": 1920 * alignment, "xanchor": 6000 * alignment,
                "ypos": 1080, "yanchor": 1080, "zoom": 1, "alpha": 1}


def triangle(seconds):
    return 1 - abs(2 * seconds - 1)


def first_lap(seconds):
    return 0.5 + seconds / 2


def table(timeline):
    return animation_from_timeline(timeline, (1920, 1080), (6000, 1080), tolerance=1)


def test_distinct_first_pass_cannot_be_encoded_as_a_single_loop():
    with pytest.raises(ValueError, match="ciclo estable"):
        table(CycleTimeline(first_lap, triangle))


def test_inherited_phase_rotates_a_periodic_loop():
    keys = table(CycleTimeline(triangle, triangle, clock_offset=.25, cycle=False))
    assert keys["loop"]
    assert keys["keyframes"][0]["x"] == 128
    assert max(keys["keyframes"], key=lambda key: key["x"])["frame"] == 15


def test_inherited_phase_past_the_first_pass_uses_the_steady_cycle():
    keys = table(CycleTimeline(first_lap, triangle, clock_offset=1.25))
    assert keys["loop"]
    assert keys["keyframes"][0]["x"] == 128
    assert keys["keyframes"] == table(CycleTimeline(triangle, triangle, clock_offset=.25, cycle=False))["keyframes"]


def test_first_pass_remainder_matching_the_cycle_is_accepted():
    def converged(seconds):
        return first_lap(seconds) if seconds < .5 else triangle(seconds)
    assert table(CycleTimeline(converged, triangle, clock_offset=.5))["keyframes"][0]["x"] == 256
    with pytest.raises(ValueError, match="ciclo estable"):
        table(CycleTimeline(converged, triangle, clock_offset=.25))


def test_phase_without_loop_or_negative_is_rejected():
    with pytest.raises(ValueError, match="reloj de fase"):
        table(CycleTimeline(triangle, triangle, clock_offset=.25, loop_start=None))
    with pytest.raises(ValueError, match="invalido"):
        table(CycleTimeline(triangle, triangle, clock_offset=-1, cycle=False))


def test_neutral_transitions_use_existing_engine_opcodes():
    assert transition_from_spec({"kind": "dissolve", "duration": 1.2}) == {"op": "ps1_transition", "type": 1, "a": 72}
    assert transition_from_spec({"kind": "fade", "out": 1, "hold": 0, "in": 2, "color": "#fff"}) == {
        "op": "ps1_transition", "type": 6, "a": 60, "b": 0, "c": 120}
    with pytest.raises(ValueError):
        transition_from_spec({"kind": "dissolve", "duration": -1})


@pytest.mark.parametrize("node", [{"op": "ps1_camera", "zoom": 0}, {"op": "ps1_transition", "type": 7},
                                  {"op": "ps1_transition", "a": -1}])
def test_resolved_temporal_opcode_ranges(node):
    with pytest.raises(ValueError):
        compile_program({"script": {"a": [{"op": "label", "name": "start", "body": [node]}]}}, ["start"])


@dataclass
class ChildTimeline(Timeline):
    children: list = field(default_factory=list)


def resolve(child):
    return {"image": {"a": 2, "b": 3}[child["image"]], "dissolve": 30 if child["transition"] else 0}


def test_child_changes_become_image_events():
    timeline = ChildTimeline(children=[{"time": 0.5, "image": "a", "transition": "dissolve"}])
    with pytest.raises(ValueError, match="resolver"):
        animation_from_timeline(timeline, (1920, 1080), (6000, 1080), tolerance=6)
    result = animation_from_timeline(timeline, (1920, 1080), (6000, 1080), tolerance=6, resolve_child=resolve)
    assert result["events"] == [{"image": 2, "dissolve": 30, "frame": 30}]


def test_looping_child_changes_must_restart_like_renpy():
    blink = [{"time": 0.5, "image": "a", "transition": None}, {"time": 0.75, "image": "b", "transition": None}]
    timeline = ChildTimeline(loop_start=0, children=blink)
    with pytest.raises(ValueError, match="reiniciar"):
        animation_from_timeline(timeline, (1920, 1080), (6000, 1080), tolerance=6, resolve_child=resolve)
    result = animation_from_timeline(timeline, (1920, 1080), (6000, 1080), tolerance=6, resolve_child=resolve,
                                     base_image=3)
    assert [event["frame"] for event in result["events"]] == [30, 45]
    starts = ChildTimeline(loop_start=0, children=[{"time": 0, "image": "a", "transition": None}, blink[1]])
    result = animation_from_timeline(starts, (1920, 1080), (6000, 1080), tolerance=6, resolve_child=resolve)
    assert [event["image"] for event in result["events"]] == [2, 3]


@dataclass
class ColorTimeline(Timeline):
    colors: list = field(default_factory=list)

    def color_at(self, seconds):
        return [], self.colors[0]["operations"], min(1, seconds)


def test_multiplicative_matrixcolor_becomes_rgb_modulation():
    timeline = ColorTimeline(colors=[{"time": 0, "duration": 1, "curve": "linear",
                                      "operations": [["colorize", ["#000", "#ff8000"]], ["opacity", [0.5]]]}])
    keys = animation_from_timeline(timeline, (1920, 1080), (6000, 1080), tolerance=6)["keyframes"]
    assert (keys[0]["r"], keys[0]["g"], keys[0]["b"], keys[0]["alpha"]) == (128, 128, 128, 255)
    assert (keys[-1]["r"], keys[-1]["g"], keys[-1]["b"], keys[-1]["alpha"]) == (128, 64, 0, 128)


def test_matrixcolor_the_gpu_cannot_multiply_is_rejected():
    timeline = ColorTimeline(colors=[{"time": 0, "duration": 1, "curve": "linear",
                                      "operations": [["brightness", [0.2]]]}])
    with pytest.raises(ValueError, match="horneada"):
        animation_from_timeline(timeline, (1920, 1080), (6000, 1080), tolerance=6)


@dataclass
class BlurTimeline(Timeline):
    def sample(self, seconds):
        return {**super().sample(seconds), "blur": 4 * seconds, "transform_anchor": 1}


def test_unknown_property_is_rejected_instead_of_dropped():
    with pytest.raises(ValueError, match="blur"):
        animation_from_timeline(BlurTimeline(), (1920, 1080), (6000, 1080), tolerance=6)


@dataclass
class MirrorTimeline(Timeline):
    def sample(self, seconds):
        return {**super().sample(seconds), "xzoom": -1}


def test_constant_mirror_becomes_flip_flag():
    with pytest.raises(ValueError, match="espejo"):
        animation_from_timeline(MirrorTimeline(), (1920, 1080), (6000, 1080), tolerance=6)
    result = animation_from_timeline(MirrorTimeline(), (1920, 1080), (6000, 1080), tolerance=6, allow_flip=True)
    assert result["flip"] is True and result["keyframes"][-1]["x"] == 256
    assert animation_from_timeline(Timeline(), (1920, 1080), (6000, 1080), tolerance=6)["flip"] is False


@dataclass
class TurningTimeline(Timeline):
    duration: float = 2
    loop_start: float | None = 0

    def sample(self, seconds):
        return {**super().sample(1), "xzoom": 1 if seconds % 2 < 1 else -1}


def test_mirror_switched_inside_a_loop_becomes_image_events():
    result = animation_from_timeline(TurningTimeline(), (1920, 1080), (6000, 1080), tolerance=6, allow_flip=True,
                                     base_image=7)
    assert result["flip"] is False
    assert result["events"] == [{"image": 7, "frame": 0, "flip": 0}, {"image": 7, "frame": 60, "flip": 1}]
    with pytest.raises(ValueError, match="espejo"):
        animation_from_timeline(TurningTimeline(), (1920, 1080), (6000, 1080), tolerance=6, allow_flip=True)


@dataclass
class IntroTimeline(Timeline):
    duration: float = 2
    loop_start: float | None = 1

    def sample(self, seconds):
        if seconds >= self.duration:
            seconds = self.loop_start + (seconds - self.loop_start) % (self.duration - self.loop_start)
        return {"xpos": 1920 * min(seconds, 1), "xanchor": 6000 * min(seconds, 1),
                "ypos": 1080, "yanchor": 1080, "zoom": 1, "alpha": 1}


def test_loop_with_intro_needs_opt_in_and_marks_the_loop_start_key():
    with pytest.raises(ValueError, match="introduccion"):
        animation_from_timeline(IntroTimeline(), (1920, 1080), (6000, 1080), tolerance=6)
    result = animation_from_timeline(IntroTimeline(), (1920, 1080), (6000, 1080), tolerance=6, allow_loop_intro=True)
    assert result["loop"] and result["keyframes"][result["loop_start"]]["frame"] == 60
