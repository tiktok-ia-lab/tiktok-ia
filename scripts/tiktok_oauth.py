import hashlib
import os
import secrets
import string
import threading
import time
import urllib.parse
import webbrowser

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests
from dotenv import load_dotenv


# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

ENV_PATH = ROOT / ".env"

load_dotenv(ENV_PATH)

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")

AUTHORIZE_URL = (
    "https://www.tiktok.com/v2/auth/authorize/"
)

TOKEN_URL = (
    "https://open.tiktokapis.com/v2/oauth/token/"
)

SCOPES = [
    "user.info.basic",
    "video.list",
]


if not CLIENT_KEY:
    raise SystemExit(
        "ERROR: falta TIKTOK_CLIENT_KEY en .env"
    )

if not CLIENT_SECRET:
    raise SystemExit(
        "ERROR: falta TIKTOK_CLIENT_SECRET en .env"
    )

if not REDIRECT_URI:
    raise SystemExit(
        "ERROR: falta TIKTOK_REDIRECT_URI en .env"
    )


# ============================================================
# PKCE
# ============================================================

def generate_code_verifier(length=64):
    """
    TikTok Desktop PKCE:
    verifier entre 43 y 128 caracteres.
    """

    alphabet = (
        string.ascii_letters
        + string.digits
        + "-._~"
    )

    return "".join(
        secrets.choice(alphabet)
        for _ in range(length)
    )


def generate_code_challenge(code_verifier):
    """
    TikTok Desktop usa SHA256 en hexadecimal.
    """

    return hashlib.sha256(
        code_verifier.encode("utf-8")
    ).hexdigest()


# ============================================================
# CALLBACK STATE
# ============================================================

callback_result = {
    "code": None,
    "state": None,
    "error": None,
    "error_description": None,
}


class CallbackHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        parsed = urllib.parse.urlparse(
            self.path
        )

        params = urllib.parse.parse_qs(
            parsed.query
        )

        callback_result["code"] = (
            params.get("code", [None])[0]
        )

        callback_result["state"] = (
            params.get("state", [None])[0]
        )

        callback_result["error"] = (
            params.get("error", [None])[0]
        )

        callback_result[
            "error_description"
        ] = params.get(
            "error_description",
            [None],
        )[0]

        body = """
        <html>
        <head>
            <meta charset="utf-8">
            <title>TikTok OAuth</title>
        </head>
        <body>
            <h1>Autorización recibida</h1>
            <p>
                Puedes cerrar esta pestaña y volver
                a la terminal.
            </p>
        </body>
        </html>
        """

        data = body.encode("utf-8")

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(data))
        )
        self.end_headers()

        self.wfile.write(data)

    def log_message(self, format, *args):
        return


# ============================================================
# LOCAL CALLBACK SERVER
# ============================================================

def parse_callback_server():

    parsed = urllib.parse.urlparse(
        REDIRECT_URI
    )

    host = parsed.hostname
    port = parsed.port

    if not host or not port:
        raise SystemExit(
            "ERROR: TIKTOK_REDIRECT_URI "
            "debe incluir host y puerto"
        )

    return host, port


def run_callback_server():

    host, port = parse_callback_server()

    server = HTTPServer(
        (host, port),
        CallbackHandler,
    )

    print()
    print(
        f"Callback escuchando en "
        f"http://{host}:{port}"
    )

    server.handle_request()

    server.server_close()


# ============================================================
# TOKEN EXCHANGE
# ============================================================

def exchange_code_for_tokens(
    code,
    code_verifier
):

    payload = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": (
            "authorization_code"
        ),
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    }

    response = requests.post(
        TOKEN_URL,
        data=payload,
        headers={
            "Content-Type": (
                "application/"
                "x-www-form-urlencoded"
            ),
            "Cache-Control": "no-cache",
        },
        timeout=30,
    )

    if not response.ok:
        print()
        print(
            "ERROR intercambiando "
            "authorization code:"
        )
        print(
            "HTTP",
            response.status_code
        )
        print(response.text)

        raise SystemExit(1)

    return response.json()


