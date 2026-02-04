# AGENTS.md - PanZoom Slideshow

Documentation pour les agents IA travaillant sur ce projet.

## 📁 Structure du projet

```
panzoom-slideshow/
├── panzoom/                # Module Python principal
│   ├── __init__.py         # Version et métadonnées
│   ├── __main__.py         # Point d'entrée (python -m panzoom)
│   ├── cli.py              # Interface ligne de commande (argparse)
│   ├── config.py           # Configuration, presets, profils export
│   ├── slideshow.py        # Génération vidéo Ken Burns
│   └── album.py            # Traitement audio (normalisation)
├── panzoom.yaml            # Configuration par défaut
├── requirements.txt        # Dépendances Python
├── run.sh                  # Script shell legacy
├── prepare_album.sh        # Script shell legacy
└── README.md               # Documentation utilisateur
```

## 🔧 Dépendances

- **Python** >= 3.8
- **FFmpeg** >= 6.x (doit être installé sur le système)
- **PyYAML** >= 6.0

## 📦 Installation

```bash
# Installer les dépendances Python
pip install -r requirements.txt

# Vérifier FFmpeg
ffmpeg -version
```

## 🚀 Commandes d'exécution

```bash
# Aide générale
python -m panzoom --help

# Générer une vidéo slideshow
python -m panzoom video -a music.wav -i ./photos

# Traiter un album audio
python -m panzoom album -i ./audio -o ./export

# Créer un fichier de configuration
python -m panzoom init

# Lister les options disponibles
python -m panzoom presets      # Presets de style
python -m panzoom transitions  # Transitions disponibles
python -m panzoom exports      # Profils d'export
```

## 🏗️ Architecture du code

### config.py
- `VideoConfig` : Dataclass pour les paramètres vidéo
- `AudioConfig` : Dataclass pour les paramètres audio
- `WatermarkConfig` : Configuration du watermark
- `TitleConfig` : Configuration des titres
- `PRESETS` : Dict des presets (fast, cinematic, slow, dynamic, minimal)
- `TRANSITIONS` : Dict des 25+ transitions FFmpeg
- `EXPORT_PROFILES` : Dict des profils (youtube, instagram, tiktok...)

### slideshow.py
- `SlideshowGenerator` : Classe principale de génération vidéo
- `ProgressInfo` : Dataclass pour le suivi de progression
- Méthodes clés : `generate()`, `generate_preview()`, `_build_filter_complex()`

### cli.py
- `cmd_video()` : Commande de génération vidéo
- `cmd_album()` : Commande de traitement audio
- `cmd_transitions()` : Liste les transitions
- `cmd_exports()` : Liste les profils d'export
- `main()` : Point d'entrée avec argparse

### album.py
- `AlbumProcessor` : Traitement et normalisation audio
- Génère metadata.txt et fichier CUE

## 🎨 Style de code

- **Dataclasses** pour toutes les configurations
- **argparse** pour le CLI
- **Type hints** sur les fonctions principales
- **Docstrings** en anglais
- **Messages utilisateur** en français
- **Pas de dépendances lourdes** (pas de click, pas de rich)

## ⚡ Options CLI importantes

### Commande `video`
| Option | Description |
|--------|-------------|
| `--preview` | Aperçu rapide basse qualité |
| `--export` | Profil d'export (youtube, instagram_reels, tiktok...) |
| `--preset` | Preset de style (cinematic, fast, slow...) |
| `--transition` | Type de transition (fade, wipeleft, random...) |
| `--shuffle` | Ordre aléatoire des images |
| `--watermark` | Fichier image du logo |
| `--zoom` / `--pan` | Intensité des effets (0.0-1.0) |

## 🧪 Tester le programme

```bash
# Test basique (nécessite images PNG et music.wav)
python -m panzoom video -a music.wav --preview

# Test avec toutes les options
python -m panzoom video -a music.wav \
  --export youtube \
  --preset cinematic \
  --shuffle \
  --transition random
```

## 📝 Notes

- FFmpeg doit supporter le filtre `xfade` (FFmpeg 4.3+)
- Les images sont redimensionnées à 2x puis zoomées pour l'effet Ken Burns
- Le mode preview génère en 640x360 @ 15fps pour un rendu rapide
