import mimetypes
from urllib.parse import urlparse
import os
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    jsonify,
    current_app,
    url_for,
    Response,
    abort,
)
from http import HTTPStatus
import mysql.connector
from mysql.connector import Error
from urllib.parse import quote
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
            database=current_app.config["MYSQL_DATABASE"],
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
    return render_template(
        "index.html",
        container_name=container_name,
        background_url=background_url,
        use_cache=current_app.config.get("USE_CACHE", False),
    )


@bp.route("/usuarios/json", methods=["GET"])
def listar_usuarios_json():
    cache_key = "usuarios_todos"
    usuarios = None
    cache_accessible = False
    use_cache = current_app.config.get("USE_CACHE", False)

    try:
        usuarios = get_cache(cache_key)
        cache_accessible = (
            True  # si get_cache pudo hablar con redis (aunque no haya key)
        )
    except Exception as e:
        print(f"Error accediendo a Redis: {e}")
        cache_accessible = False

    if usuarios is not None:
        return jsonify({"usuarios": usuarios}), HTTPStatus.OK

    conn = get_connection()
    if conn is None:
        if use_cache:
            if cache_accessible:
                return "BBDD caída y caché vacía.", HTTPStatus.SERVICE_UNAVAILABLE
            return "BBDD y caché no disponibles.", HTTPStatus.SERVICE_UNAVAILABLE
        return (
            "No se pudo conectar con la base de datos",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"No se pudo cargar los usuarios: {e}")
        return "No se pudo cargar los usuarios", HTTPStatus.SERVICE_UNAVAILABLE

    # Intentar guardar en caché
    try:
        set_cache(cache_key, usuarios)
    except Exception as e:
        print(f"No se pudo guardar en Redis: {e}")

    return jsonify({"usuarios": usuarios}), HTTPStatus.OK


@bp.route("/set", methods=["POST"])
def set_user():
    nombre = request.form["nombre"]
    apellido = request.form["apellido"]
    edad = request.form["edad"]
    correo = request.form["correo"]
    ciudad = request.form["ciudad"]

    conn = get_connection()
    if conn is None:
        return redirect("/?msg=" + quote("No se pudo conectar con la base de datos"))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO usuarios (nombre, apellido, edad, correo, ciudad)
            VALUES (%s, %s, %s, %s, %s)
        """,
            (nombre, apellido, edad, correo, ciudad),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error insertando en MySQL: {e}")

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
            return redirect(
                "/?msg=" + quote("No se pudo conectar con la base de datos")
            )

        try:
            cursor = conn.cursor()
            formato = ",".join(["%s"] * len(ids))
            cursor.execute(f"DELETE FROM usuarios WHERE id IN ({formato})", ids)
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error borrando en MySQL: {e}")

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
    db_ok = check_db()
    status["db: "] = "up" if db_ok else "down"

    use_cache = current_app.config.get("USE_CACHE", False)

    cache_ok = None
    if use_cache:
        cache_ok = check_cache()
        if cache_ok:
            status["cache: "] = "up"
        else:
            status["cache: "] = "down"

    return render_template("status.html", status=status)


def check_db() -> bool:
    conn = None
    try:
        conn = get_connection()
        return conn is not None
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def check_cache() -> bool:
    try:
        from .cache import get_cache_connection

        cache = get_cache_connection()
        return bool(cache) and bool(cache.ping())
    except Exception:
        return False


@bp.route("/live", methods=["GET"])
def live():
    """Liveness: solo confirma que Flask responde HTTP."""
    return jsonify({"ok": True}), HTTPStatus.OK


@bp.route("/health", methods=["GET"])
def health():
    """
    Health para pipeline/tests:
      - DB siempre requerida
      - Redis solo si USE_CACHE=True
    Devuelve 200 si todo lo requerido está OK, si no 503.
    """
    db_ok = check_db()

    use_cache = current_app.config.get("USE_CACHE", False)
    cache_ok = None
    if use_cache:
        cache_ok = check_cache()

    ok = db_ok and (cache_ok if use_cache else True)
    code = HTTPStatus.OK if ok else HTTPStatus.SERVICE_UNAVAILABLE

    return (
        jsonify({"ok": ok, "db": db_ok, "cache": cache_ok if use_cache else None}),
        code,
    )


@bp.route("/ready", methods=["GET"])
def ready():
    """
    Readiness para Kubernetes:
      - DEV (USE_CACHE=False): requiere DB
      - PRO (USE_CACHE=True): DB OR Redis (modo degradado)
    """
    db_ok = check_db()

    use_cache = current_app.config.get("USE_CACHE", False)
    cache_ok = None
    if use_cache:
        cache_ok = check_cache()
        ready_ok = db_ok or cache_ok
    else:
        ready_ok = db_ok

    code = HTTPStatus.OK if ready_ok else HTTPStatus.SERVICE_UNAVAILABLE

    return (
        jsonify(
            {"ready": ready_ok, "db": db_ok, "cache": cache_ok if use_cache else None}
        ),
        code,
    )


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
            minio_base,
            bucket,
            bool(access_key),
            bool(secret_key),
        )
        abort(500)

    u = urlparse(minio_base)
    endpoint = u.netloc or u.path  # por si te pasan "minio:9000" sin esquema
    secure = u.scheme == "https"

    client = Minio(
        endpoint, access_key=access_key, secret_key=secret_key, secure=secure
    )

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
