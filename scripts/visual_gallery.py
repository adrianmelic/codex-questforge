"""Generate a lightweight local Questforge visual gallery."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

try:
    from .campaign_memory import (
        VisualIndexEntry,
        get_campaign_paths,
        read_visual_index,
    )
    from .panorama_viewer import create_panorama_viewer, slugify
except ImportError:  # pragma: no cover - direct script execution path
    from campaign_memory import (
        VisualIndexEntry,
        get_campaign_paths,
        read_visual_index,
    )
    from panorama_viewer import create_panorama_viewer, slugify


IMAGE_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".webp"}
HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__TITLE_TEXT__</title>
  <style>
    :root {
      color-scheme: dark;
      --background: #11110f;
      --surface: #1b1c19;
      --surface-strong: #242720;
      --border: #3a3d35;
      --text: #f1eee5;
      --muted: #aaa79b;
      --accent: #d79b58;
      --accent-cool: #80aeb4;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--background);
      color: var(--text);
      font-family:
        Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
    }

    a {
      color: inherit;
    }

    .topbar {
      align-items: center;
      background: rgba(17, 17, 15, 0.94);
      border-bottom: 1px solid var(--border);
      display: flex;
      gap: 16px;
      justify-content: space-between;
      min-height: 72px;
      padding: 14px clamp(16px, 4vw, 40px);
      position: sticky;
      top: 0;
      z-index: 10;
    }

    .eyebrow {
      color: var(--accent);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    h1,
    h2,
    p {
      margin: 0;
    }

    h1 {
      font-size: clamp(20px, 3vw, 34px);
      font-weight: 750;
      line-height: 1.08;
    }

    .count {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--muted);
      font-size: 13px;
      min-width: 84px;
      padding: 8px 10px;
      text-align: center;
      white-space: nowrap;
    }

    .top-actions {
      align-items: center;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
    }

    .top-link {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      font-size: 13px;
      font-weight: 650;
      min-height: 36px;
      padding: 8px 11px;
      text-decoration: none;
    }

    .top-link.primary {
      border-color: rgba(215, 155, 88, 0.72);
      color: var(--accent);
    }

    .shell {
      display: grid;
      gap: 20px;
      margin: 0 auto;
      max-width: 1240px;
      padding: 18px clamp(16px, 4vw, 40px) 28px;
    }

    .timeline {
      display: grid;
      gap: 0;
    }

    .entry {
      border-bottom: 1px solid var(--border);
      display: grid;
      gap: 8px;
      padding: 20px 0;
      scroll-margin-top: 92px;
    }

    .entry:first-child {
      padding-top: 0;
    }

    .entry-frame {
      align-items: center;
      aspect-ratio: 16 / 9;
      background:
        linear-gradient(135deg, rgba(128, 174, 180, 0.12), transparent),
        #060606;
      border: 1px solid var(--border);
      border-radius: 8px;
      display: flex;
      justify-content: center;
      min-height: 280px;
      overflow: hidden;
    }

    .entry-frame img {
      display: block;
      height: 100%;
      object-fit: contain;
      width: 100%;
    }

    .entry-frame iframe {
      border: 0;
      display: block;
      height: 100%;
      width: 100%;
    }

    .entry-frame.panorama {
      min-height: 520px;
    }

    .entry-caption {
      align-items: center;
      display: flex;
      gap: 12px;
      justify-content: space-between;
      min-width: 0;
      padding: 4px 2px 10px;
    }

    .caption-main {
      color: var(--muted);
      font-size: 14px;
      font-weight: 650;
      line-height: 1.35;
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .caption-index {
      color: var(--accent);
      font-weight: 760;
    }

    .caption-kind {
      color: var(--accent-cool);
      font-weight: 760;
      text-transform: uppercase;
    }

    .caption-label {
      color: var(--text);
    }

    .caption-link {
      background: var(--surface-strong);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--accent);
      flex: 0 0 auto;
      font-size: 12px;
      font-weight: 650;
      padding: 5px 8px;
      text-decoration: none;
    }

    .empty {
      align-items: center;
      border: 1px dashed var(--border);
      border-radius: 8px;
      color: var(--muted);
      display: none;
      min-height: 280px;
      padding: 28px;
    }

    @media (max-width: 900px) {
      .entry-frame {
        min-height: 220px;
      }

      .entry-frame.panorama {
        min-height: 360px;
      }
    }

    @media (max-width: 560px) {
      .topbar {
        align-items: flex-start;
        flex-direction: column;
      }

      .top-actions {
        justify-content: flex-start;
      }

      .count {
        text-align: left;
      }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div>
      <div class="eyebrow">Codex Questforge</div>
      <h1>__TITLE_TEXT__</h1>
    </div>
    <nav class="top-actions" aria-label="Gallery navigation">
      <a class="top-link" href="#visual-1">Start</a>
      <a class="top-link primary" href="#latest" id="latest-action">Latest</a>
      <div class="count" id="count">0 images</div>
    </nav>
  </header>

  <main class="shell">
    <section class="empty" id="empty">
      No registered images yet.
    </section>
    <section class="timeline" id="timeline" aria-label="Image history"></section>
  </main>

  <script>
    const ITEMS = __ITEMS_JSON__;
    const GALLERY_VERSION = __GALLERY_VERSION_JSON__;
    const AUTO_REFRESH_MS = __AUTO_REFRESH_MS_JSON__;

    const empty = document.getElementById("empty");
    const count = document.getElementById("count");
    const timeline = document.getElementById("timeline");
    const latestAction = document.getElementById("latest-action");

    function createCaptionPart(className, text) {
      const part = document.createElement("span");
      part.className = className;
      part.textContent = text;
      return part;
    }

    function appendSeparator(container) {
      container.append(document.createTextNode(" \\u00b7 "));
    }

    function createCaptionLink(label, url) {
      if (!url) {
        return null;
      }
      const link = document.createElement("a");
      link.className = "caption-link";
      link.href = url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = label;
      return link;
    }

    function createEntry(item, index) {
      const article = document.createElement("article");
      article.className = "entry";
      article.id = `visual-${index + 1}`;
      if (index === ITEMS.length - 1) {
        article.dataset.latest = "true";
      }

      const frame = document.createElement("div");
      frame.className = "entry-frame";
      if (item.viewerUrl) {
        frame.classList.add("panorama");
        const viewer = document.createElement("iframe");
        viewer.src = item.viewerUrl;
        viewer.title = `${item.label} 360 viewer`;
        viewer.loading = index > 2 ? "lazy" : "eager";
        viewer.allow = "autoplay";
        frame.append(viewer);
      } else {
        const image = document.createElement("img");
        image.src = item.assetUrl;
        image.alt = item.label;
        image.loading = index > 2 ? "lazy" : "eager";
        frame.append(image);
      }

      const caption = document.createElement("div");
      caption.className = "entry-caption";
      const summary = document.createElement("div");
      summary.className = "caption-main";
      const summaryText = `#${index + 1} \\u00b7 ${item.kind} \\u00b7 ${item.label}`;
      summary.title = summaryText;
      summary.append(createCaptionPart("caption-index", `#${index + 1}`));
      appendSeparator(summary);
      summary.append(createCaptionPart("caption-kind", item.kind));
      appendSeparator(summary);
      summary.append(createCaptionPart("caption-label", item.label));
      caption.append(summary);

      const viewerLink = createCaptionLink("Open 360", item.viewerUrl);
      if (viewerLink) {
        caption.append(viewerLink);
      }

      article.append(frame, caption);
      return article;
    }

    function scrollToHash() {
      if (!ITEMS.length) {
        return;
      }
      let target = null;
      if (isFollowingLatest()) {
        target = timeline.querySelector("[data-latest='true']");
      } else if (/^#visual-\\d+$/.test(window.location.hash)) {
        target = document.querySelector(window.location.hash);
      }
      if (target) {
        target.scrollIntoView({ block: "start" });
      }
    }

    function isFollowingLatest() {
      return window.location.hash === "" || window.location.hash === "#latest";
    }

    function currentDocumentUrl() {
      const url = new URL(window.location.href);
      url.hash = "";
      url.searchParams.set("questforgeGalleryCheck", String(Date.now()));
      return url.href;
    }

    let failedRefreshChecks = 0;

    async function checkForGalleryUpdate() {
      if (!isFollowingLatest() || document.hidden) {
        return;
      }
      try {
        const response = await fetch(currentDocumentUrl(), {
          cache: "no-store",
        });
        if (!response.ok) {
          return;
        }
        const html = await response.text();
        const match = html.match(/const GALLERY_VERSION = "([^"]+)";/);
        if (match && match[1] !== GALLERY_VERSION) {
          window.location.reload();
        }
        failedRefreshChecks = 0;
      } catch (error) {
        failedRefreshChecks += 1;
        if (failedRefreshChecks >= 2) {
          window.location.reload();
        }
      }
    }

    function render() {
      count.textContent = `${ITEMS.length} image${ITEMS.length === 1 ? "" : "s"}`;
      if (!ITEMS.length) {
        empty.style.display = "flex";
        timeline.style.display = "none";
        latestAction.classList.add("hidden");
        return;
      }
      empty.style.display = "none";
      ITEMS.forEach((item, index) => {
        timeline.append(createEntry(item, index));
      });
      requestAnimationFrame(scrollToHash);
    }

    window.addEventListener("hashchange", scrollToHash);
    document.addEventListener("visibilitychange", checkForGalleryUpdate);
    window.setInterval(checkForGalleryUpdate, AUTO_REFRESH_MS);
    render();
  </script>
</body>
</html>
"""


