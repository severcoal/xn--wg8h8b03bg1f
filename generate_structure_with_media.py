#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Erzeugt eine klickbare Projektstruktur für GitHub-READMEs
und schreibt sie zwischen <!-- STRUCTURE:START --> und <!-- STRUCTURE:END -->.

Features:
- Verlinkt Ordner und Dateien (inkl. Bilder, Videos, Audio)
- Unterstützt Umlaute, Leerzeichen & Emojis in Dateinamen
- Steuerbare Tiefe, Dotfiles optional, zusätzliche Excludes
- Kann nur ausgeben (--no-readme) oder README automatisch aktualisieren
"""

from __future__ import annotations
import argparse
from pathlib import Path
import urllib.parse
import re
import sys
from typing import Iterable, List

# ========= Icons =========
FOLDER_ICON = "📁"
FILE_ICON   = "📄"
IMAGE_ICON  = "🖼️"
VIDEO_ICON  = "🎥"
AUDIO_ICON  = "🎵"
CODE_ICON   = "💻"
DOC_ICON    = "📝"
OTHER_ICON  = "📦"

# ========= Dateitypen =========
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}
CODE_EXTS  = {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".scss", ".json", ".yml", ".yaml", ".sh"}
DOC_EXTS   = {".md", ".txt", ".pdf", ".rst"}

# Standard-Excludes (können per --exclude ergänzt werden)
DEFAULT_EXCLUDES = {
    ".git", ".github", ".venv", "venv", "__pycache__", "node_modules",
    "dist", "build", ".idea", ".vscode"
}

def get_icon(p: Path) -> str:
    """Gibt das passende Emoji je nach Dateityp zurück."""
    if p.is_dir():
        return FOLDER_ICON
    ext = p.suffix.lower()
    if ext in IMAGE_EXTS:
        return IMAGE_ICON
    if ext in VIDEO_EXTS:
        return VIDEO_ICON
    if ext in AUDIO_EXTS:
        return AUDIO_ICON
    if ext in CODE_EXTS:
        return CODE_ICON
    if ext in DOC_EXTS:
        return DOC_ICON
    return OTHER_ICON

def natural_key(s: str):
    """Sortiert 'file2' vor 'file10'."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def is_excluded(rel_path: Path, excludes: set[str]) -> bool:
    parts = {part for part in rel_path.parts if part not in ("", ".", "/")}
    return any(part in excludes for part in parts)

def encode_relpath(p: Path) -> str:
    """URL-encoden, aber '/' unverändert lassen."""
    return urllib.parse.quote(p.as_posix(), safe="/")

def iter_entries(dir_path: Path, include_dotfiles: bool) -> List[Path]:
    try:
        items = list(dir_path.iterdir())
    except PermissionError:
        return []
    if not include_dotfiles:
        items = [x for x in items if not x.name.startswith(".")]
    # Ordner zuerst, danach Dateien; jeweils "natürlich" sortiert
    dirs  = sorted((x for x in items if x.is_dir()), key=lambda p: natural_key(p.name))
    files = sorted((x for x in items if x.is_file()), key=lambda p: natural_key(p.name))
    return dirs + files

def render_tree(root: Path,
                current: Path,
                depth: int,
                max_depth: int,
                excludes: set[str],
                include_dotfiles: bool) -> List[str]:
    if depth > max_depth:
        return []
    lines: List[str] = []
    for entry in iter_entries(current, include_dotfiles):
        rel = entry.relative_to(root)
        if is_excluded(rel, excludes):
            continue
        icon = get_icon(entry)
        link = f"./{encode_relpath(rel)}"
        indent = "  " * depth
        if entry.is_dir():
            lines.append(f"{indent}- {icon} [{entry.name}/]({link})")
            lines += render_tree(root, entry, depth + 1, max_depth, excludes, include_dotfiles)
        else:
            lines.append(f"{indent}- {icon} [{entry.name}]({link})")
    return lines

def build_markdown(root: Path,
                   max_depth: int,
                   excludes: Iterable[str],
                   include_dotfiles: bool) -> str:
    lines = ["## 📁 Projektstruktur", ""]
    lines += render_tree(root, root, 0, max_depth, set(excludes), include_dotfiles)
    return "\n".join(lines) + "\n"

def update_readme(readme_path: Path, new_block: str, start_marker: str, end_marker: str) -> str:
    start_tag = f"<!-- {start_marker} -->"
    end_tag   = f"<!-- {end_marker} -->"
    block = f"{start_tag}\n\n{new_block}\n{end_tag}\n"

    if not readme_path.exists():
        readme_path.write_text(block, encoding="utf-8")
        return "🆕 README neu erstellt."

    content = readme_path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(start_tag) + r".*?" + re.escape(end_tag), re.DOTALL)
    if pattern.search(content):
        updated = pattern.sub(block, content)
    else:
        # Wenn Marker fehlen, ans Ende anhängen
        updated = content.rstrip() + "\n\n" + block

    if updated != content:
        readme_path.write_text(updated, encoding="utf-8")
        return "✅ README aktualisiert."
    return "ℹ️ Keine Änderungen nötig."

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Erzeuge klickbare Projektstruktur (inkl. Bilder, Videos & Audio).")
    ap.add_argument("--root", default=".", help="Projektwurzel (Default: .)")
    ap.add_argument("--max-depth", type=int, default=3, help="Ordner-Tiefe (Default: 3)")
    ap.add_argument("--exclude", action="append", default=[], help="Zusätzliche Ordner-/Dateinamen ausschließen (mehrfach nutzbar)")
    ap.add_argument("--include-dotfiles", action="store_true", help="Auch .dateien/ordner aufnehmen")
    ap.add_argument("--readme", default="README.md", help="Pfad zur README (Default: README.md)")
    ap.add_argument("--start-marker", default="STRUCTURE:START", help="Start-Marker ohne Kommentar-Klammern")
    ap.add_argument("--end-marker", default="STRUCTURE:END", help="End-Marker ohne Kommentar-Klammern")
    ap.add_argument("--no-readme", action="store_true", help="Nur Markdown auf STDOUT ausgeben, README nicht ändern")
    return ap.parse_args()

def main():
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"❌ Root nicht gefunden: {root}", file=sys.stderr)
        sys.exit(1)

    excludes = set(DEFAULT_EXCLUDES).union(args.exclude or [])
    md = build_markdown(root, args.max_depth, excludes, args.include_dotfiles)

    if args.no_readme:
        sys.stdout.write(md)
        return

    readme_path = (root / args.readme).resolve()
    msg = update_readme(readme_path, md, args.start_marker, args.end_marker)
    print(msg)

if __name__ == "__main__":
    main()