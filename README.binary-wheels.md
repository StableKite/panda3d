# Experimental CPython 3.15t Linux wheels

A normal `pip install` from this repository selects the verified release wheel
for the recorded source snapshot on Linux x86_64, CPython 3.15t and glibc 2.39+.
pip performs downloading, dependency resolution and SHA256 validation.
No consumer SDK setup or extra build flag is required for this binary path.

The original PEP 517 backend and its build requirements are preserved. Changed
native/build sources, another ABI/platform, explicit configuration settings or
compiler overrides use that original source build. The JSON manifest records
the source commit, artifact hash and the checked delivery metadata. Source
builds retain their ordinary development-library prerequisites.

These are engineering dependency artifacts, not a StableKite release.

On Windows x86-64 CPython 3.15t, the source backend automatically obtains
the official Panda3D 1.10.16 Windows tools archive when no thirdparty directory
is present. It verifies the recorded 300183595-byte size and SHA256
`c94d346ce486c65a4a251c72360155b7f4f4aa8e6fd702690b7a0aca8ed3616c`
before extracting the third-party build inputs. Existing developer SDK
directories are preserved. The full original `--everything` wheel recipe
uses the running Python SDK and installed Visual Studio/Windows SDK, including
when pip runs in a venv. No consumer build flag or separate Panda SDK setup is
needed on this path; the system C++ build tools are still required.

The Linux binary's native/runtime source snapshot remains unchanged. The
manifest separately records these Windows build and packaging helpers, which
do not change the Linux runtime, and keeps guarding every other source path.
