"""Configuracion del Test Lab (testlab.toml)."""
from __future__ import annotations

import tomllib
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("tools/ctl/testlab.toml")


def find_config(path=None) -> Path:
    if path is not None:
        return Path(path)
    pkg = Path(__file__).resolve().parent / "testlab.toml"
    if pkg.exists():
        return pkg
    if DEFAULT_CONFIG_PATH.exists():
        return DEFAULT_CONFIG_PATH
    return pkg


def load_config(path=None) -> dict:
    p = find_config(path)
    if not p.exists():
        return {}
    with p.open("rb") as f:
        return tomllib.load(f)


def get_target(config, name):
    if not isinstance(config, dict) or name not in config:
        raise KeyError(f"unknown target: {name}")
    return config[name]
