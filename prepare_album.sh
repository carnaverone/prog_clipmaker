#!/bin/bash
#
# Prepare Album - Normalise et organise les fichiers audio
# Renomme, normalise le volume et supprime les silences
#

set -o pipefail

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration par defaut
OUTPUT_DIR="${OUTPUT_DIR:-export_ready}"
ARTIST="${ARTIST:-Carnaverone Studio}"
GENRE="${GENRE:-Instrumental / Celtic}"
LOUDNESS="${LOUDNESS:--14}"
SAMPLE_RATE="${SAMPLE_RATE:-44100}"

show_help() {
    cat << 'EOF'
Prepare Album - Audio Normalizer

Usage: ./prepare_album.sh [OPTIONS]

Options:
  -o, --output DIR      Dossier de sortie (defaut: export_ready)
  -a, --artist NAME     Nom de l'artiste (defaut: Carnaverone Studio)
  -g, --genre GENRE     Genre musical (defaut: Instrumental / Celtic)
  -l, --loudness DB     Niveau LUFS cible (defaut: -14)
  -r, --rate HZ         Taux d'echantillonnage (defaut: 44100)
  --help                Afficher cette aide

Exemples:
  ./prepare_album.sh
  ./prepare_album.sh -a "Mon Artiste" -g "Electronic"
  ./prepare_album.sh -o mon_album -l -16

EOF
    exit 0
}

# Parser les arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)    OUTPUT_DIR="$2"; shift 2 ;;
        -a|--artist)    ARTIST="$2"; shift 2 ;;
        -g|--genre)     GENRE="$2"; shift 2 ;;
        -l|--loudness)  LOUDNESS="$2"; shift 2 ;;
        -r|--rate)      SAMPLE_RATE="$2"; shift 2 ;;
        --help)         show_help ;;
        *)              echo -e "${RED}Option inconnue: $1${NC}"; show_help ;;
    esac
done

# Repertoire de travail = dossier du script
cd "$(dirname "$0")" || exit 1

echo -e "${BLUE}Prepare Album - Audio Normalizer${NC}"
echo "==================================="

# Verifier ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}Erreur: ffmpeg n'est pas installe${NC}"
    exit 1
fi

# Verifier qu'il y a des fichiers WAV
WAV_COUNT=$(ls -1 *.wav 2>/dev/null | wc -l)
if [[ $WAV_COUNT -eq 0 ]]; then
    echo -e "${RED}Erreur: Aucun fichier WAV trouve dans le dossier${NC}"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} $WAV_COUNT fichiers WAV trouves"
echo -e "${YELLOW}[CONFIG]${NC} Artiste: $ARTIST"
echo -e "${YELLOW}[CONFIG]${NC} Genre: $GENRE"
echo -e "${YELLOW}[CONFIG]${NC} Loudness: ${LOUDNESS} LUFS"
echo ""

mkdir -p "$OUTPUT_DIR"

n=1
errors=0
for f in *.wav; do
    filename=$(basename "$f")
    base="${filename%.*}"

    # Ajout de zero si < 10
    num=$(printf "%02d" "$n")

    # Nettoyage du nom
    cleanname=$(echo "$base" | sed 's/_/ /g' | sed 's/  */ /g' | sed 's/^ *//;s/ *$//')

    echo -e "${BLUE}[$num]${NC} $cleanname"

    # Traitement : normalisation + suppression silence + conversion WAV stereo
    if ffmpeg -hide_banner -loglevel warning -i "$f" -af "loudnorm=I=${LOUDNESS}:LRA=7:TP=-1.5,silenceremove=start_periods=1:start_duration=0.2:start_threshold=-50dB:stop_periods=1:stop_duration=0.2:stop_threshold=-50dB" -ar "$SAMPLE_RATE" -ac 2 -y "${OUTPUT_DIR}/${num} - ${cleanname}.wav" 2>/dev/null; then
        echo -e "      ${GREEN}OK${NC}"
    else
        echo -e "      ${RED}ERREUR${NC}"
        ((errors++))
    fi

    ((n++))
done

# Creation d'un fichier metadata
echo ""
echo -e "${BLUE}Creation des metadonnees...${NC}"

ALBUM_NAME=$(basename "$PWD")
{
    echo "ALBUM=$ALBUM_NAME"
    echo "ARTIST=$ARTIST"
    echo "YEAR=$(date +%Y)"
    echo "GENRE=$GENRE"
    echo ""
    echo "TRACKLIST:"
    ls "$OUTPUT_DIR"/*.wav 2>/dev/null | sort | while read -r track; do
        name=$(basename "$track" .wav)
        echo "- $name"
    done
} > "$OUTPUT_DIR/metadata.txt"

echo ""
if [[ $errors -eq 0 ]]; then
    echo -e "${GREEN}Album pret dans $OUTPUT_DIR/${NC}"
    echo "  - $((n-1)) pistes traitees"
    echo "  - Metadonnees: $OUTPUT_DIR/metadata.txt"
else
    echo -e "${YELLOW}Album cree avec $errors erreur(s)${NC}"
fi
