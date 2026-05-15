from flask import Flask

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SECRET_KEY"] = "dev-key-123"

    from app.views import views
    app.register_blueprint(views, url_prefix="/")

    return app