@dataclass(frozen=True)
class GalleryItem:
    """One visual asset rendered by the local gallery."""

    kind: str
    label: str
    session_number: int
    scene_number: int
    status: str
    asset_path: str
    asset_url: str
    prompt_path: str
    prompt_url: str
    viewer_path: str
    viewer_url: str
    source_anchors: str
    continuity_tags: str
    review_notes: str


@dataclass(frozen=True)
class VisualGalleryResult:
    """Created visual gallery artifact."""

    gallery_path: str
    gallery_url: str
    campaign_root: str
    title: str
    item_count: int
    skipped_missing_assets: int


def create_visual_gallery(
    campaign_root: Path,
    output_path: Path | None = None,
    title: str = "",
    include_rejected: bool = False,
    viewer_roots: list[Path] | None = None,
) -> VisualGalleryResult:
    """Create or refresh the standalone local gallery for a campaign."""

    campaign_root = campaign_root.expanduser().resolve()
    paths = get_campaign_paths(campaign_root)
    if not paths.root.exists():
        raise FileNotFoundError(f"Missing campaign root: {paths.root}")
    if not paths.visual_index.exists():
        raise FileNotFoundError(f"Missing visual index: {paths.visual_index}")

    if output_path is None:
        output_path = paths.root / "images" / "visual-gallery.html"
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    items, skipped_missing_assets = build_gallery_items(
        campaign_root=paths.root,
        output_dir=output_path.parent,
        include_rejected=include_rejected,
        viewer_roots=viewer_roots,
    )
    gallery_title = title.strip() or f"{paths.root.name} visual gallery"
    html = render_gallery_html(gallery_title, items)
    output_path.write_text(html, encoding="utf-8", newline="\n")

    return VisualGalleryResult(
        gallery_path=str(output_path),
        gallery_url=f"{output_path.as_uri()}#latest",
        campaign_root=str(paths.root),
        title=gallery_title,
        item_count=len(items),
        skipped_missing_assets=skipped_missing_assets,
    )


