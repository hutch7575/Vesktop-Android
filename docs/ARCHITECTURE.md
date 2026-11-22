# Technical architecture proposal

Status: Research proposal, 22 November 2026. Only the offline Python inspection layer exists. Kotlin, TypeScript, loaders, patches and the manager described below are proposed components.

## Why this approach

Discord describes its mobile clients as React Native applications. The supplied Android build contains Hermes bytecode. Vesktop's Electron process and Vencord's browser/webpack integration therefore cannot simply be compiled into this APK. Android needs host-specific loading, UI and module adapters. Sources and inspected upstream file revisions are listed in [RESEARCH.md](RESEARCH.md).

Use the official client's native and React Native layers, introduce a small loader, and expose selected Android host capabilities through versioned adapters. Choose the loader implementation after inspecting all input splits and reviewing upstream maintenance and licences. Do not commit to a fork solely because a past Discord build supported it.

## Boundaries

| Component | Responsibility | State |
| --- | --- | --- |
| Offline preflight | Read manifests, hash inputs, identify Hermes headers and missing split declarations | Implemented in Python |
| Compatibility profiles | Pin the exact inspected base APK and bundle fingerprint | One research profile; patch support disabled |
| Local patch engine | Integrate an approved loader into version-specific complete APK inputs | Proposed |
| Native loader | Run before Discord's bundle, supply configuration and recovery hooks | Proposed |
| Host adapters | Expose verified React Native modules, settings UI and theme tokens | Proposed |
| Plugin runtime | Lifecycle, configuration, cleanup and feature compatibility checks | Proposed |
| Android manager | Select local files, validate, patch, sign, install and recover | Proposed; Kotlin/Compose candidate |

## Research and input validation

The inspector understands manifest string pools and typed attributes sufficiently to read the metadata it reports. It is not an AXML decompiler, resource resolver or APK verifier. Unknown resource-typed values remain explicit. It streams archive contents to check ZIP CRCs and compute hashes; nothing is executed or extracted.

It accepts a base APK with companion split APKs and checks declared type/name dependencies, package names and version codes. It cannot prove completeness for a particular device, check signing certificates or establish Android installability. The `check` command's success means only that these metadata checks passed. `patch_supported` remains false for every report until actual patching support is implemented and validated.

## Loader selection gate

Investigate existing Android integrations first. Valenced documents a Hermes bundle, native Android loader, shared plugin core and non-root patch definitions. Revenge documents a similar separation but its organisation points new work towards Valenced. These are reference architectures, not selected dependencies.

Compare rootless patching and rooted Xposed experiments separately. The intended user workflow is rootless. A rooted proof of concept may help diagnose loading, but does not satisfy the rootless installation milestone. Record loader revision, required Android API, supported Discord builds, Hermes bytecode version and all required permissions before selecting an implementation.

Do not concatenate JavaScript onto Hermes bytecode or perform blind search-and-replace inside it. The loader must interact with the actual runtime through a verified integration point. Recompiling Hermes output requires matching tools and proof of compatibility.

## Intended local build pipeline

1. Select the complete locally supplied APK set. Validate package identity, version, exact fingerprints, source signatures and split dependencies.
2. Resolve a pinned patch profile. Reject unknown builds before modifying anything.
3. Apply reviewed project-owned or licensed loader changes in a temporary workspace. Keep original inputs intact.
4. Align each output with Android Build Tools, including native library page alignment, before signing.
5. Sign all outputs with the same local key. Verify signatures, certificates, package metadata and split consistency.
6. Produce hashes and a receipt identifying inputs, patch revision, tool versions and outputs. Installation is a separate explicit operation.

Android's signing model prevents a locally re-signed package from acting as a normal update over a package signed by Discord. Changing the application ID has separate integration risks involving authorities, deep links, authentication and notifications. Neither migration nor side-by-side installation is solved by this proposal. No current script uninstalls Discord or changes its package identity.

ZIP alignment alone cannot prove that native ELF libraries support 16 KiB pages. The complete native split set must also be examined and tested. Signature/identity-dependent services require device validation; familiar UI does not imply their behaviour survives modification.

## Recovery and trust

Proposed first-party plugins should be bundled and pinned, with no executable update fetched during startup. A user should be able to boot with customisations disabled through a native recovery path that does not depend on the failing plugin. Retain the last working settings revision and provide a clear reset action.

Plugin lifecycle guards reduce accidental failures. Plugins in Discord's process still share access to that process and its account/session data. Capability declarations and try/catch do not sandbox hostile code, stop an infinite loop or recover from every native crash. A remotely installable plugin catalogue needs a separate trust and update design before implementation.

## Immediate next work

Obtain the ABI/density splits, verify the signing set with official tooling, inventory native entry points and compare maintained Android loaders against this exact build. Then document the dependency/licence choice and implement the smallest loader smoke test. Feature work follows a successful launch and recovery test.
