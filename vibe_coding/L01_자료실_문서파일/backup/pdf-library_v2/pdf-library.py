import json
import shutil
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent

class LibraryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        if url.path in ('/', '/pdf-library.html'):
            self.send_file(ROOT / 'pdf-library.html', 'text/html; charset=utf-8')
            return
        if url.path not in ('/api/folder', '/api/pdf', '/api/markdown'):
            self.send_error(404)
            return
        try:
            relative = parse_qs(url.query).get('path', [''])[0]
            target = (ROOT / relative).resolve()
            if not target.is_relative_to(ROOT):
                self.send_error(403)
                return
            if url.path in ('/api/pdf', '/api/markdown'):
                suffixes, media_type = (('.pdf',), 'application/pdf') if url.path == '/api/pdf' else (('.md', '.markdown'), 'text/plain; charset=utf-8')
                if target.suffix.lower() not in suffixes or not target.is_file():
                    self.send_error(404)
                    return
                self.send_file(target, media_type)
                return
            if not target.is_dir():
                self.send_error(404)
                return
            entries = []
            for child in target.iterdir():
                if not child.resolve().is_relative_to(ROOT):
                    continue
                if child.is_dir():
                    entries.append({'name': child.name, 'kind': 'directory'})
                elif child.suffix.lower() in ('.pdf', '.md', '.markdown') and child.is_file():
                    entries.append({'name': child.name, 'kind': 'file'})
            data = json.dumps({'root': ROOT.name or str(ROOT), 'entries': entries},
                              ensure_ascii=False).encode('utf-8')
            self.send_headers('application/json; charset=utf-8', len(data))
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except (OSError, ValueError, RuntimeError):
            self.send_error(404)

    def send_headers(self, content_type, size):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(size))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()

    def send_file(self, path, content_type):
        try:
            stream = path.open('rb')
        except OSError:
            self.send_error(404)
            return
        with stream:
            self.send_headers(content_type, path.stat().st_size)
            try:
                shutil.copyfileobj(stream, self.wfile)
            except (BrokenPipeError, ConnectionResetError):
                pass

if __name__ == '__main__':
    with ThreadingHTTPServer(('127.0.0.1', 0), LibraryHandler) as server:
        address = f'http://127.0.0.1:{server.server_port}/'
        print(f'PDF library: {address}', flush=True)
        print('Keep this window open. Press Ctrl+C to stop.', flush=True)
        webbrowser.open(address)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

