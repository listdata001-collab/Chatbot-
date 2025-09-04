import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_babel import Babel
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
migrate = Migrate()
babel = Babel()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///botfactory.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Babel configuration
    app.config['LANGUAGES'] = ['en', 'uz', 'ru']
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    def get_locale():
        from flask import request, session
        # 1. URL parameter
        if request.args.get('lang'):
            session['language'] = request.args.get('lang')
        # 2. Session
        if 'language' in session:
            return session['language']
        # 3. Browser preference
        return request.accept_languages.best_match(app.config['LANGUAGES']) or 'en'
    
    babel.init_app(app, locale_selector=get_locale)
    
    # Make get_locale available in templates
    app.jinja_env.globals['get_locale'] = get_locale
    
    # Create database tables
    with app.app_context():
        import models
        db.create_all()
        logging.info("Database tables created")
    
    # Register blueprints
    from routes import main_bp, auth_bp, bot_bp, admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(bot_bp, url_prefix='/bot')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app
