import csv
import hashlib
import json
import os
import platform
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsApplication, Qgis


FORMAT_VERSION = 1
SETTINGS_PREFIXES = {
    "qgis_preferences": ["qgis/", "gui/", "UI/", "app/"],
    "xyz_basemaps": ["qgis/connections-xyz/"],
    "web_services": [
        "qgis/connections-wms/", "qgis/connections-wfs/",
        "qgis/connections-vector-tile/", "qgis/connections-arcgisfeatureserver/",
        "qgis/connections-arcgismapserver/", "qgis/connections-cloud/"
    ],
    "database_connections": [
        "PostgreSQL/connections/", "MSSQL/connections/", "Oracle/connections/",
        "SAP HANA/connections/", "SpatiaLite/connections/"
    ],
    "custom_projections": ["Projections/", "qgis/projections/"],
    "colors_styles": ["colors/", "qgis/customColors/", "qgis/defaultStyles/"],
}

FILE_CATEGORIES = {
    "plugins": ["python/plugins"],
    "processing_scripts": ["processing/scripts", "processing/models", "processing/rscripts"],
    "colors_styles": ["palettes", "styles", "symbols", "svg"],
    "custom_projections": ["qgis.db"],
    "templates_layouts": ["project_templates", "composer_templates", "templates"],
}

SECRET_MARKERS = ("password", "passwd", "pwd", "token", "secret", "apikey", "api_key")
SKIP_NAMES = {"__pycache__", ".git", ".svn", "cache", "crash", "logs"}


def profile_path():
    return Path(QgsApplication.qgisSettingsDirPath()).resolve()


def _json_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return {"__type__": "bytes_hex", "value": value.hex()}
    if isinstance(value, (list, tuple)):
        return [_json_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_value(v) for k, v in value.items()}
    return {"__type__": "string", "value": str(value)}


def _restore_value(value):
    if isinstance(value, list):
        return [_restore_value(v) for v in value]
    if isinstance(value, dict) and value.get("__type__") == "bytes_hex":
        return bytes.fromhex(value["value"])
    if isinstance(value, dict) and value.get("__type__") == "string":
        return value["value"]
    if isinstance(value, dict):
        return {k: _restore_value(v) for k, v in value.items()}
    return value


def _is_secret(key):
    lower = key.lower()
    return any(marker in lower for marker in SECRET_MARKERS)


def _setting_selected(key, categories):
    """Match a key to selected UI groups without letting broad qgis/ preferences swallow specialist groups."""
    categories = set(categories)
    specialist = {name: prefixes for name, prefixes in SETTINGS_PREFIXES.items() if name != "qgis_preferences"}
    for name, prefixes in specialist.items():
        if any(key.startswith(prefix) for prefix in prefixes):
            return name in categories
    return "qgis_preferences" in categories and any(
        key.startswith(prefix) for prefix in SETTINGS_PREFIXES["qgis_preferences"]
    )


def collect_settings(categories, include_secrets=False):
    settings = QSettings()
    result, redacted = {}, []
    for key in settings.allKeys():
        if not _setting_selected(key, categories):
            continue
        if _is_secret(key) and not include_secrets:
            redacted.append(key)
            continue
        result[key] = _json_value(settings.value(key))
    return result, redacted


def _safe_files(root, relative):
    source = root / relative
    if not source.exists():
        return []
    if source.is_file():
        return [(source, Path(relative))]
    found = []
    for path in source.rglob("*"):
        if not path.is_file() or any(part in SKIP_NAMES for part in path.parts):
            continue
        found.append((path, path.relative_to(root)))
    return found


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def export_package(destination, categories, include_secrets=False, progress=None):
    destination = Path(destination)
    if destination.suffix.lower() not in (".zip", ".qgismigrate"):
        destination = destination.with_suffix(".qgismigrate.zip")
    root = profile_path()
    selected_settings = [c for c in categories if c in SETTINGS_PREFIXES]
    settings, redacted = collect_settings(selected_settings, include_secrets)
    files = []
    seen = set()
    for category in categories:
        for relative in FILE_CATEGORIES.get(category, []):
            for source, archive_relative in _safe_files(root, relative):
                key = archive_relative.as_posix().lower()
                if key not in seen:
                    seen.add(key)
                    files.append((category, source, archive_relative))

    manifest = {
        "format": "qgis-profile-migrator", "format_version": FORMAT_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "qgis_version": Qgis.QGIS_VERSION,
            "python_version": platform.python_version(), "os": platform.platform(),
            "profile_name": root.name,
        },
        "categories": sorted(categories), "settings_count": len(settings),
        "redacted_setting_keys": redacted, "files": [],
        "notes": [
            "Passwords and obvious secret values are excluded unless explicitly enabled.",
            "QGIS restart is recommended after import.",
            "Compiled/native plugins may need a compatible build for the destination QGIS/OS."
        ]
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        archive.writestr("settings.json", json.dumps(settings, indent=2, ensure_ascii=False))
        for index, (category, source, relative) in enumerate(files, 1):
            arcname = "profile/" + relative.as_posix()
            archive.write(source, arcname)
            stat = source.stat()
            manifest["files"].append({
                "category": category, "path": relative.as_posix(), "size": stat.st_size,
                "sha256": _sha256(source)
            })
            if progress:
                progress(index, len(files), relative.as_posix())
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        rows = [["type", "category", "key_or_path", "size", "status"]]
        rows += [["setting", "settings", key, "", "exported"] for key in settings]
        rows += [["setting", "security", key, "", "redacted"] for key in redacted]
        rows += [["file", f["category"], f["path"], f["size"], "exported"] for f in manifest["files"]]
        buffer = []
        class Sink:
            def write(self, value): buffer.append(value); return len(value)
        writer = csv.writer(Sink(), lineterminator="\n")
        writer.writerows(rows)
        archive.writestr("inventory.csv", "".join(buffer).encode("utf-8-sig"))
    return destination, manifest


