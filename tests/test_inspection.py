import contextlib
import copy
import hashlib
import io
import json
import stat
import struct
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from fixtures import apk, binary_manifest, manifest
from vesktop_android.__main__ import main
from vesktop_android.apk import HERMES_MAGIC, InspectionError, check_profile, inspect_apk, inspect_set
from vesktop_android.axml import ANDROID, ManifestError, manifest_metadata, read_elements


class ManifestTests(unittest.TestCase):
    def test_binary_utf8_and_utf16_values(self):
        for utf8 in (True, False):
            with self.subTest(utf8=utf8):
                data = binary_manifest([('manifest', [(None, 'package', 3, 'com.example.test'),
                    (ANDROID, 'versionName', 3, '猫 😀 ' + 'x' * 150),
                    (ANDROID, 'versionCode', 0x10, 354012)]),
                    ('application', [(ANDROID, 'isSplitRequired', 0x12, 1)])], utf8=utf8)
                parsed = manifest_metadata(data)
                self.assertEqual(parsed['version_code'], 354012)
                self.assertEqual(parsed['version_name'], '猫 😀 ' + 'x' * 150)
                self.assertTrue(parsed['split_required'])

    def test_long_utf16_string(self):
        data = binary_manifest([('manifest', [(None, 'package', 3, 'a' * 33000)])], utf8=False)
        self.assertEqual(len(manifest_metadata(data)['package']), 33000)

    def test_text_false_is_not_truthy(self):
        data = ('<manifest xmlns:android="' + ANDROID + '" package="com.example" android:versionCode="12">'
                '<application android:isSplitRequired="false"><meta-data '
                'android:name="com.android.vending.splits.required" android:value="false"/></application></manifest>').encode()
        parsed = manifest_metadata(data)
        self.assertFalse(parsed['split_required'])
        self.assertFalse(parsed['play_splits_required'])
        self.assertEqual(parsed['version_code'], 12)

    def test_unknown_boolean_rejected(self):
        data = binary_manifest([('manifest', []), ('application', [(ANDROID, 'isSplitRequired', 1, 123)])])
        with self.assertRaises(ManifestError):
            manifest_metadata(data)

    def test_unknown_resource_value_remains_explicit(self):
        data = binary_manifest([('manifest', [(ANDROID, 'versionName', 1, 0x7F010001)])])
        self.assertEqual(manifest_metadata(data)['version_name'], {'type': 1, 'data': 0x7F010001})

    def test_every_truncated_prefix_is_rejected(self):
        data = manifest()
        for length in range(len(data)):
            with self.subTest(length=length), self.assertRaises(ManifestError):
                read_elements(data[:length])

    def test_zero_length_chunk_is_rejected(self):
        data = bytearray(manifest())
        struct.pack_into('<I', data, 12, 0)
        with self.assertRaises(ManifestError):
            read_elements(data)

    def test_string_offset_outside_pool_is_rejected(self):
        data = bytearray(manifest())
        struct.pack_into('<I', data, 36, 0xFFFFFF00)
        with self.assertRaises(ManifestError):
            read_elements(data)

    def test_invalid_attribute_bounds_are_rejected(self):
        data = bytearray(manifest())
        start = 8 + struct.unpack_from('<I', data, 12)[0]
        struct.pack_into('<H', data, start + 28, 65535)
        with self.assertRaises(ManifestError):
            read_elements(data)

    def test_duplicate_attribute_is_rejected(self):
        data = binary_manifest([('manifest', [(None, 'package', 3, 'a'), (None, 'package', 3, 'b')])])
        with self.assertRaises(ManifestError):
            read_elements(data)

    def test_invalid_root_and_text(self):
        for data in (b'<not-manifest/>', b'<manifest', b'not XML'):
            with self.subTest(data=data), self.assertRaises(ManifestError):
                read_elements(data)


class ApkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def make(self, name='base.apk', **kwargs):
        return apk(self.root / name, **kwargs)

    def full_set(self):
        base = self.make(required='base__abi,base__density', extra={'assets/index.android.bundle': HERMES_MAGIC + struct.pack('<I', 98) + b'fixture'})
        abi = self.make('abi.apk', split='config.arm64_v8a', types='base__abi', extra={'lib/arm64-v8a/libfixture.so': b'not executable'})
        density = self.make('density.apk', split='config.xxhdpi', types='base__density')
        return [base, abi, density]

    def test_incomplete_base_reports_both_missing_types(self):
        report = inspect_set([self.full_set()[0]])
        self.assertFalse(report['set']['declared_requirements_met'])
        self.assertIn('Missing declared split type: base__abi', report['set']['blockers'])
        self.assertIn('Missing declared split type: base__density', report['set']['blockers'])
        self.assertTrue(any('no native libraries' in b for b in report['set']['blockers']))

    def test_complete_declared_set_is_not_a_patch_or_signature_claim(self):
        report = inspect_set(self.full_set())
        self.assertTrue(report['set']['declared_requirements_met'])
        self.assertEqual(report['set']['native_abis'], ['arm64-v8a'])
        self.assertFalse(report['set']['patch_supported'])
        self.assertFalse(report['set']['installation_verified'])
        self.assertEqual(report['set']['signature_verification'], 'not_performed')

    def test_version_mismatch_blocks(self):
        paths = [self.make(), self.make('split.apk', split='feature', code=2)]
        self.assertIn('APK package names or version codes do not match', inspect_set(paths)['set']['blockers'])

    def test_package_mismatch_blocks(self):
        paths = [self.make(), self.make('split.apk', split='feature', package='other.package')]
        self.assertFalse(inspect_set(paths)['set']['declared_requirements_met'])

    def test_split_without_base_blocks(self):
        path = self.make(split='feature')
        self.assertIn('Exactly one base APK is required', inspect_set([path])['set']['blockers'])

    def test_two_bases_block(self):
        self.assertFalse(inspect_set([self.make(), self.make('other.apk')])['set']['declared_requirements_met'])

    def test_duplicate_split_id_blocks(self):
        paths = [self.make(), self.make('a.apk', split='feature'), self.make('b.apk', split='feature')]
        self.assertIn('Duplicate split identifiers', inspect_set(paths)['set']['blockers'])

    def test_missing_named_dependency_blocks(self):
        path = self.make(uses=('feature.camera',))
        self.assertIn('Missing required split: feature.camera', inspect_set([path])['set']['blockers'])

    def test_missing_config_target_blocks(self):
        paths = [self.make(), self.make('split.apk', split='config.foo', target='feature.foo')]
        self.assertIn('Missing target for configuration split: feature.foo', inspect_set(paths)['set']['blockers'])

    def test_duplicate_input_rejected(self):
        path = self.make()
        with self.assertRaises(InspectionError):
            inspect_set([path, path])

    def test_hermes_header_and_input_unchanged(self):
        path = self.full_set()[0]
        before = path.read_bytes()
        report = inspect_apk(path)
        self.assertEqual(report['sha256'], hashlib.sha256(before).hexdigest())
        self.assertEqual(report['bundle']['hermes_bytecode_version'], 98)
        self.assertEqual(path.read_bytes(), before)
        self.assertNotIn(str(self.root), json.dumps(report))

    def test_unidentified_bundle_is_not_guessed(self):
        path = self.make(extra={'assets/index.android.bundle': b'hello'})
        self.assertEqual(inspect_apk(path)['bundle']['format'], 'unidentified')

    def test_truncated_hermes_header_rejected(self):
        path = self.make(extra={'assets/index.android.bundle': HERMES_MAGIC})
        with self.assertRaises(InspectionError):
            inspect_apk(path)

    def test_invalid_zip_and_missing_manifest(self):
        path = self.root / 'bad.apk'
        path.write_bytes(b'bad zip')
        with self.assertRaises(InspectionError):
            inspect_apk(path)

        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('empty.txt', b'empty')
        with self.assertRaises(InspectionError):
            inspect_apk(path)

    def test_unresolved_identity_and_split_metadata_rejected(self):
        for field in ('split', 'requiredSplitTypes', 'versionCode'):
            namespace = None if field == 'split' else ANDROID
            attrs = [(None, 'package', 3, 'com.example'), (namespace, field, 1, 123)]
            if field != 'versionCode':
                attrs.append((ANDROID, 'versionCode', 0x10, 1))
            path = self.root / 'unresolved.apk'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('AndroidManifest.xml', binary_manifest([('manifest', attrs)]))
            with self.subTest(field=field), self.assertRaises(InspectionError):
                inspect_apk(path)
    def test_unsafe_paths_rejected(self):
        for name in ('../outside', '/absolute', 'assets/../file', 'assets\\file', 'assets//file', 'C:/file'):
            with self.subTest(name=name), self.assertRaises(InspectionError):
                inspect_apk(self.make(extra={name: b'x'}))

    def test_duplicate_entries_rejected(self):
        path = self.make()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(path, 'a') as archive:
                archive.writestr('AndroidManifest.xml', manifest())
        with self.assertRaises(InspectionError):
            inspect_apk(path)

    def test_symbolic_link_rejected(self):
        path = self.make()
        info = zipfile.ZipInfo('assets/link')
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(path, 'a') as archive:
            archive.writestr(info, '../outside')
        with self.assertRaises(InspectionError):
            inspect_apk(path)

    def test_bad_crc_rejected(self):
        path = self.make(extra={'assets/plain': b'unique-fixture-payload'})
        content = path.read_bytes().replace(b'unique-fixture-payload', b'Unique-fixture-payload', 1)
        path.write_bytes(content)
        with self.assertRaises(InspectionError):
            inspect_apk(path)

    def profile(self, report):
        base = report['apks'][0]
        return {'schema_version': 1, 'base': {'package': base['manifest']['package'],
            'version_code': base['manifest']['version_code'], 'sha256': base['sha256'],
            'bundle_sha256': base['bundle']['sha256'], 'hermes_bytecode_version': 98}}

    def test_profile_exact_match_and_each_field_mismatch(self):
        report = inspect_set(self.full_set())
        profile = self.profile(report)
        self.assertEqual(check_profile(report, profile), [])
        for key in profile['base']:
            changed = copy.deepcopy(profile)
            changed['base'][key] = '0' * 64 if 'sha256' in key else (999 if key != 'package' else 'other.package')
            self.assertEqual(len(check_profile(report, changed)), 1)

    def test_bad_profile_schema_and_hashes_rejected(self):
        report = inspect_set(self.full_set())
        for value in ([], {}, {'schema_version': True, 'base': {}}, {'schema_version': 1, 'base': {}}):
            with self.subTest(value=value), self.assertRaises(InspectionError):
                check_profile(report, value)
        profile = self.profile(report)
        profile['base']['sha256'] = 'not-a-hash'
        with self.assertRaises(InspectionError):
            check_profile(report, profile)

    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_cli_inspect_and_check_exit_codes(self):
        paths = self.full_set()
        code, out, _ = self.run_cli(['inspect', str(paths[0])])
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(out)['set']['declared_requirements_met'])
        self.assertEqual(self.run_cli(['check', str(paths[0])])[0], 2)
        self.assertEqual(self.run_cli(['check', *map(str, paths)])[0], 0)
        code, _, err = self.run_cli(['check', str(self.root / 'missing.apk')])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(err)['patch_supported'])

    def test_cli_profile_and_invalid_json(self):
        paths = self.full_set()
        profile = self.profile(inspect_set(paths))
        file = self.root / 'profile.json'
        file.write_text(json.dumps(profile))
        argv = ['check', *map(str, paths), '--profile', str(file)]
        self.assertEqual(self.run_cli(argv)[0], 0)
        profile['base']['sha256'] = '0' * 64
        file.write_text(json.dumps(profile))
        self.assertEqual(self.run_cli(argv)[0], 2)
        file.write_text('{')
        self.assertEqual(self.run_cli(argv)[0], 1)


if __name__ == '__main__':
    unittest.main()
