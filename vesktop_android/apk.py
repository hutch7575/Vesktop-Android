"""Read-only APK and split-set inspection. APK contents are never executed."""

from __future__ import annotations

import hashlib
import re
import stat
import struct
import zipfile
from pathlib import Path

from .axml import MAX_MANIFEST, ManifestError, manifest_metadata

MAX_ARCHIVE = 1024 * 1024 * 1024
MAX_ENTRY = 512 * 1024 * 1024
MAX_EXPANDED = 2 * 1024 * 1024 * 1024
MAX_ENTRIES = 30000
HERMES_MAGIC = bytes.fromhex("c61fbc03c103191f")


class InspectionError(ValueError):
    """An APK or profile failed validation."""


def _digest(stream) -> str:
    return hashlib.file_digest(stream, "sha256").hexdigest()


def _validate_entries(entries: list[zipfile.ZipInfo]) -> None:
    if len(entries) > MAX_ENTRIES or sum(e.file_size for e in entries) > MAX_EXPANDED:
        raise InspectionError("Archive exceeds inspection limits")
    seen = set()
    for entry in entries:
        name = entry.filename
        parts = name.rstrip("/").split("/")
        if (entry.orig_filename != name or not name or name.startswith("/")
                or "\\" in name or ":" in name or any(p in ("", ".", "..") for p in parts)
                or any(ord(c) < 32 for c in name)):
            raise InspectionError("Unsafe archive entry name")
        if name in seen:
            raise InspectionError("Duplicate archive entry: " + name)
        seen.add(name)
        if stat.S_ISLNK(entry.external_attr >> 16):
            raise InspectionError("Symbolic links are unsupported")
        if entry.flag_bits & 1:
            raise InspectionError("Encrypted entries are unsupported")
        if entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise InspectionError("Unsupported ZIP compression")
        if entry.file_size > MAX_ENTRY:
            raise InspectionError("Entry exceeds inspection size limit")


def inspect_apk(path: Path) -> dict:
    path = path.resolve()
    if not path.is_file() or path.suffix.lower() != ".apk":
        raise InspectionError("Expected an existing .apk file: " + path.name)
    if path.stat().st_size > MAX_ARCHIVE:
        raise InspectionError("APK exceeds inspection size limit")
    try:
        with path.open("rb") as source, zipfile.ZipFile(source) as archive:
            entries = archive.infolist()
            _validate_entries(entries)
            names = {e.filename for e in entries}
            if "AndroidManifest.xml" not in names:
                raise InspectionError("AndroidManifest.xml is missing")
            if archive.getinfo("AndroidManifest.xml").file_size > MAX_MANIFEST:
                raise InspectionError("Manifest exceeds inspection size limit")
            # Hashing every entry also checks local ZIP headers and CRCs. Nothing
            # is extracted. Streaming bounds memory use for large bundles.
            hashes = {}
            for entry in entries:
                with archive.open(entry) as stream:
                    hashes[entry.filename] = _digest(stream)
            manifest = manifest_metadata(archive.read("AndroidManifest.xml"))
            if not isinstance(manifest["package"], str) or not manifest["package"]:
                raise InspectionError("Manifest application ID is missing")
            for field in ("version_code", "version_code_major"):
                value = manifest[field]
                if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
                    raise InspectionError("Unresolved manifest version code")
            for field in ("split", "config_for_split", "required_split_types", "split_types"):
                if manifest[field] is not None and not isinstance(manifest[field], str):
                    raise InspectionError("Unresolved manifest split metadata")
            if any(not isinstance(name, str) or not name for name in manifest["uses_splits"]):
                raise InspectionError("Unresolved required split name")
            bundle = None
            name = "assets/index.android.bundle"
            if name in names:
                with archive.open(name) as stream:
                    prefix = stream.read(12)
                hermes = prefix[:8] == HERMES_MAGIC
                if hermes and len(prefix) < 12:
                    raise InspectionError("Truncated Hermes bundle header")
                bundle = {
                    "path": name,
                    "size_bytes": archive.getinfo(name).file_size,
                    "sha256": hashes[name],
                    "format": "hermes_bytecode" if hermes else "unidentified",
                    "hermes_bytecode_version": struct.unpack_from("<I", prefix, 8)[0] if hermes else None,
                }
            source.seek(0)
            return {
                "file_name": path.name,
                "sha256": _digest(source),
                "size_bytes": path.stat().st_size,
                "entry_count": len(entries),
                "expanded_size_bytes": sum(e.file_size for e in entries),
                "manifest": manifest,
                "manifest_sha256": hashes["AndroidManifest.xml"],
                "bundle": bundle,
                "dex_files": sorted(n for n in names if re.fullmatch(r"classes(?:[2-9]|[1-9][0-9]+)?\.dex", n)),
                "native_libraries": sorted(n for n in names if n.startswith("lib/") and n.endswith(".so")),
                "signature_verification": "not_performed",
            }
    except (zipfile.BadZipFile, ManifestError, EOFError, RuntimeError, NotImplementedError, struct.error) as exc:
        raise InspectionError("Invalid APK: " + str(exc)) from exc