def inspect_package(package):
    package = Path(package)
    with zipfile.ZipFile(package, "r") as archive:
        names = set(archive.namelist())
        if "manifest.json" not in names or "settings.json" not in names:
            raise ValueError("This is not a valid QGIS Profile Migrator package.")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("format") != "qgis-profile-migrator":
            raise ValueError("Unknown package format.")
        if int(manifest.get("format_version", 0)) > FORMAT_VERSION:
            raise ValueError("Package was created by a newer plugin version.")
        settings = json.loads(archive.read("settings.json"))
    return manifest, settings


def preview_import(package, categories):
    manifest, settings = inspect_package(package)
    files = [f for f in manifest.get("files", []) if f.get("category") in categories]
    selected_settings = {key: value for key, value in settings.items() if _setting_selected(key, categories)}
    source_major_minor = ".".join(manifest.get("source", {}).get("qgis_version", "").split(".")[:2])
    current_major_minor = ".".join(Qgis.QGIS_VERSION.split(".")[:2])
    warnings = []
    if source_major_minor and source_major_minor != current_major_minor:
        warnings.append("Source QGIS {} differs from destination {}.".format(source_major_minor, current_major_minor))
    if manifest.get("redacted_setting_keys"):
        warnings.append("{} secret-like settings were redacted and must be entered again.".format(len(manifest["redacted_setting_keys"])))
    return {
        "manifest": manifest, "settings_to_write": len(selected_settings),
        "files_to_write": len(files), "bytes_to_write": sum(f.get("size", 0) for f in files),
        "warnings": warnings, "selected_files": files
    }


def _safe_member(relative):
    path = Path(relative)
    return not path.is_absolute() and ".." not in path.parts


def import_package(package, categories, overwrite=True, create_backup=True, progress=None):
    manifest, all_settings = inspect_package(package)
    preview = preview_import(package, categories)
    root = profile_path()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = root / "profile_migrator_backups" / timestamp
    touched = []
    selected = preview["selected_files"]
    selected_paths = {f["path"]: f for f in selected}

    if create_backup:
        backup.mkdir(parents=True, exist_ok=True)
        current_settings, _ = collect_settings([c for c in categories if c in SETTINGS_PREFIXES], True)
        (backup / "settings-before-import.json").write_text(json.dumps(current_settings, indent=2), encoding="utf-8")
        for relative in selected_paths:
            target = root / relative
            if target.is_file():
                out = backup / "profile" / relative
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, out)

    with zipfile.ZipFile(package, "r") as archive:
        for index, (relative, metadata) in enumerate(selected_paths.items(), 1):
            if not _safe_member(relative):
                raise ValueError("Unsafe path in package: {}".format(relative))
            member = "profile/" + relative
            target = root / relative
            if target.exists() and not overwrite:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as src, tempfile.NamedTemporaryFile(delete=False, dir=str(target.parent)) as tmp:
                shutil.copyfileobj(src, tmp)
                temp_name = tmp.name
            if _sha256(temp_name) != metadata["sha256"]:
                os.unlink(temp_name)
                raise ValueError("Checksum failed for {}".format(relative))
            os.replace(temp_name, target)
            touched.append(relative)
            if progress:
                progress(index, len(selected), relative)

    selected_settings = {key: value for key, value in all_settings.items() if _setting_selected(key, categories)}
    if selected_settings:
        settings = QSettings()
        for key, value in selected_settings.items():
            settings.setValue(key, _restore_value(value))
        settings.sync()
    return {"backup": str(backup) if create_backup else None, "files_written": len(touched), "settings_written": preview["settings_to_write"]}
