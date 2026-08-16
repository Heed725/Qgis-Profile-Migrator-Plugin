from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .dialog import MigratorDialog


class ProfileMigratorPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None

    def initGui(self):
        self.action = QAction(QIcon(self._icon()), "QGIS Profile Migrator", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&QGIS Profile Migrator", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginMenu("&QGIS Profile Migrator", self.action)
            self.iface.removeToolBarIcon(self.action)

    def _icon(self):
        import os
        return os.path.join(os.path.dirname(__file__), "icon.svg")

    def run(self):
        if self.dialog is None:
            self.dialog = MigratorDialog(self.iface.mainWindow())
        self.dialog.refresh_profile()
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
