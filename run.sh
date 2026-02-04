#!/bin/bash
#
# Pan-Zoom Slideshow Generator
# Cree une video Ken Burns a partir d'images PNG et d'une piste audio
#

set -o pipefail

# Configuration par defaut
D="${DURATION:-12}"           # Duree par image (secondes)
X="${CROSSFADE:-2.0}"         # Duree du fondu enchaine (secondes)
FPS="${FPS:-60}"              # Images par seconde
W="${WIDTH:-1920}"            # Largeur video
H="${HEIGHT:-1080}"           # Hauteur video
P="${PAN_AMOUNT:-0.25}"       # Amplitude du pan (0-1)
OUT="${OUTPUT:-slideshow.mp4}" # Fichier de sortie
AUD="${AUDIO:-music.wav}"     # Fichier audio

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    cat << 'EOF'
Pan-Zoom Slideshow Generator

Usage: ./run.sh [OPTIONS]

Options:
  -d, --duration SEC    Duree par image (defaut: 12)
  -x, --crossfade SEC   Duree du fondu (defaut: 2.0)
  -f, --fps NUM         Images par seconde (defaut: 60)
  -w, --width PX        Largeur video (defaut: 1920)
  -g, --height PX       Hauteur video (defaut: 1080)
  -p, --pan AMOUNT      Amplitude du pan 0-1 (defaut: 0.25)
  -o, --output FILE     Fichier de sortie (defaut: slideshow.mp4)
  -a, --audio FILE      Fichier audio (defaut: music.wav)
  --help                Afficher cette aide

Exemples:
  ./run.sh                              # Utilise les valeurs par defaut
  ./run.sh -d 8 -o ma_video.mp4         # 8 sec/image, sortie personnalisee
  ./run.sh --audio musique.wav --fps 30 # Audio et FPS personnalises

Variables d'environnement (alternative aux options):
  DURATION, CROSSFADE, FPS, WIDTH, HEIGHT, PAN_AMOUNT, OUTPUT, AUDIO

EOF
    exit 0
}

# Parser les arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--duration)  D="$2"; shift 2 ;;
        -x|--crossfade) X="$2"; shift 2 ;;
        -f|--fps)       FPS="$2"; shift 2 ;;
        -w|--width)     W="$2"; shift 2 ;;
        -g|--height)    H="$2"; shift 2 ;;
        -p|--pan)       P="$2"; shift 2 ;;
        -o|--output)    OUT="$2"; shift 2 ;;
        -a|--audio)     AUD="$2"; shift 2 ;;
        --help)         show_help ;;
        *)              echo -e "${RED}Option inconnue: $1${NC}"; show_help ;;
    esac
done

echo -e "${BLUE}Pan-Zoom Slideshow Generator${NC}"
echo "================================"

# Verifier les dependances
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}Erreur: ffmpeg n'est pas installe${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Erreur: python3 n'est pas installe${NC}"
    exit 1
fi

# Verifier le fichier audio
if [[ ! -f "$AUD" ]]; then
    echo -e "${RED}Erreur: Fichier audio '$AUD' introuvable${NC}"
    exit 1
fi

# Lister les images
TMPFILE="/tmp/imgs_$$.txt"
ls -1 *.png 2>/dev/null | sort > "$TMPFILE"

IMG_COUNT=$(wc -l < "$TMPFILE")
if [[ $IMG_COUNT -eq 0 ]]; then
    echo -e "${RED}Erreur: Aucune image PNG trouvee dans le dossier${NC}"
    rm -f "$TMPFILE"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} $IMG_COUNT images trouvees"
echo -e "${GREEN}[OK]${NC} Audio: $AUD"
echo -e "${YELLOW}[CONFIG]${NC} ${D}s/image, ${FPS}fps, ${W}x${H}"
echo ""

# Generer et executer la commande FFmpeg
python3 - "$D" "$X" "$FPS" "$W" "$H" "$P" "$OUT" "$AUD" "$TMPFILE" <<'PYTHON_SCRIPT'
import shlex, subprocess, sys

D = float(sys.argv[1])
X = float(sys.argv[2])
FPS = int(sys.argv[3])
W = int(sys.argv[4])
H = int(sys.argv[5])
P = float(sys.argv[6])
OUT = sys.argv[7]
AUD = sys.argv[8]
TMPFILE = sys.argv[9]

imgs = [l.strip() for l in open(TMPFILE) if l.strip()]
NF = max(2, int(round(D * FPS)))  # frames par image

cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", "-stats"]
for f in imgs:
    cmd += ["-loop", "1", "-t", str(D), "-i", f]
cmd += ["-i", AUD]

fg = []
for i in range(len(imgs)):
    lr = (i % 2 == 0)   # L->R, puis R->L
    zin = (i % 2 == 0)  # IN, puis OUT

    frac = f"(on/{NF-1})"
    zexpr = f"(1+0.06*{frac})" if zin else f"(1.06-0.06*{frac})"
    xexpr = f"(iw-ow)*({P}*{frac})" if lr else f"(iw-ow)*({P}*(1-{frac}))"
    yexpr = f"(ih-oh)*0.22"

    fg.append(
        f"[{i}:v]"
        f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
        f"zoompan=z='{zexpr}':x='{xexpr}':y='{yexpr}':d={NF}:s={W}x{H}:fps={FPS},"
        f"format=yuv420p[v{i}]"
    )

cur = "[v0]"
t = D - X
for i in range(1, len(imgs)):
    fg.append(f"{cur}[v{i}]xfade=transition=fade:duration={X}:offset={t}[x{i}]")
    cur = f"[x{i}]"
    t += D - X

fg.append(f"{cur}format=yuv420p[v]")

cmd += [
    "-filter_complex", ";".join(fg),
    "-map", "[v]", "-map", f"{len(imgs)}:a",
    "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "320k",
    "-shortest", OUT
]

print("Generation en cours...")
result = subprocess.run(cmd)
sys.exit(result.returncode)
PYTHON_SCRIPT

EXIT_CODE=$?
rm -f "$TMPFILE"

if [[ $EXIT_CODE -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}Video creee avec succes: $OUT${NC}"
    if command -v du &> /dev/null; then
        SIZE=$(du -h "$OUT" | cut -f1)
        echo "   Taille: $SIZE"
    fi
else
    echo -e "${RED}Erreur lors de la generation de la video${NC}"
    exit $EXIT_CODE
fi
