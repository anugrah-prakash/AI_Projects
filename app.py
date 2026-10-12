"""Run with python app.py; open http://127.0.0.1:8501."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from core import ROOT, settings, prepare, generate
from demo import sample_report

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Do not log user evidence or API credentials.

    def send(self, status, payload, content_type='application/json; charset=utf-8'):
        body = json.dumps(payload, ensure_ascii=False).encode() if isinstance(payload, dict) else payload
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = urlparse(self.path).path
        if route == '/api/defaults':
            self.send(200, json.loads((ROOT/'sample_data.json').read_text(encoding='utf-8')))
        elif route == '/api/status':
            config = settings()
            self.send(200, {'key_configured': bool(config['OPENAI_API_KEY']), 'model': config['OPENAI_MODEL']})
        elif route in ['/', '/app.js', '/style.css']:
            name = {'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[route]
            mime = {'/':'text/html','/app.js':'text/javascript','/style.css':'text/css'}[route]
            self.send(200, (ROOT/'static'/name).read_bytes(), mime+'; charset=utf-8')
        else: self.send(404, {'error':'Not found.'})

    def do_POST(self):
        # Only accept browser same-origin JSON calls; server binds to loopback only.
        expected = f'http://{self.headers.get("Host", "")}'
        if self.headers.get('Origin') not in (None, expected) or self.headers.get('Sec-Fetch-Site') == 'cross-site':
            return self.send(403, {'error':'Cross-origin requests are not accepted.'})
        if self.path != '/api/compare': return self.send(404, {'error':'Not found.'})
        if self.headers.get('Content-Type','').split(';')[0] != 'application/json':
            return self.send(415, {'error':'Expected JSON.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 100000: raise ValueError('Request is empty or too large.')
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict): raise ValueError('Expected an object.')
            context = prepare(data)
            demo = data.get('demo') is True
            if demo:
                defaults = json.loads((ROOT/'sample_data.json').read_text(encoding='utf-8'))
                if any(data.get(k) != defaults[k] for k in ['goal','brief','feedback','competitors','constraints']):
                    raise ValueError('Offline sample mode supports the original fictional scenario and budget changes only. Reset the sample or use live AI for edited inputs.')
            report = sample_report(context) if demo else generate(context, settings())
            self.send(200, {'report':report,'context':context,'demo':demo,'model':'Offline sample' if demo else settings()['OPENAI_MODEL']})
        except (ValueError, TypeError) as error: self.send(400, {'error':str(error)})
        except Exception: self.send(500, {'error':'Unexpected server error. Restart the app and retry.'})

if __name__ == '__main__':
    port = int(settings()['PORT'])
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'AI Strategy Copilot: http://127.0.0.1:{port}\nPress Ctrl+C to stop.')
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
