# fmd2-docker

[Free Manga Downloader 2](https://github.com/dazedcat19/FMD2) in a container, for Unraid.

FMD2 is a Windows program, so it runs under Wine and its window is shown in the browser (port 3000). A small organiser runs next to it and files every finished download into a manga library laid out for Kavita or Komga.

## What happens to a download

1. You pick a series and chapters in the FMD2 window.
2. FMD2 saves each chapter as a CBZ into a staging folder inside appdata (`/config/staging`).
3. About a minute after a chapter is finished, the organiser:
   - reads the volume and chapter numbers from the chapter name,
   - adds a `ComicInfo.xml` (series, number, volume, chapter title, author, artist, page count) unless the archive already has one,
   - renames the file to `Series v03 c021.cbz`, `Series c021.cbz` or `Series v03.cbz`,
   - moves it into `/library/<Series>/`.

If the library already has a folder for the series (compared ignoring case, accents and punctuation), that folder and its spelling of the name are used. A file that already exists in the library is never overwritten: the new one stays in staging and the container log says so. Nothing already in the library is renamed or changed.

FMD2 only knows the title, author, artist and source site, so that is all the metadata there is. Summaries, genres and covers come from Kavita or Komga's own metadata matching.

## Install on Unraid

In the Unraid terminal:

```bash
wget -O /boot/config/plugins/dockerMan/templates-user/my-fmd2.xml https://raw.githubusercontent.com/Crivons1/fmd2-docker/main/my-fmd2.xml
```

Then Docker → Add Container → Template → `fmd2`, check the two paths, Apply, and open `http://<server>:3000/`.

Or with the Compose Manager plugin: Docker → Add New Stack → name it `fmd2` → Edit Stack → Compose File, paste [docker-compose.yml](docker-compose.yml), Save, Compose Up.

| Container path | Default on Unraid | Purpose |
|---|---|---|
| `/config` | `/mnt/user/appdata/fmd2` | FMD2 itself, settings, favourites, Wine, staging |
| `/library` | `/mnt/user/books/mangas` | Manga library, one folder per series |

Optional variables: `CUSTOM_USER` and `PASSWORD` put a login on the web page; `ORGANISER_INTERVAL` (seconds between scans, default 30); `ORGANISER_SETTLE_SECONDS` (how long a file must be untouched, default 45).

## Do not change these FMD2 options

The organiser relies on them (Options → Save to):

- Save to: `Z:\config\staging\`
- Manga folder name: `%MANGA% ~~ %AUTHOR% ~~ %ARTIST% ~~ %WEBSITE%`
- Chapter name: `%CHAPTER%`
- Compress: CBZ

## Limits

- Sites behind Cloudflare do not work under Wine.
- The base image (`linuxserver/baseimage-kasmvnc`) is no longer updated upstream.

## Build it yourself

```bash
docker build -t fmd2 https://github.com/Crivons1/fmd2-docker.git#main
```

## Credits

`icon.png` is the FMD2 application icon, taken from the FMD2 project (GPLv2).

Container recipe based on the archived [Banh-Canh/docker-FMD2](https://github.com/Banh-Canh/docker-FMD2) and [ElryGH/docker-FMD2](https://github.com/ElryGH/docker-FMD2) (MIT).
