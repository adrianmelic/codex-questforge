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

Say anything and let the world keep up. Questforge turns a conversation into an original 5E-compatible fantasy campaign played inside Codex. Create or import a hero, attempt actions in natural language, and let the Game Master continue a world that remembers what changed. Questforge uses transparent rulings and dice, tracks character and campaign state, and supports combat, inventory, shops, advancement, checkpoints, and failure-forward play. Static generated scenes can appear in the conversation. On writable local Codex workspaces, a chronological visual gallery, interactive 360 POV viewers, and optional original ambience extend the table without replacing the textual source of truth. Other supported surfaces use a compact conversation ledger and never claim local files were created.

## Starter Prompts

1. `I want to play. Create a quick hero and begin.`
2. `Guide me through creating a hero, then begin.`
3. `Continue my latest Questforge campaign.`

## Availability

Select all countries and regions where skills-only plugins are supported. Questforge is general-audience entertainment, does not sell goods or services, and does not operate a publisher-controlled data service. English and Spanish have bundled rules primers; other languages use the English rules index while preserving the user's conversation language.

## Release Notes

Questforge 1.2.0 adds a redesigned book-and-anvil icon, a local visual-table flow that can remain open beside the conversation and follow new assets, and a substantially improved panorama viewer with natural drag direction, inertial movement, smooth zoom, and keyboard controls. Scene-appropriate approved ambience can be attached when a viewer is first created, remains muted for a new player, and is enabled only through a voluntary speaker control. The release retains six scoped skills, offline English/Spanish rules primers, optional full SRD 5.2.1 indexing, persistent campaign and mechanical state, transparent dice and failure-forward adjudication, native visual planning, chat-only fallbacks, and deterministic validation. No authentication or publisher-controlled server is required.

## Reviewer Notes

- Questforge is unofficial and is not affiliated with or endorsed by OpenAI or Wizards of the Coast LLC.
- The default first run is offline and installs no packages. Complete SRD download requires explicit user consent; Questforge never installs `pypdf` or any other dependency.
- Local analytics are campaign files, not publisher telemetry.
- Static generated images appear once in the conversation when native image generation is available. Local galleries, audio, and 360 viewers are optional desktop enhancements.
- Before any future submission, run the final installed-plugin acceptance gate described in `submission/release-playtest-report.md`; a silent `prompt-saved` opening is a failed release test.
- The plugin never needs credentials or sensitive personal data.
