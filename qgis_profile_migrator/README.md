# QGIS Profile Migrator

QGIS Profile Migrator moves selected configuration from one QGIS installation/profile to another. It is designed for a configured office computer, a new clean computer, training labs, or standardizing several workstations.

## What it transfers

The Export and Import screens let the user independently select:

- QGIS settings and interface preferences
1. XYZ Tiles and other basemaps
2. WMS/WMTS, WFS and ArcGIS REST connections
3. Python plugins
4. Processing scripts, models and R scripts
5. Colour palettes, styles, symbols and SVG files
6. Custom projections and CRS database
7. Project and print-layout templates
8. Optional database connection definitions

Use **Select all** or **Clear all** for faster selection. Database connections remain unticked by default because they often refer to private servers and credentials.

The exported `.qgismigrate.zip` contains:

- `manifest.json` — versions, categories, file hashes and compatibility information
- `settings.json` — transferable QSettings keys and values
- `inventory.csv` — human-readable inventory that opens in Excel
- `profile/` — selected profile files in their original relative paths

## Installation

1. Download `qgis_profile_migrator.zip`.
2. In QGIS, open **Plugins → Manage and Install Plugins**.
3. Select **Install from ZIP**.
4. Choose the ZIP and install it.
5. Enable **QGIS Profile Migrator** if QGIS does not enable it automatically.
6. Open it from the toolbar button or **Plugins → QGIS Profile Migrator**.

QGIS 3.22 or newer is supported.

## Export from the configured QGIS

1. Open the plugin and select **Export**.
2. Tick the categories required on the new computer.
3. Normally leave **Include password/token-like settings** unticked.
4. Click **Export portable package** and save the archive.
5. Copy the archive to the clean computer using a trusted drive or network location.

## Import into a clean QGIS

1. Install the plugin on the clean QGIS.
2. Open **Import**, choose the exported package, and select categories.
3. Click **Preview / dry run**. Check QGIS versions, file count and warnings.
4. Keep **Create backup before import** enabled.
5. Click **Import selected items**, confirm, and restart QGIS.
6. Open **Plugins → Manage and Install Plugins** and confirm plugins are enabled.
7. Test basemaps and database connections. Re-enter passwords where required.

## Important limitations and safety

- Passwords, tokens and obvious secret settings are redacted by default. The QGIS Authentication Database is deliberately not copied. Re-enter credentials on the destination.
- A Python plugin copied from one QGIS version may be incompatible with another version. The preview warns when source and destination major/minor versions differ.
- Native/compiled plugins may depend on the operating system or QGIS build. Reinstall them from the official repository if copying is insufficient.
- Network paths, fonts, drivers, database clients, certificates and environment variables are external dependencies; the plugin cannot move them.
- Browser favorites and provider definitions stored under supported QSettings prefixes are included, but passwords remain excluded by default.
- The importer validates SHA-256 hashes and blocks archive path traversal.
- Existing files can be preserved by unticking overwrite. With backup enabled, touched destination files and current selected settings are saved under `profile_migrator_backups/<timestamp>` inside the current QGIS profile.
- Import writes into the active profile only. Create or select the intended QGIS profile before importing.

## Moving between QGIS profiles on the same computer

Use **Settings → User Profiles → New Profile**, switch to the new profile, install this plugin, and import the package. This is safer than manually copying the whole profile because the plugin provides selection, preview, redaction, checksums and backup.

## Troubleshooting

### Basemap appears but does not load

Check internet access, URL/API key, proxy settings and provider terms. API tokens are normally redacted and must be added again.

### Plugin is copied but disabled

Open **Plugins → Manage and Install Plugins → Installed** and enable it. If QGIS reports incompatibility, install the appropriate release from the QGIS plugin repository.

### Custom CRS is missing

Import both **Projection and CRS settings** and **User CRS database**, then restart QGIS. If the destination already has important custom CRS definitions, keep the automatic backup and review conflicts carefully because `qgis.db` is a database file, not a row-by-row merge.

### Settings did not visually change

Restart QGIS. Some UI state is cached until shutdown. Also confirm that import was run in the intended active profile shown at the top of the plugin window.

### Restore after a bad import

Close QGIS. Open the active profile folder, locate `profile_migrator_backups/<timestamp>`, and restore the saved files. `settings-before-import.json` records the settings that existed immediately before import.

## Package format

The format is intentionally open and inspectable. JSON and CSV can be audited without QGIS; files retain their relative paths. Do not edit or re-zip a package unless you also update its manifest hashes.

## License

MIT License.
