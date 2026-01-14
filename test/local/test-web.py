#!/usr/bin/env python3
import json
import sys
import time
import urllib.request
import urllib.error


def http_get_json(url: str, timeout: int = 5):
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="replace")
            code = r.getcode()
    except urllib.error.HTTPError as e:
        code = e.code
        body = e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None, None, str(e)

    try:
        data = json.loads(body)
    except Exception:
        data = None

    return code, data, body


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def wait_for_health(base_url: str, timeout_s: int = 30) -> dict:
    """
    Espera hasta que /health devuelva JSON (200 o 503) para poder leer db/cache.
    Si no hay respuesta útil, termina en error.
    """
    deadline = time.time() + timeout_s
    last_body = ""
    last_code = None

    while time.time() < deadline:
        code, data, body = http_get_json(f"{base_url}/health", timeout=3)
        last_code = code
        last_body = body

        if isinstance(data, dict) and code in (200, 503):
            return data

        time.sleep(2)

    # Si tras timeout no conseguimos JSON, consideramos que el endpoint no es usable
    print("endpoint /health.....fail")
    print(f"Último código: {last_code}")
    print(f"Último body: {last_body}")
    sys.exit(1)


def main():
    if len(sys.argv) < 3:
        print("Uso: scripts/local_integration_tests.py <dev|pro> <base_url>", file=sys.stderr)
        print("Ej: scripts/local_integration_tests.py dev http://app.dev.localhost", file=sys.stderr)
        print("Ej: scripts/local_integration_tests.py pro http://app.pro.localhost", file=sys.stderr)
        sys.exit(2)

    env = sys.argv[1].strip().lower()
    base_url = sys.argv[2].strip().rstrip("/")

    if env not in ("dev", "pro"):
        fail("El primer argumento debe ser dev o pro")

    print(f"Running local integration tests: entorno {env} contra {base_url}")

    data = wait_for_health(base_url, timeout_s=30)
    print("endpoint /health.....ok")

    ok_all = True

    if data.get("db") is not True:
        print("Base de datos........fail")
        ok_all = False
    else:
        print("Base de datos........ok")

    if env == "pro":
        if data.get("cache") is not True:
            print("Redis................fail")
            ok_all = False
        else:
            print("Redis................ok")

    # Exit code para automatización
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()