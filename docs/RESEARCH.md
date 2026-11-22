# Upstream research

Reviewed 22 November 2026. These are sources for design decisions, not vendored dependencies. No upstream implementation code is included in this repository. Licence observations below describe the inspected files; dependency adoption still needs a review of all included components and notices.

| Source | Observation | Project implication |
| --- | --- | --- |
| [Discord: mobile performance](https://discord.com/blog/supercharging-discord-mobile-our-journey-to-a-faster-app) | Describes React Native mobile clients, the Android transition and Hermes | Investigate the native/React Native host, and measure overhead before claiming gains |
| [Vesktop package metadata](https://github.com/Vencord/Vesktop/blob/main/package.json) | Electron desktop build; declares GPL-3.0-or-later | Use the product philosophy as inspiration; its desktop process is not an Android loader |
| [Vencord webpack integration](https://github.com/Vendicated/Vencord/blob/main/src/webpack/patchWebpack.ts) | Hooks webpack factories and browser globals; declares GPL-3.0-or-later | Desktop plugins depending on these internals need Android adapters or rewrites |
| [Revenge organisation](https://github.com/revenge-mod) | Announces maintenance mode and points to Valenced | Review the successor before selecting a long-term base |
| [Revenge bundle](https://github.com/revenge-mod/revenge-bundle) | Separate runtime bundle and loaders; README identifies BSD-3-Clause for this bundle | Useful architecture reference; does not determine licences for loaders or other forks |
| [RevengeXposed](https://github.com/revenge-mod/revenge-xposed) | Android loader for a Hermes bundle; README identifies GPL-3.0 | Demonstrates a native loader boundary; rooted support is distinct from the intended rootless workflow |
| [Valenced](https://github.com/Valenced/valenced) | TypeScript and Kotlin Multiplatform; native loaders, Hermes bundle and plugin core | Investigate this integration before creating a competing loader from scratch |
| [Valenced licence notes](https://github.com/Valenced/valenced#-license) | README identifies GPL-3.0 for the project and AGPL-3.0 for `android/patches` | Review each component before reuse and keep required notices |
| [Android APK Analyzer CLI](https://developer.android.com/tools/apkanalyzer) | Official manifest and archive inspection commands | Independently cross-check the custom inspector using the complete APK set |
| [Android app signing](https://developer.android.com/studio/publish/app-signing) | Certificates establish app/update identity | Plan consistent local signing and investigate identity-dependent integrations |
| [zipalign](https://developer.android.com/tools/zipalign) | Documents alignment before apksigner and `-P 16` for shared libraries | Align unsigned outputs and verify separately; do not modify signed outputs |
| [apksigner](https://developer.android.com/tools/apksigner) | Official signing and signature-verification tool | Verify every supplied/output split, not just the base APK |
| [AOSP resource format definitions](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/libs/androidfw/include/androidfw/ResourceTypes.h) | Defines binary XML string pools, nodes and typed attributes | Format reference for the original bounded metadata reader |
| [Hermes bytecode header](https://github.com/meta/hermes/blob/main/include/hermes/BCGen/HBC/BytecodeFileFormat.h) | Defines the bytecode magic and version header | Identify bundle format without executing or decompiling the bundle |

## Inspected source-file identities

Git blob IDs identify the exact file content returned by GitHub during research. They are not release tags or a complete dependency lockfile.

| Repository | File | Git blob SHA |
| --- | --- | --- |
| `Vencord/Vesktop` | `package.json` | `292f1db92f60a0e7d35d8cf6855efcb62568bde0` |
| `Vendicated/Vencord` | `src/webpack/patchWebpack.ts` | `4ea71b8557142cb34890ea182e12b706a8acfac8` |
| `revenge-mod/revenge-xposed` | `README.md` | `dfcf85f3a07e9649b272036302de895516d0dc70` |
| `Valenced/valenced` | `README.md` | `115b8acaa96196faa65027d66559245317ce074a` |

## Open questions

The complete build's loader entry point, native library compatibility, rootless patch support, signing behaviour and push/voice reliability remain unverified. A project being public or recently maintained does not establish compatibility with Discord `354012`. No blanket Vencord plugin compatibility is claimed.
