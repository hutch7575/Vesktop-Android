# Security reporting

Do not post account tokens, private messages, signing keys or full device logs in public issues. For a vulnerability involving executable plugins, update integrity or credential exposure, use GitHub's private vulnerability reporting if it is enabled. If it is unavailable, request a private reporting channel without disclosing exploit details publicly.

The current tools inspect local APK metadata only. They do not verify APK signatures or establish whether an APK is trustworthy. A SHA-256 match identifies bytes; it does not prove their origin or safety.

This project is a research foundation with no supported client releases. Future in-process plugins will not be secure sandboxes merely because their manifests declare permissions or their startup handlers catch errors.
