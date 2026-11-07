"""Run on hina-server. Install only the isolated TIRT collector and its Caddy route."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess

root = Path('/srv/docker/tirt-data')
assert Path(__file__).resolve().parent == root
config = root / 'config.json'
if not config.exists():
    with config.open('x') as stream:
        os.chmod(config, 0o600)
        json.dump({'ingest_token': secrets.token_urlsafe(36), 'read_token': secrets.token_urlsafe(36)}, stream)
    # The container is deliberately unprivileged; only this UID can read config.
    subprocess.run(['sudo', '-n', 'chown', '1000:1000', str(config)], check=True)
data = Path('/srv/shared/tirt-data')
subprocess.run(['sudo', '-n', 'mkdir', '-p', str(data)], check=True)
subprocess.run(['sudo', '-n', 'chown', '1000:1000', str(data)], check=True)
subprocess.run(['sudo', '-n', 'chmod', '700', str(data)], check=True)
subprocess.run(['docker', 'compose', 'up', '-d', '--build'], cwd=root, check=True)
subprocess.run(['curl', '--fail', '--silent', '--retry', '10', '--retry-connrefused', '--retry-all-errors',
                '--retry-delay', '1', 'http://127.0.0.1:8212/health'], check=True)
caddy = Path('/srv/docker/caddy/Caddyfile')
original = caddy.read_bytes()
text = original.decode()
marker = '\t# Hina Web (Next.js)'
block = '''\t# TIRT telemetry: authenticated durable batches, independent from the simulator
\tredir /tirt-data /tirt-data/
\thandle_path /tirt-data/* {
\t\trequest_body {
\t\t\tmax_size 256KB
\t\t}
\t\treverse_proxy 127.0.0.1:8212
\t}

'''
if '/tirt-data/' not in text:
    if text.count(marker) != 1:
        raise RuntimeError('Caddy marker missing or ambiguous')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = caddy.with_name('Caddyfile.pre-tirt-data-'+stamp)
    shutil.copy2(caddy, backup)
    if caddy.read_bytes() != original:
        raise RuntimeError('Caddy changed during preparation')
    try:
        # Keep the inode used by the container's bind mount.
        caddy.write_bytes(text.replace(marker, block+marker).encode())
        subprocess.run(['docker', 'exec', 'caddy', 'caddy', 'validate', '--config', '/etc/caddy/Caddyfile'], check=True)
        subprocess.run(['docker', 'exec', 'caddy', 'caddy', 'reload', '--config', '/etc/caddy/Caddyfile'], check=True)
    except Exception:
        caddy.write_bytes(original)
        subprocess.run(['docker', 'exec', 'caddy', 'caddy', 'reload', '--config', '/etc/caddy/Caddyfile'], check=False)
        raise
    (root/'deployment.json').write_text(json.dumps({'caddy_backup': str(backup),
        'caddy_before_sha256': hashlib.sha256(original).hexdigest(),
        'caddy_after_sha256': hashlib.sha256(caddy.read_bytes()).hexdigest()}, indent=2)+'\n')
print('\nTIRT telemetry API deployed; credentials remain in private config.json.')
