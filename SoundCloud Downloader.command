#!/bin/bash
# SoundCloud Downloader - Double-clickable launcher for macOS
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:$PATH"

echo "=============================================="
echo "  Запуск SoundCloud MP3 Downloader..."
echo "=============================================="

# Check Python 3
if ! command -v python3 &>/dev/null; then
    osascript -e 'display alert "Ошибка" message "Python 3 не найден. Установите Python через Homebrew: brew install python"'
    exit 1
fi

# Check yt-dlp
if ! command -v yt-dlp &>/dev/null; then
    echo "yt-dlp не найден в стандартных путях, проверяю Homebrew..."
    if [ -f "/opt/homebrew/bin/yt-dlp" ]; then
        export PATH="/opt/homebrew/bin:$PATH"
    fi
fi

python3 "$DIR/app.py"
