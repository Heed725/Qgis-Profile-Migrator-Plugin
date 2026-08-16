# QGIS Profile Migrator 1.1.0

First public release of the QGIS Profile Migrator plugin.

## Highlights

- Export selected QGIS settings and profile resources into one portable archive.
- Independently select QGIS preferences and eight migration groups during import.
- Separate XYZ basemaps from WMS/WMTS, WFS and ArcGIS REST connections.
- Preview/dry-run import counts before changing the destination.
- Automatically back up destination settings and affected files.
- Redact password/token-like settings by default.
- Verify all transferred profile files with SHA-256 checksums.
- Include a JSON manifest and Excel-readable CSV inventory.

## Installation

Download `qgis_profile_migrator.zip`, then use **QGIS → Plugins → Manage and Install Plugins → Install from ZIP**.

QGIS 3.22 or newer is required. Restart QGIS after importing a profile package.
