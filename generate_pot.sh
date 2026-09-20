#!/usr/bin/env bash
#
# generate_pot.sh — Génère (ou met à jour) le template de traduction .pot
# du fork GCM à partir des chaînes marquées `_("...")` / `N_("...")` dans le
# code Python et des propriétés `translatable="yes"` du fichier .glade.
#
# Usage:
#   ./generate_pot.sh                  # génère po/gcm.pot
#   ./generate_pot.sh --update-po      # génère le .pot PUIS met à jour tous
#                                       # les po/*.po existants avec msgmerge
#   ./generate_pot.sh --check          # génère dans un fichier temporaire et
#                                       # affiche juste le diff avec le .pot
#                                       # actuel, sans rien écraser (CI-friendly)
#
# Prérequis : le paquet `gettext` (fournit xgettext, msgmerge, msgcat).
#   sudo dnf install gettext      # Rocky/Fedora
#   sudo apt install gettext      # Debian/Ubuntu
#
# Conçu pour tourner depuis la racine du dépôt (là où se trouve
# gnome_connection_manager.py) ou être appelé depuis n'importe où : le
# script se repositionne sur son propre répertoire.

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration — à adapter si besoin
# ---------------------------------------------------------------------------
PACKAGE_NAME="GNOME Connection Manager"
PACKAGE_VERSION="$(date +%Y.%m.%d)"          # pas de numéro de version formel dans ce fork
COPYRIGHT_HOLDER="Mathilde Deuscher"
BUGS_ADDRESS=""                               # ex. "https://github.com/<toi>/gcm-fork/issues"

PO_DIR="po"
POTFILES_IN="${PO_DIR}/POTFILES.in"
OUTPUT_POT="${PO_DIR}/gcm.pot"

# Fichiers sources à scanner. On liste explicitement plutôt que `*.py`
# aveugle pour exclure les scripts de dev ponctuels (analyse/migration de
# code) qui n'appartiennent pas à l'application livrée et ne doivent pas
# polluer le template de traduction.
PYTHON_SOURCES=(
    "gnome_connection_manager.py"
    "widgets.py"
    "utils.py"
    "models.py"
    "urlregex.py"
    "key_picker_dialog.py"
    "ssh_config_editor.py"
    "ssh_config_parser.py"
    "ssh_key_manager_dialog.py"
    "ssh_migrate_gcm.py"
)
GLADE_SOURCES=(
    "gnome-connection-manager.glade"
)

# Mots-clés marquant une chaîne traduisible dans le code Python.
# `_`  : gettext direct (gettext.gettext), utilisé partout dans ce projet.
# `N_` : marquage différé (ngettext-style "noop"), pas utilisé actuellement
#        mais gardé par précaution si introduit plus tard.
KEYWORDS=(--keyword=_ --keyword=N_)

# ---------------------------------------------------------------------------
# Résolution des chemins
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if ! command -v xgettext >/dev/null 2>&1; then
    echo "Erreur : xgettext introuvable. Installe le paquet 'gettext' (voir en-tête du script)." >&2
    exit 1
fi

mkdir -p "${PO_DIR}"

# ---------------------------------------------------------------------------
# Vérifie que tous les fichiers déclarés existent réellement (évite un .pot
# tronqué silencieusement si un fichier a été renommé/déplacé sans mettre à
# jour ce script).
# ---------------------------------------------------------------------------
missing=0
for f in "${PYTHON_SOURCES[@]}" "${GLADE_SOURCES[@]}"; do
    if [[ ! -f "${f}" ]]; then
        echo "Attention : fichier source introuvable, ignoré : ${f}" >&2
        missing=1
    fi
done
if [[ "${missing}" -eq 1 ]]; then
    echo "  (vérifie PYTHON_SOURCES/GLADE_SOURCES en tête de script)" >&2
fi

