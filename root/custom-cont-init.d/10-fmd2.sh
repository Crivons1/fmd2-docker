#!/bin/bash
# Runs as root at every container start, before the desktop session.
# FMD2 lives in /config/FMD2 (appdata) so settings, favourites, Lua modules
# and in-app updates all survive a container rebuild.
set -e

APP=/config/FMD2
DIST=/opt/fmd2-dist
STAGING="${STAGING_DIR:-/config/staging}"

mkdir -p "$APP" "$STAGING"

# Install on first start, or when the image carries a different FMD2 release
# than the one last installed. userdata/ is never part of the image copy.
if [ ! -f "$APP/fmd.exe" ] || ! cmp -s "$DIST/.image-version" "$APP/.image-version"; then
    echo "[fmd2] installing FMD2 $(cat "$DIST/.image-version") into $APP"
    cp -a "$DIST/." "$APP/"
fi

mkdir -p "$APP/userdata"
if [ ! -f "$APP/userdata/settings.json" ]; then
    echo "[fmd2] writing default settings (save to staging as CBZ)"
    cp /defaults/fmd2-settings.json "$APP/userdata/settings.json"
fi

chown -R abc:abc "$APP" "$STAGING"
# The library (/library) is deliberately left alone: existing files keep
# their owner and permissions.
