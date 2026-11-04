// Media & SoundCloud Downloader - Frontend Controller

let activeTab = "soundcloud"; // "soundcloud" or "video"
let detectedOS = "macos";     // "macos" or "windows" or "linux" or "cloud"
let isCloudMode = false;
let currentInspection = null;
let currentConfig = null;
let currentMode = "audio";    // "video" or "audio"
let sseSource = null;
let lastDownloadPath = "";
let lastDownloadUrl = "";

// DOM Elements - OS & Brand
const osBadge = document.getElementById("osBadge");
const osIcon = document.getElementById("osIcon");
const osName = document.getElementById("osName");
const settingsOsName = document.getElementById("settingsOsName");
const pasteShortcut = document.getElementById("pasteShortcut");
const browseBtnLabel = document.getElementById("browseBtnLabel");
const openManagerBtnLabel = document.getElementById("openManagerBtnLabel");
const autoOpenLabel = document.getElementById("autoOpenLabel");
const notifLabel = document.getElementById("notifLabel");

// DOM Elements - Navigation
const tabSoundCloud = document.getElementById("tabSoundCloud");
const tabVideo = document.getElementById("tabVideo");
const logoSubtitle = document.getElementById("logoSubtitle");

// DOM Elements - Input
const urlInput = document.getElementById("urlInput");
const btnPaste = document.getElementById("btnPaste");
const btnInspect = document.getElementById("btnInspect");
const inspectSpinner = document.getElementById("inspectSpinner");
const inspectText = document.getElementById("inspectText");
const hintText = document.getElementById("hintText");
const errorAlert = document.getElementById("errorAlert");
const errorMsg = document.getElementById("errorMsg");

// DOM Elements - Preview
const previewCard = document.getElementById("previewCard");
const prevArtwork = document.getElementById("prevArtwork");
const artOverlayTag = document.getElementById("artOverlayTag");
const artOverlayText = document.getElementById("artOverlayText");
const prevPlatformBadge = document.getElementById("prevPlatformBadge");
const prevTypeBadge = document.getElementById("prevTypeBadge");
const prevCountBadge = document.getElementById("prevCountBadge");
const prevTitle = document.getElementById("prevTitle");
const prevArtist = document.getElementById("prevArtist");

const videoModeSelector = document.getElementById("videoModeSelector");
const btnModeVideo = document.getElementById("btnModeVideo");
const btnModeAudio = document.getElementById("btnModeAudio");
const qualityRow = document.getElementById("qualityRow");
const qualitySelect = document.getElementById("qualitySelect");

const destLabel = document.getElementById("destLabel");
const targetFolderInput = document.getElementById("targetFolderInput");
const albumSubfolderRow = document.getElementById("albumSubfolderRow");
const albumFolderInput = document.getElementById("albumFolderInput");
const fullPathPreview = document.getElementById("fullPathPreview");
const btnBrowseFolder = document.getElementById("btnBrowseFolder");
const btnStartDownload = document.getElementById("btnStartDownload");
const downloadBtnText = document.getElementById("downloadBtnText");
const tracklistSection = document.getElementById("tracklistSection");
const tracklistItems = document.getElementById("tracklistItems");

// DOM Elements - Progress
const progressCard = document.getElementById("progressCard");
const progStageBadge = document.getElementById("progStageBadge");
const progTitle = document.getElementById("progTitle");
const progCurrentTrack = document.getElementById("progCurrentTrack");
const btnCancelDownload = document.getElementById("btnCancelDownload");
const progressBar = document.getElementById("progressBar");
const progPercent = document.getElementById("progPercent");
const progSpeed = document.getElementById("progSpeed");
const progEta = document.getElementById("progEta");
const progItemCount = document.getElementById("progItemCount");
const progItemsWrapper = document.getElementById("progItemsWrapper");
const logOutput = document.getElementById("logOutput");

