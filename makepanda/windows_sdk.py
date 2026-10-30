"""Fetch the recorded official Windows third-party tools for plain pip builds."""
import hashlib
import os
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from urllib.request import urlopen

URL = "https://www.panda3d.org/download/panda3d-1.10.16/panda3d-1.10.16-tools-win64.zip"
SHA256 = "c94d346ce486c65a4a251c72360155b7f4f4aa8e6fd702690b7a0aca8ed3616c"
SIZE = 300183595
PREFIX = "panda3d-1.10.16/thirdparty/"


def ensure_sdk(source):
    source = Path(source).resolve(strict=True)
    target = source / "thirdparty"
    # An existing directory belongs to the developer's source configuration.
    if target.exists():
        return
    with tempfile.TemporaryDirectory(prefix=".panda-sdk-", dir=source) as temporary:
        work = Path(temporary).resolve()
        assert work.is_relative_to(source)
        archive = work / "sdk.zip"
        digest = hashlib.sha256()
        size = 0
        with urlopen(URL, timeout=120) as response, archive.open("xb") as output:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > SIZE:
                    raise RuntimeError("Official Panda tools archive exceeds recorded size")
                digest.update(chunk)
                output.write(chunk)
        if size != SIZE or digest.hexdigest() != SHA256:
            raise RuntimeError("Official Panda tools archive size or SHA256 mismatch")
        staged = work / "thirdparty"
        staged.mkdir()
        with zipfile.ZipFile(archive) as packed:
            for member in packed.infolist():
                if not member.filename.startswith(PREFIX):
                    continue
                relative = member.filename[len(PREFIX):]
                if not relative:
                    continue
                path = PurePosixPath(relative)
                if (path.is_absolute() or ".." in path.parts or ":" in relative
                        or "\\" in relative):
                    raise RuntimeError("Unexpected official Panda tools archive path")
                destination = staged.joinpath(*path.parts)
                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with packed.open(member) as content, destination.open("xb") as output:
                        while chunk := content.read(1024 * 1024):
                            output.write(chunk)
        if not (staged / "win-libs-vc14-x64").is_dir():
            raise RuntimeError("Official Panda tools archive lacks x64 libraries")
        assert staged.resolve().is_relative_to(source)
        assert target.resolve().is_relative_to(source)
        os.replace(staged, target)