# ============================================================
# SAVE TOKENS
# ============================================================

def update_env(tokens):

    access_token = tokens.get(
        "access_token"
    )

    refresh_token = tokens.get(
        "refresh_token"
    )

    open_id = tokens.get(
        "open_id"
    )

    if not access_token:
        raise SystemExit(
            "ERROR: TikTok no devolvió "
            "access_token"
        )

    lines = []

    if ENV_PATH.exists():
        lines = ENV_PATH.read_text().splitlines()

    values = {
        "TIKTOK_ACCESS_TOKEN":
            access_token,
        "TIKTOK_REFRESH_TOKEN":
            refresh_token or "",
        "TIKTOK_OPEN_ID":
            open_id or "",
    }

    existing_keys = set()

    new_lines = []

    for line in lines:

        if "=" not in line:
            new_lines.append(line)
            continue

        key = line.split(
            "=",
            1
        )[0].strip()

        if key in values:

            new_lines.append(
                f"{key}={values[key]}"
            )

            existing_keys.add(key)

        else:
            new_lines.append(line)

    for key, value in values.items():

        if key not in existing_keys:

            new_lines.append(
                f"{key}={value}"
            )

    ENV_PATH.write_text(
        "\n".join(new_lines) + "\n"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    state = secrets.token_urlsafe(32)

    code_verifier = (
        generate_code_verifier()
    )

    code_challenge = (
        generate_code_challenge(
            code_verifier
        )
    )

    params = {
        "client_key": CLIENT_KEY,
        "response_type": "code",
        "scope": ",".join(SCOPES),
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "code_challenge":
            code_challenge,
        "code_challenge_method":
            "S256",
    }

    authorization_url = (
        AUTHORIZE_URL
        + "?"
        + urllib.parse.urlencode(
            params
        )
    )

    server_thread = threading.Thread(
        target=run_callback_server,
        daemon=True,
    )

    server_thread.start()

    time.sleep(0.4)

    print()
    print("=" * 72)
    print("TIKTOK OAUTH")
    print("=" * 72)

    print()
    print(
        "Se abrirá TikTok en el navegador."
    )

    print(
        "Autoriza solamente los scopes "
        "que esperas:"
    )

    print(
        "  user.info.basic"
    )

    print(
        "  video.list"
    )

    print()

    webbrowser.open(
        authorization_url
    )

    server_thread.join(
        timeout=300
    )

    if callback_result["error"]:

        print()
        print(
            "TikTok devolvió un error:"
        )

        print(
            callback_result["error"]
        )

        if callback_result[
            "error_description"
        ]:
            print(
                callback_result[
                    "error_description"
                ]
            )

        raise SystemExit(1)

    code = callback_result["code"]

    returned_state = (
        callback_result["state"]
    )

    if not code:
        raise SystemExit(
            "ERROR: no se recibió "
            "authorization code"
        )

    if returned_state != state:
        raise SystemExit(
            "ERROR: state OAuth no coincide"
        )

    print(
        "Authorization code recibido."
    )

    print(
        "Intercambiando por tokens..."
    )

    tokens = exchange_code_for_tokens(
        code,
        code_verifier
    )

    granted_scope = tokens.get(
        "scope",
        ""
    )

    print()
    print("=" * 72)
    print("AUTORIZACIÓN COMPLETADA")
    print("=" * 72)

    print()
    print(
        "Scopes concedidos:"
    )

    print(
        f"  {granted_scope}"
    )

    print()
    print(
        "Access token recibido: YES"
    )

    print(
        "Refresh token recibido:",
        "YES"
        if tokens.get(
            "refresh_token"
        )
        else "NO",
    )

    update_env(tokens)

    print()
    print(
        "Tokens guardados en .env"
    )

    print(
        "No los muestres ni los añadas "
        "a Git."
    )


if __name__ == "__main__":
    main()