// DOM Elements - Done
const doneCard = document.getElementById("doneCard");
const doneTitle = document.getElementById("doneTitle");
const doneSubtitle = document.getElementById("doneSubtitle");
const donePathText = document.getElementById("donePathText");
const btnOpenInFinder = document.getElementById("btnOpenInFinder");
const btnDownloadFileAgain = document.getElementById("btnDownloadFileAgain");
const downloadFileBtnText = document.getElementById("downloadFileBtnText");
const btnNewDownload = document.getElementById("btnNewDownload");

// DOM Elements - Settings
const btnSettings = document.getElementById("btnSettings");
const settingsModal = document.getElementById("settingsModal");
const btnCloseSettings = document.getElementById("btnCloseSettings");
const btnSaveSettings = document.getElementById("btnSaveSettings");
const cfgAlbumDir = document.getElementById("cfgAlbumDir");
const cfgTracksDir = document.getElementById("cfgTracksDir");
const cfgVideoDir = document.getElementById("cfgVideoDir");
const cfgAudioDir = document.getElementById("cfgAudioDir");
const cfgNumberTracks = document.getElementById("cfgNumberTracks");
const cfgAutoOpen = document.getElementById("cfgAutoOpen");
const cfgNotifications = document.getElementById("cfgNotifications");
const btnBrowseCfgAlbum = document.getElementById("btnBrowseCfgAlbum");
const btnBrowseCfgTracks = document.getElementById("btnBrowseCfgTracks");
const btnBrowseCfgVideo = document.getElementById("btnBrowseCfgVideo");
const btnBrowseCfgAudio = document.getElementById("btnBrowseCfgAudio");

// DOM Elements - History
const btnHistory = document.getElementById("btnHistory");
const historyModal = document.getElementById("historyModal");
const btnCloseHistory = document.getElementById("btnCloseHistory");
const btnClearHistory = document.getElementById("btnClearHistory");
const historyList = document.getElementById("historyList");
const historyBadge = document.getElementById("historyBadge");

// Detect client OS from browser
function getClientBrowserOS() {
  const ua = navigator.userAgent || "";
  const plat = navigator.userAgentData?.platform || navigator.platform || "";
  if (/Win/i.test(plat) || /Win/i.test(ua)) return "windows";
  if (/Mac/i.test(plat) || /Mac/i.test(ua)) return "macos";
  if (/Linux/i.test(plat) || /Linux/i.test(ua)) return "linux";
  return "macos";
}

function applyOSToUI(os, cloudFlag = false) {
  detectedOS = os;
  isCloudMode = cloudFlag || (os === "cloud");
  document.body.dataset.os = os;

  if (isCloudMode) {
    osIcon.textContent = "☁️";
    osName.textContent = "Облако / Web";
    settingsOsName.textContent = "Облако";
    pasteShortcut.textContent = "Вставить";
    browseBtnLabel.textContent = "Загрузка в браузер";
    openManagerBtnLabel.textContent = "Скачать файл";
    autoOpenLabel.textContent = "Автоматически начинать скачивание в браузере";
    notifLabel.textContent = "Показывать уведомления браузера";
    if (btnBrowseFolder) btnBrowseFolder.style.display = "none";
    if (targetFolderInput) targetFolderInput.parentElement.style.display = "none";
    if (fullPathPreview) fullPathPreview.parentElement.style.display = "none";
    if (destLabel) destLabel.innerHTML = "📥 Файл сохранится напрямую в <b>Загрузки</b> на вашем устройстве";
  } else if (os === "windows") {
    osIcon.textContent = "🪟";
    osName.textContent = "Windows";
    settingsOsName.textContent = "Windows";
    pasteShortcut.textContent = "Ctrl+V";
    browseBtnLabel.textContent = "Выбрать папку (Обзор)...";
    openManagerBtnLabel.textContent = "Открыть в Проводнике";
    autoOpenLabel.textContent = "Автоматически открывать папку в Проводнике";
    notifLabel.textContent = "Отправлять системное уведомление Windows";
  } else {
    osIcon.textContent = "🍎";
    osName.textContent = "macOS";
    settingsOsName.textContent = "macOS";
    pasteShortcut.textContent = "⌘V";
    browseBtnLabel.textContent = "Выбрать папку (Finder)...";
    openManagerBtnLabel.textContent = "Открыть в Finder";
    autoOpenLabel.textContent = "Автоматически открывать папку в Finder";
    notifLabel.textContent = "Отправлять системное уведомление macOS";
  }
}

