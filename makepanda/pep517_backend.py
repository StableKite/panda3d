"""Use Panda3D's existing wheel recipe from a standard pip invocation."""
import os
import shutil
import subprocess
import sys
import sysconfig
import zipfile
from pathlib import Path


def get_requires_for_build_wheel(config_settings=None):
    """Declare the ELF wheel packager used by the native source build."""
    if sys.platform not in ("win32", "darwin") and not sys.platform.startswith("cygwin"):
        return ["patchelf"]
    return []


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    source = Path(__file__).resolve().parents[1]
    suffix = getattr(sys, "abiflags", "")
    if not suffix and sysconfig.get_config_var('Py_GIL_DISABLED') == 1:
        suffix = 't'
    abi = f"cp{sys.version_info[0]}{sys.version_info[1]}{suffix}"
    jobs = 2
    if (sys.platform == 'win32' and sysconfig.get_platform() == 'win-amd64'
            and sys.version_info[:2] == (3, 15)
            and sysconfig.get_config_var('Py_GIL_DISABLED') == 1):
        from makepanda.windows_sdk import ensure_sdk
        ensure_sdk(source)
        jobs = min(6, os.cpu_count() or 1)
    subprocess.run(
        [sys.executable, str(source / "makepanda/makepanda.py"),
         "--everything", "--threads=" + str(jobs), "--wheel", "--outputdir=build-" + abi],
        cwd=source, check=True,
    )
    candidates = []
    for wheel in source.glob("panda3d-*.whl"):
        with zipfile.ZipFile(wheel) as archive:
            if any(name.startswith("panda3d/core.") and name.endswith((".so", ".pyd"))
                   for name in archive.namelist()):
                candidates.append(wheel)
    if len(candidates) != 1:
        raise RuntimeError("Expected one Panda3D wheel containing the native Python core")
    wheel = candidates[0]
    dest = Path(wheel_directory) / wheel.name
    shutil.copy2(wheel, dest)
    return wheel.name


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    # Native compilation belongs to build_wheel, not dependency resolution.
    from sysconfig import get_platform
    source = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(source / "makepanda"))
    from makepandacore import GetMetadataValue
    from makewheel import get_wheel_metadata
    version = GetMetadataValue("version")
    name = "panda3d-" + version + ".dist-info"
    dest = Path(metadata_directory) / name
    dest.mkdir(exist_ok=True)
    platform = get_platform().replace("-", "_").replace(".", "_")
    (dest / "METADATA").write_text(get_wheel_metadata(version, platform), encoding="utf-8")
    return name
