<h1 align="center">🎞️ PanZoom Slideshow</h1>

<p align="center">
Create cinematic video slideshows from images and music with the Ken Burns effect, audio mastering, and export profiles — all via the command line.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/FFmpeg-6.x-green?style=for-the-badge&logo=ffmpeg" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

---

## 📌 Overview

**PanZoom Slideshow** is a professional CLI tool that converts folders of images and audio files into cinematic slideshows using pan/zoom effects, transitions, and more.

**Key features:**

- 🎬 Ken Burns-style motion (pan + zoom)
- 🎭 25+ transitions (fade, slide, dissolve, etc.)
- 📦 Export presets (YouTube, Instagram, TikTok)
- 🎵 Audio mastering & normalization
- 🧾 YAML configuration support
- 🏷️ Watermark/logo overlay
- 👁️ Fast preview mode

---

## ⚙️ Requirements
## add picture.png and music.wav in folder
### Check Python version

```bash
python --version
```

> ✅ Required: Python 3.8 or higher

---

### Check FFmpeg installation

```bash
ffmpeg -version
```

> ✅ Required: FFmpeg 6.x or higher  
> 🔗 Download: https://ffmpeg.org/download.html

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-org/panzoom-slideshow.git
```

---

### 2. Enter the project folder

```bash
cd panzoom-slideshow
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Create Your First Video

### Basic slideshow from images + audio

```bash
python -m panzoom video -i ./photos -a music.wav
```

---

### Use cinematic preset

```bash
python -m panzoom video -i ./photos -a music.wav --preset cinematic
```

---

### Shuffle image order

```bash
python -m panzoom video -i ./photos -a music.wav --shuffle
```

---

### Export for Instagram Reels

```bash
python -m panzoom video -i ./photos -a music.wav --export instagram_reels
```

---

### Add watermark/logo

```bash
python -m panzoom video -i ./photos -a music.wav --watermark logo.png
```

---

### Preview mode (low resolution)

```bash
python -m panzoom video -i ./photos -a music.wav --preview
```

---

## 🎵 Normalize an Audio Album

### Basic audio processing

```bash
python -m panzoom album -i ./audio -o ./ready_album
```

---

### Add metadata to album

```bash
python -m panzoom album -i ./audio --artist "My Band" --genre "Ambient"
```

---

## 🛠️ Generate Config File

### Create default YAML configuration

```bash
python -m panzoom init
```

> Generates a file: `panzoom.yaml`

---

## 📝 YAML Example

```yaml
video:
  fps: 60
  width: 1920
  height: 1080
  duration: 10
  crossfade: 2
  zoom_intensity: 0.08
  pan_intensity: 0.25
  crf: 18
  preset: cinematic

audio:
  loudness: -14
  sample_rate: 44100

artist: "Carnaverone Studio"
genre: "Ambient"
```

---

## 🎛️ Common Options

- `--preset cinematic`
- `--transition fade`
- `--zoom 0.12`
- `--pan-dir random`
- `--shuffle`
- `--preview`
- `--export youtube`
- `--watermark logo.png`

---

## 📦 Export Profiles

| Profile           | Resolution      | Use Case         |
|-------------------|------------------|------------------|
| youtube           | 1920×1080 60fps  | YouTube HD       |
| youtube4k         | 3840×2160 60fps  | YouTube 4K       |
| instagram_feed    | 1080×1080 30fps  | Instagram square |
| instagram_reels   | 1080×1920 30fps  | Reels / TikTok   |
| tiktok            | 1080×1920 30fps  | TikTok           |
| preview           | 640×360 15fps    | Fast preview     |

---

## 🎬 Presets

| Name      | Description                   |
|-----------|-------------------------------|
| cinematic | Smooth, 12s/image, fades      |
| fast      | 6s/image, quick pace          |
| slow      | 15s/image, calm motion        |
| dynamic   | Strong zoom/pan movement      |
| minimal   | Subtle, minimal motion        |

---

## 🗂 Project Structure

```
panzoom-slideshow/
├── panzoom/
│   ├── cli.py
│   ├── slideshow.py
│   ├── album.py
│   └── config.py
├── requirements.txt
├── panzoom.yaml
└── README.md
```

---

## ✅ Supported Formats

**Images:** PNG, JPG, JPEG, WebP, BMP, TIFF  
**Audio:** WAV, MP3, AAC, FLAC, OGG, M4A  
**Video Output:** MP4 (H.264 + AAC)

---

## 🤝 Contributing

We welcome issues, pull requests, and feature suggestions.

You can help by:

- Proposing new presets or export profiles  
- Suggesting new transitions  
- Improving CLI options or config structure

---

## 🔚 Conclusion

**PanZoom Slideshow** is made for creators who want high-quality, automated slideshows with full control from the command line.

Ideal for:

- 🎥 Video editors  
- 🎹 Music creators  
- 🧑‍💻 Automation & pipeline developers  

---

## 📄 License

MIT License  
© 2026 **Carnaverone Studio**
