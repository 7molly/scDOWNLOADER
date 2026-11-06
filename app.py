#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SoundCloud & YouTube / TikTok Downloader
Cross-platform Desktop & Cloud Web Application (Docker / Render / Railway / Local)
Optimized for Mobile Devices & Long Videos (up to 2 hours)
"""

import os
import sys
import re
import json
import time
import uuid
import queue
import shutil
import signal
import zipfile
import urllib.parse
import urllib.request
import subprocess
import threading
import webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Detect Environment
IS_MAC = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")
IS_CLOUD = bool(os.environ.get("CLOUD_MODE") or os.environ.get("RENDER") or os.environ.get("RAILWAY_STATIC_URL") or os.environ.get("DYNO"))

MAX_VIDEO_DURATION_SECONDS = 7200  # 2 hours limit

def get_os_type() -> str:
    if IS_CLOUD:
        return "cloud"
    if IS_MAC:
        return "macos"
    elif IS_WINDOWS:
        return "windows"
    return "linux"

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
CONFIG_FILE = BASE_DIR / "config.json"
HISTORY_FILE = BASE_DIR / "history.json"
STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", str(BASE_DIR / "downloads_cache")))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Setup PATH for macOS Homebrew
if IS_MAC:
    SYSTEM_PATHS = [
        "/opt/homebrew/bin",
        "/opt/homebrew/sbin",
        "/usr/local/bin",
        str(Path.home() / ".local/bin"),
        "/usr/bin",
        "/bin"
    ]
    for p in reversed(SYSTEM_PATHS):
        if p not in os.environ.get("PATH", ""):
            os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")


def get_default_paths():
    home = Path.home()
    return str(home / "Music" / "SoundCloud"), str(home / "Downloads")


DEFAULT_MUSIC_DIR, DEFAULT_DL_DIR = get_default_paths()

DEFAULT_CONFIG = {
    "album_base_dir": DEFAULT_MUSIC_DIR,
    "single_tracks_dir": DEFAULT_DL_DIR,
    "video_dir": DEFAULT_DL_DIR,
    "audio_dir": DEFAULT_DL_DIR,
    "default_video_quality": "best",
    "number_tracks": True,
    "auto_open_folder": True,
    "show_notifications": True,
    "port": int(os.environ.get("PORT", 5077))
}


def find_binary(name: str) -> str:
    """Find CLI tools (yt-dlp, ffmpeg) on macOS, Windows, or Linux/Docker."""
    if IS_WINDOWS:
        for ext in [".exe", ".bat", ".cmd", ""]:
            local_bin = BASE_DIR / (name + ext)
            if local_bin.is_file():
                return str(local_bin)

    found = shutil.which(name)
    if found:
        return found

    for prefix in ["/usr/local/bin", "/usr/bin", "/opt/homebrew/bin"]:
        p = Path(prefix) / name
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)

    return name


YT_DLP_BIN = find_binary("yt-dlp")
FFMPEG_BIN = find_binary("ffmpeg")


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', " ", name)
    cleaned = re.sub(r'\s+', " ", cleaned).strip()
    return cleaned or "Media"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                cfg = DEFAULT_CONFIG.copy()
                cfg.update(data)
                return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def add_history_item(item: dict):
    hist = load_history()
    hist.insert(0, item)
    hist = hist[:70]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)


def send_system_notification(title: str, message: str):
    if IS_CLOUD:
        return
    try:
        if IS_MAC:
            title_esc = title.replace('"', '\\"')
            msg_esc = message.replace('"', '\\"')
            script = f'display notification "{msg_esc}" with title "{title_esc}" sound name "Glass"'
            subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif IS_WINDOWS:
            title_esc = title.replace('"', '`"')
            msg_esc = message.replace('"', '`"')
            ps_script = f'''
            [reflection.assembly]::loadwithpartialname("System.Windows.Forms") | Out-Null
            $notify = new-object system.windows.forms.notifyicon
            $notify.icon = [system.drawing.systemicons]::Information
            $notify.visible = $true
            $notify.showballoontip(4000, "{title_esc}", "{msg_esc}", [system.windows.forms.tooltipicon]::Info)
            '''
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def open_in_file_manager(target_path: str):
    if IS_CLOUD:
        return
    try:
        p = Path(os.path.expanduser(target_path))
        if not p.exists():
            return
        if IS_MAC:
            subprocess.run(["open", str(p)], check=False)
        elif IS_WINDOWS:
            if hasattr(os, "startfile"):
                os.startfile(str(p))
            else:
                subprocess.run(["explorer", str(p)], check=False)
        else:
            subprocess.run(["xdg-open", str(p)], check=False)
    except Exception:
        pass


def pick_folder_dialog(prompt="Выберите папку для сохранения") -> str:
    if IS_CLOUD:
        return ""
    if IS_MAC:
        script = f'''
        tell application "System Events"
            activate
            set chosen to POSIX path of (choose folder with prompt "{prompt}")
            return chosen
        end tell
        '''
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip().rstrip("/")
        return ""

    elif IS_WINDOWS:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            folder = filedialog.askdirectory(title=prompt)
            root.destroy()
            if folder:
                return os.path.normpath(folder)
        except Exception:
            pass

        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = "{prompt}"
        if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {{
            Write-Output $dialog.SelectedPath
        }}
        '''
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip()
        return ""

    return ""


def detect_platform(url: str) -> str:
    u = url.lower()
    if "soundcloud.com" in u:
        return "soundcloud"
    elif "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    elif "tiktok.com" in u:
        return "tiktok"
    elif "instagram.com" in u:
        return "instagram"
    elif "vk.com" in u:
        return "vk"
    return "media"


def cleanup_storage_daemon():
    """Background worker that purges downloaded temp files older than 45 minutes."""
    while True:
        try:
            now = time.time()
            for p in STORAGE_DIR.iterdir():
                if p.is_dir() and (now - p.stat().st_mtime > 45 * 60):
                    shutil.rmtree(p, ignore_errors=True)
        except Exception:
            pass
        time.sleep(300)


threading.Thread(target=cleanup_storage_daemon, daemon=True).start()


class DownloadManager:
    """Manages active download subprocess and broadcasts events via SSE."""

    def __init__(self):
        self.lock = threading.Lock()
        self.active_process = None
        self.is_running = False
        self.current_job = None
        self.listeners = []

    def subscribe(self) -> queue.Queue:
        q = queue.Queue(maxsize=100)
        with self.lock:
            self.listeners.append(q)
        return q

    def unsubscribe(self, q: queue.Queue):
        with self.lock:
            if q in self.listeners:
                self.listeners.remove(q)

    def broadcast(self, event_type: str, data: dict):
        msg = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        with self.lock:
            dead = []
            for q in self.listeners:
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    dead.append(q)
            for d in dead:
                self.listeners.remove(d)

    def cancel(self) -> bool:
        with self.lock:
            if self.active_process and self.is_running:
                try:
                    self.active_process.terminate()
                    threading.Timer(2.0, self._force_kill, args=[self.active_process]).start()
                    self.broadcast("cancelled", {"message": "Загрузка отменена"})
                    self.is_running = False
                    return True
                except Exception:
                    return False
        return False

    def _force_kill(self, proc):
        try:
            if proc.poll() is None:
                proc.kill()
        except Exception:
            pass

    def start_download(self, job: dict):
        with self.lock:
            if self.is_running:
                raise RuntimeError("Другая загрузка уже выполняется")
            self.is_running = True
            self.current_job = job

        threading.Thread(target=self._run_download, args=[job], daemon=True).start()

    def _run_download(self, job: dict):
        url = job["url"]
        platform = job.get("platform") or detect_platform(url)
        mode = job.get("mode", "audio")
        is_album = bool(job.get("is_album", False)) and platform == "soundcloud"
        cfg = load_config()

        job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        job_dir = STORAGE_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        download_file_name = ""
        full_folder = ""

        # Common reliability flags
        reliability_flags = [
            "--socket-timeout", "30",
            "--retries", "10",
            "--fragment-retries", "10"
        ]

        # Cloud mode or Local mode target
        if platform == "soundcloud" and is_album:
            album_title = sanitize_filename(job.get("album_title") or "SoundCloud Album")
            album_folder = job_dir / album_title
            album_folder.mkdir(parents=True, exist_ok=True)
            full_folder = str(album_folder)

            if cfg.get("number_tracks", True):
                output_tpl = str(album_folder / "%(playlist_index)02d. %(uploader,artist)s - %(title)s.%(ext)s")
            else:
                output_tpl = str(album_folder / "%(uploader,artist)s - %(title)s.%(ext)s")

            cmd = [
                YT_DLP_BIN,
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--embed-thumbnail",
                "--embed-metadata",
                "--add-metadata",
                "--newline",
                "--no-mtime",
                "--windows-filenames",
                "--ffmpeg-location", FFMPEG_BIN,
                "--parse-metadata", "%(playlist_title,title)s:%(album)s",
                "-o", output_tpl,
            ] + reliability_flags + [url]

        elif mode == "video":
            full_folder = str(job_dir)
            output_tpl = str(job_dir / "%(title)s.%(ext)s")

            quality = job.get("quality", cfg.get("default_video_quality", "best"))
            if quality == "720":
                fmt = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]/best"
            elif quality == "480":
                fmt = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]/best"
            else:
                fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best"

            cmd = [
                YT_DLP_BIN,
                "-f", fmt,
                "--merge-output-format", "mp4",
                "--embed-thumbnail",
                "--embed-metadata",
                "--newline",
                "--no-mtime",
                "--windows-filenames",
                "--ffmpeg-location", FFMPEG_BIN,
                "-o", output_tpl,
            ] + reliability_flags

            if platform == "youtube":
                cmd += ["--geo-bypass", "--extractor-args", "youtube:player_client=visionos,android_vr"]

            cmd.append(url)

        else:
            full_folder = str(job_dir)
            if platform == "soundcloud":
                output_tpl = str(job_dir / "%(uploader,artist)s - %(title)s.%(ext)s")
            else:
                output_tpl = str(job_dir / "%(uploader,creator,channel)s - %(title)s.%(ext)s")

            cmd = [
                YT_DLP_BIN,
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--embed-thumbnail",
                "--embed-metadata",
                "--add-metadata",
                "--newline",
                "--no-mtime",
                "--no-playlist",
                "--windows-filenames",
                "--ffmpeg-location", FFMPEG_BIN,
                "-o", output_tpl,
            ] + reliability_flags

            if platform == "youtube":
                cmd += ["--geo-bypass", "--extractor-args", "youtube:player_client=visionos,android_vr"]

            cmd.append(url)

        self.broadcast("start", {
            "title": job.get("title", ""),
            "platform": platform,
            "mode": mode,
            "is_album": is_album,
            "target_folder": full_folder,
            "track_count": job.get("track_count", 1)
        })

        current_item = 1
        total_items = job.get("track_count", 1)
        current_title = job.get("title", "")
        last_pct = 0.0

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=os.environ
            )
            with self.lock:
                self.active_process = proc

            last_lines = []
            for raw_line in iter(proc.stdout.readline, ""):
                line = raw_line.strip()
                if not line:
                    continue
                last_lines.append(line)
                if len(last_lines) > 6:
                    last_lines.pop(0)

                item_match = re.search(r'Downloading item (\d+) of (\d+)', line, re.I)
                if item_match:
                    current_item = int(item_match.group(1))
                    total_items = int(item_match.group(2))

                dest_match = re.search(r'Destination:\s+(.+)', line)
                if dest_match:
                    filename = Path(dest_match.group(1)).stem
                    current_title = filename

                pct_match = re.search(r'\[download\]\s+([\d\.]+)%', line)
                speed_match = re.search(r'at\s+([\d\.]+\s*\w+/s)', line)
                eta_match = re.search(r'ETA\s+([\d:]+|\w+)', line)
                size_match = re.search(r'of\s+(~?\s*[\d\.]+\s*\w+)', line)

                stage = "downloading"
                if "[Merger]" in line or "Merging formats" in line:
                    stage = "merging"
                elif "[ExtractAudio]" in line or "Correcting container" in line:
                    stage = "converting"
                elif "[EmbedThumbnail]" in line or "[Metadata]" in line:
                    stage = "embedding_artwork"

                if pct_match:
                    last_pct = float(pct_match.group(1))

                self.broadcast("progress", {
                    "stage": stage,
                    "item": current_item,
                    "total_items": total_items,
                    "percent": last_pct,
                    "speed": speed_match.group(1) if speed_match else "",
                    "eta": eta_match.group(1) if eta_match else "",
                    "size": size_match.group(1) if size_match else "",
                    "current_track": current_title,
                    "log": line
                })

            proc.wait()
            return_code = proc.returncode

            if return_code == 0:
                download_url = ""
                if is_album:
                    zip_name = f"{album_title}.zip"
                    zip_path = job_dir / zip_name
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for root, _, files in os.walk(album_folder):
                            for f in files:
                                if f.endswith(".zip"):
                                    continue
                                full_f = os.path.join(root, f)
                                rel = os.path.relpath(full_f, str(album_folder))
                                zf.write(full_f, arcname=os.path.join(album_title, rel))
                    download_file_name = zip_name
                    download_url = f"/api/download-file?id={job_id}&file={urllib.parse.quote(zip_name)}"
                else:
                    media_files = list(job_dir.glob("*.mp3")) + list(job_dir.glob("*.mp4"))
                    if media_files:
                        download_file_name = media_files[0].name
                        download_url = f"/api/download-file?id={job_id}&file={urllib.parse.quote(download_file_name)}"

                # Local mode disk saving
                if not IS_CLOUD and job.get("target_folder"):
                    try:
                        dest = Path(os.path.expanduser(job["target_folder"]))
                        dest.mkdir(parents=True, exist_ok=True)
                        if is_album:
                            shutil.copytree(album_folder, dest / album_title, dirs_exist_ok=True)
                            full_folder = str(dest / album_title)
                        else:
                            for mf in media_files:
                                shutil.copy2(mf, dest / mf.name)
                            full_folder = str(dest)
                    except Exception:
                        pass

                history_entry = {
                    "id": str(int(time.time() * 1000)),
                    "title": job.get("title", current_title),
                    "artist": job.get("artist", ""),
                    "platform": platform,
                    "mode": mode,
                    "is_album": is_album,
                    "track_count": total_items if is_album else 1,
                    "thumbnail": job.get("thumbnail", ""),
                    "target_folder": full_folder,
                    "download_url": download_url,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                add_history_item(history_entry)

                if cfg.get("show_notifications", True):
                    notif_title = "Альбом скачан!" if is_album else "Файл скачан!"
                    send_system_notification(notif_title, job.get('title', ''))

                if not IS_CLOUD and cfg.get("auto_open_folder", True):
                    open_in_file_manager(full_folder)

                self.broadcast("done", {
                    "success": True,
                    "platform": platform,
                    "mode": mode,
                    "target_folder": full_folder,
                    "download_url": download_url,
                    "download_file_name": download_file_name,
                    "title": job.get("title", ""),
                    "is_album": is_album,
                    "track_count": total_items if is_album else 1
                })
            else:
                err_hint = ""
                for l in reversed(last_lines):
                    if "error" in l.lower() or "warning" in l.lower():
                        err_hint = f": {l}"
                        break
                if not err_hint and last_lines:
                    err_hint = f": {last_lines[-1]}"
                self.broadcast("error", {
                    "success": False,
                    "message": f"Ошибка скачивания (код {return_code}){err_hint}. Попробуйте другое качество или ссылку."
                })

        except Exception as ex:
            self.broadcast("error", {
                "success": False,
                "message": f"Произошла ошибка: {str(ex)}"
            })
        finally:
            with self.lock:
                self.is_running = False
                self.active_process = None
                self.current_job = None


DOWNLOADER = DownloadManager()


def inspect_media_url(url: str, tab="auto") -> dict:
    url = url.strip()
    platform = detect_platform(url)

    cmd = [
        YT_DLP_BIN,
        "--flat-playlist",
        "-J",
        "--socket-timeout", "20",
        "--geo-bypass"
    ]
    if platform == "youtube":
        cmd += ["--extractor-args", "youtube:player_client=visionos,android_vr"]

    cmd.append(url)

    res = subprocess.run(cmd, capture_output=True, text=True, env=os.environ)
    if res.returncode != 0:
        err = res.stderr.strip() or "Не удалось получить информацию о медиафайле"
        # Friendly error messages
        if "This video is unavailable" in err:
            err = "Видео недоступно на YouTube или ссылка указана с ошибкой. Проверьте правильность ссылки."
        elif "Private video" in err:
            err = "Это приватное видео, доступ к нему ограничен автором."
        elif "Sign in to confirm you're not a bot" in err:
            err = "YouTube запросил подтверждение. Повторите запрос через несколько секунд."
        elif "HTTP Error 429" in err:
            err = "YouTube временно ограничил запросы с этого IP. Повторите запрос через несколько секунд."
        raise ValueError(err)

    info = json.loads(res.stdout)
    _type = info.get("_type", "")
    entries = info.get("entries") or []

    is_album = (platform == "soundcloud") and ((_type == "playlist") or ("/sets/" in url) or (len(entries) > 1))

    duration = info.get("duration")
    if duration and duration > MAX_VIDEO_DURATION_SECONDS:
        dur_mins = int(duration // 60)
        raise ValueError(f"Видео слишком длинное ({dur_mins} мин). Максимальная поддерживаемая длительность — 2 часа (120 мин).")

    thumbnail = ""
    thumbnails = info.get("thumbnails") or []
    if thumbnails:
        for th in reversed(thumbnails):
            if th.get("id") in ("original", "maxresdefault", "t500x500", "crop", "large", "high"):
                thumbnail = th.get("url")
                break
        if not thumbnail:
            thumbnail = thumbnails[-1].get("url", "")
    if not thumbnail and info.get("thumbnail"):
        thumbnail = info.get("thumbnail")

    title = info.get("title", "Unknown Title")
    uploader = info.get("uploader") or info.get("creator") or info.get("channel") or info.get("artist") or platform.capitalize()

    track_count = len(entries) if is_album else 1

    cfg = load_config()

    if platform == "soundcloud":
        if is_album:
            default_folder = os.path.expanduser(cfg.get("album_base_dir"))
            suggested_path = os.path.join(default_folder, sanitize_filename(title))
        else:
            default_folder = os.path.expanduser(cfg.get("single_tracks_dir"))
            suggested_path = os.path.join(default_folder, f"{sanitize_filename(uploader)} - {sanitize_filename(title)}.mp3")
    else:
        default_video_dir = os.path.expanduser(cfg.get("video_dir", DEFAULT_DL_DIR))
        suggested_path = os.path.join(default_video_dir, f"{sanitize_filename(title)}.mp4")

    return {
        "url": url,
        "platform": platform,
        "is_album": is_album,
        "title": title,
        "artist": uploader,
        "thumbnail": thumbnail,
        "track_count": track_count,
        "duration": duration,
        "suggested_folder_name": sanitize_filename(title) if is_album else "",
        "suggested_path": suggested_path,
        "entries": [e.get("title") for e in entries[:8] if isinstance(e, dict)] if is_album else []
    }


class AppRequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for web UI, REST API, and browser file downloads."""

    def log_message(self, format, *args):
        return

    def send_json(self, data: dict, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/download-file":
            query = urllib.parse.parse_qs(parsed.query)
            job_id = query.get("id", [""])[0]
            filename = query.get("file", [""])[0]

            if not job_id or not filename or ".." in job_id or ".." in filename:
                self.send_error(400, "Bad Request")
                return

            target_file = (STORAGE_DIR / job_id / filename).resolve()
            if not target_file.is_file() or not str(target_file).startswith(str(STORAGE_DIR)):
                self.send_error(404, "Файл не найден или устарел")
                return

            file_size = target_file.stat().st_size
            ext = target_file.suffix.lower()
            mime_types = {
                ".mp3": "audio/mpeg",
                ".mp4": "video/mp4",
                ".zip": "application/zip",
                ".m4a": "audio/mp4"
            }
            content_type = mime_types.get(ext, "application/octet-stream")

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_size))
            safe_name = urllib.parse.quote(target_file.name)
            self.send_header("Content-Disposition", f'attachment; filename="{target_file.name}"; filename*=UTF-8\'\'{safe_name}')
            self.end_headers()

            with open(target_file, "rb") as f:
                shutil.copyfileobj(f, self.wfile, length=64 * 1024)
            return

        elif path == "/api/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            q = DOWNLOADER.subscribe()
            try:
                init_data = json.dumps({
                    "is_running": DOWNLOADER.is_running,
                    "job": DOWNLOADER.current_job,
                    "os": get_os_type(),
                    "is_cloud": IS_CLOUD
                }, ensure_ascii=False)
                self.wfile.write(f"event: init\ndata: {init_data}\n\n".encode("utf-8"))
                self.wfile.flush()

                while True:
                    try:
                        msg = q.get(timeout=20)
                        self.wfile.write(msg.encode("utf-8"))
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                DOWNLOADER.unsubscribe(q)
            return

        elif path == "/api/config":
            cfg = load_config()
            cfg["os"] = get_os_type()
            cfg["is_cloud"] = IS_CLOUD
            self.send_json(cfg)
            return

        elif path == "/api/history":
            self.send_json({"history": load_history(), "os": get_os_type(), "is_cloud": IS_CLOUD})
            return

        elif path == "/api/status":
            self.send_json({
                "is_running": DOWNLOADER.is_running,
                "job": DOWNLOADER.current_job,
                "os": get_os_type(),
                "is_cloud": IS_CLOUD,
                "max_duration_seconds": MAX_VIDEO_DURATION_SECONDS,
                "yt_dlp": YT_DLP_BIN,
                "ffmpeg": FFMPEG_BIN
            })
            return

        # Static files
        if path == "/" or path == "":
            file_path = STATIC_DIR / "index.html"
        else:
            rel = path.lstrip("/")
            file_path = (STATIC_DIR / rel).resolve()
            if not str(file_path).startswith(str(STATIC_DIR)):
                self.send_error(403, "Forbidden")
                return

        if file_path.is_file():
            mime_types = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".json": "application/json; charset=utf-8",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".svg": "image/svg+xml",
                ".ico": "image/x-icon"
            }
            content_type = mime_types.get(file_path.suffix.lower(), "application/octet-stream")
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            req_data = json.loads(post_body.decode("utf-8")) if post_body else {}
        except Exception:
            req_data = {}

        if path == "/api/inspect":
            url = req_data.get("url", "").strip()
            tab = req_data.get("tab", "auto")
            if not url:
                self.send_json({"error": "Укажите ссылку на медиафайл"}, status=400)
                return
            try:
                info = inspect_media_url(url, tab=tab)
                self.send_json(info)
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)

        elif path == "/api/pick-folder":
            prompt = req_data.get("prompt", "Выберите папку")
            chosen = pick_folder_dialog(prompt)
            self.send_json({"folder": chosen, "cancelled": not bool(chosen)})

        elif path == "/api/config":
            cfg = load_config()
            cfg.update(req_data)
            save_config(cfg)
            self.send_json({"success": True, "config": cfg})

        elif path == "/api/download":
            url = req_data.get("url", "").strip()
            if not url:
                self.send_json({"error": "Ссылка отсутствует"}, status=400)
                return
            try:
                DOWNLOADER.start_download(req_data)
                self.send_json({"success": True, "message": "Загрузка запущена"})
            except Exception as ex:
                self.send_json({"error": str(ex)}, status=400)

        elif path == "/api/cancel":
            ok = DOWNLOADER.cancel()
            self.send_json({"success": ok})

        elif path == "/api/open-folder":
            target = req_data.get("path", "")
            if target:
                open_in_file_manager(target)
                self.send_json({"success": True})
            else:
                self.send_json({"error": "Путь не указан"}, status=400)

        elif path == "/api/clear-history":
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
            self.send_json({"success": True})

        else:
            self.send_error(404, "Not Found")


def start_server(port=None, open_browser=True):
    cfg = load_config()
    server_port = port or int(os.environ.get("PORT", cfg.get("port", 5077)))
    host = "0.0.0.0"

    server = None
    for p in range(server_port, server_port + 20):
        try:
            server = ThreadingHTTPServer((host, p), AppRequestHandler)
            server_port = p
            break
        except OSError:
            if IS_CLOUD:
                raise
            continue

    if not server:
        print("❌ Не удалось запустить сервер")
        sys.exit(1)

    url = f"http://localhost:{server_port}"
    print("=" * 60)
    print(f"🎶 Media Downloader ({'Cloud Mode' if IS_CLOUD else 'Local Desktop Mode'})")
    print(f"🌐 Сервер запущен: {url} (listening on 0.0.0.0:{server_port})")
    print(f"🛠 yt-dlp: {YT_DLP_BIN}")
    print(f"🛠 ffmpeg: {FFMPEG_BIN}")
    print("=" * 60)

    if open_browser and not IS_CLOUD:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    def handle_sigint(signum, frame):
        print("\nОстановка сервера...")
        DOWNLOADER.cancel()
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    no_open = "--no-browser" in sys.argv or IS_CLOUD
    start_server(open_browser=not no_open)
