import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "makepanda"))
import makepandacore as core


def test_isolated_sdk_is_used_without_reinstalling_or_rewriting(tmp_path):
    source = tmp_path / "installed"
    output = tmp_path / "output"
    suffix = ".exe" if sys.platform == "win32" else ""
    files = [Path("interrogate/interrogate" + suffix),
             Path("interrogate_module/interrogate_module" + suffix)]
    for file in files:
        path = source / file
        path.parent.mkdir(parents=True)
        path.write_bytes(b"original SDK")
    sdk = SimpleNamespace(files=files, locate_file=lambda p: source / p)
    with patch.object(core, "GetOutputDir", return_value=str(output)), \
            patch("importlib.metadata.distribution", return_value=sdk), \
            patch.object(core, "oscmd", side_effect=AssertionError("unexpected pip install")):
        core.INTERROGATE_DIR = None
        cache = Path(core.GetInterrogateDir())
        tool = cache / files[0]
        timestamp = tool.stat().st_mtime_ns
        os.utime(source / files[0], ns=(timestamp + 100000, timestamp + 100000))
        core.INTERROGATE_DIR = None
        assert Path(core.GetInterrogateDir()) == cache
        assert tool.stat().st_mtime_ns == timestamp
        (source / files[0]).write_bytes(b"new native SDK")
        core.INTERROGATE_DIR = None
        core.GetInterrogateDir()
        assert tool.read_bytes() == b"new native SDK"
    core.INTERROGATE_DIR = None


def test_incomplete_declared_sdk_does_not_fall_back_to_stale_cache(tmp_path):
    sdk = SimpleNamespace(files=[Path("METADATA")], locate_file=lambda p: tmp_path / p)
    with patch.object(core, "GetOutputDir", return_value=str(tmp_path)), \
            patch("importlib.metadata.distribution", return_value=sdk):
        core.INTERROGATE_DIR = None
        with pytest.raises(RuntimeError, match="missing its native tools"):
            core.GetInterrogateDir()
    core.INTERROGATE_DIR = None
