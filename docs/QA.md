# QA and performance gates

All Android/device results are currently **not run**. The Python tests verify local inspection behaviour only. They do not validate Discord startup or compatibility.

## Functional matrix for the first development build

| Area | Scenarios | Result |
| --- | --- | --- |
| Installation | Complete split set, same signer, rejected unknown build, failed update recovery | Not run |
| Account access | Login, existing session, logout and authentication links | Not run |
| Messaging | DM, server message, replies, editing, deletion, reconnect and offline recovery | Not run |
| Notifications | Foreground/background/locked screen, reply action, Android permission states | Not run |
| Voice | Join/leave, mute/deafen, speaker/Bluetooth/wired route, reconnect, background call | Not run |
| Video | Camera permissions, camera switching, incoming/outgoing calls | Not run |
| Media | Images, video, files, download/share, failed upload recovery | Not run |
| UI | Light/dark, text scaling, accessibility, landscape, gesture and button navigation | Not run |
| Recovery | Invalid plugin/theme, process death, interrupted patch, disabled customisations | Not run |

Derive the supported Android range from the actual patched inputs and native dependencies. Do not advertise every version above the base manifest's minimum API without tests. Include at least a lower-memory device and the primary target device; record ABI, density, Android API, manufacturer and battery restrictions.

## Benchmark protocol

Compare stock and modified builds from the same complete input set, on the same device, with matching account/server state, network, cache state, screen refresh rate, temperature and battery conditions. Record plugin/theme configuration. Separate cold/warm starts, first launch and steady-state measurements.

Measure startup to a usable channel, frame timing while scrolling, memory after a repeatable session, and background/voice battery behaviour. Use Android profiling tools for system traces and frame timings; shell activity launch time alone does not prove React Native content is ready. Record raw samples and use at least 20 comparable samples for startup claims; report median, p95, sample count and observed variability. Keep profiling overhead consistent.

For battery tests, record test duration, radio/network conditions and device power settings. Require repeat runs and a sufficiently long observation interval; a short idle test does not establish a battery improvement. Privacy changes are benchmarked independently and rerun through the notifications/voice matrix.

## Release evidence

Every candidate needs the source commit, input and output SHA-256 hashes, patch profile, toolchain versions, signer certificate fingerprint, device matrix, functional results, benchmark data and known issues. Publish project-owned/licensed sources and patch definitions, keeping proprietary APK inputs, private signing keys, account tokens and private messages out of the repository and CI artefacts.
