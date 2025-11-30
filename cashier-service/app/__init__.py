from flask import Flask

from icash_common import setup_logging, register_frontend


def create_app():
    setup_logging()
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="../templates",
        static_folder="../static",
    )

    # Load base config
    app.config.from_object("app.config.Config")
    register_frontend(app)
    return app
