"""Local preview with consistent ES-module MIME types on Windows and Linux."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml'}

if __name__=='__main__':
    root=Path(__file__).resolve().parent/'docs'
    server=ThreadingHTTPServer(('127.0.0.1',8765),partial(Handler,directory=str(root)))
    print('Preview: http://127.0.0.1:8765',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()
