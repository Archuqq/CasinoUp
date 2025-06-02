from flask import Flask, render_template, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from config import Config
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
import traceback
from sqlalchemy import inspect, func

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()

def get_site_stats(app):
    try:
        with app.app_context():
            from app.models import User, Transaction, PromoCode
            stats = {
                'total_users': User.query.count(),
                'total_transactions': Transaction.query.count(),
                'total_volume': db.session.query(func.sum(Transaction.amount)).filter(Transaction.amount > 0).scalar() or 0,
                'active_promos': PromoCode.query.filter_by(is_active=True).count()
            }
            return stats
    except Exception as e:
        app.logger.error(f'Error getting site stats: {str(e)}')
        return None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Настройка логирования
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('CasinoUp startup')

    @app.context_processor
    def inject_site_stats():
        if not getattr(g, '_site_stats', None):
            g._site_stats = get_site_stats(app)
        return dict(site_stats=g._site_stats)

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        app.logger.error(traceback.format_exc())
        return render_template('errors/500.html'), 500

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    try:
        # Инициализация расширений
        db.init_app(app)
        login_manager.init_app(app)
        bcrypt.init_app(app)
        migrate.init_app(app, db)

        with app.app_context():
            app.logger.info('Checking database connection...')
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            app.logger.info(f'Existing tables: {existing_tables}')

            if not existing_tables:
                app.logger.info('No tables found. Creating database schema...')
                db.create_all()
                app.logger.info('Database schema created successfully')
            else:
                app.logger.info('Database tables already exist')

            # Проверяем подключение
            db.engine.connect()
            app.logger.info('Database connection verified')

    except Exception as e:
        app.logger.error(f'Database initialization error: {str(e)}')
        app.logger.error(traceback.format_exc())
        raise

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

    # Регистрация blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.games import bp as games_bp
    app.register_blueprint(games_bp, url_prefix='/games')

    return app 