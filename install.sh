#!/usr/bin/env bash
# Install and apply the OS7 Pinstripe theme for KDE Plasma 6.
# Run ./install.sh --help for options.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD="$DIR/build"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
BACKUP="$DATA/os7-pinstripe/backup.env"
ID=OS7Pinstripe

SCALE=2
WALLPAPER=gray
PANEL_TOP=0
COPY_ONLY=0
SET_FONT=1

usage() {
  cat <<EOF
Usage: ./install.sh [options]

  --scale 1|2|3        Title bar size: 1 = 19 px (original), 2 = 38 px (default), 3 = 57 px
  --wallpaper NAME     bw | gray (default) | violet | none
  --panel-top          Move your panel(s) to the top edge, like a menu bar
  --no-font            Do not change the window title font
  --copy-only          Only copy the files; choose them yourself in System Settings
  -h, --help           Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scale) SCALE="${2:-}"; shift ;;
    --wallpaper) WALLPAPER="${2:-}"; shift ;;
    --panel-top) PANEL_TOP=1 ;;
    --no-font) SET_FONT=0 ;;
    --copy-only) COPY_ONLY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
  shift
done

case "$SCALE" in 1) FONT_PT=13 ;; 2) FONT_PT=18 ;; 3) FONT_PT=26 ;; *) echo "--scale must be 1, 2 or 3"; exit 1 ;; esac
case "$WALLPAPER" in bw|gray|violet|none) ;; *) echo "--wallpaper must be bw, gray, violet or none"; exit 1 ;; esac
DECO="$ID"; [[ $SCALE != 1 ]] && DECO="$ID-${SCALE}x"

for cmd in python3 kwriteconfig6 kreadconfig6 dbus-send plasma-apply-colorscheme plasma-apply-desktoptheme; do
  command -v "$cmd" >/dev/null || { echo "Missing required command: $cmd (is this a KDE Plasma 6 session?)"; exit 1; }
done

python3 "$DIR/generate.py" --scale "$SCALE"

plasma_js() {
  dbus-send --session --print-reply --dest=org.kde.plasmashell /PlasmaShell \
    org.kde.PlasmaShell.evaluateScript "string:$1" | sed -n 's/^ *string "\(.*\)"$/\1/p'
}

echo "→ Copying files to $DATA"
mkdir -p "$DATA/aurorae/themes" "$DATA/color-schemes" "$DATA/plasma/desktoptheme" "$DATA/wallpapers/$ID"
rm -rf "$DATA/aurorae/themes/$ID" "$DATA/aurorae/themes/$ID-"* "$DATA/plasma/desktoptheme/$ID"
cp -r "$BUILD/aurorae/$ID"* "$DATA/aurorae/themes/"
cp "$BUILD/color-schemes/$ID.colors" "$DATA/color-schemes/"
cp -r "$BUILD/desktoptheme/$ID" "$DATA/plasma/desktoptheme/"
cp "$BUILD/wallpapers/"*.png "$DATA/wallpapers/$ID/"
rm -rf "$HOME/.cache/plasma-svgelements"* "$HOME/.cache/plasma_theme_"* 2>/dev/null || true

if [[ $COPY_ONLY == 1 ]]; then
  echo "Done. Pick the theme parts in System Settings (see README)."
  exit 0
fi

# Back up the current settings (first run only)
if [[ ! -f "$BACKUP" ]]; then
  echo "→ Backing up your current settings to $BACKUP"
  mkdir -p "$(dirname "$BACKUP")"
  {
    printf 'DECO_LIB=%q\n'     "$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key library)"
    printf 'DECO_THEME=%q\n'   "$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme)"
    printf 'BTN_LEFT=%q\n'     "$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft)"
    printf 'BTN_RIGHT=%q\n'    "$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight)"
    printf 'TITLE_FONT=%q\n'   "$(kreadconfig6 --file kdeglobals --group WM --key activeFont)"
    printf 'COLORS=%q\n'       "$(kreadconfig6 --file kdeglobals --group General --key ColorScheme)"
    printf 'PLASMA_THEME=%q\n' "$(kreadconfig6 --file plasmarc --group Theme --key name)"
    printf 'WALLPAPER_IMG=%q\n' "$(plasma_js 'var d=desktops()[0]; d.currentConfigGroup=["Wallpaper","org.kde.image","General"]; print(d.readConfig("Image"))')"
    printf 'WALLPAPER_FILL=%q\n' "$(plasma_js 'var d=desktops()[0]; d.currentConfigGroup=["Wallpaper","org.kde.image","General"]; print(d.readConfig("FillMode"))')"
    printf 'PANEL_LOC=%q\n'    "$(plasma_js 'print(panels().map(function(p){return p.location}).join(","))')"
  } > "$BACKUP"
fi

echo "→ Window decoration: $DECO"
LIB=org.kde.kwin.aurorae
for d in /usr/lib64 /usr/lib /usr/lib/x86_64-linux-gnu /usr/lib/aarch64-linux-gnu; do
  [[ -e "$d/qt6/plugins/org.kde.kdecoration3/org.kde.kwin.aurorae.v2.so" ]] && LIB=org.kde.kwin.aurorae.v2
done
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library "$LIB"
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme "__aurorae__svg__$DECO"
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft X
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight AI

if [[ $SET_FONT == 1 ]]; then
  if fc-list 2>/dev/null | grep -qi 'ChicagoFLF'; then
    echo "→ Title font: ChicagoFLF $FONT_PT pt"
    kwriteconfig6 --file kdeglobals --group WM --key activeFont "ChicagoFLF,$FONT_PT,-1,5,400,0,0,0,0,0,0,0,0,0,0,1,Regular"
  else
    echo "  (ChicagoFLF font not found: keeping your title font. See README → Recommended font.)"
  fi
fi
dbus-send --session --type=method_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure

echo "→ Color scheme"
plasma-apply-colorscheme "$ID" >/dev/null || true

echo "→ Plasma Style"
plasma-apply-desktoptheme "$ID" >/dev/null || true

if [[ $WALLPAPER != none ]]; then
  echo "→ Wallpaper: $WALLPAPER pattern"
  IMG="file://$DATA/wallpapers/$ID/pattern-$WALLPAPER.png"
  plasma_js "desktops().forEach(function(d){d.wallpaperPlugin='org.kde.image';d.currentConfigGroup=['Wallpaper','org.kde.image','General'];d.writeConfig('Image','$IMG');d.writeConfig('FillMode',3);d.reloadConfig();})" >/dev/null
fi

if [[ $PANEL_TOP == 1 ]]; then
  echo "→ Moving panel(s) to the top edge"
  plasma_js "panels().forEach(function(p){p.location='top';})" >/dev/null
fi

echo
echo "Done! To restore your previous look, run: $DIR/uninstall.sh"
