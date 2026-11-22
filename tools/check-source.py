"""Reject accidental proprietary artefacts or signing material in the git tree."""

import pathlib
import subprocess
import sys

blocked = {".apk", ".apks", ".aab", ".xapk", ".dex", ".hbc", ".so", ".jks", ".keystore", ".pk8", ".pem", ".zip"}
result = subprocess.run(["git", "ls-files", "-z"], check=True, capture_output=True)
paths = [p.decode("utf-8") for p in result.stdout.split(b"\0") if p]
bad = [p for p in paths if pathlib.Path(p).suffix.lower() in blocked
       or pathlib.PurePosixPath(p).name in {"index.android.bundle", "local.properties"}]
if bad:
    print("Forbidden tracked artefacts:\n" + "\n".join(bad), file=sys.stderr)
    sys.exit(1)
print("Tracked source contains no blocked artefacts.")
