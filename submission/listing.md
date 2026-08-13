# Questforge Listing

## Submission Type

Skills only.

## Public Info

- Plugin name: `Questforge`
- Developer identity: `Adrián Melic`
- Category: `Entertainment`
- Short description: `Open-ended fantasy RPG`
- Website: `https://adrianmelic.com/questforge`
- Support: `https://adrianmelic.com/en/#contact`
- Privacy policy: `https://adrianmelic.com/privacy-policy`
- Terms of service: `https://adrianmelic.com/terms-of-service`
- Repository: `https://github.com/adrianmelic/codex-questforge`
- Logo: `assets/icon.png` (512 px).
- Public product visuals: `assets/screenshots/questforge-scene-v2.png`, `assets/screenshots/questforge-tactical-map-v2.png`, and `assets/screenshots/questforge-360-pov-v2.png`. These are coherent generated examples from one original scene, not a simulated Codex conversation. They are for the public product page; the skills-only Platform submission does not configure screenshots.

## Long Description

Say anything and let the world keep up. Questforge turns a conversation into an original 5E-compatible fantasy campaign played inside Codex. Create or import a hero, attempt actions in natural language, and let the Game Master continue a world that remembers what changed. Questforge uses transparent rulings and dice, tracks character and campaign state, and supports combat, inventory, shops, advancement, checkpoints, and failure-forward play. Version 1.3 adds meaningful-turn local autosaves, portable ZIP exports, and opt-in cross-device synchronization through a writable storage connector and exact folder selected by the player. Static generated scenes can appear in the conversation. On writable local Codex workspaces, a chronological visual gallery, interactive 360 POV viewers, and optional original ambience extend the table without replacing the textual source of truth. Surfaces without a writable filesystem can use an authorized storage connector or fall back honestly to an in-conversation ledger.

## Starter Prompts

1. `I want to play. Create a quick hero and begin.`
2. `Guide me through creating a hero, then begin.`
3. `Continue my latest Questforge campaign.`

## Availability

Select all countries and regions where skills-only plugins are supported. Questforge is general-audience entertainment, does not sell goods or services, and does not operate a publisher-controlled data service. English and Spanish have bundled rules primers; other languages use the English rules index while preserving the user's conversation language.

## Release Notes

Questforge 1.3.0 lets players continue a campaign beyond one conversation or computer without delaying the opening scene with storage setup. A new seventh skill creates verified local snapshots after meaningful turns, compacts continuity at scene boundaries, exports canonical or media-inclusive ZIP files, migrates older campaigns conservatively, and can synchronize directly to one user-selected writable cloud folder through an installed storage connector. Schema-2 manifests add stable campaign IDs, SHA-256 file records, revision lineage, and an explicit session/scene resume point. Cloud writes verify permission, compare remote ancestry, update canonical files first, and write/read back `questforge.json` last; partial saves and conflicts are never reported as complete. Google Drive is the first end-to-end tested beta target. Questforge still operates no publisher-controlled campaign server and receives no copy of player saves.

## Reviewer Notes

- Questforge is unofficial and is not affiliated with or endorsed by OpenAI or Wizards of the Coast LLC.
- The default first run is offline and installs no packages. Complete SRD download requires explicit user consent; Questforge never installs `pypdf` or any other dependency.
- Local analytics are campaign files, not publisher telemetry.
- Static generated images appear once in the conversation when native image generation is available. Local galleries, audio, and 360 viewers are optional desktop enhancements.
- Cloud saves are optional and use a storage connector already installed by the player. Folder detection is only a hint; the player must select one exact target and authorize writes. Google Drive passed the 1.3.0 end-to-end acceptance on 2026-08-12 using disposable synthetic campaigns only.
- The canonical SaveSet synchronizes separately from optional large media. Each critical file and the final manifest require readback before a save is called complete.
- Repeat the final installed-plugin and claimed-provider acceptance gates described in `submission/release-playtest-report.md` before each future release; a silent `prompt-saved` opening is a failed release test.
- The plugin never needs credentials or sensitive personal data.