def build_gallery_items(
    campaign_root: Path,
    output_dir: Path,
    include_rejected: bool = False,
    viewer_roots: list[Path] | None = None,
) -> tuple[list[GalleryItem], int]:
    paths = get_campaign_paths(campaign_root)
    resolved_viewer_roots = resolve_viewer_roots(campaign_root, viewer_roots)
    entries = sorted(
        read_visual_index(paths.visual_index),
        key=lambda entry: (
            entry.session_number,
            entry.scene_number,
            entry.prompt_path,
            entry.label,
        ),
    )

    items: list[GalleryItem] = []
    skipped_missing_assets = 0
    for entry in entries:
        if not entry.asset_path:
            continue
        if entry.status == "rejected" and not include_rejected:
            continue
        asset_path = resolve_index_path(campaign_root, entry.asset_path)
        if not asset_path.exists() or not asset_path.is_file():
            skipped_missing_assets += 1
            continue
        if asset_path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        prompt_path = resolve_index_path(campaign_root, entry.prompt_path)
        viewer_path = find_panorama_viewer(
            resolved_viewer_roots,
            entry,
            asset_path,
        )
        if viewer_path is None and looks_like_panorama(entry, asset_path):
            viewer_path = create_default_panorama_viewer(
                paths.root,
                entry,
                asset_path,
            )
        items.append(
            GalleryItem(
                kind=entry.kind,
                label=entry.label,
                session_number=entry.session_number,
                scene_number=entry.scene_number,
                status=entry.status,
                asset_path=relative_or_file_url(asset_path, output_dir),
                asset_url=relative_or_file_url(asset_path, output_dir),
                prompt_path=(
                    relative_or_file_url(prompt_path, output_dir)
                    if prompt_path.exists()
                    else ""
                ),
                prompt_url=(
                    relative_or_file_url(prompt_path, output_dir)
                    if prompt_path.exists()
                    else ""
                ),
                viewer_path=(
                    relative_or_file_url(viewer_path, output_dir)
                    if viewer_path
                    else ""
                ),
                viewer_url=(
                    relative_or_file_url(viewer_path, output_dir)
                    if viewer_path
                    else ""
                ),
                source_anchors=entry.source_anchors,
                continuity_tags=entry.continuity_tags,
                review_notes=entry.review_notes,
            )
        )
    return items, skipped_missing_assets


