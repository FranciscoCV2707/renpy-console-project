import shutil

import pytest

from platforms.switch.build import build


@pytest.mark.skipif(shutil.which("docker") is None, reason="Docker no disponible")
def test_switch_build_package():
	package = build()
	assert package.is_file()
	assert package.name == "snoot.nro"
