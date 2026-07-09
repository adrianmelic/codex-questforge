# OpenAI Platform Submission

This folder contains the public listing copy and the exact reviewer materials for the initial Questforge submission.

Build the upload archive from the repository root:

```powershell
python scripts\package_plugin.py
```

Upload `dist/questforge-skills-1.0.0.zip` as a **Skills only** plugin. Use `listing.md` for the Info, Prompts, Global, and Submit tabs, and `test-cases.md` for the required five positive and three negative tests.

Before selecting **Submit for Review**, confirm that the publisher identity is verified as Adrian Melic, the public GitHub Pages URLs are live, the archive hash matches the local build output, and every test has been rerun with the final archive.
