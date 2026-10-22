"""Servidor local de consulta y acciones explícitas de conversación."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from hashlib import sha256
import json
import secrets
from pathlib import Path
import threading
import time
from urllib.parse import parse_qs, urlsplit

from trading_ai.lab_catalog import ROOT, ERRORS
from trading_ai.lab_service import LabService


ASSETS = Path(__file__).with_name("lab_static")
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"


class BoundedServer(ThreadingHTTPServer):
    """Sin cola ilimitada ni un hilo nuevo por cada conexión recibida."""
    request_queue_size = 8
    daemon_threads = False

    def __init__(self, address, handler, service, workers, conversation=None):
        self.service = service
        self.conversation = conversation
        self._slots = threading.BoundedSemaphore(workers)
        super().__init__(address, handler)

    def process_request(self, request, address):
        request.settimeout(10)
        if not self._slots.acquire(blocking=False):
            try:
                # Consumir las cabeceras evita un cierre con RST en Windows,
                # que puede impedir al cliente recibir la respuesta 503.
                request.settimeout(0.1)
                headers = b""
                while b"\r\n\r\n" not in headers and len(headers) < 16384:
                    part = request.recv(4096)
                    if not part: break
                    headers += part
                request.sendall(b"HTTP/1.0 503 Service Unavailable\r\nContent-Length: 0\r\nRetry-After: 1\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n")
            except OSError: pass
            finally: self.shutdown_request(request)
            return
        try: super().process_request(request, address)
        except Exception:
            self._slots.release()
            raise

    def process_request_thread(self, request, address):
        try: super().process_request_thread(request, address)
        finally: self._slots.release()

    def server_close(self):
        try:
            super().server_close()
            if self.conversation is not None: self.conversation.close()
        finally: self.service.close()


def create_server(*, root=ROOT, port=8765, workers=4, refresh_interval=2.0, chat_provider=None):
    """La dirección no es configurable: nunca escucha en interfaces de red."""
    if type(port) is not int or not 0 <= port <= 65535: raise ValueError("Puerto inválido.")
    if type(workers) is not int or not 1 <= workers <= 8: raise ValueError("Concurrencia inválida.")
    project_root = Path(root).resolve()
    service = LabService(project_root, interval=refresh_interval)
    from trading_ai.conversation import ConversationService, strict
    conversation = ConversationService(project_root, provider=chat_provider)
    action_token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        server_version = "TiresIAs"

        def log_message(self, *_):
            pass

        def _send(self, status, content, mime="application/json; charset=utf-8", *, head=False, cache="no-store", etag=None):
            if not isinstance(content, bytes):
                content = json.dumps(content, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", mime)
            if status != 304: self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", cache)
            if etag: self.send_header("ETag", etag)
            self.send_header("Server-Timing", "request;dur=" + str(round((time.perf_counter() - self.started) * 1000, 2)))
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
            self.started = time.perf_counter()
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
                      "/chat.css": ("chat.css", "text/css; charset=utf-8"),
                      "/style.css": ("style.css", "text/css; charset=utf-8")}
            try:
                if route in static:
                    name, mime = static[route]
                    raw = (ASSETS / name).read_bytes()
                    etag = '"' + sha256(raw).hexdigest() + '"'
                    tags = [tag.strip().removeprefix("W/") for tag in self.headers.get("If-None-Match", "").split(",")]
                    matched = etag in tags or "*" in tags
                    self._send(304 if matched else 200, b"" if matched else raw, mime, head=head,
                               cache="private, no-cache", etag=etag)
                    return
                if route == "/api/chat":
                    self._send(200, {**conversation.overview(), "action_token": action_token}, head=head)
                    return
                if route == "/api/chat/source":
                    self._send(200, conversation.source(), head=head)
                    return
                chat_parts = route.strip("/").split("/")
                if len(chat_parts) in (3, 5) and chat_parts[:2] == ["api", "chat"]:
                    if len(chat_parts) == 3: result = conversation.detail(chat_parts[2])
                    elif chat_parts[3] == "results": result = conversation.result(chat_parts[2], chat_parts[4])
                    else: raise KeyError(route)
                    self._send(200, result, head=head)
                    return
                args = parse_qs(parsed.query, max_num_fields=16)
                params = {key: values[-1] for key, values in args.items()}
                parts = route.strip("/").split("/")
                force = params.pop("refresh", "") == "1"
                overviews = {"/api/home": "home", "/api/experiments": "experiments", "/api/consumption": "consumption"}
                detail_route = len(parts) == 3 and parts[:2] == ["api", "experiments"]
                account_route = len(parts) == 5 and parts[:2] == ["api", "experiments"] and parts[3] == "accounts"
                source_route = len(parts) == 2 and parts[0] == "sources"
                if route not in overviews and route != "/api/compare" and not (detail_route or account_route or source_route):
                    self._send(404, {"error": "Ruta no disponible."}, head=head)
                    return
                if route in overviews:
                    result = service.overview(overviews[route], force=force, filters=params)
                    if route == "/api/consumption": result["conversation"] = conversation.usage()
                    self._send(200, result, head=head)
                    return
                query, index = service.query(force=force)
                if route == "/api/compare":
                    left, right = params.get("left", "").split(":"), params.get("right", "").split(":")
                    if len(left) != 2 or len(right) != 2: raise ValueError("Selecciona dos cuentas.")
                    result = query.compare(*left, *right)
                elif detail_route:
                    result = query.detail(parts[2])
                elif account_route:
                    result = query.account(parts[2], parts[4])
                elif source_route:
                    _, raw = query.catalog.file(parts[1])
                    self._send(200, raw, "text/plain; charset=utf-8", head=head)
                    return
                else:
                    self._send(404, {"error": "Ruta no disponible."}, head=head)
                    return
                result["index"] = index
                self._send(200, result, head=head)
            except (ConnectionError, TimeoutError):
                raise
            except KeyError:
                self._send(404, {"error": "Registro o archivo no catalogado."}, head=head)
            except ERRORS as error:
                self._send(422, {"error": "Consulta incompleta: " + str(error)}, head=head)

        def do_GET(self):
            try: self._get()
            except (ConnectionError, TimeoutError): pass
        def do_HEAD(self):
            try: self._get(head=True)
            except (ConnectionError, TimeoutError): pass

        def _readonly(self):
            self.started = time.perf_counter()
            self._send(405, {"error": "La interfaz solo admite consultas GET y HEAD."})

        def do_POST(self):
            self.started = time.perf_counter()
            parts = urlsplit(self.path).path.strip("/").split("/")
            if parts[:2] != ["api", "chat"]:
                self._readonly()
                return
            origin = self.headers.get("Origin")
            fetch_site = self.headers.get("Sec-Fetch-Site")
            token = self.headers.get("X-Tiresias-Action", "")
            if (not self._allowed() or origin not in {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}
                    or fetch_site not in (None, "same-origin") or not secrets.compare_digest(token, action_token)):
                self._send(403, {"error": "Acción local no autenticada. Recarga TiresIAs."})
                return
            try:
                if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) != 1:
                    raise ValueError("Longitud de petición ambigua.")
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16384:
                    self._send(413, {"error": "Petición demasiado grande o vacía."})
                    return
                if self.headers.get("Content-Type") != "application/json":
                    self._send(415, {"error": "Se requiere application/json."})
                    return
                body = strict(self.rfile.read(length).decode("utf-8"))
                if not isinstance(body, dict): raise ValueError("Se requiere un objeto JSON.")
                if parts == ["api", "chat"]:
                    if set(body) != {"request_id", "title"}: raise ValueError("Campos de conversación desconocidos.")
                    result = conversation.create(body["request_id"], body["title"])
                elif len(parts) == 4 and parts[3] in ("messages", "experiments"):
                    result = conversation.submit(parts[2], "message" if parts[3] == "messages" else "experiment", body)
                elif len(parts) == 4 and parts[3] == "revisions": result = conversation.revise(parts[2], body)
                elif len(parts) == 5 and parts[3] == "cancel":
                    if body: raise ValueError("Cancelación sin campos adicionales.")
                    result = conversation.cancel(parts[2], parts[4])
                else: raise KeyError(self.path)
                self._send(202, result)
            except KeyError:
                self._send(404, {"error": "Conversación, revisión o acción inexistente."})
            except (ConnectionError, TimeoutError): pass
            except (ValueError, TypeError, OSError, RecursionError) as error:
                self._send(422, {"error": str(error)})

        do_PUT = do_PATCH = do_DELETE = do_OPTIONS = _readonly

    return BoundedServer(("127.0.0.1", port), Handler, service, workers, conversation)


def main(argv=None):
    parser = argparse.ArgumentParser(description="TiresIAs — laboratorio local y conversación con el agente")
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
