import shutil

import pytest

# Compilan en Docker (minutos): solo con `pytest -m consoles`
pytestmark = pytest.mark.consoles

from platforms.vita.build import build


@pytest.mark.skipif(shutil.which("docker") is None, reason="Docker no disponible")
def test_vita_build_trace_package():
	package = build(trace=True)
	assert package.is_file()
	assert package.name == "snoot.vpk"
	assert package.stat().st_size > 0
