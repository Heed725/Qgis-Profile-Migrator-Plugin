from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QCheckBox, QDialog, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QTabWidget, QVBoxLayout, QWidget
)

from .migrator import FILE_CATEGORIES, SETTINGS_PREFIXES, export_package, import_package, preview_import, profile_path


CATEGORY_LABELS = {
    "qgis_preferences": "QGIS settings and interface preferences",
    "xyz_basemaps": "1. XYZ Tiles and other basemaps",
    "web_services": "2. WMS/WMTS, WFS and ArcGIS REST connections",
    "plugins": "3. Python plugins",
    "processing_scripts": "4. Processing scripts, models and R scripts",
    "colors_styles": "5. Colour palettes, styles, symbols and SVG files",
    "custom_projections": "6. Custom projections and CRS database",
    "templates_layouts": "7. Project and print-layout templates",
    "database_connections": "8. Optional database connection definitions",
}


class MigratorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QGIS Profile Migrator")
        self.resize(760, 650)
        self.tabs = QTabWidget()
        self.export_checks = self._checks()
        self.import_checks = self._checks()
        self.profile_label = QLabel()
        self.log = QPlainTextEdit(); self.log.setReadOnly(True)
        self.progress = QProgressBar(); self.progress.setVisible(False)
        layout = QVBoxLayout(self)
        intro = QLabel("Move a configured QGIS profile into another QGIS installation. Export creates one portable archive; import can preview it before writing anything.")
        intro.setWordWrap(True)
        layout.addWidget(intro); layout.addWidget(self.profile_label); layout.addWidget(self.tabs)
        layout.addWidget(self.progress); layout.addWidget(self.log)
        self._build_export(); self._build_import()

    def _checks(self):
        return {key: QCheckBox(label) for key, label in CATEGORY_LABELS.items()}

    def _category_box(self, checks):
        box = QGroupBox("Choose what to transfer")
        v = QVBoxLayout(box)
        for key, check in checks.items():
            check.setChecked(key not in ("database_connections",))
            v.addWidget(check)
        actions = QHBoxLayout()
        select_all = QPushButton("Select all")
        clear_all = QPushButton("Clear all")
        select_all.clicked.connect(lambda: [check.setChecked(True) for check in checks.values()])
        clear_all.clicked.connect(lambda: [check.setChecked(False) for check in checks.values()])
        actions.addWidget(select_all); actions.addWidget(clear_all); actions.addStretch()
        v.addLayout(actions)
        return box

    def _build_export(self):
        page = QWidget(); v = QVBoxLayout(page)
        v.addWidget(self._category_box(self.export_checks))
        self.secrets = QCheckBox("Include password/token-like settings (not recommended)")
        self.secrets.setToolTip("Only use this on a trusted, encrypted transfer path. QGIS Authentication Database passwords are not exported.")
        v.addWidget(self.secrets)
        button = QPushButton("Export portable package…"); button.clicked.connect(self.do_export)
        v.addWidget(button); v.addStretch(); self.tabs.addTab(page, "Export")

    def _build_import(self):
        page = QWidget(); v = QVBoxLayout(page)
        self.package_label = QLabel("No package selected")
        choose = QPushButton("Choose package…"); choose.clicked.connect(self.choose_package)
        row = QHBoxLayout(); row.addWidget(self.package_label, 1); row.addWidget(choose); v.addLayout(row)
        v.addWidget(self._category_box(self.import_checks))
        self.overwrite = QCheckBox("Overwrite destination files with package versions"); self.overwrite.setChecked(True)
        self.backup = QCheckBox("Create backup before import"); self.backup.setChecked(True)
        v.addWidget(self.overwrite); v.addWidget(self.backup)
        buttons = QHBoxLayout()
        preview = QPushButton("Preview / dry run"); preview.clicked.connect(self.do_preview)
        run = QPushButton("Import selected items"); run.clicked.connect(self.do_import)
        buttons.addWidget(preview); buttons.addWidget(run); v.addLayout(buttons)
        v.addStretch(); self.tabs.addTab(page, "Import")
        self.package_path = None

    def refresh_profile(self):
        self.profile_label.setText("Current QGIS profile: <b>{}</b>".format(profile_path()))

    def _selected(self, checks):
        return {key for key, check in checks.items() if check.isChecked()}

    def _progress(self, current, total, name):
        self.progress.setVisible(True); self.progress.setMaximum(max(total, 1)); self.progress.setValue(current)
        self.progress.setFormat("%p% — " + name[-45:])
        from qgis.PyQt.QtWidgets import QApplication
        QApplication.processEvents()

    def choose_package(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose migration package", "", "QGIS migration (*.zip *.qgismigrate);;All files (*)")
        if path:
            self.package_path = path; self.package_label.setText(path); self.do_preview()

    def do_export(self):
        categories = self._selected(self.export_checks)
        if not categories:
            QMessageBox.warning(self, "Nothing selected", "Select at least one category."); return
        suggested = str(Path.home() / "qgis-profile-{}.qgismigrate.zip".format(profile_path().name))
        path, _ = QFileDialog.getSaveFileName(self, "Save portable package", suggested, "QGIS migration (*.zip)")
        if not path: return
        try:
            output, manifest = export_package(path, categories, self.secrets.isChecked(), self._progress)
            self.log.setPlainText("Export complete\n{}\n\n{} settings\n{} files\n{} secret-like settings redacted".format(output, manifest["settings_count"], len(manifest["files"]), len(manifest["redacted_setting_keys"])))
            QMessageBox.information(self, "Export complete", "Portable package created:\n{}".format(output))
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
        finally: self.progress.setVisible(False)

    def do_preview(self):
        if not self.package_path:
            QMessageBox.warning(self, "Choose a package", "Choose a migration package first."); return
        try:
            result = preview_import(self.package_path, self._selected(self.import_checks))
            source = result["manifest"]["source"]
            lines = ["DRY RUN — no changes made", "", "Source: QGIS {} on {}".format(source.get("qgis_version"), source.get("os")), "Created: {}".format(result["manifest"].get("created_utc")), "Settings to write: {}".format(result["settings_to_write"]), "Files to write: {} ({:.2f} MB)".format(result["files_to_write"], result["bytes_to_write"] / 1048576)]
            if result["warnings"]: lines += ["", "Warnings:"] + ["• " + x for x in result["warnings"]]
            self.log.setPlainText("\n".join(lines))
        except Exception as exc: QMessageBox.critical(self, "Preview failed", str(exc))

    def do_import(self):
        if not self.package_path:
            QMessageBox.warning(self, "Choose a package", "Choose a migration package first."); return
        self.do_preview()
        answer = QMessageBox.question(self, "Confirm import", "Import selected items into the current profile?\n\nClose open projects first. Restart QGIS after import.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes: return
        try:
            result = import_package(self.package_path, self._selected(self.import_checks), self.overwrite.isChecked(), self.backup.isChecked(), self._progress)
            text = "Import complete\n{} settings written\n{} files written".format(result["settings_written"], result["files_written"])
            if result["backup"]: text += "\nBackup: " + result["backup"]
            text += "\n\nRestart QGIS now."
            self.log.setPlainText(text); QMessageBox.information(self, "Import complete", text)
        except Exception as exc: QMessageBox.critical(self, "Import failed", str(exc))
        finally: self.progress.setVisible(False)
