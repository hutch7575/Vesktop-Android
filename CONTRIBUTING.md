# Contributing

Start with the current roadmap and architecture. Describe a concrete problem and the expected behaviour before implementing a new host hook or changing the loader approach. Keep original APKs, extracted proprietary bundles and native libraries local.

Run `python3 -m unittest discover -s tests -v` from the repository root for tooling changes. Include meaningful malformed-input and split-set cases when changing inspection. Tests use generated fixtures and do not need Discord or an account. If a real APK drives a finding, publish its metadata and hashes rather than its contents.

Performance changes need before/after measurements under the QA protocol. A feature remains planned until it runs on the declared Android build/device and passes the core regression matrix. Update the roadmap with evidence and known limitations.

Do not add external implementation code until the repository licence is selected and that component's licence and notices are reviewed. Identify upstream work accurately; this project is independent of Discord, Vesktop and Vencord.
