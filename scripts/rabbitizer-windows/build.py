#!/usr/bin/env python3
"""Build and test the pinned Rabbitizer wheel without installing it.

Requires x64 CPython 3.13.15, the pinned build requirements, Git and Visual
Studio x64 C++ tools. Inputs are explicit local archives; nothing is downloaded.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import struct
import subprocess
import sys
import sysconfig
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(path, pin):
    if Path(path).stat().st_size != pin['size'] or sha256(path) != pin['sha256']:
        raise ValueError(f'Pinned input mismatch: {path}')
    return Path(path)


def safe_name(name):
    path = PurePosixPath(name)
    if not path.parts or path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
        raise ValueError(f'Unsafe archive path: {name}')
    return path


def new_work(path):
    if path.exists():
        raise ValueError(f'Use a new work folder; preserving {path}')
    if str(path).startswith('\\\\'):
        raise ValueError('Use a local Windows work folder; cmd.exe cannot use a UNC working directory')
    path.mkdir(parents=True)


def extract_source(archive, target, pin):
    checked(archive, pin)
    prefix = pin['name'] + '-' + pin['version']
    with tarfile.open(archive, 'r:gz') as bundle:
        members = bundle.getmembers()
        for member in members:
            path = safe_name(member.name)
            if path.parts[0] != prefix or not (member.isdir() or member.isfile()):
                raise ValueError(f'Unexpected source archive member: {member.name}')
        for member in members:
            if member.isfile():
                destination = target.joinpath(*safe_name(member.name).parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with bundle.extractfile(member) as source, destination.open('xb') as output:
                    shutil.copyfileobj(source, output)
    return target / prefix


def patch_source(source, lock, git, run):
    for name, pin in lock['patched_files'].items():
        if sha256(source / name) != pin['before_sha256']:
            raise ValueError(f'Unexpected original source: {name}')
    patch = HERE / 'unsigned-values.patch'
    if sha256(patch) != lock['patch_sha256']:
        raise ValueError('Unexpected unsigned-values.patch')
    run([git, '-c', 'core.autocrlf=false', 'apply', '--check', patch], source)
    run([git, '-c', 'core.autocrlf=false', 'apply', patch], source)
    for name, pin in lock['patched_files'].items():
        if sha256(source / name) != pin['after_sha256']:
            raise ValueError(f'Unexpected patched source: {name}')
    metadata = source / 'pyproject.toml'
    text = metadata.read_text(encoding='utf-8')
    original = 'version = "' + lock['source']['version'] + '"'
    if text.count(original) != 1:
        raise ValueError('Unexpected distribution version metadata')
    metadata.write_bytes(text.replace(original, 'version = "' + lock['wheel_version'] + '"').encode())


def extract_sdk(archive, target, pin):
    """Copy only the official headers, import libraries and license. Rabbitizer 1.16
    builds against the stable ABI (Py_LIMITED_API), so it links python3.lib."""
    checked(archive, pin)
    files = {}
    libraries = ('tools/libs/python313.lib', 'tools/libs/python3.lib')
    with zipfile.ZipFile(archive) as bundle:
        selected = [name for name in bundle.namelist() if not name.endswith('/') and
                    (name.startswith('tools/include/') or name in (*libraries, 'tools/LICENSE.txt'))]
        required = {'tools/include/Python.h', *libraries, 'tools/LICENSE.txt'}
        if not required.issubset(selected):
            raise ValueError('Python SDK headers, import library or license missing')
        for name in selected:
            safe_name(name)
        for name in selected:
            destination = target.joinpath(*PurePosixPath(name).parts[1:])
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as output:
                output.write(bundle.read(name))
            files[destination.relative_to(target).as_posix()] = sha256(destination)
    return files


def msvc_environment(work):
    env = dict(os.environ)
    vswhere = Path(env.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    installation = subprocess.check_output([
        str(vswhere), '-latest', '-products', '*', '-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath', '-utf8',
    ], text=True, encoding='utf-8').strip()
    if not installation:
        raise ValueError('Visual Studio x64 C++ build tools are required')
    vcvars = Path(installation) / 'VC/Auxiliary/Build/vcvars64.bat'
    command = 'cmd.exe /d /u /s /c ""' + str(vcvars) + '" >nul && set"'
    output = subprocess.check_output(command, cwd=work, env=env, text=True, encoding='utf-16-le')
    for line in output.splitlines():
        if '=' not in line or line.startswith('='):
            continue
        key, value = line.split('=', 1)
        for old in list(env):
            if old.lower() == key.lower():
                del env[old]
        env[key] = value
    return env


def pe_machine(data):
    if len(data) < 64 or data[:2] != b'MZ':
        raise ValueError('Missing PE header')
    offset = struct.unpack_from('<I', data, 0x3c)[0]
    if offset + 6 > len(data) or data[offset:offset + 4] != b'PE\0\0':
        raise ValueError('Invalid PE header')
    return struct.unpack_from('<H', data, offset + 4)[0]


def wheel_extension(wheel, version):
    expected = 'rabbitizer-' + version + '-cp313-cp313-win_amd64.whl'
    if wheel.name != expected:
        raise ValueError(f'Unexpected wheel version or ABI: {wheel.name}')
    with zipfile.ZipFile(wheel) as bundle:
        names = bundle.namelist()
        extensions = [name for name in names if name.endswith('.pyd')]
        if len(extensions) != 1 or len(safe_name(extensions[0]).parts) != 1:
            raise ValueError('Expected one top-level Rabbitizer extension')
        if not any('LICENSE' in name.upper() for name in names):
            raise ValueError('Wheel is missing its upstream license')
        data = bundle.read(extensions[0])
        if pe_machine(data) != 0x8664:
            raise ValueError('Expected an x64 extension')
        return extensions[0], data


def build(args):
    lock = json.loads(args.inputs.read_text())
    if os.name != 'nt' or sysconfig.get_platform() != 'win-amd64' or platform.python_version() != lock['python_version']:
        raise ValueError('Use x64 CPython ' + lock['python_version'] + ' on Windows, including on ARM hosts')
    for name, pin in lock['build_dependencies'].items():
        if importlib.metadata.version(name) != pin['version']:
            raise ValueError('Install the exact hashed build-requirements.txt in an isolated environment')
    checked(args.source_archive, lock['source'])
    checked(args.sdk_archive, lock['python_sdk'])
    work = args.work.resolve()
    new_work(work)
    env = msvc_environment(work)
    temp = work / 'temp'; temp.mkdir()
    env.update(TEMP=str(temp), TMP=str(temp), DISTUTILS_USE_SDK='1', MSSdk='1',
               CL='/std:c11', SOURCE_DATE_EPOCH='1760313600')
    # Do not inherit compiler flags or import paths from an unrelated build.
    for name in ('_CL_', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS', 'PYTHONPATH', 'PYTHONHOME'):
        env.pop(name, None)
    commands = []
    with (work / 'build.log').open('wb') as log:
        def run(argv, cwd=work):
            command = [str(value) for value in argv]
            commands.append(command)
            log.write((repr(command) + '\n').encode()); log.flush()
            subprocess.run(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        source = extract_source(args.source_archive, work / 'source', lock['source'])
        patch_source(source, lock, args.git, run)
        sdk = work / 'python-sdk'
        sdk_files = extract_sdk(args.sdk_archive, sdk, lock['python_sdk'])
        for key, subdir in (('INCLUDE', 'include'), ('LIB', 'libs')):
            actual = next(name for name in env if name.upper() == key)
            env[actual] = str(sdk / subdir) + ';' + env[actual]
        compiler = shutil.which('cl.exe', path=env.get('PATH', env.get('Path')))
        if not compiler or pe_machine(Path(compiler).read_bytes()) != 0x8664:
            raise ValueError('Expected the x64 MSVC compiler selected by vcvars64')
        banner = subprocess.run([compiler], cwd=work, env=env, capture_output=True, text=True)
        wheels = work / 'wheels'; wheels.mkdir()
        run([sys.executable, '-I', '-B', '-c',
             'import setuptools.build_meta,sys; setuptools.build_meta.build_wheel(sys.argv[1])', wheels], source)
        found = list(wheels.glob('*.whl'))
        if len(found) != 1:
            raise ValueError('Expected exactly one newly built wheel')
        wheel = found[0]
        name, data = wheel_extension(wheel, lock['wheel_version'])
        package = work / 'test-package'; package.mkdir()
        (package / name).write_bytes(data)
        # Test the wheel bytes directly without changing this interpreter's packages.
        run([sys.executable, '-I', '-B', '-c',
             'import runpy,sys; sys.path.insert(0,sys.argv.pop(1)); '
             'sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name="__main__")',
             package, HERE / 'test_unsigned.py'])
        notices = work / 'notices'; notices.mkdir()
        for path, destination in ((source / 'LICENSE', 'Rabbitizer-LICENSE'),
                                  (sdk / 'LICENSE.txt', 'Python-LICENSE.txt'),
                                  (args.inputs, args.inputs.name),
                                  (HERE / 'unsigned-values.patch', 'unsigned-values.patch')):
            shutil.copyfile(path, notices / destination)
        receipt = {'source': lock['source'], 'wheel_version': lock['wheel_version'],
                   'input_lock_sha256': sha256(args.inputs),
                   'patch_sha256': lock['patch_sha256'], 'patched_files': lock['patched_files'],
                   'python': sys.version, 'python_executable': sys.executable,
                   'compiler': compiler, 'compiler_sha256': sha256(compiler),
                   'compiler_banner': (banner.stdout + banner.stderr).strip(),
                   'compiler_pe_machine': '0x8664', 'extension_pe_machine': '0x8664',
                   'host_machine': platform.machine(), 'sdk_archive': lock['python_sdk'],
                   'sdk_selected_files': sdk_files, 'build_dependencies': lock['build_dependencies'],
                   'wheel': str(wheel), 'wheel_sha256': sha256(wheel), 'commands': commands}
        (work / 'provenance.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return wheel


def main():
    if os.name == 'nt':
        for stream in (sys.stdout, sys.stderr):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-archive', type=Path, required=True)
    parser.add_argument('--sdk-archive', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True, help='New local Windows directory')
    parser.add_argument('--git', default='git')
    parser.add_argument('--inputs', type=Path, default=HERE / 'inputs.json',
                        help='Version pin (inputs.json: 1.14.3 for SnapPad; inputs-1.16.2.json: AnnePad)')
    args = parser.parse_args()
    try:
        print(build(args))
    except (OSError, ValueError, subprocess.CalledProcessError, importlib.metadata.PackageNotFoundError) as error:
        parser.exit(1, f'Rabbitizer build stopped: {error}\nInput archives and previous work were preserved.\n')


if __name__ == '__main__':
    main()
