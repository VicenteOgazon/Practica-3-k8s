import mimetypes
from urllib.parse import urlparse
import os
from flask import Blueprint, render_template, request, redirect, jsonify, current_app, url_for, Response, abort
from http import HTTPStatus
import mysql.connector
from mysql.connector import Error
from minio import Minio
from minio.error import S3Error

bp = Blueprint("main", __name__)

def get_container_name():
   return current_app.config["INSTANCE_NAME"]

# --- Funciones vacías de caché (se sobrescribirán en __init__.py si se usa Redis), me devuelven el error si estoy de entorno dev ---
def get_cache(key):
    raise ConnectionError("Redis no disponible en este entorno")

def set_cache(key, value):
    raise ConnectionError("Redis no disponible en este entorno")

def delete_cache(key):
    raise ConnectionError("Redis no disponible en este entorno")



# --- Conexión MySQL ---
def get_connection():
    try:
        conn = mysql.connector.connect(
            host=current_app.config["MYSQL_HOST"],
            user=current_app.config["MYSQL_USER"],
            password=current_app.config["MYSQL_PASSWORD"],
            database=current_app.config["MYSQL_DATABASE"]
        )
        return conn
    except Error as e:
        print(f"Error de conexión con MySQL: {e}")
        return None


# --- Rutas ---
@bp.route("/", methods=["GET"])
def index():
    container_name = get_container_name()
    
    background_url = url_for("main.asset", key="fondo.png")
    return render_template("index.html", container_name=container_name, background_url=background_url)


@bp.route("/usuarios/json", methods=["GET"])
def listar_usuarios_json():
    cache_key = "usuarios_todos"
    usuarios = None

    # Intentar obtener desde caché
    try:
        usuarios = get_cache(cache_key)
    except Exception as e:
        print(f"Error accediendo a Redis: {e}")

    if usuarios:
        return jsonify({"usuarios": usuarios})

    conn = get_connection()
    if conn is None:
        return jsonify({"error": "No se pudo conectar con la base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al ejecutar consulta MySQL: {e}")
        return jsonify({"error": "Error al consultar la base de datos"}), 500

    # Intentar guardar en caché
    try:
        set_cache(cache_key, usuarios)
    except Exception as e:
        print(f"No se pudo guardar en Redis: {e}")

    return jsonify({"usuarios": usuarios})


@bp.route("/set", methods=["POST"])
def set_user():
    nombre = request.form["nombre"]
    apellido = request.form["apellido"]
    edad = request.form["edad"]
    correo = request.form["correo"]
    ciudad = request.form["ciudad"]

    conn = get_connection()
    if conn is None:
        return jsonify({"error": "No se pudo conectar con la base de datos"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (nombre, apellido, edad, correo, ciudad)
            VALUES (%s, %s, %s, %s, %s)
        """, (nombre, apellido, edad, correo, ciudad))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        
        return jsonify({"error": "Error al modificar la base de datos"}), 500

    # Borrar caché tras inserción
    try:
        delete_cache("usuarios_todos")
    except Exception as e:
        print(f"No se pudo eliminar en Redis: {e}")

    return redirect("/")


@bp.route("/delete", methods=["POST"])
def delete_users():
    ids = request.form.getlist("ids")
    if ids:
        conn = get_connection()
        if conn is None:
            return jsonify({"error": "No se pudo conectar con la base de datos"}), 500
        try:
            cursor = conn.cursor()
            formato = ",".join(["%s"] * len(ids))
            cursor.execute(f"DELETE FROM usuarios WHERE id IN ({formato})", ids)
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            
            return jsonify({"error": "Error al modificar la base de datos"}), 500

        try:
            delete_cache("usuarios_todos")
        except Exception as e:
            print(f"No se pudo eliminar en Redis: {e}")

    return redirect("/")


@bp.route("/status", methods=["GET"])
def status_page():
    """Renderiza una página HTML con el estado de los servicios."""
    status = {"web: ": "up", "db: ": "unknown", "cache: ": "unknown"}

    # --- Base de datos ---
    conn = get_connection()
    status["db: "] = "up" if conn else "down"
    if conn:
        conn.close()

    try:
        from .cache import get_cache_connection
        cache = get_cache_connection()
        if cache and cache.ping():
            status["cache: "] = "up"
        else:
            status["cache: "] = "down"
    except Exception:
        status["cache: "] = "down"

    return render_template("status.html", status=status)


@bp.route("/health", methods=["GET"])
def health():
    # DB requerida
    conn = get_connection()
    db_ok = conn is not None
    if conn:
        conn.close()

    # Redis solo si USE_CACHE=True
    use_cache = current_app.config.get("USE_CACHE", False)

    cache_ok = True
    if use_cache:
        try:
            from .cache import get_cache_connection
            cache = get_cache_connection()
            cache_ok = bool(cache) and bool(cache.ping())
        except Exception:
            cache_ok = False

    ok = db_ok and cache_ok
    code = HTTPStatus.OK if ok else HTTPStatus.SERVICE_UNAVAILABLE

    return jsonify({
        "ok": ok,
        "db": db_ok,
        "cache": cache_ok if use_cache else None
    }), code


@bp.route("/crash")
def crash():
    
    os._exit(1)
    
    return "This will never be returned"


@bp.route("/assets/<path:key>", methods=["GET"])
def asset(key: str):
    # Seguridad básica: si solo quieres permitir el fondo, restringe.
    if key != "fondo.png":
        abort(404)

    minio_base = os.getenv("MINIO_PUBLIC_URL")
    bucket = os.getenv("MINIO_BUCKET")
    access_key = os.getenv("MINIO_ROOT_USER")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD")

    if not minio_base or not bucket or not access_key or not secret_key:
        # Mejor: loguea para saber qué falta
        current_app.logger.error(
            "Missing MinIO config: MINIO_PUBLIC_URL=%r MINIO_BUCKET=%r MINIO_ACCESS_KEY=%r MINIO_SECRET_KEY=%r",
            minio_base, bucket, bool(access_key), bool(secret_key)
        )
        abort(500)

    u = urlparse(minio_base)
    endpoint = u.netloc or u.path  # por si te pasan "minio:9000" sin esquema
    secure = (u.scheme == "https")

    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    try:
        obj = client.get_object(bucket, key)
    except S3Error:
        abort(404)

    content_type, _ = mimetypes.guess_type(key)
    if not content_type:
        content_type = "application/octet-stream"

    def stream():
        try:
            for data in obj.stream(32 * 1024):
                yield data
        finally:
            obj.close()
            obj.release_conn()

    return Response(stream(), mimetype=content_type)