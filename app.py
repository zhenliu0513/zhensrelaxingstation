"""
App entry point and factory-like setup.
"""
import os
from flask import Flask
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_login import LoginManager
from models import db, User
from utils import create_default_admin

load_dotenv()  # load .env in development

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change_this_secret_key')
    # Database URL
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///data.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints / routes
    from auth import auth_bp
    from views import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Create DB tables and default admin on first run
    with app.app_context():
        db.create_all()
        create_default_admin()

    return app

app = create_app()

if __name__ == "__main__":
    # dev server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=(os.environ.get('FLASK_ENV') != 'production'))
