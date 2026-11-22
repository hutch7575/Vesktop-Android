"""Generated Android-format metadata, containing no Discord code or resources."""

import struct
import zipfile
from pathlib import Path

from vesktop_android.axml import ANDROID

NIL = 0xFFFFFFFF


def binary_manifest(nodes, utf8=True):
    strings = []

    def index(value):
        if value not in strings:
            strings.append(value)
        return strings.index(value)

    def length(value):
        if utf8:
            return bytes([value]) if value < 128 else bytes([0x80 | (value >> 8), value & 255])
        return struct.pack('<H', value) if value < 32768 else struct.pack('<HH', 0x8000 | (value >> 16), value & 65535)

    chunks = []
    for tag, attrs in nodes:
        attributes = []
        for namespace, name, kind, value in attrs:
            ns = index(namespace) if namespace else NIL
            name_id = index(name)
            raw = index(value) if kind == 3 else NIL
            encoded = raw if kind == 3 else value
            attributes.append(struct.pack('<IIIHBBI', ns, name_id, raw, 8, 0, kind, encoded))
        body = struct.pack('<IIHHHHHH', NIL, index(tag), 20, 20, len(attrs), 0, 0, 0) + b''.join(attributes)
        chunks.append(struct.pack('<HHIII', 0x102, 16, 16 + len(body), 1, NIL) + body)
    for tag, _ in reversed(nodes):
        chunks.append(struct.pack('<HHIIIII', 0x103, 16, 24, 1, NIL, NIL, index(tag)))
    offsets, storage = [], bytearray()
    for value in strings:
        offsets.append(len(storage))
        raw = value.encode('utf-8' if utf8 else 'utf-16le')
        units = len(value.encode('utf-16le')) // 2
        if utf8:
            storage.extend(length(units))
        storage.extend(length(len(raw) if utf8 else units))
        storage.extend(raw)
        storage.extend(bytes(1 if utf8 else 2))
    storage.extend(bytes((-len(storage)) % 4))
    start = 28 + 4 * len(strings)
    pool = struct.pack('<HHIIIIII', 1, 28, start + len(storage), len(strings), 0, 0x100 if utf8 else 0, start, 0)
    pool += b''.join(struct.pack('<I', o) for o in offsets) + storage
    body = pool + b''.join(chunks)
    return struct.pack('<HHI', 3, 8, 8 + len(body)) + body


def manifest(*, package='com.example.fixture', code=1, split=None, types='', required='', uses=(), target=None):
    attrs = [(None, 'package', 3, package), (ANDROID, 'versionCode', 0x10, code),
             (ANDROID, 'versionName', 3, '1.0')]
    if split:
        attrs.append((None, 'split', 3, split))
    if target:
        attrs.append((None, 'configForSplit', 3, target))
    if types:
        attrs.append((ANDROID, 'splitTypes', 3, types))
    if required:
        attrs.append((ANDROID, 'requiredSplitTypes', 3, required))
    nodes = [('manifest', attrs), ('application', [(ANDROID, 'isSplitRequired', 0x12, int(bool(required)))])]
    nodes += [('uses-split', [(ANDROID, 'name', 3, name)]) for name in uses]
    return binary_manifest(nodes)


def apk(path: Path, *, extra=None, **kwargs):
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('AndroidManifest.xml', manifest(**kwargs))
        for name, value in (extra or {}).items():
            archive.writestr(name, value)
    return path
