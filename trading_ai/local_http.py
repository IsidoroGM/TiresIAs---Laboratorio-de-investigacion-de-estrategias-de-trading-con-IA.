"""Rechazos HTTP locales: consumir cuerpos pequeños evita RST prematuro en Windows."""


def discard_small_body(handler):
    sizes = handler.headers.get_all("Content-Length", [])
    if len(sizes) != 1 or not sizes[0].isascii() or not sizes[0].isdigit() or len(sizes[0]) > 6: return
    size = int(sizes[0])
    if not 0 < size <= 65536: return
    timeout = handler.connection.gettimeout()
    try:
        handler.connection.settimeout(0.05)
        handler.rfile.read(size)
    except OSError: pass
    finally: handler.connection.settimeout(timeout)