# ---------------------------------------------------------------------------
# Génère po/POTFILES.in — utile pour que les traducteurs (et les outils type
# Poedit/Weblate) sachent quels fichiers sont couverts, et pour que ce script
# reste diffable/auditable dans git indépendamment du .pot lui-même.
# ---------------------------------------------------------------------------
{
    echo "# Généré par generate_pot.sh — NE PAS ÉDITER À LA MAIN (regénérer via le script)"
    for f in "${PYTHON_SOURCES[@]}" "${GLADE_SOURCES[@]}"; do
        [[ -f "${f}" ]] && echo "${f}"
    done
} > "${POTFILES_IN}"

# ---------------------------------------------------------------------------
# Extraction xgettext
# ---------------------------------------------------------------------------
# --from-code=UTF-8      : le code source est en UTF-8 (accents, emojis 🌐⚙…)
# --language non précisé : xgettext détecte Python vs Glade via l'extension
#                          de chaque fichier listé dans POTFILES.in (testé et
#                          validé — un seul appel suffit, pas besoin de
#                          fusionner deux .pot séparés).
# --sort-by-file          : ordre stable/diffable d'une génération à l'autre
#                          (plus lisible en review que l'ordre par défaut).
# --add-comments=TRANSLATORS: reprend les commentaires "# TRANSLATORS: ..."
#                          juste au-dessus d'un _(...) s'il y en a (aucun
#                          actuellement, mais gratuit et sans risque).
generate() {
    local target="$1"
    local extra_args=()
    if [[ -n "${BUGS_ADDRESS}" ]]; then
        extra_args+=(--msgid-bugs-address="${BUGS_ADDRESS}")
    fi
    xgettext \
        --from-code=UTF-8 \
        "${KEYWORDS[@]}" \
        --files-from="${POTFILES_IN}" \
        --sort-by-file \
        --add-comments=TRANSLATORS: \
        --package-name="${PACKAGE_NAME}" \
        --package-version="${PACKAGE_VERSION}" \
        --copyright-holder="${COPYRIGHT_HOLDER}" \
        "${extra_args[@]}" \
        --output="${target}"
}

# ---------------------------------------------------------------------------
# Modes d'exécution
# ---------------------------------------------------------------------------
MODE="${1:-}"

case "${MODE}" in
    --check)
        tmp_pot="$(mktemp --suffix=.pot)"
        trap 'rm -f "${tmp_pot}"' EXIT
        generate "${tmp_pot}"
        if [[ ! -f "${OUTPUT_POT}" ]]; then
            echo "Aucun ${OUTPUT_POT} existant — ce serait une première génération."
            n=$(grep -c '^msgid "' "${tmp_pot}")
            echo "${n} chaîne(s) seraient extraites."
            exit 0
        fi
        # Compare uniquement les msgid (ignore les métadonnées d'en-tête et
        # les numéros de ligne qui bougent à chaque commit, sans intérêt ici).
        diff \
            <(grep '^msgid "' "${OUTPUT_POT}" | sort -u) \
            <(grep '^msgid "' "${tmp_pot}" | sort -u) \
            && echo "Aucun changement de chaînes traduisibles." \
            || echo "^ Chaînes ajoutées (>) / supprimées (<) depuis ${OUTPUT_POT}."
        exit 0
        ;;
    --update-po)
        generate "${OUTPUT_POT}"
        echo "Généré : ${OUTPUT_POT} ($(grep -c '^msgid "' "${OUTPUT_POT}") chaîne(s))"
        shopt -s nullglob
        po_files=("${PO_DIR}"/*.po)
        shopt -u nullglob
        if [[ ${#po_files[@]} -eq 0 ]]; then
            echo "Aucun fichier .po existant dans ${PO_DIR}/ à mettre à jour."
        else
            for po in "${po_files[@]}"; do
                echo "Mise à jour de ${po} (msgmerge)…"
                msgmerge --update --backup=numbered --previous "${po}" "${OUTPUT_POT}"
            done
        fi
        ;;
    "")
        generate "${OUTPUT_POT}"
        echo "Généré : ${OUTPUT_POT} ($(grep -c '^msgid "' "${OUTPUT_POT}") chaîne(s))"
        ;;
    *)
        echo "Usage: $0 [--update-po|--check]" >&2
        exit 2
        ;;
esac
