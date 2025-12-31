import redis
import json
from flask import current_app

def get_cache_connection():
    """Obtiene una conexión nueva a Redis usando la configuración de Flask."""
    try:
        return redis.StrictRedis(
            host=current_app.config["REDIS_HOST"],
            port=current_app.config["REDIS_PORT"],
            decode_responses=True
        )
    except Exception as e:
        print(f"Redis no disponible: {e}")
        return None


def get_cache(key):
    try:
        cache = get_cache_connection()
        if not cache:
            return None

        data = cache.get(key)
        if data:
            return json.loads(data)
        return None
    except redis.exceptions.ConnectionError as e:
        print(f"Error de conexión con Redis: {e}")
        return None
    except json.JSONDecodeError:
        return None


def set_cache(key, value, ttl=None):
    try:
        cache = get_cache_connection()
        if not cache:
            return
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        if ttl:
            cache.setex(key, ttl, value)
        else:
            cache.set(key, value)
    except redis.exceptions.ConnectionError as e:
        print(f"No se pudo guardar en Redis: {e}")


def delete_cache(key):
    try:
        cache = get_cache_connection()
        if not cache:
            return
        cache.delete(key)
    except redis.exceptions.ConnectionError as e:
        print(f"No se pudo eliminar clave de Redis: {e}")