// Initialization
document.addEventListener("DOMContentLoaded", async () => {
  // Initial detection from browser
  applyOSToUI(getClientBrowserOS());

  await loadConfig();
  await loadHistory();
  initSSE();
  setupEventListeners();
  switchTab("soundcloud");
});

// Setup Events
function setupEventListeners() {
  // Tabs
  tabSoundCloud.addEventListener("click", () => switchTab("soundcloud"));
  tabVideo.addEventListener("click", () => switchTab("video"));

  // Input & Inspection
  btnPaste.addEventListener("click", handlePaste);
  btnInspect.addEventListener("click", handleInspect);
  urlInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleInspect();
  });
  urlInput.addEventListener("paste", () => {
    setTimeout(handleInspect, 100);
  });

  // Mode Buttons (Video / Audio)
  btnModeVideo.addEventListener("click", () => setVideoMode("video"));
  btnModeAudio.addEventListener("click", () => setVideoMode("audio"));
  qualitySelect.addEventListener("change", updateDownloadButtonAndPath);

  // Path & Browsing
  btnBrowseFolder.addEventListener("click", () => pickFolderForTarget());
  albumFolderInput.addEventListener("input", updatePathPreview);
  targetFolderInput.addEventListener("input", updatePathPreview);

  // Download Actions
  btnStartDownload.addEventListener("click", startDownload);
  btnCancelDownload.addEventListener("click", cancelDownload);

  btnOpenInFinder.addEventListener("click", () => {
    if (lastDownloadPath) openFolder(lastDownloadPath);
  });

  btnNewDownload.addEventListener("click", () => {
    doneCard.style.display = "none";
    urlInput.value = "";
    urlInput.focus();
  });

  // Settings
  btnSettings.addEventListener("click", openSettings);
  btnCloseSettings.addEventListener("click", () => settingsModal.style.display = "none");
  settingsModal.addEventListener("click", (e) => {
    if (e.target === settingsModal) settingsModal.style.display = "none";
  });
  btnSaveSettings.addEventListener("click", saveSettings);

  btnBrowseCfgAlbum.addEventListener("click", async () => {
    const f = await requestFolderPicker("Выберите папку для альбомов SoundCloud");
    if (f) cfgAlbumDir.value = f;
  });
  btnBrowseCfgTracks.addEventListener("click", async () => {
    const f = await requestFolderPicker("Выберите папку для треков SoundCloud");
    if (f) cfgTracksDir.value = f;
  });
  btnBrowseCfgVideo.addEventListener("click", async () => {
    const f = await requestFolderPicker("Выберите папку для видео YouTube/TikTok");
    if (f) cfgVideoDir.value = f;
  });
  btnBrowseCfgAudio.addEventListener("click", async () => {
    const f = await requestFolderPicker("Выберите папку для аудио YouTube/TikTok");
    if (f) cfgAudioDir.value = f;
  });

  // History
  btnHistory.addEventListener("click", () => {
    historyModal.style.display = "flex";
    loadHistory();
  });
  btnCloseHistory.addEventListener("click", () => historyModal.style.display = "none");
  historyModal.addEventListener("click", (e) => {
    if (e.target === historyModal) historyModal.style.display = "none";
  });
  btnClearHistory.addEventListener("click", clearHistory);
}

