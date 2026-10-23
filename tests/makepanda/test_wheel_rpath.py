import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "makepanda"))
import makewheel


@pytest.mark.skipif(sys.platform != "linux", reason="ELF wheel packaging")
@pytest.mark.parametrize("external_dependencies", [True, False])
def test_tools_find_a_library_already_bundled_in_another_package(tmp_path, monkeypatch, external_dependencies):
    for tool in ("cc", "strip", "patchelf"):
        if not shutil.which(tool):
            pytest.skip(tool + " is required")
    monkeypatch.chdir(tmp_path)
    (tmp_path / "library.c").write_text("int fixture(void) { return 68; }\n")
    (tmp_path / "tool.c").write_text(
        "extern int fixture(void); int main(void) { return fixture() == 68 ? 0 : 1; }\n")
    subprocess.run(["cc", "-shared", "-fPIC", "-Wl,-soname,libfixture.so", "library.c", "-o", "libfixture.so"], check=True)
    subprocess.run(["cc", "tool.c", "-L.", "-lfixture", "-Wl,-rpath,$ORIGIN", "-o", "probe"], check=True)
    monkeypatch.setattr(makewheel, "GetStrip", lambda: shutil.which("strip"))
    if not external_dependencies:
        monkeypatch.setattr(makewheel, "IGNORE_UNIX_DEPS_OF", ["panda3d_tools/probe"])
    wheel = makewheel.WheelFile("fixture", "0.0.1", "linux_x86_64")
    wheel.lib_path = [str(tmp_path)]
    wheel.consider_add_dependency("panda3d/libfixture.so", "libfixture.so")
    wheel.write_file("panda3d_tools/probe", str(tmp_path / "probe"))
    wheel.close()
    filename = next(tmp_path.glob("*.whl"))
    installed = tmp_path / "installed"
    with zipfile.ZipFile(filename) as archive:
        archive.extractall(installed)
    tool = installed / "panda3d_tools/probe"
    tool.chmod(0o755)
    env = os.environ.copy()
    env.pop("LD_LIBRARY_PATH", None)
    subprocess.run([str(tool)], cwd="/", env=env, check=True)
