#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import urllib.parse
from pathlib import Path

# Emojis für verschiedene Typen
FOLDER_ICON = "📁"
FILE_ICON = "📄"
IMAGE_ICON = "🖼️"
CODE_ICON = "💻"
DOC_ICON = "📝"
OTHER_ICON = "📦"

# Dateiendungen für Typen
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
CODE_EXTS = {".py", ".js", ".ts", ".html", ".css", ".json"}
DOC_EXTS = {".md", ".txt", ".pdf"}

def get_icon(path: Path) -> str:
    if path.is_dir():
        return FOLDER_ICON
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return IMAGE_ICON
    if ext in CODE_EXTS:
        return CODE_ICON
    if ext in DOC_EXTS:
        return DOC_ICON
    return OTHER_ICON

def generate_tree(root: Path, depth=0, max_depth=3):
    if depth > max_depth:
        return []
    entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    lines = []
    for entry in entries:
        if entry.name.startswith("."):  # Versteckte Dateien ignorieren
            continue
        rel_path = entry.relative_to(start_dir)
        encoded = urllib.parse.quote(str(rel_path))
        icon = get_icon(entry)
        indent = "  " * depth
        if entry.is_dir():
            lines.append(f"{indent}- {icon} [{entry.name}/](./{encoded})")
            lines.extend(generate_tree(entry, depth + 1, max_depth))
        else:
            lines.append(f"{indent}- {icon} [{entry.name}](./{encoded})")
    return lines

# Einstellungen
start_dir = Path(".").resolve()
max_depth = 3  # Wie tief soll verschachtelt werden?
output_file = "README.md"
start_marker = "<!-- STRUCTURE:START -->"
end_marker = "<!-- STRUCTURE:END -->"

# Struktur erzeugen
tree_lines = ["## 📁 Projektstruktur", ""]
tree_lines += generate_tree(start_dir, 0, max_depth)
tree_md = "\n".join(tree_lines)

# README aktualisieren oder neu anlegen
readme = Path(output_file)
if readme.exists():
    text = readme.read_text(encoding="utf-8")
    import re
    import sys
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
    new_block = f"{start_marker}\n\n{tree_md}\n\n{end_marker}"
    if pattern.search(text):
        new_text = pattern.sub(new_block, text)
    else:
        new_text = text + "\n\n" + new_block
    if new_text != text:
        readme.write_text(new_text, encoding="utf-8")
        print("✅ README aktualisiert!")
    else:
        print("ℹ️ Keine Änderungen nötig.")
else:
    readme.write_text(f"{start_marker}\n\n{tree_md}\n\n{end_marker}\n", encoding="utf-8")
    print("🆕 README neu erstellt!")