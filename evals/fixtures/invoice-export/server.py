#!/usr/bin/env python3
"""Loopback-only E2E fixture: browser -> HTTP -> SQLite -> persisted readback.

This is a synthetic evaluation application, not a production invoicing service.
Use public-safe identifiers only. Each explicit submission replaces the latest export.
"""
import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sqlite3

from worker import export_invoice_ids


STYLE = """
body { margin: 0; color: #202a26; background: #f6f7f3; font: 18px/1.5 system-ui, sans-serif; }
main { max-width: 680px; margin: 36px auto; padding: 28px 36px; border: 1px solid #c8d0c8; background: white; }
h1 { margin: 12px 0; font-size: 36px; line-height: 1.15; }
label, textarea, output { display: block; }
label { font-weight: 650; margin-top: 20px; }
textarea { box-sizing: border-box; width: 100%; margin: 8px 0; padding: 12px; font: 18px/1.4 monospace; }
button { padding: 10px 18px; margin-top: 16px; font: inherit; color: white; background: #245a42; border: 0; cursor: pointer; }
button:disabled { opacity: .6; cursor: wait; }
a { color: #245a42; text-underline-offset: 3px; }
output { margin: 12px 0; min-height: 27px; }
li { padding: 5px 0; font-family: monospace; }
.eyebrow { font-size: 13px; letter-spacing: .12em; }
.note { font-size: 14px; color: #526159; border-top: 1px solid #c8d0c8; padding-top: 16px; }
[hidden] { display: none; }
:focus-visible { outline: 3px solid #b77812; outline-offset: 3px; }
"""
FORM = r"""
<h1>Invoice export</h1>
<p>Remove repeated identifiers, keep their first-appearance order, and save the result.</p>
<form id="export-form">
  <label for="invoice-ids">Invoice identifiers, one per line</label>
  <textarea id="invoice-ids" rows="4" autocomplete="off" spellcheck="false"></textarea>
  <div id="input-status" aria-live="polite">0 identifiers entered</div>
  <button id="export" type="submit">Save unique export</button>
</form>
<output id="summary" aria-live="polite"></output>
<a id="view-export" href="/saved" hidden>View saved export</a>
<script>
const form = document.querySelector('#export-form');
const input = document.querySelector('#invoice-ids');
const status = document.querySelector('#input-status');
const summary = document.querySelector('#summary');
const link = document.querySelector('#view-export');
const button = document.querySelector('#export');
const identifiers = () => input.value.split(/\r?\n/).filter(value => value.length > 0);
input.addEventListener('input', () => {
  status.textContent = `${identifiers().length} identifiers entered`;
});
form.addEventListener('submit', async event => {
  event.preventDefault();
  button.disabled = true;
  link.hidden = true;
  summary.textContent = 'Saving export…';
  try {
    const response = await fetch('/exports', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ids: identifiers()})
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    summary.textContent = `Export saved: ${result.ids.length} unique invoices from ${result.source_count} identifiers.`;
    link.hidden = false;
  } catch (error) {
    summary.textContent = `Export failed: ${error.message}`;
  } finally {
    button.disabled = false;
  }
});
</script>
"""


def page(body):
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Invoice export · Deepmode E2E fixture</title><style>' + STYLE + '</style></head>'
            '<body><main><p class="eyebrow">DEEPMODE / E2E FIXTURE</p>' + body +
            '<p class="note">Local evaluation fixture. Synthetic identifiers only; no customer data.</p>'
            '</main></body></html>').encode('utf-8')


class Handler(BaseHTTPRequestHandler):
    def send(self, status, content, content_type='text/html; charset=utf-8'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, status, value):
        self.send(status, json.dumps(value).encode('utf-8'), 'application/json')

    def do_GET(self):
        if self.path == '/':
            self.send(200, page(FORM))
        elif self.path == '/saved':
            with sqlite3.connect(self.server.database) as database:
                row = database.execute('SELECT ids_json, source_count FROM exports WHERE id = 1').fetchone()
            if row is None:
                self.send(404, page('<h1>No export saved</h1><a href="/">Create an export</a>'))
                return
            ids = json.loads(row[0])
            items = ''.join('<li>' + html.escape(value) + '</li>' for value in ids)
            self.send(200, page('<h1>Saved invoice export</h1><p id="saved-count">' +
                               f'{len(ids)} unique invoices from {row[1]} identifiers</p>' +
                               '<ol id="invoice-list">' + items + '</ol><a href="/">Start another export</a>'))
        elif self.path == '/popup':
            self.send(200, page('<h1>Popup boundary fixture</h1>'
                               '<a id="popup" href="/" target="_blank" rel="noopener">Open another tab</a>'))
        elif self.path == '/favicon.ico':
            self.send(204, b'')
        else:
            self.send(404, page('<h1>Not found</h1>'))

    def do_POST(self):
        if self.path != '/exports':
            self.send_json(404, {'error': 'Unknown endpoint'})
            return
        expected_host = f'127.0.0.1:{self.server.server_port}'
        if self.headers.get('Host') != expected_host or self.headers.get('Origin') not in (None, 'http://' + expected_host):
            self.send_json(403, {'error': 'Loopback fixture origin required'})
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 1 <= size <= 32768 or self.headers.get_content_type() != 'application/json':
                raise ValueError('Expected bounded JSON')
            request = json.loads(self.rfile.read(size))
            ids = request.get('ids') if isinstance(request, dict) else None
            if not isinstance(ids, list) or len(ids) > 100 or not all(isinstance(value, str) and 1 <= len(value) <= 256 for value in ids):
                raise ValueError('Expected at most 100 nonempty identifiers, each at most 256 characters')
            unique = export_invoice_ids(ids)
            with sqlite3.connect(self.server.database) as database:
                database.execute('INSERT OR REPLACE INTO exports VALUES (1, ?, ?)', (json.dumps(unique), len(ids)))
            self.send_json(200, {'ids': unique, 'source_count': len(ids)})
        except (ValueError, UnicodeError) as error:
            self.send_json(400, {'error': str(error)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True, help='dedicated fixture database; latest row is replaced on submission')
    parser.add_argument('--port', type=int, default=18991)
    args = parser.parse_args()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.database) as database:
        database.execute('CREATE TABLE IF NOT EXISTS exports (id INTEGER PRIMARY KEY CHECK (id = 1), ids_json TEXT NOT NULL, source_count INTEGER NOT NULL)')
    with HTTPServer(('127.0.0.1', args.port), Handler) as server:
        server.database = args.database
        print(f'invoice-e2e listening http://127.0.0.1:{server.server_port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
