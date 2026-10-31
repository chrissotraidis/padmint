# Pinned Rabbitizer Windows wheel

Maintainer source tooling only. No game manifest, managed tool pin or published
wheel consumes this candidate. It does not install into an existing environment
or download anything. Recipe adoption and distribution remain separate work.

Rabbitizer 1.14.3 converts two `uint32_t` results through `PyLong_FromLong`.
Windows has a 32-bit signed C `long`, so high addresses and float bit patterns
become negative Python integers. This loses address/type information during
disassembly even when a rebuilt ROM matches. `unsigned-values.patch` changes
only those two conversions to `PyLong_FromUnsignedLong`. Signed offsets, parser
algorithms and instruction semantics remain unchanged.

`inputs.json` pins the original PyPI source, both original and patched C files,
the patch, build requirements, and the official Python 3.13.15 NuGet archive.
The resulting distribution is `1.14.3+padmint.1`; its C library version remains
1.14.3. This prevents the candidate being confused with official wheel bytes.

Use **x64 CPython 3.13.15**, including on a Windows ARM64 host, and installed
Visual Studio x64 C++ build tools. The producer selects an installation with the
x64 component and invokes `vcvars64.bat` only for its child environment. Git
must be available, or pass its executable as `--git`. Start in this directory:

```powershell
py -3.13-64 -m venv NEW_BUILD_ENV
& NEW_BUILD_ENV/Scripts/python.exe -m pip install --require-hashes -r build-requirements.txt
& NEW_BUILD_ENV/Scripts/python.exe build.py --source-archive CACHED_RABBITIZER_TAR_GZ --sdk-archive CACHED_PYTHON_NUPKG --work NEW_LOCAL_WORK_FOLDER
```

Obtain the two archives from their exact URLs in `inputs.json`; every byte is
checked against the recorded size and SHA-256 before extraction. Existing work
folders are refused. Inputs and earlier outputs are never replaced. The only
SDK files extracted are Python headers, `python313.lib`, `python3.lib` (1.16.2
links the stable ABI) and its license; no
Python runtime or system setting is installed. Build requirements belong in the
new build environment. They are checked again before compiling.

The producer adds MSVC's `/std:c11`, while retaining the upstream source build
settings. Visual Studio discovery uses explicit UTF-8 output and compiler setup
captures Unicode environment text, preserving non-English temporary directories
and inherited values. Windows CLI output uses UTF-8 so printing a successfully
built wheel's path cannot turn the run into an encoding failure. It records the
compiler path, hash, banner and x64 PE architecture,
Python identity, input pins, selected SDK hashes, commands and wheel checksum in
`provenance.json`. `build.log` retains compiler output. `notices/` contains the
upstream MIT license, Python license, exact pins and patch. A fixed wheel ZIP
timestamp is used; byte-identical wheels across different compiler installations
or work paths are not claimed.

The newly built x64 extension is extracted into a temporary test package and
loaded by the same interpreter. Four hand-authored API tests cover high-bit
addresses, half-float bit patterns, unset state and unchanged signed/jump values.
The wheel is never installed by this script. Ordinary repository tests also run
the offline archive, architecture and preservation checks. Windows CI builds the
actual public source in Japanese work and temporary paths and runs the four API
tests with an explicit x64 interpreter;
it does not upload the wheel or use game inputs.

## Source and maintenance

Rabbitizer is [Decompollaborate's MIT-licensed project](https://github.com/Decompollaborate/rabbitizer).
The source archive is the official [1.14.3 PyPI release](https://pypi.org/project/rabbitizer/1.14.3/).
The SDK comes from [CPython's official NuGet package](https://www.nuget.org/packages/python/3.13.15),
using only the development files described above. Build requirement licenses
remain in the isolated build environment's installed distribution metadata.

The same constructor correction was made upstream for the neighboring
`getJrInfo` API in [commit 8c175f5](https://github.com/Decompollaborate/rabbitizer/commit/8c175f51dbbae012921046b6a4809a2c97a8b3d5).
At the October 2026 review, both remaining sites were still present in upstream
1.16.2 (`724a49a5b4dbfb99f1a9e6992e63964fd29c90c8`), so an unreviewed version
upgrade would not solve them. Prefer a reviewed upstream release once it contains
the fix; retain the public API regressions and revalidate generated metadata as
well as matching ROM bytes before changing a game dependency.
