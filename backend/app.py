from flask import Flask
from flask_cors import CORS

from config import Config
from extensions import db, migrate
from routes.stories import stories_bp
from routes.imagens import imagens_bp
from routes.postagens import postagens_bp

import models


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    CORS(app)

    db.init_app(app)

    migrate.init_app(
        app,
        db
    )

    app.register_blueprint(
        stories_bp
    )

    app.register_blueprint(
        imagens_bp
    )

    app.register_blueprint(
        postagens_bp
    )


    @app.get("/health")
    def health():

        return {
            "status": "ok"
        }

    return app


app = create_app()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )