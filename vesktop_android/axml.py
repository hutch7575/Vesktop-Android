"""Bounded reader for manifest metadata in Android binary XML.

This reads attributes, not resources or executable code. It is intentionally
smaller than a general AXML decompiler. Unknown value types remain explicit.
"""

from __future__ import annotations

import struct
import xml.etree.ElementTree as ET


class ManifestError(ValueError):
    """The manifest cannot be safely interpreted."""


ANDROID = "http://schemas.android.com/apk/res/android"
NO_INDEX = 0xFFFFFFFF
MAX_MANIFEST = 8 * 1024 * 1024


def _number(data: bytes, offset: int, fmt: str = "I") -> int:
    size = struct.calcsize("<" + fmt)
    if offset < 0 or offset + size > len(data):
        raise ManifestError("Truncated binary XML value")
    return struct.unpack_from("<" + fmt, data, offset)[0]


def _length(data: bytes, offset: int, utf8: bool) -> tuple[int, int]:
    unit, high, mask, shift = (1, 0x80, 0x7F, 8) if utf8 else (2, 0x8000, 0x7FFF, 16)
    fmt = "B" if utf8 else "H"
    first = _number(data, offset, fmt)
    offset += unit
    if first & high:
        first = ((first & mask) << shift) | _number(data, offset, fmt)
        offset += unit
    return first, offset


def _strings(chunk: bytes) -> list[str]:
    header = _number(chunk, 2, "H")
    count, styles, flags, start, styles_start = struct.unpack_from("<IIIII", chunk, 8)
    table_end = header + 4 * (count + styles)
    end = styles_start or len(chunk)
    if header < 28 or table_end > start or start > end or end > len(chunk):
        raise ManifestError("Invalid string-pool bounds")
    utf8 = bool(flags & 0x100)
    result = []
    pool = chunk[:end]
    for i in range(count):
        offset = start + _number(chunk, header + 4 * i)
        if offset < start or offset >= end:
            raise ManifestError("String outside string pool")
        if utf8:
            _, offset = _length(pool, offset, True)
        length, offset = _length(pool, offset, utf8)
        width = 1 if utf8 else 2
        finish = offset + length * width
        if finish + width > end or pool[finish:finish + width] != bytes(width):
            raise ManifestError("Invalid string-pool terminator")
        try:
            result.append(pool[offset:finish].decode("utf-8" if utf8 else "utf-16le"))
        except UnicodeError as exc:
            raise ManifestError("Invalid string-pool encoding") from exc
    return result


def read_elements(data: bytes) -> list[tuple[str, dict[str, object]]]:
    """Return start-element names and namespace-qualified attributes."""
    if len(data) > MAX_MANIFEST:
        raise ManifestError("Manifest exceeds size limit")
    # Text XML is useful for generated fixtures and decoded manifest inspection.
    if data.lstrip().startswith(b"<"):
        try:
            root = ET.fromstring(data)
        except ET.ParseError as exc:
            raise ManifestError("Invalid text XML manifest") from exc
        if root.tag != "manifest":
            raise ManifestError("Manifest root is missing")
        return [(e.tag, dict(e.attrib)) for e in root.iter()]
    if len(data) < 8 or _number(data, 0, "H") != 3:
        raise ManifestError("Expected Android binary XML")
    size, offset = _number(data, 4), _number(data, 2, "H")
    if size != len(data) or offset != 8:
        raise ManifestError("Invalid XML file header")
    strings: list[str] | None = None
    result = []

    def string(index: int) -> str:
        if strings is None or index >= len(strings):
            raise ManifestError("Invalid XML string index")
        return strings[index]

    while offset < size:
        kind = _number(data, offset, "H")
        header = _number(data, offset + 2, "H")
        length = _number(data, offset + 4)
        if header < 8 or length < header or offset + length > size:
            raise ManifestError("Invalid XML chunk bounds")
        chunk = data[offset:offset + length]
        if kind == 1:
            if strings is not None or length < 28:
                raise ManifestError("Invalid or repeated string pool")
            strings = _strings(chunk)
        elif kind == 0x0102:
            if header != 16 or length < 36:
                raise ManifestError("Invalid start-element chunk")
            name = string(_number(chunk, 20))
            attr_start = 16 + _number(chunk, 24, "H")
            attr_size = _number(chunk, 26, "H")
            count = _number(chunk, 28, "H")
            if attr_start < 36 or attr_size < 20 or attr_start + attr_size * count > length:
                raise ManifestError("Invalid attribute bounds")
            attrs: dict[str, object] = {}
            for i in range(count):
                at = attr_start + i * attr_size
                ns, key, raw = struct.unpack_from("<III", chunk, at)
                value_size = _number(chunk, at + 12, "H")
                value_type = _number(chunk, at + 15, "B")
                value = _number(chunk, at + 16)
                if value_size != 8:
                    raise ManifestError("Invalid typed attribute")
                key = string(key)
                if ns != NO_INDEX:
                    key = "{" + string(ns) + "}" + key
                if key in attrs:
                    raise ManifestError("Duplicate XML attribute")
                if value_type == 3:
                    parsed: object = string(value)
                elif value_type == 0x12:
                    parsed = bool(value)
                elif value_type in (0x10, 0x11):
                    parsed = value
                elif raw != NO_INDEX:
                    parsed = string(raw)
                else:
                    parsed = {"type": value_type, "data": value}
                attrs[key] = parsed
            result.append((name, attrs))
        offset += length
    if not result or result[0][0] != "manifest":
        raise ManifestError("Manifest root is missing")
    return result


def manifest_metadata(data: bytes) -> dict:
    elements = read_elements(data)
    root = elements[0][1]
    android = lambda name: "{" + ANDROID + "}" + name
    app = next((attrs for tag, attrs in elements if tag == "application"), {})
    metadata = {attrs.get(android("name")): attrs.get(android("value"))
                for tag, attrs in elements if tag == "meta-data"}

    def boolean(value: object) -> bool:
        if value in (False, "false", "0", None):
            return False
        if value in (True, "true", "1"):
            return True
        raise ManifestError("Unresolved manifest boolean")

    def integer(value: object) -> object:
        if isinstance(value, str) and value.isdecimal():
            return int(value)
        return value

    return {
        "package": root.get("package"),
        "version_name": root.get(android("versionName")),
        "version_code": integer(root.get(android("versionCode"))),
        "version_code_major": integer(root.get(android("versionCodeMajor"), 0)),
        "split": root.get("split"),
        "config_for_split": root.get("configForSplit"),
        "is_feature_split": boolean(root.get(android("isFeatureSplit"), False)),
        "split_required": boolean(app.get(android("isSplitRequired"), False)),
        "required_split_types": root.get(android("requiredSplitTypes")),
        "split_types": root.get(android("splitTypes")),
        "uses_splits": [attrs.get(android("name")) for tag, attrs in elements if tag == "uses-split"],
        "play_splits_required": boolean(metadata.get("com.android.vending.splits.required", False)),
        "min_sdk": next((a.get(android("minSdkVersion")) for t, a in elements if t == "uses-sdk"), None),
        "target_sdk": next((a.get(android("targetSdkVersion")) for t, a in elements if t == "uses-sdk"), None),
    }
