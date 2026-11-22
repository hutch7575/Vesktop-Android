# Development setup

## Current tooling

Use Python 3.11+ from the repository root. The tooling uses only the Python standard library; no dependency install or Android SDK is needed for the inspection step.

```sh
python3 -m unittest discover -s tests -v
python3 -m vesktop_android --version
python3 -m vesktop_android inspect /path/to/base.apk
python3 -m vesktop_android check /path/to/base.apk --profile compatibility/discord-354012.json
```

On Windows, replace `python3` with `py -3`. `inspect` produces JSON and returns zero for a valid readable input even when the set is incomplete. `check` returns `2` for missing declared splits or a profile mismatch, `1` for invalid input, and `0` for matching metadata. Zero is not proof of signatures, device installation or patch support.

Pass all exported `.apk` paths as positional arguments to inspect a complete set. The current CLI does not unpack `.zip`, `.apks` or `.xapk` containers. Extract an export ZIP into a local folder first. PowerShell example:

```powershell
$apkFiles = @((Get-ChildItem -LiteralPath '.\Discord-APK-Export' -Filter '*.apk').FullName)
py -3 -m vesktop_android check @apkFiles --profile compatibility/discord-354012.json
```

The profile pins the supplied base and bundle bytes. An app update or a separately generated APK may have different bytes even if its displayed version matches. A profile match does not claim the project supports patching that build.

## Export every installed Discord APK on Windows

Install [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools), connect the phone with USB debugging enabled and authorise that computer on the phone. Keep Discord on the same version during the export. The script requires an existing ADB installation and does not download software or change device settings.

From the repository root in PowerShell:

```powershell
.\tools\export-discord.ps1 -AdbPath 'C:\platform-tools\adb.exe'
```

For more than one device, add `-Serial` with the chosen serial from `adb devices`. Add `-Destination` to select a new output folder. The default creates a dated folder in the current directory and an adjacent ZIP. The script refuses an existing destination. Its ZIP contains application packages only; SHA-256 checksums remain alongside the exported APK files in the folder.

Manual equivalent, using the package paths returned by the first command:

```sh
adb shell pm path com.discord
adb pull /data/app/EXACT_RETURNED_DIRECTORY/base.apk
adb pull /data/app/EXACT_RETURNED_DIRECTORY/split_config.arm64_v8a.apk
```

Pull **every path actually returned**. The split example is illustrative; device filenames vary. The export copies installed app code/resources rather than Discord's private data. It does not require root or uninstall anything. See [ADB documentation](https://developer.android.com/tools/adb).

The script has not been exercised against a physical phone in this environment. Device access is needed to validate it end to end.

## Independently verify inputs

Before loader work, install the official Android SDK Command-Line Tools and Build Tools, record their versions and inspect each APK with `apkanalyzer`. Use `apksigner verify --verbose --print-certs` on every file; check that all splits belong to the same signer/package/version family. Signature verification has not yet been performed on the supplied input here.

Future patched outputs need alignment **before** signing. Android documents `zipalign -P 16 -v 4` for shared library alignment and a separate `zipalign -c -P 16 -v 4` check. Follow [zipalign](https://developer.android.com/tools/zipalign) and [apksigner](https://developer.android.com/tools/apksigner). Do not treat this as a complete patch recipe: loader integration, manifest/split changes and native compatibility remain unresolved.

Keep APKs, extracted application code, keys and local results outside tracked source. The project currently has no Android Gradle app, implemented loader or installable release.