// Switch Tabs
function switchTab(tab) {
  activeTab = tab;
  document.body.dataset.tab = tab;

  const osTitle = isCloudMode ? "" : (detectedOS === "windows" ? "для Windows" : "для macOS");

  if (tab === "soundcloud") {
    tabSoundCloud.classList.add("active");
    tabVideo.classList.remove("active");
    urlInput.placeholder = "Вставьте ссылку на трек или альбом SoundCloud...";
    hintText.innerHTML = "<span>Поддерживаются:</span> одиночные треки и плейлисты/альбомы (со ссылками вида <code>soundcloud.com/artist/sets/...</code>)";
    logoSubtitle.textContent = `Скачивание треков и альбомов с обложками в MP3 ${osTitle}`.trim();
  } else {
    tabVideo.classList.add("active");
    tabSoundCloud.classList.remove("active");
    urlInput.placeholder = "Вставьте ссылку на видео YouTube, Shorts или TikTok...";
    hintText.innerHTML = "<span>Поддерживаются:</span> YouTube (видео до 2 часов, Shorts, плейлисты) и TikTok (клипы)";
    logoSubtitle.textContent = `Скачивание видео (MP4) или извлечение MP3 ${osTitle}`.trim();
  }

  hideError();
  previewCard.style.display = "none";
  doneCard.style.display = "none";
  urlInput.value = "";
  urlInput.focus();
}

// Config
async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    currentConfig = await res.json();
    if (currentConfig.os) {
      applyOSToUI(currentConfig.os, currentConfig.is_cloud);
    }
    cfgAlbumDir.value = currentConfig.album_base_dir || "~/Music/SoundCloud";
    cfgTracksDir.value = currentConfig.single_tracks_dir || "~/Downloads";
    cfgVideoDir.value = currentConfig.video_dir || "~/Downloads";
    cfgAudioDir.value = currentConfig.audio_dir || "~/Downloads";
    cfgNumberTracks.checked = currentConfig.number_tracks !== false;
    cfgAutoOpen.checked = currentConfig.auto_open_folder !== false;
    cfgNotifications.checked = currentConfig.show_notifications !== false;
  } catch (e) {
    console.error("Failed to load config", e);
  }
}

async function saveSettings() {
  const updated = {
    album_base_dir: cfgAlbumDir.value.trim(),
    single_tracks_dir: cfgTracksDir.value.trim(),
    video_dir: cfgVideoDir.value.trim(),
    audio_dir: cfgAudioDir.value.trim(),
    number_tracks: cfgNumberTracks.checked,
    auto_open_folder: cfgAutoOpen.checked,
    show_notifications: cfgNotifications.checked
  };
  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updated)
    });
    const d = await res.json();
    if (d.success) {
      currentConfig = d.config;
      settingsModal.style.display = "none";
    }
  } catch (e) {
    alert("Ошибка сохранения настроек: " + e.message);
  }
}

function openSettings() {
  if (currentConfig) {
    cfgAlbumDir.value = currentConfig.album_base_dir;
    cfgTracksDir.value = currentConfig.single_tracks_dir;
    cfgVideoDir.value = currentConfig.video_dir || "~/Downloads";
    cfgAudioDir.value = currentConfig.audio_dir || "~/Downloads";
    cfgNumberTracks.checked = currentConfig.number_tracks;
    cfgAutoOpen.checked = currentConfig.auto_open_folder;
    cfgNotifications.checked = currentConfig.show_notifications;
  }
  settingsModal.style.display = "flex";
}

// SSE Connection
function initSSE() {
  if (sseSource) sseSource.close();
  sseSource = new EventSource("/api/events");

  sseSource.addEventListener("init", (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.os) applyOSToUI(data.os);
    } catch (_) {}
  });

  sseSource.addEventListener("start", (e) => {
    const data = JSON.parse(e.data);
    onDownloadStart(data);
  });

  sseSource.addEventListener("progress", (e) => {
    const data = JSON.parse(e.data);
    onDownloadProgress(data);
  });

  sseSource.addEventListener("done", (e) => {
    const data = JSON.parse(e.data);
    onDownloadDone(data);
  });

  sseSource.addEventListener("error", (e) => {
    try {
      const data = JSON.parse(e.data);
      onDownloadError(data.message || "Ошибка загрузки");
    } catch (_) {}
  });

  sseSource.addEventListener("cancelled", () => {
    hideProgress();
    showError("Загрузка отменена");
  });
}

