# QGIS Profile Migrator

[![QGIS](https://img.shields.io/badge/QGIS-3.22%2B-589632?logo=qgis&logoColor=white)](https://qgis.org/)
[![Release](https://img.shields.io/github/v/release/Heed725/Qgis-Profile-Migrator-Plugin)](https://github.com/Heed725/Qgis-Profile-Migrator-Plugin/releases/latest)
[![Build](https://github.com/Heed725/Qgis-Profile-Migrator-Plugin/actions/workflows/release.yml/badge.svg)](https://github.com/Heed725/Qgis-Profile-Migrator-Plugin/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Move settings from a configured QGIS profile to a clean QGIS installation without manually hunting through profile folders. The plugin creates one auditable migration package, previews exactly what will change, verifies file checksums, and backs up the destination before import.

## Download

Download **`qgis_profile_migrator.zip`** from the [latest release](https://github.com/Heed725/Qgis-Profile-Migrator-Plugin/releases/latest). Do not download GitHub's automatically generated “Source code” ZIP for installation.

## What can be selected

The Export and Import screens allow every group to be selected independently:

- **QGIS settings and interface preferences**
1. **XYZ Tiles and other basemaps**
2. **WMS/WMTS, WFS and ArcGIS REST connections**
3. **Python plugins**
4. **Processing scripts, models and R scripts**
5. **Colour palettes, styles, symbols and SVG files**
6. **Custom projections and CRS database**
7. **Project and print-layout templates**
8. **Optional database connection definitions**

The Import screen also provides **Select all**, **Clear all**, and **Preview / dry run**. Database connections are unticked by default.

## Install in QGIS

1. Download `qgis_profile_migrator.zip` from Releases.
2. Open QGIS.
3. Go to **Plugins → Manage and Install Plugins**.
4. Open **Install from ZIP**.
5. Select the downloaded file and approve the security prompt.
6. Enable **QGIS Profile Migrator** under **Installed** if necessary.
7. Open it from the toolbar or **Plugins → QGIS Profile Migrator**.

Supported version: **QGIS 3.22 or newer**.

## Export from the configured computer

1. Start the plugin and open **Export**.
2. Tick only the groups you want to move.
3. Leave **Include password/token-like settings** unticked for normal use.
4. Click **Export portable package**.
5. Save the generated `.qgismigrate.zip` file and move it to the destination computer through a trusted location.

## Import into a clean QGIS

1. Create or select the intended destination profile from **Settings → User Profiles**.
2. Install and open this plugin.
3. Open **Import** and choose the `.qgismigrate.zip` package.
4. Tick only the groups required on this computer.
5. Click **Preview / dry run** and review the source QGIS version, settings count, file count, size, and warnings.
6. Keep **Create backup before import** enabled.
7. Choose whether existing destination files may be overwritten.
8. Click **Import selected items** and confirm.
9. Restart QGIS.
10. Test plugins, basemaps, database connections, custom CRS, and Processing scripts.

## Portable package contents

| Entry | Purpose |
|---|---|
| `manifest.json` | Format version, source environment, selected groups, hashes, sizes and warnings |
| `settings.json` | Structured QGIS settings that preserve lists, booleans and other value types |
| `inventory.csv` | Human-readable inventory that opens in Excel |
| `profile/` | Selected scripts, plugins, palettes, SVGs, templates and databases in their relative paths |

JSON is the source of truth because Excel cannot preserve directory trees and nested settings safely. CSV is included for auditing and reporting.

## Safety and privacy

- Passwords, tokens and other obvious secrets are redacted by default.
- The QGIS Authentication Database is deliberately not exported.
- Each imported file is checked using SHA-256 before it replaces a destination file.
- Unsafe archive paths such as `../` are rejected.
- Import affects only the active QGIS profile displayed in the plugin window.
- A timestamped backup is created under `profile_migrator_backups/<timestamp>` when backup is enabled.
- The plugin never deletes the source profile.

## Compatibility limitations

- A plugin may not work across substantially different QGIS versions. Reinstall incompatible plugins from the official QGIS plugin repository.
- Compiled/native plugins can depend on QGIS, Python, GDAL, Qt, and the operating system.
- Fonts, ODBC drivers, database clients, certificates, environment variables, VPN access, and referenced network folders are external dependencies and are not copied.
- API keys redacted from basemap URLs or service settings must be entered again.
- `qgis.db` is copied as a database file; it is not merged row-by-row with an existing destination database.

## Troubleshooting

### The plugin is installed but not visible

Open **Plugins → Manage and Install Plugins → Installed**, enable it, then look under the Plugins menu and toolbar. Restart QGIS if necessary.

### A basemap appears but does not load

Check the service URL, internet connection, proxy, API key and provider restrictions. Credentials are normally excluded from migration.

### A copied Python plugin is disabled

Enable it from the plugin manager. If QGIS reports incompatibility, install a compatible release from the official repository.

### Custom CRS definitions are missing

Import **Custom projections and CRS database**, restart QGIS, and confirm you imported into the intended active profile.

### Restore after an unwanted import

1. Close QGIS.
2. Open the destination QGIS profile directory.
3. Find `profile_migrator_backups/<timestamp>`.
4. Restore the required files from its `profile` folder.
5. Use `settings-before-import.json` to review the previous settings.

## Development

The installable ZIP must contain the `qgis_profile_migrator/` directory at its root:

```text
qgis_profile_migrator/
├── __init__.py
├── plugin.py
├── dialog.py
├── migrator.py
├── metadata.txt
├── icon.svg
├── README.md
└── LICENSE
```

Run the basic validation and package commands:

```bash
python -m compileall -q qgis_profile_migrator
zip -r qgis_profile_migrator.zip qgis_profile_migrator \
  -x '*/__pycache__/*' '*.pyc'
unzip -t qgis_profile_migrator.zip
```

The included GitHub Actions workflow performs these checks and publishes the installation ZIP.

## License

[MIT License](LICENSE) — copyright © 2026 Hemed Lungo.
