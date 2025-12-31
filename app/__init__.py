from flask import Flask
import os
from .config import DevelopmentConfig, ProductionConfig
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics.for_app_factory()

def create_app():
    app = Flask(__name__)

    env = os.getenv("APP_ENV", "development")
    if env == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    metrics.init_app(app)

    # Importar blueprint principal
    from . import routes as app_routes
    app.register_blueprint(app_routes.bp)

    # Configurar caché si está habilitada
    if app.config.get("USE_CACHE", False):
        from .cache import get_cache, set_cache, delete_cache
        app_routes.get_cache = get_cache
        app_routes.set_cache = set_cache
        app_routes.delete_cache = delete_cache

    return app