// Clipboard Paste
async function handlePaste() {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      urlInput.value = text.trim();
      handleInspect();
    }
  } catch (err) {
    urlInput.focus();
  }
}

// Inspect URL
async function handleInspect() {
  const url = urlInput.value.trim();
  if (!url) return;

  hideError();
  previewCard.style.display = "none";
  doneCard.style.display = "none";

  btnInspect.disabled = true;
  inspectSpinner.style.display = "inline-block";
  inspectText.textContent = "Анализ...";

  try {
    const res = await fetch("/api/inspect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, tab: activeTab })
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      throw new Error(data.error || "Не удалось загрузить информацию");
    }

    currentInspection = data;
    renderPreview(data);
  } catch (err) {
    showError(err.message);
  } finally {
    btnInspect.disabled = false;
    inspectSpinner.style.display = "none";
    inspectText.textContent = "Найти";
  }
}

// Render Preview Card
function renderPreview(data) {
  prevTitle.textContent = data.title;
  prevArtist.textContent = data.artist || data.platform.toUpperCase();

  // Thumbnail
  if (data.thumbnail) {
    prevArtwork.src = data.thumbnail;
    prevArtwork.style.display = "block";
  } else {
    prevArtwork.src = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' fill='%23333'><rect width='100%' height='100%'/></svg>";
  }

  // Platform Badge
  const p = data.platform;
  if (p === "youtube") {
    prevPlatformBadge.textContent = "YouTube";
    prevPlatformBadge.style.background = "#ff0000";
    prevPlatformBadge.style.color = "#fff";
  } else if (p === "tiktok") {
    prevPlatformBadge.textContent = "TikTok";
    prevPlatformBadge.style.background = "#010101";
    prevPlatformBadge.style.color = "#00f2fe";
  } else {
    prevPlatformBadge.textContent = "SoundCloud";
    prevPlatformBadge.style.background = "#ff5500";
    prevPlatformBadge.style.color = "#fff";
  }

  // Duration
  if (data.duration) {
    prevCountBadge.textContent = formatDuration(data.duration);
    prevCountBadge.style.display = "inline-block";
  } else if (data.is_album) {
    prevCountBadge.textContent = `${data.track_count} треков`;
    prevCountBadge.style.display = "inline-block";
  } else {
    prevCountBadge.style.display = "none";
  }

  if (p === "soundcloud") {
    videoModeSelector.style.display = "none";
    currentMode = "audio";

    if (data.is_album) {
      prevTypeBadge.textContent = "💿 Альбом / Сет";
      prevTypeBadge.className = "badge-tag badge-album";
      destLabel.innerHTML = isCloudMode ? "📥 Альбом скачается в ZIP-архиве в <b>Загрузки</b>" : "📁 Создать папку альбома в:";
      targetFolderInput.value = currentConfig?.album_base_dir || "~/Music/SoundCloud";
      albumFolderInput.value = data.suggested_folder_name || data.title;
      albumSubfolderRow.style.display = isCloudMode ? "none" : "flex";
      downloadBtnText.textContent = `Скачать альбом в MP3 (${data.track_count} треков)`;
      artOverlayText.textContent = "Вшивается в каждый MP3";

      if (data.entries && data.entries.length > 0) {
        tracklistItems.innerHTML = "";
        data.entries.forEach((t) => {
          const li = document.createElement("li");
          li.textContent = t || "Трек";
          tracklistItems.appendChild(li);
        });
        tracklistSection.style.display = "block";
      } else {
        tracklistSection.style.display = "none";
      }
    } else {
      prevTypeBadge.textContent = "🎵 Одиночный трек";
      prevTypeBadge.className = "badge-tag badge-track";
      destLabel.innerHTML = isCloudMode ? "📥 Трек сохранится в <b>Загрузки</b>" : "📁 Сохранить трек в:";
      targetFolderInput.value = currentConfig?.single_tracks_dir || "~/Downloads";
      albumSubfolderRow.style.display = "none";
      downloadBtnText.textContent = "Скачать трек в MP3 (320 kbps)";
      artOverlayText.textContent = "Вшивается в MP3";
      tracklistSection.style.display = "none";
    }
  } else {
    // Video platforms (YouTube, TikTok)
    prevTypeBadge.textContent = "🎬 Видеоклип";
    prevTypeBadge.className = "badge-tag badge-video";
    albumSubfolderRow.style.display = "none";
    tracklistSection.style.display = "none";
    videoModeSelector.style.display = "flex";

    setVideoMode("video");
  }

  updatePathPreview();
  previewCard.style.display = "block";
}

