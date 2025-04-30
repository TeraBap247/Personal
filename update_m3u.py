import os
import time
import hashlib
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

def generate_token(secret, expire_seconds=3600):
    expires = int(time.time()) + expire_seconds
    raw = f"{secret}{expires}".encode()
    token = hashlib.md5(raw).hexdigest()
    return token, expires

def add_token_to_url(url, token, expires):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query['token'] = token
    query['expires'] = str(expires)
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

input_file = 'template.m3u'
output_file = 'ottrxs.m3u'

# Get secret key from environment variable
secret = os.environ.get("TOKEN_SECRET")

if not secret:
    raise ValueError("TOKEN_SECRET environment variable not found!")

with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
        if line.startswith("http") and (".m3u8" in line or ".mpd" in line):
            token, expires = generate_token(secret)
            updated_url = add_token_to_url(line.strip(), token, expires)
            outfile.write(f"{updated_url}\n")
        else:
            outfile.write(line)