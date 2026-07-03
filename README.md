# Inscura’s Plex Metadata Plugin

Languages: **English** | [简体中文](docs/README-zh.md) | [日本語](docs/README-ja.md) | [한국어](docs/README-ko.md)

Inscura is a local media library app that organizes information such as movie details, cast, genres, collections, cover art, and background images. Plex handles playback and media library management, but it is not aware of the data that Inscura has already organized.

This plugin connects Inscura’s local API service to Plex. When Plex scans a title, the plugin writes the title, synopsis, release date, rating, genre, tags, collections, cast, director, screenwriter, producer, cover art, and background image to Plex’s metadata.

The plugin only reads media library data and image resources generated within Inscura; it does not download, move, rename, delete, or modify the original media files.

## Current Capabilities

- Prioritizes matching based on the actual file paths and filenames provided by Plex to reduce mis-matches caused by manually modified Plex titles.
- If no path match is found, it will continue to attempt matching based on file numbers, identifiers in filenames, and Plex titles.
- Uses the duration provided by Plex to assist scoring, improving matching accuracy for files with the same or similar names.
- Supports writing movie metadata fields that Plex can accept, including title, original title, sort title, synopsis, tagline, release date, year, rating, content rating, studio, genre, country, tags, collections, cast, director, screenwriter, producer, poster, and background image.
- Plex metadata agents cannot create trailer or featurette entries from metadata responses, so trailer resources in Inscura will not be written to unsupported fields in Plex.

## Enabling the Inscura Local API Service

1. Open Inscura and open the media library you want to sync to Plex.
2. Go to the API settings in Settings and enable the local API service.
3. We recommend keeping the authentication method set to token mode and saving the API token displayed on the settings page.
4. On the device hosting the Plex server, access the health check URL to verify that the service is reachable.

Example:

```bash
curl "http://[ip]:28687/api/v1/health"
```

If Plex and Inscura are not running on the same machine, do not enter `127.0.0.1` as the service address in the plugin. Instead, enter the LAN address of the computer running Inscura, for example:

```text
http://[ip]:28687
```

The local API service runs for the duration of the current media library’s lifecycle: it listens on the port while the media library is open and the service is enabled, and **stops when the media library is locked, closed, or the application exits.**

## Plugin Files

Available on [GitHub](https://github.com/InscuraApp/inscura-plex-plugin/archive/refs/heads/main.zip) or [Releases](https://github.com/InscuraApp/inscura-plex-plugin/releases).

This repository contains two files that need to be installed on Plex:


| File | Location | Purpose |
| -------------------- | ---------------------------------------------------------- | --------------------- |
| `Inscura.bundle`     | /PlexMediaServer/AppData/Plex Media Server/Plug-ins | Metadata agent responsible for searching, matching, and writing metadata   |
| `Inscura Scanner.py` | /PlexMediaServer/AppData/Plex Media Server/Scanners/Movies | Scans movie files and passes the actual file paths to the matching process |


After installation, you should see the following in Plex:

- Scanner: `Inscura Scanner`
- Agent: `Inscura`



## Plex Data Directory

The actual Plex directory is affected by the package source, system version, volume name, container mapping, and installation method. The locations listed below are common examples; if your device differs, refer to the Plex package page, container mapping, or the actual data directory on your system.

[How to Find the Plex Plug-in Directory?](https://support.plex.tv/articles/201106098-how-do-i-find-the-plug-ins-folder/)

Once you’ve located the Plex data directory, place this plug-in in:

```text
Plex data directory/Plug-ins/Inscura.bundle
Plex data directory/Scanners/Movies/Inscura Scanner.py
```



## Enabling the Plugin in Plex

1. Go to Plex Library Management.
2. Edit an existing movie library.
3. In Advanced Settings, change the scanner to `Inscura Scanner`.
4. Change the agent to `Inscura`.
5. Enter the Inscura service URL and API token.
6. Save the settings.
7. Rescan the library.
8. Re-match or refresh the metadata for existing movies so that Plex writes the Inscura match IDs and metadata.



## Plugin Settings Guide


| Setting | Description |
| ------------- | ------------------------------------------------------------------- |
| Inscura Service Address  | The local Inscura API service address. Must be a local network address if Plex and Inscura are not on the same machine |
| Inscura API Token  | Enter this when the local API service uses token authentication; leave blank if Inscura is set to no authentication |
| Number of Search Results | The number of candidates requested from Inscura per match |
| Minimum Score for Auto-Match | The plugin will not automatically select a candidate if its score is below this value |
| Import Inscura Collections | When disabled, the plugin will not modify existing collections in Plex at all |
| Replace Plex Collections    | Only takes effect when "Import Inscura Collections" is enabled. When enabled, it clears existing Plex collections and replaces them with Inscura’s collections and series; when disabled, it only appends Inscura’s collections and series |


Combination Rules for Collection Settings:


| Import Inscura Collections | Replace Plex Collections | Result |
| ------------- | ---------- | --------------------------- |
| Off | Off or On | Do not write to collections; retain existing Plex collections |
| On | Off | Append Inscura collections and series |
| On | On | Replace existing Plex collections with Inscura collections and series |




## Recommendations

- When using this for the first time, we recommend selecting a small number of movies to re-match first. Once you’ve confirmed that the titles, cast, cover art, and collections match your expectations, you can then refresh your library in bulk.
- If movie titles in Plex have been manually edited, the plugin will still prioritize matching based on the actual file path and filename, rather than relying solely on the title.
- If the Inscura service address or token has been changed, you must update it in the Plex plugin settings and then refresh the metadata.
- If the Inscura media library is locked or shut down, Plex will be unable to read the metadata.



## Troubleshooting



### Plex Cannot Detect the Inscura Agent or Scanner

1. Verify that `Inscura.bundle` is located at `Plex Data Directory/Plug-ins/Inscura.bundle`.
2. Verify that `Inscura.bundle/Contents` exists.
3. Verify that `Inscura Scanner.py` is located at `Plex Data Directory/Scanners/Movies/Inscura Scanner.py`.
4. Verify that the Plex process has permission to read these files.
5. Restart the Plex Media Server.
6. Reopen the Plex web interface and check the Library Advanced Settings.



### Plex Can See the Plugin but Has No Metadata

1. On the device hosting the Plex server, visit the Inscura health check URL.
2. Verify that the Inscura media library is enabled and that the local API service is running.
3. Verify that the service address in the Plex plugin is not the incorrect `127.0.0.1`.
4. If the API uses token-based authentication, verify that the correct token is entered in the Plex plugin.
5. Re-match or refresh the metadata for the movie.



### Cover art or cast photos are not displayed

1. Verify that the Plex server can access the Inscura service address.
2. If the API uses token-based authentication, verify that the plugin token is correct.
3. Verify that the corresponding media or actor in Inscura actually has available image resources.
4. Refresh the movie’s metadata.



## Upgrading the Plugin

1. Stop or prepare to restart the Plex Media Server.
2. Delete the old `Plex Data Directory/Plug-ins/Inscura.bundle`.
3. Copy the new `Inscura.bundle` to the plugin directory.
4. Overwrite `Plex Data Directory/Scanners/Movies/Inscura Scanner.py`.
5. Fix the permissions.
6. Restart the Plex Media Server.

If the Plex web interface still displays the old settings after the upgrade, first force-refresh the browser page, then reopen the library editing window.