// Set Video Mode
function setVideoMode(mode) {
  currentMode = mode;
  if (mode === "video") {
    btnModeVideo.classList.add("active");
    btnModeAudio.classList.remove("active");
    qualityRow.style.display = "flex";
    destLabel.innerHTML = isCloudMode ? "📥 Видео сохранится напрямую в <b>Загрузки</b>" : "📁 Сохранить видео в:";
    targetFolderInput.value = currentConfig?.video_dir || "~/Downloads";
    artOverlayText.textContent = "Превью видео";
  } else {
    btnModeAudio.classList.add("active");
    btnModeVideo.classList.remove("active");
    qualityRow.style.display = "none";
    destLabel.innerHTML = isCloudMode ? "📥 Аудио MP3 сохранится напрямую в <b>Загрузки</b>" : "📁 Сохранить аудио MP3 в:";
    targetFolderInput.value = currentConfig?.audio_dir || "~/Downloads";
    artOverlayText.textContent = "Вшивается в MP3";
  }
  updateDownloadButtonAndPath();
}

function updateDownloadButtonAndPath() {
  if (!currentInspection) return;
  if (currentInspection.platform === "soundcloud") return;

  if (currentMode === "video") {
    let qText = "Макс. качество";
    if (qualitySelect.value === "720") qText = "720p HD";
    else if (qualitySelect.value === "480") qText = "480p SD";
    downloadBtnText.textContent = `Скачать видео в MP4 (${qText})`;
  } else {
    downloadBtnText.textContent = "Извлечь аудио в MP3 (320 kbps + обложка)";
  }
  updatePathPreview();
}

function updatePathPreview() {
  if (!currentInspection) return;
  const base = targetFolderInput.value.trim();
  const sep = detectedOS === "windows" ? "\\" : "/";

  if (currentInspection.platform === "soundcloud") {
    if (currentInspection.is_album) {
      const sub = albumFolderInput.value.trim();
      fullPathPreview.textContent = `${base}${sep}${sub}${sep}`;
    } else {
      const fn = `${currentInspection.artist} - ${currentInspection.title}.mp3`;
      fullPathPreview.textContent = `${base}${sep}${fn}`;
    }
  } else {
    if (currentMode === "video") {
      fullPathPreview.textContent = `${base}${sep}${currentInspection.title}.mp4`;
    } else {
      fullPathPreview.textContent = `${base}${sep}${currentInspection.artist} - ${currentInspection.title}.mp3`;
    }
  }
}

