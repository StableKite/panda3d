"""Native bindings must not silently enable the process-wide GIL."""
import importlib
from pathlib import Path
import sys
import sysconfig

import pytest
import panda3d


@pytest.mark.skipif(not sysconfig.get_config_var("Py_GIL_DISABLED"),
                    reason="requires a free-threaded CPython build")
def test_native_module_gil_declarations():
    assert not sys._is_gil_enabled()
    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    for extension in Path(panda3d.__file__).parent.glob("*" + suffix):
        name = extension.name[:-len(suffix)]
        importlib.import_module("panda3d." + name)
        assert not sys._is_gil_enabled(), name
