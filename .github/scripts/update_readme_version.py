#!/usr/bin/env python3
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print("Usage: update_readme_version.py <tag>", file=sys.stderr)
    sys.exit(2)

tag = sys.argv[1].strip()  # expected like v1.2.0 or 1.2.0
if not tag:
    print("Tag is empty", file=sys.stderr)
    sys.exit(2)

# Normalize: ensure tag has single leading 'v'
tag = "v" + tag.lstrip("v")
version = tag.lstrip("v")  # version without leading 'v' for filenames

readme_path = Path("README.md")
content = readme_path.read_text(encoding="utf-8")

# Update URLs to the latest tag and filenames to exactly 'mydylms-client-v<version>-...'
# Windows
win_pattern = re.compile(
    r"(releases/download/)[^/]+(/mydylms-client-)v+[^/]+(-win-x64\.exe)"
)


def win_repl(m: re.Match) -> str:
    return f"{m.group(1)}{tag}{m.group(2)}v{version}{m.group(3)}"


# Linux (download or tag)
linux_pattern = re.compile(
    r"(releases/(?:download|tag)/)[^/]+(/mydylms-client-)v+[^/]+(-linux-x86__64(?:\.tar\.gz)?)"
)


def linux_repl(m: re.Match) -> str:
    return f"{m.group(1)}{tag}{m.group(2)}v{version}{m.group(3)}"


# macOS
mac_pattern = re.compile(
    r"(releases/download/)[^/]+(/mydylms-client-)v+[^/]+(-macos-arm64(?:\.zip)?)"
)


def mac_repl(m: re.Match) -> str:
    return f"{m.group(1)}{tag}{m.group(2)}v{version}{m.group(3)}"


updated = content
updated = win_pattern.sub(win_repl, updated)
updated = linux_pattern.sub(linux_repl, updated)
updated = mac_pattern.sub(mac_repl, updated)

if updated != content:
    readme_path.write_text(updated, encoding="utf-8")
    print(f"README.md updated to {tag}")
else:
    print("README.md already up-to-date")
