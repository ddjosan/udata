def init_app(app):
    # Import the CSV adapter to register it
    import udata.core.user.csv  # noqa
