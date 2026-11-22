# Proposed plugin contract

Status: Design only. No plugin runtime or Android host adapter is implemented.

Use a small versioned manifest with a stable plugin ID, version, plugin API version, supported host-adapter versions, description, dependency IDs and capability declarations. Unknown APIs and missing dependencies should disable the plugin with a readable reason.

First-party plugins should expose an asynchronous `start(context)` lifecycle and register cleanup functions for hooks, listeners, timers and settings views. The manager should call cleanup in reverse order on disable, record failures and avoid leaving partially applied changes active. Dependency cycles, duplicate IDs and repeated enable/disable actions need explicit tests.

The context should expose approved host adapters, plugin-scoped storage, settings registration, logging and cleanup registration. UI hooks must use verified React Native components. Theme imports should contain data, not JavaScript. Desktop CSS selectors, DOM nodes, Electron APIs and webpack module IDs are not valid Android integration contracts.

An initial plugin shortlist is appearance tokens, local interface preferences and a clearly scoped telemetry control. These are candidates, not working features. Review each Vencord-inspired feature for Android host access, licence obligations and core functionality regressions before accepting it.

Permissions are descriptive unless enforced at a genuine isolation boundary. Code running inside the Discord process can potentially access session data or block the JavaScript thread. This contract provides lifecycle discipline, not a secure sandbox. Native recovery must be designed before enabling externally supplied executable plugins.