function formatDuration(sec) {
  if (!sec) return "";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s < 10 ? "0" : ""}${s}`;
}

// Pick Folder Dialog
async function requestFolderPicker(prompt = "Выберите папку") {
  try {
    const res = await fetch("/api/pick-folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });
    const d = await res.json();
    if (d.folder) return d.folder;
  } catch (e) {
    console.error("Folder picker failed", e);
  }
  return null;
}

async function pickFolderForTarget() {
  const origBtnText = btnBrowseFolder.innerHTML;
  btnBrowseFolder.textContent = "Выбор...";
  btnBrowseFolder.disabled = true;

  let prompt = "Выберите папку для сохранения";
  if (currentInspection?.platform === "soundcloud" && currentInspection?.is_album) {
    prompt = "Выберите папку, где создать папку с альбомом";
  }

  const folder = await requestFolderPicker(prompt);
  if (folder) {
    targetFolderInput.value = folder;
    updatePathPreview();
  }

  btnBrowseFolder.innerHTML = origBtnText;
  btnBrowseFolder.disabled = false;
}

// Start Download
async function startDownload() {
  if (!currentInspection) return;

  hideError();
  const job = {
    url: currentInspection.url,
    platform: currentInspection.platform,
    mode: currentMode,
    quality: qualitySelect.value,
    is_album: currentInspection.is_album,
    title: currentInspection.title,
    artist: currentInspection.artist,
    thumbnail: currentInspection.thumbnail,
    track_count: currentInspection.track_count,
    target_folder: targetFolderInput.value.trim(),
    album_title: currentInspection.is_album ? albumFolderInput.value.trim() : ""
  };

  try {
    const res = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(job)
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      throw new Error(data.error || "Не удалось запустить загрузку");
    }

    previewCard.style.display = "none";
    doneCard.style.display = "none";
    progressCard.style.display = "flex";
    progTitle.textContent = currentInspection.title;
    progCurrentTrack.textContent = "Подключение к источнику...";
    progStageBadge.textContent = "Запуск...";
    progressBar.style.width = "0%";
    progPercent.textContent = "0%";
    progSpeed.textContent = "--";
    progEta.textContent = "--";
    logOutput.textContent = "";

    if (currentInspection.is_album) {
      progItemsWrapper.style.display = "flex";
      progItemCount.textContent = `1 / ${currentInspection.track_count}`;
    } else {
      progItemsWrapper.style.display = "none";
    }
  } catch (e) {
    showError(e.message);
  }
}

// Cancel Download
async function cancelDownload() {
  btnCancelDownload.disabled = true;
  btnCancelDownload.textContent = "Отмена...";
  try {
    await fetch("/api/cancel", { method: "POST" });
  } catch (_) {}
  finally {
    btnCancelDownload.disabled = false;
    btnCancelDownload.innerHTML = `
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="6" y="6" width="12" height="12"/>
      </svg> Отмена`;
  }
}

// Download Events
function onDownloadStart(data) {
  progressCard.style.display = "flex";
  progTitle.textContent = data.title;
  lastDownloadPath = data.target_folder;
}

function onDownloadProgress(data) {
  if (data.stage === "merging") {
    progStageBadge.textContent = "Объединение дорожек (MP4)";
  } else if (data.stage === "converting") {
    progStageBadge.textContent = "Конвертация в MP3 (320k)";
  } else if (data.stage === "embedding_artwork") {
    progStageBadge.textContent = "Вшивание обложки & метаданных";
  } else {
    progStageBadge.textContent = "Загрузка данных";
  }

  if (data.percent !== undefined) {
    progressBar.style.width = `${Math.min(data.percent, 100)}%`;
    progPercent.textContent = `${data.percent.toFixed(1)}%`;
  }
  if (data.speed) progSpeed.textContent = data.speed;
  if (data.eta) progEta.textContent = data.eta;
  if (data.current_track) progCurrentTrack.textContent = data.current_track;

  if (data.item && data.total_items > 1) {
    progItemsWrapper.style.display = "flex";
    progItemCount.textContent = `${data.item} / ${data.total_items}`;
  }

  if (data.log) {
    logOutput.textContent += data.log + "\n";
    logOutput.scrollTop = logOutput.scrollHeight;
  }
}

function onDownloadDone(data) {
  progressCard.style.display = "none";
  doneCard.style.display = "flex";
  lastDownloadPath = data.target_folder;
  lastDownloadUrl = data.download_url;

  if (data.is_album) {
    doneTitle.textContent = `Альбом "${data.title}" готов!`;
    doneSubtitle.textContent = isCloudMode
      ? `Все ${data.track_count} треков упакованы в ZIP-архив с обложками.`
      : `Все ${data.track_count} треков сохранены в MP3 с обложками в отдельную папку:`;
  } else if (data.mode === "video") {
    doneTitle.textContent = `Видео "${data.title}" скачано!`;
    doneSubtitle.textContent = `Видеофайл сохранен в формате MP4:`;
  } else {
    doneTitle.textContent = `Аудио "${data.title}" скачано!`;
    doneSubtitle.textContent = `Аудиофайл сохранен в формате MP3 с обложкой и тегами:`;
  }

  donePathText.textContent = isCloudMode ? (data.download_file_name || "") : data.target_folder;

  // Browser direct download trigger
  if (data.download_url) {
    btnDownloadFileAgain.href = data.download_url;
    btnDownloadFileAgain.download = data.download_file_name || "";
    btnDownloadFileAgain.style.display = "inline-flex";

    if (data.is_album) {
      downloadFileBtnText.textContent = "📥 Скачать архив альбома (.zip)";
    } else {
      downloadFileBtnText.textContent = "📥 Скачать файл на устройство";
    }

    // Auto-trigger browser download
    try {
      const a = document.createElement("a");
      a.href = data.download_url;
      a.download = data.download_file_name || "";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (_) {}
  } else {
    btnDownloadFileAgain.style.display = "none";
  }

  if (isCloudMode) {
    btnOpenInFinder.style.display = "none";
  } else {
    btnOpenInFinder.style.display = "inline-flex";
  }

  loadHistory();
}

function onDownloadError(msg) {
  hideProgress();
  showError(msg);
}

function hideProgress() {
  progressCard.style.display = "none";
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorAlert.style.display = "flex";
}

function hideError() {
  errorAlert.style.display = "none";
}

// Open Folder in OS File Manager
async function openFolder(path) {
  try {
    await fetch("/api/open-folder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path })
    });
  } catch (e) {
    alert("Не удалось открыть папку: " + e.message);
  }
}

// History
async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    const d = await res.json();
    const hist = d.history || [];

    if (hist.length > 0) {
      historyBadge.textContent = hist.length;
      historyBadge.style.display = "inline-block";
      renderHistory(hist);
    } else {
      historyBadge.style.display = "none";
      historyList.innerHTML = '<p class="history-empty">История пока пуста</p>';
    }
  } catch (e) {
    console.error("Failed to load history", e);
  }
}

function renderHistory(items) {
  historyList.innerHTML = "";
  items.forEach((item) => {
    const el = document.createElement("div");
    el.className = "history-item";

    const art = document.createElement("img");
    art.className = "history-art";
    art.src = item.thumbnail || "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' fill='%23333'><rect width='100%' height='100%'/></svg>";

    const info = document.createElement("div");
    info.className = "history-info";

    let prefix = "🎵 ";
    if (item.is_album) prefix = "💿 [Альбом] ";
    else if (item.mode === "video") prefix = "🎬 [Видео] ";

    const title = document.createElement("div");
    title.className = "history-title";
    title.textContent = `${prefix}${item.title}`;

    const meta = document.createElement("div");
    meta.className = "history-meta";
    const platName = (item.platform || "media").toUpperCase();
    meta.textContent = `${platName} • ${item.artist || ""} • ${item.is_album ? item.track_count + " треков • " : ""}${item.timestamp}`;

    info.appendChild(title);
    info.appendChild(meta);

    const btnOpen = document.createElement("button");
    btnOpen.className = "btn-browse";
    const managerName = detectedOS === "windows" ? "Проводник" : "Finder";
    btnOpen.innerHTML = `
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
      </svg> ${managerName}`;
    btnOpen.addEventListener("click", () => openFolder(item.target_folder));

    el.appendChild(art);
    el.appendChild(info);
    el.appendChild(btnOpen);

    historyList.appendChild(el);
  });
}

async function clearHistory() {
  if (!confirm("Очистить историю скачиваний?")) return;
  try {
    await fetch("/api/clear-history", { method: "POST" });
    await loadHistory();
  } catch (e) {
    alert("Ошибка очистки истории: " + e.message);
  }
}
