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

# Site modules (lua/). The FMD2 release has none, so the image carries a copy;
# at each start the current ones are fetched from the FMD2 repository, and the
# copy already in place is kept when that fails (no internet, GitHub down).
if [ ! -d "$APP/lua/modules" ]; then
    echo "[fmd2] installing site modules from the image"
    cp -a "$DIST/lua" "$APP/"
fi
if [ "${FMD2_UPDATE_MODULES:-true}" = "true" ]; then
    TMP="$(mktemp -d)"
    if curl -fsSL --max-time 120 -o "$TMP/src.tar.gz" \
            https://codeload.github.com/dazedcat19/FMD2/tar.gz/refs/heads/master \
       && tar -xzf "$TMP/src.tar.gz" -C "$TMP" --strip-components=1 --wildcards '*/lua/*' \
       && [ -d "$TMP/lua/modules" ]; then
        cp -a "$TMP/lua/." "$APP/lua/"
        echo "[fmd2] site modules updated: $(ls "$APP/lua/modules" | wc -l) modules"
    else
        echo "[fmd2] could not fetch current site modules, keeping the installed ones"
    fi
    rm -rf "$TMP"
fi

mkdir -p "$APP/userdata"
if [ ! -f "$APP/userdata/settings.json" ]; then
    echo "[fmd2] writing default settings (save to staging as CBZ)"
    cp /defaults/fmd2-settings.json "$APP/userdata/settings.json"
fi

chown -R abc:abc "$APP" "$STAGING"
# The library (/library) is deliberately left alone: existing files keep
# their owner and permissions.
