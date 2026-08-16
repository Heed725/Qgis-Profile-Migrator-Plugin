def classFactory(iface):
    from .plugin import ProfileMigratorPlugin
    return ProfileMigratorPlugin(iface)
