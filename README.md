# PanZoom Slideshow

**Générateur professionnel de vidéos Ken Burns** - Créez des diaporamas cinématiques avec effets de pan et zoom à partir de vos images et musique.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FFmpeg](https://img.shields.io/badge/FFmpeg-6.x-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Fonctionnalités

- 🎬 **Effet Ken Burns** - Pan et zoom fluides sur chaque image
- 🔀 **Ordre aléatoire** - Mélangez vos images automatiquement
- ⚡ **Presets** - Configurations prêtes à l'emploi (cinematic, fast, slow...)
- 🎚️ **Contrôle total** - Ajustez vitesse, zoom, pan, qualité
- 🎵 **Traitement audio** - Normalisation et préparation d'albums
- 📝 **Configuration YAML** - Sauvegardez vos paramètres préférés

### 🆕 Nouvelles fonctionnalités v1.1

- 👁️ **Mode Preview** - Aperçu rapide basse qualité avant le rendu final
- 📊 **Barre de progression** - Suivez l'avancement en temps réel avec ETA
- 🎭 **25+ Transitions** - Fade, wipe, slide, circle, dissolve, pixelize...
- 📱 **Profils d'export** - YouTube, Instagram, TikTok, Facebook, Twitter
- 🏷️ **Watermark** - Ajoutez votre logo en filigrane
- 📝 **Titres** - Cartes titre avec sous-titres

## 📦 Installation

### Prérequis

- Python 3.8+
- FFmpeg 6.x

```bash
# Cloner le dépôt
git clone <repo-url>
cd panzoom-slideshow

# Installer les dépendances Python
pip install -r requirements.txt

# Vérifier FFmpeg
ffmpeg -version
```

## 🚀 Utilisation rapide

### Créer une vidéo

```bash
# Usage basique
python -m panzoom video -a music.wav -i ./photos

# Avec preset cinématique
python -m panzoom video -a music.wav --preset cinematic

# Images aléatoires + zoom personnalisé
python -m panzoom video -a music.wav --shuffle --zoom 0.12

# Preview rapide (basse qualité)
python -m panzoom video -a music.wav --preview

# Export pour Instagram Reels
python -m panzoom video -a music.wav --export instagram_reels

# Avec transition et watermark
python -m panzoom video -a music.wav --transition wipeleft --watermark logo.png
```

### Préparer un album audio

```bash
# Normaliser des fichiers audio
python -m panzoom album -i ./audio -o ./export

# Avec métadonnées personnalisées
python -m panzoom album -i ./audio --artist "Mon Groupe" --genre "Electronic"
```

### Lister les options disponibles

```bash
python -m panzoom transitions  # Voir toutes les transitions
python -m panzoom exports      # Voir les profils d'export
python -m panzoom presets      # Voir les presets
```

## 📖 Guide complet

### Commande `video` - Génération de slideshow

```bash
python -m panzoom video [OPTIONS]
```

#### Options principales

| Option | Description | Défaut |
|--------|-------------|--------|
| `-i, --images` | Dossier des images | `.` (actuel) |
| `-a, --audio` | Fichier audio (requis) | - |
| `-o, --output` | Fichier de sortie | `slideshow.mp4` |
| `--preset` | Preset de configuration | - |

#### Options de timing

| Option | Description | Défaut |
|--------|-------------|--------|
| `-d, --duration` | Durée par image (secondes) | 10 |
| `-x, --crossfade` | Durée du fondu (secondes) | 2 |
| `-f, --fps` | Images par seconde | 60 |

#### Options d'effet Ken Burns

| Option | Description | Défaut |
|--------|-------------|--------|
| `--zoom` | Intensité du zoom (0.0 - 0.2) | 0.08 |
| `--pan` | Intensité du pan (0.0 - 1.0) | 0.25 |
| `--zoom-dir` | Direction: `in`, `out`, `alternate`, `random` | `alternate` |
| `--pan-dir` | Direction: `left`, `right`, `alternate`, `random` | `alternate` |

#### Options d'ordre des images

| Option | Description |
|--------|-------------|
| `--shuffle` | Ordre aléatoire |
| `--reverse` | Ordre inversé |

#### Options de qualité

| Option | Description | Défaut |
|--------|-------------|--------|
| `-w, --width` | Largeur vidéo | 1920 |
| `-g, --height` | Hauteur vidéo | 1080 |
| `-q, --quality` | CRF (0-51, plus bas = meilleur) | 18 |

#### Transitions

| Option | Description |
|--------|-------------|
| `--transition` | Type de transition (`fade`, `wipeleft`, `dissolve`, `random`...) |

Voir toutes les transitions : `python -m panzoom transitions`

#### Watermark (logo)

| Option | Description |
|--------|-------------|
| `--watermark` | Fichier image du logo (PNG) |
| `--watermark-pos` | Position: `top-left`, `top-right`, `bottom-left`, `bottom-right`, `center` |
| `--watermark-opacity` | Opacité (0.0-1.0) |
| `--watermark-scale` | Taille relative (0.0-1.0) |

#### Mode preview

| Option | Description |
|--------|-------------|
| `--preview` | Génère un aperçu rapide (640x360, 15fps) |

### Presets disponibles

```bash
python -m panzoom presets
```

| Preset | Description |
|--------|-------------|
| `fast` | Rapide, 6s/image, 30fps |
| `cinematic` | Cinématique, 12s/image, transitions longues |
| `slow` | Lent et contemplatif, 15s/image |
| `dynamic` | Dynamique avec zoom prononcé |
| `minimal` | Effets subtils |

### Profils d'export

```bash
python -m panzoom exports
```

| Profile | Résolution | Description |
|---------|------------|-------------|
| `youtube` | 1920x1080 60fps | YouTube HD |
| `youtube4k` | 3840x2160 60fps | YouTube 4K |
| `instagram_feed` | 1080x1080 30fps | Instagram carré |
| `instagram_reels` | 1080x1920 30fps | Instagram/TikTok vertical |
| `tiktok` | 1080x1920 30fps | TikTok vertical |
| `facebook` | 1280x720 30fps | Facebook |
| `twitter` | 1280x720 30fps | Twitter/X |
| `preview` | 640x360 15fps | Aperçu rapide |

### Exemples avancés

```bash
# Style cinématique avec images aléatoires
python -m panzoom video -a music.wav --preset cinematic --shuffle

# Export Instagram avec transition circulaire
python -m panzoom video -a music.wav --export instagram_reels --transition circleopen

# Zoom fort + pan aléatoire + transitions aléatoires
python -m panzoom video -a music.wav --zoom 0.15 --pan 0.4 --pan-dir random --transition random

# Avec watermark
python -m panzoom video -a music.wav --watermark logo.png --watermark-pos bottom-right --watermark-opacity 0.5

# Preview rapide avant rendu final
python -m panzoom video -a music.wav --preview -o preview.mp4

# Export 4K
python -m panzoom video -a music.wav -w 3840 -g 2160 --fps 30

# Utiliser un fichier de config
python -m panzoom video -a music.wav -c panzoom.yaml
```

### Commande `album` - Traitement audio

```bash
python -m panzoom album [OPTIONS]
```

| Option | Description | Défaut |
|--------|-------------|--------|
| `-i, --input` | Dossier source | `.` |
| `-o, --output` | Dossier de sortie | `export_ready` |
| `--artist` | Nom de l'artiste | Carnaverone Studio |
| `--genre` | Genre musical | Instrumental |
| `-l, --loudness` | Niveau LUFS cible | -14 |
| `-r, --sample-rate` | Taux d'échantillonnage | 44100 |

### Commande `init` - Créer un fichier de config

```bash
python -m panzoom init              # Crée panzoom.yaml
python -m panzoom init -o config.yaml  # Nom personnalisé
```

## ⚙️ Configuration YAML

Créez un fichier `panzoom.yaml` pour sauvegarder vos paramètres :

```yaml
video:
  duration: 10.0
  crossfade: 2.0
  fps: 60
  width: 1920
  height: 1080
  
  # Effet Ken Burns
  zoom_intensity: 0.08
  pan_intensity: 0.25
  zoom_direction: alternate  # in, out, alternate, random
  pan_direction: alternate   # left, right, alternate, random
  
  # Ordre des images
  shuffle: false
  reverse: false
  
  # Qualité
  crf: 18
  preset: slow

audio:
  loudness: -14.0
  sample_rate: 44100
  remove_silence: true

artist: "Mon Studio"
genre: "Ambient"
```

## 📁 Structure du projet

```
panzoom-slideshow/
├── panzoom/                # Module Python principal
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              # Interface en ligne de commande
│   ├── config.py           # Gestion de configuration
│   ├── slideshow.py        # Génération vidéo
│   └── album.py            # Traitement audio
├── panzoom.yaml            # Configuration par défaut
├── requirements.txt        # Dépendances Python
├── run.sh                  # Script shell (legacy)
├── prepare_album.sh        # Script shell (legacy)
└── README.md
```

## 🔧 Scripts shell (legacy)

Les scripts shell originaux sont toujours disponibles :

```bash
./run.sh --help
./prepare_album.sh --help
```

## 📝 Formats supportés

**Images:** PNG, JPG, JPEG, WebP, BMP, TIFF

**Audio:** WAV, MP3, AAC, FLAC, OGG, M4A

**Sortie:** MP4 (H.264 + AAC)

## 🤝 Contribution

Les contributions sont bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

 - Carnaverone Studio
