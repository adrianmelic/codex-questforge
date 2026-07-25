# OpenAI Platform Publication

This folder preserves the public listing copy, reviewer notes, test cases, and release evidence for Questforge. Version 1.2.0 is published in the ChatGPT Plugins directory.

For a future release, build the upload archive from the repository root:

```powershell
python scripts\package_plugin.py
```

Upload the versioned archive printed by `package_plugin.py` as a **Skills only** plugin. Use `listing.md` for the public metadata, `test-cases.md` for the required positive and negative tests, and `release-playtest-report.md` for conversational and publication evidence.

Before submitting another version, confirm that the publisher identity is verified as Adrián Melic, the canonical product and legal URLs are live, the compatibility GitHub Pages URLs still work if the current Platform version references them, the archive hash matches the local build output, and every test has been rerun with the final archive. Platform publication, GitHub synchronization, tagging, and GitHub release creation are separate explicit gates.
