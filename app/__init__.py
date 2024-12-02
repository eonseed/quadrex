from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.categories import bp as categories_bp
    app.register_blueprint(categories_bp)  # Blueprint with url_prefix='/categories'
    
    from app.transactions import bp as transactions_bp
    app.register_blueprint(transactions_bp)

    from app.cli import register_commands
    register_commands(app)

    return app

from app import models
