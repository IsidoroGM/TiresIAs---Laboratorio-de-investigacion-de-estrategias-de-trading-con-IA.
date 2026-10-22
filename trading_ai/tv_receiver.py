"""Receptor de ensayo: solo loopback, autenticado, sin procesar la contabilidad."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import re
import threading

from trading_ai.tv_contracts import canonical
from trading_ai.local_http import discard_small_body


class InboxServer(ThreadingHTTPServer):
    daemon_threads = False
    request_queue_size = 4

    def __init__(self, address, handler, workers):
        self.slots = threading.BoundedSemaphore(workers)
        super().__init__(address, handler)

    def process_request(self, request, address):
        request.settimeout(2)
        if not self.slots.acquire(blocking=False):
            try:
                request.settimeout(0.1)
                headers = b""
                while b"\r\n\r\n" not in headers and len(headers) < 16384:
                    part = request.recv(4096)
                    if not part: break
                    headers += part
                request.sendall(b"HTTP/1.0 503 Service Unavailable\r\nContent-Length: 0\r\nRetry-After: 1\r\nConnection: close\r\n\r\n")
            except OSError: pass
            finally: self.shutdown_request(request)
            return
        try: super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try: super().process_request_thread(request, address)
        finally: self.slots.release()


def create_receiver(ledger, *, token, port=8766, workers=4):
    """No acepta dirección de red ni imprime el secreto. Requiere un emisor local.

    TradingView no puede acceder a 127.0.0.1. Un futuro relay HTTPS externo requiere
    su propio diseño y configuración; este receptor no se publica por sí solo.
    """
    if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", token): raise ValueError("Se requiere un token local de 32 a 128 caracteres seguros.")
    if type(port) is not int or not 0 <= port <= 65535: raise ValueError("Puerto inválido.")
    if type(workers) is not int or not 1 <= workers <= 8: raise ValueError("Concurrencia inválida.")
    expected_auth = ("Bearer " + token).encode("ascii")

    class Handler(BaseHTTPRequestHandler):
        server_version = "TiresIAsInbox"

        def log_message(self, *_): pass

        def reply(self, status, value):
            if status >= 400 and self.command == "POST": discard_small_body(self)
            raw = canonical(value)
            self.close_connection = True
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Connection", "close")
            self.end_headers()
            if self.command != "HEAD": self.wfile.write(raw)

        def do_POST(self):
            hosts = {f"localhost:{self.server.server_port}", f"127.0.0.1:{self.server.server_port}"}
            # Un navegador no debe poder usar esta ruta como formulario/acción.
            if self.headers.get_all("Host", []) != [self.headers.get("Host")] or self.headers.get("Host") not in hosts or self.headers.get("Origin") is not None:
                self.reply(403, {"error": "Emisor local sin origen de navegador requerido."}); return
            if self.path != "/events":
                self.reply(404, {"error": "Ruta desconocida."}); return
            authorization = self.headers.get_all("Authorization", [])
            try: authorized = len(authorization) == 1 and hmac.compare_digest(authorization[0].encode("ascii"), expected_auth)
            except UnicodeError: authorized = False
            if not authorized:
                self.reply(401, {"error": "Autenticación requerida."}); return
            sizes = self.headers.get_all("Content-Length", [])
            if self.headers.get("Transfer-Encoding") is not None or len(sizes) != 1 or not re.fullmatch(r"[0-9]{1,6}", sizes[0]):
                self.reply(400, {"error": "Longitud única requerida; no se acepta transferencia fragmentada."}); return
            size = int(sizes[0])
            if not 1 <= size <= 65536:
                self.reply(413, {"error": "Evento entre 1 y 65536 bytes requerido."}); return
            content_types = self.headers.get_all("Content-Type", [])
            if len(content_types) != 1 or content_types[0].lower() not in ("application/json", "application/json; charset=utf-8"):
                self.reply(415, {"error": "JSON UTF-8 requerido."}); return
            try:
                raw = self.rfile.read(size)
                if len(raw) != size:
                    self.reply(400, {"error": "Cuerpo incompleto; no se conserva como ejecución."}); return
                # receive confirma solo después de commit. Puede guardar un original
                # inválido/desconocido, cuya recepción tampoco equivale a ejecución.
                receipt = ledger.receive(raw, transport="authenticated_webhook", source={"receiver": "loopback_v1"})
                self.reply(202, {**receipt, "durably_received": True, "accounting_processed": False})
            except (ValueError, OSError):
                # No revelar rutas, SQL, eventos ni secretos en un error de transporte.
                self.reply(503, {"error": "No se puede confirmar almacenamiento duradero; revisar antes de reintentar."})

        def unsupported(self): self.reply(405, {"error": "Solo POST /events; recibir no contabiliza."})
        do_GET = do_HEAD = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = unsupported

    return InboxServer(("127.0.0.1", port), Handler, workers)