def _types(value: object) -> set[str]:
    if value in (None, ""):
        return set()
    if not isinstance(value, str):
        raise InspectionError("Unresolved split-type metadata")
    return {part.strip() for part in value.split(",") if part.strip()}


def inspect_set(paths: list[Path]) -> dict:
    if not paths or len(paths) > 100:
        raise InspectionError("Provide between 1 and 100 APK paths")
    resolved = [p.resolve() for p in paths]
    if len(set(resolved)) != len(resolved):
        raise InspectionError("An input APK was supplied more than once")
    apks = [inspect_apk(p) for p in paths]
    bases = [a for a in apks if not a["manifest"]["split"]]
    blockers = []
    if len(bases) != 1:
        blockers.append("Exactly one base APK is required")
    identities = {(a["manifest"]["package"], str(a["manifest"]["version_code"]),
                   str(a["manifest"]["version_code_major"])) for a in apks}
    if len(identities) != 1:
        blockers.append("APK package names or version codes do not match")
    split_names = [a["manifest"]["split"] for a in apks if a["manifest"]["split"]]
    if len(set(split_names)) != len(split_names):
        blockers.append("Duplicate split identifiers")
    required, provided = set(), set()
    for apk in apks:
        manifest = apk["manifest"]
        target = manifest["config_for_split"]
        if target and target != "base" and target not in split_names:
            blockers.append("Missing target for configuration split: " + str(target))
        required.update(_types(manifest["required_split_types"]))
        provided.update(_types(manifest["split_types"]))
        for name in manifest["uses_splits"]:
            if name not in split_names:
                blockers.append("Missing required split: " + str(name))
    for missing in sorted(required - provided):
        blockers.append("Missing declared split type: " + missing)
    if len(bases) == 1:
        manifest = bases[0]["manifest"]
        requires = manifest["split_required"] or manifest["play_splits_required"] or required
        if requires and not split_names:
            blockers.append("Base APK declares required splits; none were supplied")
    libraries = sorted({n for a in apks for n in a["native_libraries"]})
    if any(a["bundle"] and a["bundle"]["format"] == "hermes_bytecode" for a in apks) and not libraries:
        blockers.append("Hermes bundle is present but the supplied set has no native libraries")
    return {
        "schema_version": 1,
        "tool_version": "0.1.0.dev0",
        "apks": apks,
        "set": {
            "declared_requirements_met": not blockers,
            "required_split_types": sorted(required),
            "provided_split_types": sorted(provided),
            "native_abis": sorted({n.split("/")[1] for n in libraries}),
            "blockers": sorted(set(blockers)),
            "signature_verification": "not_performed",
            "installation_verified": False,
            "patch_supported": False,
            "reason": "Research tooling only; no Android loader or production patch recipe implemented",
        },
    }


def check_profile(report: dict, profile: dict) -> list[str]:
    """Require an exact base APK fingerprint; a match does not enable patching."""
    if (not isinstance(profile, dict) or type(profile.get("schema_version")) is not int
            or profile["schema_version"] != 1 or not isinstance(profile.get("base"), dict)):
        raise InspectionError("Unsupported compatibility profile schema")
    expected = profile["base"]
    required = {"package", "version_code", "sha256", "bundle_sha256", "hermes_bytecode_version"}
    if set(expected) != required:
        raise InspectionError("Compatibility profile must specify an exact base and bundle fingerprint")
    for key in ("sha256", "bundle_sha256"):
        if not isinstance(expected[key], str) or not re.fullmatch("[0-9a-f]{64}", expected[key]):
            raise InspectionError("Invalid SHA-256 in compatibility profile")
    if (not isinstance(expected["package"], str) or not expected["package"]
            or type(expected["version_code"]) is not int
            or type(expected["hermes_bytecode_version"]) is not int):
        raise InspectionError("Invalid compatibility profile identity")
    bases = [a for a in report["apks"] if not a["manifest"]["split"]]
    if len(bases) != 1:
        return ["Cannot match a profile without exactly one base APK"]
    base = bases[0]
    bundle = base["bundle"] or {}
    actual = {"package": base["manifest"]["package"], "version_code": base["manifest"]["version_code"],
              "sha256": base["sha256"], "bundle_sha256": bundle.get("sha256"),
              "hermes_bytecode_version": bundle.get("hermes_bytecode_version")}
    return ["Base APK does not match profile field: " + key
            for key in sorted(required) if str(actual[key]) != str(expected[key])]
