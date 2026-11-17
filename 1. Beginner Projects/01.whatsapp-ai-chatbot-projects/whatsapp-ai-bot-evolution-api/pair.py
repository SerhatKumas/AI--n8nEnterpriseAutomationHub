#!/usr/bin/env python3
"""Display the Escape Towns pairing QR locally, using the existing SSH key."""
import argparse
import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REMOTE = """
import json, subprocess, urllib.request
container = json.loads(subprocess.check_output(['sudo', 'docker', 'inspect', 'evolution_api']))[0]
env = dict(value.split('=', 1) for value in container['Config']['Env'])
def get(path):
    request = urllib.request.Request('http://127.0.0.1:8080' + path,
        headers={'apikey': env['AUTHENTICATION_API_KEY']})
    return json.load(urllib.request.urlopen(request, timeout=15))
state = get('/instance/connectionState/escapetowns')['instance']['state']
result = {'state': state}
if state != 'open':
    qr = get('/instance/connect/escapetowns')
    result['base64'] = qr.get('base64')
print(json.dumps(result))
"""

PAGE = b"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>Connect Escape Towns</title>
<style>body{font:18px system-ui;max-width:620px;margin:50px auto;padding:20px;text-align:center}
img{width:320px;max-width:100%;image-rendering:pixelated}p{line-height:1.5}</style>
<h1>Connect Escape Towns</h1>
<p>On your phone, open WhatsApp &rarr; Settings &rarr; Linked Devices &rarr; Link a Device.</p>
<img id="qr" alt="WhatsApp pairing QR code" hidden><p id="status">Loading QR code...</p>
<p>This page refreshes the QR automatically. Keep it private.</p>
<script>
async function refresh(){
 const status=document.getElementById('status'), image=document.getElementById('qr');
 try {
  const r=await fetch('/qr',{cache:'no-store'}), d=await r.json();
  if(!r.ok) throw new Error(d.error||'Could not load QR');
  if(d.state==='open'){image.hidden=true;status.textContent='Connected! Escape Towns is linked to WhatsApp.';return;}
  image.hidden=!d.base64;
  if(d.base64) image.src=d.base64;
  status.textContent=d.base64?'Scan this QR with your phone.':'Waiting for WhatsApp to issue a QR...';
 }catch(e){image.hidden=true;status.textContent=e.message;}
 setTimeout(refresh,15000);
}
refresh();
</script></html>"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', default='ubuntu@89.168.108.192')
    parser.add_argument('--key', default=str(Path.home() / '.ssh/id_ed25519'))
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                data, kind, status = PAGE, 'text/html; charset=utf-8', 200
            elif self.path == '/qr':
                try:
                    result = subprocess.run(
                        ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                         '-i', args.key, args.server, 'python3 -'],
                        input=REMOTE, text=True, capture_output=True, timeout=50, check=True)
                    data = json.dumps(json.loads(result.stdout)).encode()
                    status = 200
                except (subprocess.SubprocessError, ValueError):
                    data = b'{"error":"Cannot retrieve QR. Check SSH access and Evolution API health."}'
                    status = 502
                kind = 'application/json'
            else:
                self.send_error(404)
                return
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = HTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Open http://127.0.0.1:{args.port} and scan with WhatsApp. Ctrl+C stops the page.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
