# Foundation validation — 22 November 2026

Validated locally on Linux with Python `3.12.14`.

| Check | Result |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | 34 tests passed |
| Binary manifest fixtures | UTF-8/UTF-16, long lengths, typed values and malformed bounds covered |
| APK/set fixtures | Split requirements, identity mismatches, unsafe names, duplicate entries, bad CRC and profile mismatches covered |
| Input immutability | Tests confirm inspection leaves input bytes unchanged |
| Supplied Discord base | SHA-256, version and Hermes header match the recorded research profile |
| Complete-set preflight | Correctly returns exit code `2` for the supplied base alone |
| Python compile check | Passed |
| Tracked-source artefact guard | Passed; proprietary inputs and signing material excluded |
| Git whitespace check | Passed |
| GitHub workflow | Configured to run the fixture suite and source guard on push/PR; consult Actions for remote results |
| PowerShell export on a phone | Not run; physical device and Windows/PowerShell validation still required |
| APK signature verification | Not run |
| Android loader/build/install/device tests | Not run; no loader or patch engine implemented |
| Performance measurements | Not run; no improvement claimed |

Tests use generated data, not Discord implementation code. The source guard blocks common binary/signing extensions; it is an additional check rather than a comprehensive provenance or secret scanner.
