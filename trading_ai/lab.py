"""Servidor local explícito de TiresIAs. Todas las rutas son de consulta."""

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from trading_ai.lab_catalog import ROOT, ERRORS
from trading_ai.lab_query import LabQuery


ASSETS = Path(__file__).with_name("lab_static")
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"


def create_server(*, root=ROOT, port=8765):
    """La dirección no es configurable: nunca escucha en interfaces de red."""
    if type(port) is not int or not 0 <= port <= 65535: raise ValueError("Puerto inválido.")
    project_root = Path(root).resolve()

    class Handler(BaseHTTPRequestHandler):
        server_version = "TiresIAs"

        def log_message(self, *_):
            pass

        def _send(self, status, content, mime="application/json; charset=utf-8", *, head=False):
            if not isinstance(content, bytes):
                content = json.dumps(content, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", CSP)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            if not head: self.wfile.write(content)

        def _allowed(self):
            port = self.server.server_port
            hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
            if self.headers.get("Host") not in hosts: return False
            origin = self.headers.get("Origin")
            return origin is None or origin in {"http://" + host for host in hosts}

        def _get(self, head=False):
            if not self._allowed():
                self._send(403, {"error": "Solo se permiten consultas desde el origen local de TiresIAs."}, head=head)
                return
            if len(self.path) > 4096:
                self._send(414, {"error": "Consulta demasiado larga."}, head=head)
                return
            parsed = urlsplit(self.path)
            route = parsed.path
            static = {"/": ("index.html", "text/html; charset=utf-8"),
                      "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                      "/style.css": ("style.css", "text/css; charset=utf-8")}
            try:
                if route in static:
                    name, mime = static[route]
                    self._send(200, (ASSETS / name).read_bytes(), mime, head=head)
                    return
                query = LabQuery(project_root)
                args = parse_qs(parsed.query, max_num_fields=16)
                params = {key: values[-1] for key, values in args.items()}
                parts = route.strip("/").split("/")
                if route == "/api/home": result = query.home()
                elif route == "/api/experiments": result = query.experiments(params)
                elif route == "/api/consumption": result = query.consumption()
                elif route == "/api/compare":
                    left, right = params.get("left", "").split(":"), params.get("right", "").split(":")
                    if len(left) != 2 or len(right) != 2: raise ValueError("Selecciona dos cuentas.")
                    result = query.compare(*left, *right)
                elif len(parts) == 3 and parts[:2] == ["api", "experiments"]:
                    result = query.detail(parts[2])
                elif len(parts) == 5 and parts[:2] == ["api", "experiments"] and parts[3] == "accounts":
                    result = query.account(parts[2], parts[4])
                elif len(parts) == 2 and parts[0] == "sources":
                    _, raw = query.catalog.file(parts[1])
                    self._send(200, raw, "text/plain; charset=utf-8", head=head)
                    return
                else:
                    self._send(404, {"error": "Ruta no disponible."}, head=head)
                    return
                self._send(200, result, head=head)
            except KeyError:
                self._send(404, {"error": "Registro o archivo no catalogado."}, head=head)
            except ERRORS as error:
                self._send(422, {"error": "Consulta incompleta: " + str(error)}, head=head)

        def do_GET(self): self._get()
        def do_HEAD(self): self._get(head=True)

        def _readonly(self):
            self._send(405, {"error": "La interfaz solo admite consultas GET y HEAD."})

        do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = _readonly

    # HTTPServer secuencial: sin parches globales ni verificadores concurrentes.
    return HTTPServer(("127.0.0.1", port), Handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description="TiresIAs — interfaz local de consulta del laboratorio")
    parser.add_argument("--port", type=int, default=8765, help="Puerto local (8765 por defecto)")
    args = parser.parse_args(argv)
    try:
        with create_server(port=args.port) as server:
            print(f"TiresIAs: http://127.0.0.1:{server.server_port} — cerrar con Ctrl+C", flush=True)
            try: server.serve_forever()
            except KeyboardInterrupt: print("\nTiresIAs cerrado.")
    except (OSError, ValueError) as error:
        parser.exit(1, f"No se pudo abrir TiresIAs: {error}\n")


if __name__ == "__main__": main()
