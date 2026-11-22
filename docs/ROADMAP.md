# Development roadmap

This is a sequence of engineering gates, not a release schedule. v1.0.0 is a target. A milestone is complete only when its evidence is recorded here.

## Stage 01 — Research & architecture

**Status: In progress**

- [x] Inspect the supplied Discord APK and identify its package, version, bundle format and split requirements.
- [x] Review the roles of Vesktop, Vencord, Revenge and Valenced using their primary sources.
- [x] Establish repository structure, offline inspection tooling and development standards.
- [x] Document an architecture proposal and known limits.
- [ ] Obtain the complete installed APK set and verify signatures and native libraries.
- [ ] Compare the current Android loader options against this exact build and select a maintained integration path.
- [ ] Finish the dependency/licence decision and pin the chosen toolchain and upstream revisions.

**Milestone:** A documented technical architecture and development environment validated against the complete input set.

## Stage 02 — Foundation & APK patching

**Status: Planned**

- [ ] Develop a reproducible workflow that operates on local, hash-verified input APKs.
- [ ] Implement a version-specific loader integration with explicit failure checks.
- [ ] Establish signing, split handling, installation and debugging procedures.
- [ ] Build twice with the same inputs and compare the unsigned payloads.
- [ ] Validate startup, login, messaging, notifications and voice on a test device.
- [ ] Confirm recovery to an unmodified installation and document any data migration limits.

**Milestone:** First functional development build. A repackaged APK that has not booted successfully on a device does not meet this gate.

## Stage 03 — Plugin framework

**Status: Planned**

- [ ] Implement loader lifecycle, version checks, enable/disable controls and per-plugin configuration.
- [ ] Define host adapters for the selected Discord Android build.
- [ ] Support cleanup and recovery when plugin startup or shutdown fails.
- [ ] Add initial Android-specific plugins and an explicit compatibility list.
- [ ] Evaluate Vencord plugins one at a time; record reusable logic and Android replacements.
- [ ] Test restricted startup/recovery outside the failing JavaScript plugin path.

**Milestone:** Functional plugin system with initial supported plugins. Catching exceptions is not security isolation from arbitrary plugin code.

## Stage 04 — Appearance & customisation

**Status: Planned**

- [ ] Build the appearance manager using verified React Native integration points.
- [ ] Support named colour tokens, validated theme imports and reversible overrides.
- [ ] Add font customisation with file validation and font-specific licence checks.
- [ ] Test dark/light modes, system contrast, text scaling, landscape and tablets.
- [ ] Explore Vesktop-inspired enhancements suited to Android.

**Milestone:** Customisable Android client with a dependable reset-to-defaults option. Desktop CSS themes are not an Android theme format.

## Stage 05 — Performance & privacy

**Status: Planned**

- [ ] Establish the baseline protocol in [QA.md](QA.md) on stock and modified clients.
- [ ] Profile startup, frame timing, memory and background behaviour.
- [ ] Benchmark targeted optimisations separately and reject changes that regress core features.
- [ ] Implement optional controls for specific verified telemetry paths.
- [ ] Test battery use, notifications, attachments and voice with each privacy control.

**Milestone:** Publish measurements supporting the claimed improvements, including devices, builds, sample counts and limitations.

## Stage 06 — Stability & quality assurance

**Status: Planned**

- [ ] Run the messaging, notifications, media, voice and video matrix.
- [ ] Test supported Android versions, ABIs, display densities and device classes.
- [ ] Investigate crashes, memory leaks, process death, reconnects and split compatibility.
- [ ] Exercise broken plugins, invalid themes, interrupted updates and rollback.
- [ ] Complete extended reliability testing and document unresolved issues.

**Milestone:** Release candidate suitable for broader testing, with a declared support matrix and test evidence.

## Stage 07 — Public release

**Status: Planned**

- [ ] Finalise installation instructions, key management, versioning and recovery instructions.
- [ ] Publish only project-owned or appropriately licensed artefacts after distribution review.
- [ ] Record checksums, toolchain versions, changelog and known limitations.
- [ ] Establish issue reporting, contribution and maintenance workflows.
- [ ] Release only after earlier gates are met.

**Milestone:** Vesktop Android v1.0.0.