def create_default_panorama_viewer(
    campaign_root: Path,
    entry: VisualIndexEntry,
    asset_path: Path,
) -> Path:
    """Create a default local viewer for a panorama-like visual asset."""

    output_path = (
        campaign_root
        / "images"
        / "viewers"
        / f"{slugify(entry.label)}-360.html"
    )
    create_panorama_viewer(
        image_path=asset_path,
        output_path=output_path,
        title=entry.label,
        narration=entry.label,
        initial_zoom_level=14,
    )
    return output_path.resolve()


def resolve_viewer_roots(
    campaign_root: Path,
    viewer_roots: list[Path] | None = None,
) -> list[Path]:
    roots = [campaign_root.resolve()]
    for viewer_root in viewer_roots or []:
        candidate = viewer_root.expanduser()
        if not candidate.is_absolute():
            candidate = campaign_root / candidate
        if candidate.exists():
            roots.append(candidate.resolve())
    return roots


def resolve_index_path(campaign_root: Path, index_path: str) -> Path:
    candidate = Path(index_path)
    if candidate.is_absolute():
        return candidate.resolve()
    return (campaign_root / index_path).resolve()


def find_panorama_viewer(
    search_roots: list[Path],
    entry: VisualIndexEntry,
    asset_path: Path,
) -> Path | None:
    """Find a matching local 360 viewer for a panorama asset, if one exists."""

    target_slugs = {
        slug_for_match(entry.label),
        slug_for_match(asset_path.stem),
    }
    candidates: list[tuple[int, Path]] = []
    for search_root in search_roots:
        for viewer_path in search_root.rglob("*.html"):
            viewer_slug = slug_for_match(viewer_path.stem)
            if "visual-gallery" in viewer_slug:
                continue
            if not any(
                marker in viewer_slug
                for marker in ("360", "panorama", "viewer")
            ):
                continue
            score = best_viewer_score(viewer_slug, target_slugs)
            if score:
                candidates.append((score, viewer_path.resolve()))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], str(item[1]).casefold()))
    return candidates[0][1]


def looks_like_panorama(entry: VisualIndexEntry, asset_path: Path) -> bool:
    marker_text = slug_for_match(
        f"{entry.kind} {entry.label} {asset_path.stem}"
    )
    return any(
        marker in marker_text
        for marker in ("pov-360", "360", "panorama", "panoramico")
    )


def slug_for_match(value: str) -> str:
    return "".join(
        character.lower() if character.isalnum() else "-"
        for character in value
    ).strip("-")


def best_viewer_score(viewer_slug: str, target_slugs: set[str]) -> int:
    score = 0
    for target_slug in target_slugs:
        if not target_slug:
            continue
        if target_slug in viewer_slug:
            score = max(score, len(target_slug))
    return score


def relative_or_file_url(path: Path, base_dir: Path) -> str:
    try:
        relative_path = Path(os.path.relpath(path, base_dir))
    except ValueError:
        return path.as_uri()
    return relative_path.as_posix()


def render_gallery_html(title: str, items: list[GalleryItem]) -> str:
    items_payload = [
        {
            "kind": item.kind,
            "label": item.label,
            "sessionNumber": item.session_number,
            "sceneNumber": item.scene_number,
            "status": item.status,
            "assetPath": item.asset_path,
            "assetUrl": item.asset_url,
            "promptPath": item.prompt_path,
            "promptUrl": item.prompt_url,
            "viewerPath": item.viewer_path,
            "viewerUrl": item.viewer_url,
            "sourceAnchors": item.source_anchors,
            "continuityTags": item.continuity_tags,
            "reviewNotes": item.review_notes,
        }
        for item in items
    ]
    return (
        HTML_TEMPLATE.replace("__TITLE_TEXT__", escape_html_text(title))
        .replace("__ITEMS_JSON__", safe_json_script(items_payload))
        .replace(
            "__GALLERY_VERSION_JSON__",
            json.dumps(create_gallery_version(items_payload)),
        )
        .replace("__AUTO_REFRESH_MS_JSON__", json.dumps(8000))
    )


def create_gallery_version(payload: object) -> str:
    version_source = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(version_source).hexdigest()[:16]


def safe_json_script(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")


def escape_html_text(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or refresh a local Questforge visual gallery."
    )
    parser.add_argument("--campaign-root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--title", default="")
    parser.add_argument("--include-rejected", action="store_true")
    parser.add_argument(
        "--viewer-root",
        action="append",
        default=[],
        type=Path,
        help=(
            "Optional extra folder to scan for matching 360 viewer HTML "
            "files. Relative paths are resolved from the campaign root."
        ),
    )
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    result = create_visual_gallery(
        campaign_root=parsed_arguments.campaign_root,
        output_path=parsed_arguments.output,
        title=parsed_arguments.title,
        include_rejected=parsed_arguments.include_rejected,
        viewer_roots=parsed_arguments.viewer_root,
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
