def upgrade(session, logger):
    """Create or upgrade an instance or my_project."""
    if session.is_initialization:
        logger.info("Installing modules on fresh database")
        session.install_modules(['sale'])
        return
