"""Make `custom_components/neore/api.py` importable without Home Assistant.

`custom_components/neore/__init__.py` imports `homeassistant`, which this
project does not (and should not) list as a test dependency for a module as
self-contained as `api.py`. A plain `import custom_components.neore.api`
would still run that `__init__.py` first, because it is a real package.

To avoid that, register `custom_components` and `custom_components.neore` as
empty namespace packages in `sys.modules` *before* anything imports them.
Python's import machinery then finds submodules (`api`, `const`, ...) via
each package's `__path__` without ever executing the real `__init__.py`.
"""

from __future__ import annotations

import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
CUSTOM_COMPONENTS = ROOT / "custom_components"
NEORE = CUSTOM_COMPONENTS / "neore"


def _register_namespace_package(name: str, path: pathlib.Path) -> None:
    if name in sys.modules:
        return
    module = types.ModuleType(name)
    module.__path__ = [str(path)]  # type: ignore[attr-defined]
    sys.modules[name] = module


_register_namespace_package("custom_components", CUSTOM_COMPONENTS)
_register_namespace_package("custom_components.neore", NEORE)
