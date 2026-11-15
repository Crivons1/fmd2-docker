# FMD2 (Windows app) under Wine, shown in the browser through KasmVNC,
# plus a small organiser that files finished downloads into a manga library.
FROM ghcr.io/linuxserver/baseimage-kasmvnc:ubuntunoble

# FMD2 release to bake in. Override with: docker build --build-arg FMD2_VERSION=x.y.z.w
ARG FMD2_VERSION=2.0.34.5

ENV TITLE=FMD2 \
    HOME=/config \
    WINEARCH=win64 \
    WINEDEBUG=-all \
    WINEDLLOVERRIDES="mscoree,mshtml=" \
    STAGING_DIR=/config/staging \
    LIBRARY_DIR=/library

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y wine wine64 python3 p7zip-full curl ca-certificates && \
    curl -fsSL -o /tmp/fmd2.7z \
      "https://github.com/dazedcat19/FMD2/releases/download/${FMD2_VERSION}/fmd_${FMD2_VERSION}_x86_64-win64.7z" && \
    7z x -y -o/opt/fmd2-dist /tmp/fmd2.7z > /dev/null && \
    test -f /opt/fmd2-dist/fmd.exe && \
    # The release ships without site modules: take lua/ from the source tree.
    curl -fsSL -o /tmp/fmd2-src.tar.gz https://codeload.github.com/dazedcat19/FMD2/tar.gz/refs/heads/master && \
    tar -xzf /tmp/fmd2-src.tar.gz -C /opt/fmd2-dist --strip-components=1 --wildcards '*/lua/*' && \
    test -d /opt/fmd2-dist/lua/modules && \
    rm /tmp/fmd2-src.tar.gz && \
    rm -rf /opt/fmd2-dist/userdata /tmp/fmd2.7z && \
    echo "${FMD2_VERSION}" > /opt/fmd2-dist/.image-version && \
    apt-get purge -y p7zip-full && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY root/ /

# Restore exec bits (lost when the repo is checked out on Windows).
RUN chmod +x /custom-cont-init.d/10-fmd2.sh \
             /usr/local/bin/start-fmd2 \
             /usr/local/bin/fmd2-organiser \
             /etc/s6-overlay/s6-rc.d/svc-fmd2-organiser/run

VOLUME /config /library
EXPOSE 3000
