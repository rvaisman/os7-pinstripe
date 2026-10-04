#!/usr/bin/env bash
# Restore the settings saved by install.sh and remove the OS7 Pinstripe files.
set -euo pipefail

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
BACKUP="$DATA/os7-pinstripe/backup.env"
ID=OS7Pinstripe

plasma_js() {
  dbus-send --session --print-reply --dest=org.kde.plasmashell /PlasmaShell \
    org.kde.PlasmaShell.evaluateScript "string:$1" >/dev/null
}

set_or_delete() { # file group key value
  if [[ -n "$4" ]]; then kwriteconfig6 --file "$1" --group "$2" --key "$3" "$4"
  else kwriteconfig6 --file "$1" --group "$2" --key "$3" --delete; fi
}

if [[ -f "$BACKUP" ]]; then
  # shellcheck disable=SC1090
  source "$BACKUP"
  echo "→ Restoring window decoration and title font"
  set_or_delete kwinrc org.kde.kdecoration2 library "$DECO_LIB"
  set_or_delete kwinrc org.kde.kdecoration2 theme "$DECO_THEME"
  set_or_delete kwinrc org.kde.kdecoration2 ButtonsOnLeft "$BTN_LEFT"
  set_or_delete kwinrc org.kde.kdecoration2 ButtonsOnRight "$BTN_RIGHT"
  set_or_delete kdeglobals WM activeFont "$TITLE_FONT"
  dbus-send --session --type=method_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure

  echo "→ Restoring color scheme and Plasma Style"
  plasma-apply-colorscheme "${COLORS:-BreezeLight}" >/dev/null || true
  plasma-apply-desktoptheme "${PLASMA_THEME:-default}" >/dev/null || true

  if [[ -n "$WALLPAPER_IMG" ]]; then
    echo "→ Restoring wallpaper"
    plasma_js "desktops().forEach(function(d){d.currentConfigGroup=['Wallpaper','org.kde.image','General'];d.writeConfig('Image','$WALLPAPER_IMG');d.writeConfig('FillMode',${WALLPAPER_FILL:-2});d.reloadConfig();})"
  fi
  if [[ -n "$PANEL_LOC" ]]; then
    echo "→ Restoring panel position"
    plasma_js "var l='$PANEL_LOC'.split(','); panels().forEach(function(p,i){ if(l[i]) p.location=l[i]; })"
  fi
  rm -f "$BACKUP"
else
  echo "No backup found: only the theme files will be removed."
  echo "If the theme is still selected, pick another one in System Settings first."
fi

echo "→ Removing theme files"
rm -rf "$DATA/aurorae/themes/$ID" "$DATA/aurorae/themes/$ID-"* \
       "$DATA/plasma/desktoptheme/$ID" "$DATA/wallpapers/$ID" "$DATA/os7-pinstripe"
rm -f "$DATA/color-schemes/$ID.colors"
echo "Done."
