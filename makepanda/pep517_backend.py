"""Use Panda3D's existing wheel recipe from a standard pip invocation."""
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    source = Path(__file__).resolve().parents[1]
    abi = "cp%d%d%s" % (*sys.version_info[:2], getattr(sys, "abiflags", ""))
    subprocess.run(
        [sys.executable, str(source / "makepanda/makepanda.py"),
         "--everything", "--threads=2", "--wheel", "--outputdir=build-" + abi],
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
    from makewheel import get_wheel_metadata
    from makepandacore import GetMetadataValue
    version = GetMetadataValue("version")
    name = "panda3d-" + version + ".dist-info"
    dest = Path(metadata_directory) / name
    dest.mkdir(exist_ok=True)
    platform = get_platform().replace("-", "_").replace(".", "_")
    (dest / "METADATA").write_text(get_wheel_metadata(version, platform), encoding="utf-8")
    return name
