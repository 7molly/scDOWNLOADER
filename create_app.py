#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generates a native macOS .app bundle for SoundCloud Downloader
"""

import os
import sys
import zlib
import struct
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_NAME = "SoundCloud Downloader.app"
APP_DIR = BASE_DIR / APP_NAME
CONTENTS_DIR = APP_DIR / "Contents"
MACOS_DIR = CONTENTS_DIR / "MacOS"
RESOURCES_DIR = CONTENTS_DIR / "Resources"


def create_png_icon(width: int, height: int, output_path: str):
    raw_data = bytearray()
    cx, cy = width / 2.0, height / 2.0
    r_max = width * 0.44

    for y in range(height):
        raw_data.append(0)  # Filter byte None
        for x in range(width):
            dx = (x - cx)
            dy = (y - cy)
            dist = (dx * dx + dy * dy) ** 0.5

            if dist <= r_max:
                factor = min(1.0, max(0.0, y / height))
                r = 255
                g = int(85 + factor * 50)
                b = int(10 + factor * 20)
                a = 255

                # Draw musical note inside
                h1 = ((x - (cx - width * 0.1)) ** 2 + (y - (cy + height * 0.12)) ** 2) ** 0.5
                h2 = ((x - (cx + width * 0.14)) ** 2 + (y - (cy + height * 0.06)) ** 2) ** 0.5
                stem1 = (abs(x - (cx - width * 0.04)) < width * 0.035 and (cy - height * 0.2) <= y <= (cy + height * 0.12))
                stem2 = (abs(x - (cx + width * 0.20)) < width * 0.035 and (cy - height * 0.25) <= y <= (cy + height * 0.06))
                beam = ((cx - width * 0.04) <= x <= (cx + width * 0.20) and abs(y - (cy - height * 0.22)) < height * 0.045)

                if h1 <= width * 0.085 or h2 <= width * 0.085 or stem1 or stem2 or beam:
                    r, g, b = 255, 255, 255
            elif dist <= r_max + 1.5:
                r, g, b = 255, 100, 25
                a = int(255 * (1.0 - (dist - r_max) / 1.5))
            else:
                r, g, b, a = 0, 0, 0, 0

            raw_data.extend([r, g, b, a])

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
    idat = chunk(b'IDAT', zlib.compress(bytes(raw_data)))
    iend = chunk(b'IEND', b'')
    with open(output_path, 'wb') as f:
        f.write(header + ihdr + idat + iend)


def build_icns(iconset_dir: Path, output_icns: Path):
    iconset_dir.mkdir(parents=True, exist_ok=True)
    sizes = [16, 32, 64, 128, 256, 512]
    for s in sizes:
        create_png_icon(s, s, str(iconset_dir / f"icon_{s}x{s}.png"))
        if s <= 256:
            create_png_icon(s * 2, s * 2, str(iconset_dir / f"icon_{s}x{s}@2x.png"))
    create_png_icon(1024, 1024, str(iconset_dir / "icon_512x512@2x.png"))

    subprocess.run(["iconutil", "-c", "icns", str(iconset_dir), "-o", str(output_icns)], check=True)
    shutil.rmtree(iconset_dir)


def create_app_bundle():
    print(f"📦 Создание {APP_NAME}...")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)

    MACOS_DIR.mkdir(parents=True, exist_ok=True)
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)

    # Generate ICNS
    temp_iconset = BASE_DIR / "temp.iconset"
    icns_path = RESOURCES_DIR / "AppIcon.icns"
    build_icns(temp_iconset, icns_path)

    # Info.plist
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.timur.soundclouddownloader</string>
    <key>CFBundleName</key>
    <string>SoundCloud Downloader</string>
    <key>CFBundleDisplayName</key>
    <string>SoundCloud Downloader</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
"""
    with open(CONTENTS_DIR / "Info.plist", "w", encoding="utf-8") as f:
        f.write(plist_content)

    # Launcher script
    launcher_content = """#!/bin/bash
DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:$PATH"
cd "$DIR"

# If server already running, just open browser
if curl -s http://127.0.0.1:5077/api/status > /dev/null 2>&1; then
    open "http://127.0.0.1:5077"
    exit 0
fi

# Run background server
nohup python3 "$DIR/app.py" > /tmp/scdown.log 2>&1 &
"""
    launcher_path = MACOS_DIR / "launcher"
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(launcher_content)

    # Make executable
    os.chmod(launcher_path, 0o755)

    print(f"✅ Успешно создано: {APP_DIR}")


if __name__ == "__main__":
    create_app_bundle()
