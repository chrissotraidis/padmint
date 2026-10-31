"""Offline preservation and validation tests; no tool or game downloads."""
import importlib.util
import io
import os
import shutil
import struct
import subprocess
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('rabbitizer_producer', HERE / 'build.py')
producer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(producer)


def pin(path):
    return {'name': 'rabbitizer', 'version': '1.14.3', 'size': path.stat().st_size,
            'sha256': producer.sha256(path)}


class ProducerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_windows_cli_prints_unicode_output_without_utf8_environment(self):
        output, errors = io.BytesIO(), io.BytesIO()
        stdout = io.TextIOWrapper(output, encoding='cp1252')
        stderr = io.TextIOWrapper(errors, encoding='cp1252')
        wheel = self.root / 'wheel \u96ea.whl'
        arguments = ['build.py', '--source-archive', 'source.tar.gz',
                     '--sdk-archive', 'sdk.nupkg', '--work', 'new-work']
        with patch.object(producer, 'os', SimpleNamespace(name='nt')), \
                patch.object(producer, 'build', return_value=wheel), \
                patch.object(producer.sys, 'argv', arguments), \
                patch.object(producer.sys, 'stdout', stdout), \
                patch.object(producer.sys, 'stderr', stderr):
            producer.main()
        stdout.flush(); stderr.flush()
        self.assertEqual(output.getvalue().replace(b'\r\n', b'\n'), (str(wheel) + '\n').encode('utf-8'))
        self.assertEqual(errors.getvalue(), b'')

    def archive(self, name='rabbitizer-1.14.3/hello.c', kind=tarfile.REGTYPE):
        path = self.root / 'source.tar.gz'
        with tarfile.open(path, 'w:gz') as bundle:
            member = tarfile.TarInfo(name)
            member.type = kind
            if kind == tarfile.REGTYPE:
                member.size = 3
                bundle.addfile(member, io.BytesIO(b'abc'))
            else:
                member.linkname = '../outside'
                bundle.addfile(member)
        return path

    def test_extracts_checked_source_without_changing_archive(self):
        archive = self.archive()
        before = archive.read_bytes()
        source = producer.extract_source(archive, self.root / 'source', pin(archive))
        self.assertEqual((source / 'hello.c').read_bytes(), b'abc')
        self.assertEqual(archive.read_bytes(), before)

    def test_bad_checksum_preserves_input_and_creates_no_source(self):
        archive = self.archive()
        expected = pin(archive)
        expected['sha256'] = '0' * 64
        before = archive.read_bytes()
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            producer.extract_source(archive, self.root / 'source', expected)
        self.assertFalse((self.root / 'source').exists())
        self.assertEqual(archive.read_bytes(), before)

    def test_bad_size_preserves_input(self):
        archive = self.archive()
        expected = pin(archive)
        expected['size'] += 1
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            producer.checked(archive, expected)
        self.assertEqual(producer.sha256(archive), expected['sha256'])

    def test_existing_work_is_preserved(self):
        work = self.root / 'work'
        work.mkdir()
        saved = work / 'prior-output'
        saved.write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError, 'preserving'):
            producer.new_work(work)
        self.assertEqual(saved.read_bytes(), b'keep')

    def test_archive_rejects_traversal_absolute_and_wrong_root_before_writes(self):
        for name in ('rabbitizer-1.14.3/../../outside', '/outside', 'C:/outside',
                     'rabbitizer-1.14.3/..\\outside', 'wrong/hello.c'):
            with self.subTest(name=name):
                archive = self.archive(name)
                with self.assertRaises(ValueError):
                    producer.extract_source(archive, self.root / 'source', pin(archive))
                self.assertFalse((self.root / 'source').exists())

    def test_archive_rejects_links_before_writes(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
            with self.subTest(kind=kind):
                archive = self.archive(kind=kind)
                with self.assertRaises(ValueError):
                    producer.extract_source(archive, self.root / 'source', pin(archive))
                self.assertFalse((self.root / 'source').exists())

    def test_changed_original_source_refuses_patch_without_command(self):
        source = self.root / 'source'; source.mkdir()
        file = source / 'input.c'; file.write_bytes(b'changed')
        lock = {'patched_files': {'input.c': {'before_sha256': '0' * 64}}}
        run = Mock()
        with self.assertRaisesRegex(ValueError, 'original source'):
            producer.patch_source(source, lock, 'git', run)
        run.assert_not_called()
        self.assertEqual(file.read_bytes(), b'changed')

    def test_sdk_extracts_only_headers_import_library_and_license(self):
        archive = self.root / 'sdk.zip'
        with zipfile.ZipFile(archive, 'w') as bundle:
            for name in ('include/Python.h', 'libs/python313.lib', 'libs/python3.lib', 'LICENSE.txt', 'python.exe'):
                bundle.writestr('tools/' + name, name.encode())
        files = producer.extract_sdk(archive, self.root / 'sdk', pin(archive))
        self.assertEqual(set(files), {'include/Python.h', 'libs/python313.lib', 'libs/python3.lib', 'LICENSE.txt'})
        self.assertFalse((self.root / 'sdk/python.exe').exists())

    def test_sdk_missing_license_refuses_before_writes(self):
        archive = self.root / 'sdk.zip'
        with zipfile.ZipFile(archive, 'w') as bundle:
            bundle.writestr('tools/include/Python.h', b'header')
            bundle.writestr('tools/libs/python313.lib', b'import library')
        with self.assertRaisesRegex(ValueError, 'license missing'):
            producer.extract_sdk(archive, self.root / 'sdk', pin(archive))
        self.assertFalse((self.root / 'sdk').exists())

    def wheel(self, machine=0x8664, license=True, version='1.14.3+padmint.1'):
        path = self.root / ('rabbitizer-' + version + '-cp313-cp313-win_amd64.whl')
        data = bytearray(134)
        data[:2] = b'MZ'; struct.pack_into('<I', data, 0x3c, 128)
        data[128:132] = b'PE\0\0'; struct.pack_into('<H', data, 132, machine)
        with zipfile.ZipFile(path, 'w') as bundle:
            bundle.writestr('rabbitizer.cp313-win_amd64.pyd', data)
            if license:
                bundle.writestr('rabbitizer.dist-info/licenses/LICENSE', b'license')
        return path

    def test_wheel_accepts_only_expected_x64_abi_and_license(self):
        wheel = self.wheel()
        name, data = producer.wheel_extension(wheel, '1.14.3+padmint.1')
        self.assertEqual(name, 'rabbitizer.cp313-win_amd64.pyd')
        self.assertEqual(producer.pe_machine(data), 0x8664)
        for kwargs, message in (({'machine': 0xaa64}, 'x64'),
                                ({'license': False}, 'license'),
                                ({'version': '1.14.3'}, 'version or ABI')):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, message):
                producer.wheel_extension(self.wheel(**kwargs), '1.14.3+padmint.1')

    def test_malformed_pe_fails_cleanly(self):
        for data in (b'', b'MZ', b'MZ' + b'\xff' * 62):
            with self.subTest(data=data[:2]), self.assertRaises(ValueError):
                producer.pe_machine(data)

    @unittest.skipUnless(shutil.which('git'), 'Git is required for the checkout conversion fixture')
    def test_hashed_patches_keep_lf_with_windows_git_conversion(self):
        repository = self.root / 'original'; repository.mkdir()
        expected = {}
        for name in ('ido-windows', 'rabbitizer-windows'):
            directory = repository / name; directory.mkdir()
            for file in (HERE.parent / name).iterdir():
                if file.suffix == '.patch' or file.name == '.gitattributes':
                    data = file.read_bytes()
                    (directory / file.name).write_bytes(data)
                    if file.suffix == '.patch':
                        expected[name + '/' + file.name] = data
        (repository / 'ordinary.txt').write_bytes(b'first\nsecond\n')
        env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')
        def git(*args):
            subprocess.run(['git', '-c', 'core.autocrlf=true', '-c', 'user.name=Fixture',
                            '-c', 'user.email=fixture@example.invalid', *args],
                           cwd=repository, env=env, check=True, capture_output=True)
        git('init')
        git('add', '.')
        git('commit', '-qm', 'Public patch fixture')
        checkout = self.root / 'windows checkout'
        git('clone', '--no-local', str(repository), str(checkout))
        # The ordinary file proves conversion actually ran, including on macOS.
        self.assertEqual((checkout / 'ordinary.txt').read_bytes(), b'first\r\nsecond\r\n')
        for name, data in expected.items():
            self.assertEqual((checkout / name).read_bytes(), data, name)
            self.assertNotIn(b'\r', (checkout / name).read_bytes(), name)


if __name__ == '__main__':
    unittest.main()
