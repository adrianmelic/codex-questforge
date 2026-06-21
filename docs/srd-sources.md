# SRD Sources And License Notes

Verified on 2026-05-17.

Use SRD sources as the reusable rules base:

- Official SRD hub: https://www.dndbeyond.com/srd
- SRD 5.2.1 PDF: https://media.dndbeyond.com/compendium-images/srd/5.2/SRD_CC_v5.2.1.pdf
- Spanish SRD 5.2.1 PDF: https://media.dndbeyond.com/compendium-images/srd/5.2/SP_SRD_CC_v5.2.1.pdf
- CC-BY-4.0 license: https://creativecommons.org/licenses/by/4.0/
- Wizards Fan Content Policy: https://company.wizards.com/en/legal/fancontentpolicy

Operational rules for the plugin:

- Prefer SRD 5.2.1 for rules, classes, spells, monsters, and equipment.
- Download SRD PDFs into `.questforge/downloads/` or another local cache rather
  than committing them to the plugin repo.
- Generate structured Markdown resources under `.questforge/resources/srd/` so
  Codex can navigate rules by language and section without redistributing the
  raw PDF in git.
- Include attribution when storing campaign notes that derive from SRD content.
- Do not copy commercial manuals into the repo.
- Do not use official logos, cover art, character art, setting maps, or product
  identity in generated images or plugin assets.
- For private play, the user can bring their own table preferences, but the
  plugin should not redistribute or preserve non-SRD copyrighted text.
