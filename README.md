# Vesktop Android

**A native Android Discord modification project.**

Bringing the customisation, freedom and performance-focused philosophy of Vesktop to Android.

**Performance · Customisation · Privacy · Stability**

## Project overview

Vesktop Android aims to bring selected ideas from Vesktop and Vencord to Discord's existing Android application through a reproducible, user-side patching system. The intended result keeps Discord's familiar mobile interface, messaging, media, voice calls and notifications.

This project targets the existing Android client and its React Native runtime. It will investigate a native loader and Android-specific plugins rather than a WebView shell or a replacement Discord implementation.

**Current status: research foundation. There is no installable Vesktop Android client yet.** The repository currently contains offline APK inspection tools, an analysis of Discord build `354012`, an architecture proposal and a staged development plan. No performance improvement, working plugin support or device compatibility has been demonstrated.

## Planned features

| Feature | Intended behaviour | Status |
| --- | --- | --- |
| Native Android experience | Preserve Discord's mobile interface and core communication features | Planned; requires device validation |
| Plugin framework | Modular features, configuration and selected Vencord-inspired adaptations | Planned; desktop plugins will need individual review and porting |
| Appearance manager | Themes, colours, fonts and interface adjustments | Planned |
| Performance improvements | Profile startup, memory, rendering and battery use before making targeted changes | Planned; no benchmark results yet |
| Privacy controls | Optional controls for identified telemetry paths, with regression testing | Planned |
| Reliable updates | Version checks, reproducible patches, recovery and tested releases | Planned |

## Development roadmap

| Stage | Focus | Milestone | Status |
| --- | --- | --- | --- |
| 01 | Research & architecture | Documented architecture and development environment | In progress |
| 02 | Foundation & APK patching | First functional development build | Planned; complete input APK set needed |
| 03 | Plugin framework | Loader, manager and initial supported plugins | Planned |
| 04 | Appearance & customisation | Customisable Android client | Planned |
| 05 | Performance & privacy | Measured improvements with core functionality preserved | Planned |
| 06 | Stability & QA | Release candidate tested across the declared device matrix | Planned |
| 07 | Public release | Vesktop Android v1.0.0 | Planned |

See the [full roadmap and acceptance criteria](docs/ROADMAP.md).

## Start with the inspection tools

Requires Python 3.11 or newer. No Python dependencies, Android SDK or installation step is needed to inspect APKs from the repository root.

```sh
python3 -m unittest discover -s tests -v
python3 -m vesktop_android inspect /path/to/base.apk
python3 -m vesktop_android check /path/to/base.apk /path/to/split_config.arm64_v8a.apk /path/to/split_config.xxhdpi.apk
```

On Windows, use `py -3` in place of `python3`. `inspect` prints JSON; `check` additionally returns exit code `2` when declared split requirements or an optional fingerprint profile do not match. A successful check is metadata preflight only: APK signatures, installation and loader compatibility remain unverified.

The tools read APKs without extracting or executing their contents. They do not patch, sign, download or install Discord.

### First APK findings

Discord `354.12 - Stable` (`354012`) contains a 51,017,904-byte Hermes bundle using bytecode version `98`. The provided file is a base APK declaring required ABI and density splits. It contains no native `.so` libraries, so that file alone is insufficient for the intended installation workflow.

See the [APK report](docs/APK-354012.md). The [Windows export script](tools/export-discord.ps1) pulls every installed Discord APK through ADB and creates a ZIP locally. See [development setup](docs/DEVELOPMENT.md) for usage.

## Development principles

**Stability before features.** Protect messaging, notifications, voice and video as changes are introduced.

**Optimisation through evidence.** Record baselines and repeatable benchmarks; publish results alongside the device and build details.

**Modular by design.** Keep patches, host integration, plugins and appearance configuration independently maintainable where possible.

**Transparent development.** Document progress, technical limitations, failed experiments and known issues.

**Maintainability.** Pin compatible inputs, verify hashes and minimise manual update steps.

## Project information

| Item | Detail |
| --- | --- |
| Repository | `Vesktop-Android` |
| Platform | Android |
| Development | Intended open-source community project |
| Status | Planning and technical research |
| Initial public target | v1.0.0; no release date set |
| Licence | Pending dependency and distribution review; see [licensing status](LICENSE.md) |

Read the [architecture](docs/ARCHITECTURE.md), [upstream research](docs/RESEARCH.md), [plugin design](docs/PLUGINS.md), [QA plan](docs/QA.md) and [contribution guide](CONTRIBUTING.md).

Vesktop Android is an independent community project. It is not affiliated with, endorsed by or officially supported by Discord, Vesktop or Vencord. No upstream code has been copied into this foundation. The project intends to distribute its own source and patch definitions, with proprietary application inputs supplied locally by users. Modified clients may violate Discord's terms of service.

## The vision

**Your Discord. Your Plugins. Your Experience.**

A faster, more personal and more flexible Discord experience on Android.

**Vesktop Android — Customisation without compromise.**
