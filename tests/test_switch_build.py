import shutil

import pytest

# Compilan en Docker (minutos): solo con `pytest -m consoles`
pytestmark = pytest.mark.consoles

from platforms.switch.build import build


@pytest.mark.skipif(shutil.which("docker") is None, reason="Docker no disponible")
def test_switch_build_package():
	package = build()
	assert package.is_file()
	assert package.name == "snoot.nro"
