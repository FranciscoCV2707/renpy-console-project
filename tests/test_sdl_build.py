from pathlib import Path

from platforms.sdl.build import build


def test_sdl_build_trace_executable():
    executable = build(trace=True)
    assert executable.is_file()
    assert (Path("build/pc") / "SDL2.dll").is_file()
