from flask import Flask
from flask_bootstrap import Bootstrap


def create_app(config_name):
    app = Flask(__name__)
    Bootstrap(app)

    if config_name is not None:
        app.config.from_object(config_name)

    if not app.debug:
        import logging
        from logging.handlers import SysLogHandler
        file_handler = SysLogHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

    with app.app_context():
        # the app context is needed to switch the storage
        # backend based on the config parameter.
        # (which is bound to the app object)
        from eudat_http_api.http_storage.init import http_storage
        app.register_blueprint(http_storage)

        from eudat_http_api.registration.init import registration
        app.register_blueprint(registration)

        from eudat_http_api.registration.models import db
        #jj: fucked up blueprints, after blowing up tests now they blow up the ORM
        db.app = app
        db.init_app(app)

    return app
