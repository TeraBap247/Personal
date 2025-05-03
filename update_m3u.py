import os
import requests
import re
import hashlib
from datetime import datetime, timedelta

# --- Settings ---
ignore_names = {
    name.lower() for name in [
        "Sony Pal HD", "Sony PIX HD", "SSC Sport 1", "Sony SAB HD", "Nick Hindi", "ATN Bangla",
        "Sony aath", "Jamuna TV", "Independent Tv", "DBC News", "Ekattor TV", "Somoy News TV",
        "ATN News", "Gazi TV HD", "Channel 9", "BTV News", "BTV CTG", "NTV", "Channel I",
        "Sony BBC Earth HD", "Disney Hindi-2", "Sony Sports Ten 1", "Sony Sports Ten 2",
        "Sony Sports Ten 3", "Sony Sports Ten 4", "Sony Sports Ten 5", "Sony Sports Ten 1 HD",
        "Sony Sports Ten 2 HD", "Sony Sports Ten 3 HD", "Sony Sports Ten 4 HD",
        "Sony Sports Ten 5 HD", "PTV Sports", "Sony Yay Hindi", "Sony MAX HD",

        "Team RXS", "Nick Pluto TV", "Disney XD Marathon", "Disney XD", "Mr Bean",
        "Cartoon Network English", "Cartoon Network HD", "Cartoon Network Pakistan",
        "Nick HD Plus", "AAKAASH", "NAT GEO BANGLA", "HBO", "HBO Hits", "HBO Family",
        "HBO Signature", "Cinemax", "Movies Now", "SSC Sport 2", "SSC Sport 3", "SSC Sport 4",
        "SSC Sport 5", "SSC Sport Extra 1", "SSC Sport Extra 2", "SSC Sport Extra 3",
        "beIN Sports MENA English 1", "beIN Sports MENA English 2", "beIN Sports MENA English 3",
        "beIN Sports MENA 1", "beIN Sports MENA 2", "beIN Sports MENA 3", "beIN Sports MENA 4",
        "beIN Sports MENA 5", "beIN Sports MENA 6", "beIN Sports MENA 7", "beIN Sports MENA 8",
        "beIN Sports MENA 9", "beIN SPORTS XTRA 1", "beIN SPORTS XTRA 2", "TNT Sports 1 UK",
        "TNT Sports 2 UK", "TNT Sports 3 UK", "TNT Sports 4 UK", "TNT Brazil",
        "TNT Sports Argentina", "TNT Sports HD Chile", "TNT USA", "DAZN 1 Bar DE",
        "DAZN 2 Bar DE", "DAZN 1 Spain", "DAZN 2 Spain", "DAZN 3 Spain", "DAZN 4 Spain",
        "DAZN F1 ES", "DAZN LaLiga", "DAZN LaLiga 2", "STAR MOVIES SELECT HD", "Songsad TV",
        "Star Plus HD", "Star Jalsha SD", "WB Tv", "Fight TV Premium", "Movies Action"
    ]
}

def safe_run(section_name, func):
    try:
        func()
    except Exception as e:
        print(f"[{section_name}] তে সমস্যা হয়েছে: {e}")

# --- Step 1: Cartoon Network HD Header Update ---
def update_cartoon_network():
    source_url = "https://raw.githubusercontent.com/byte-capsule/Toffee-Channels-Link-Headers/main/toffee_OTT_Navigator.m3u"
    response = requests.get(source_url)
    source_data = response.text

    channel_name = "Cartoon Network HD"
    pattern = re.compile(
        rf'#EXTINF:-1.*?,\s*{re.escape(channel_name)}\s*\n(#EXTVLCOPT:.*\n)?(#EXTHTTP:.*\n)?(https?://.*)',
        re.MULTILINE
    )
    match = pattern.search(source_data)

    if not match:
        print("Cartoon Network HD খুঁজে পাওয়া যায়নি।")
        return

    new_vlcopt = match.group(1) or ''
    new_exthttp = match.group(2) or ''

    with open("template.m3u", "r") as file:
        lines = file.readlines()

    updated_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if channel_name in line:
            updated_lines.append(line)
            i += 1
            if i < len(lines) and lines[i].startswith("#EXTVLCOPT:"):
                i += 1
            if i < len(lines) and lines[i].startswith("#EXTHTTP:"):
                i += 1
            if new_vlcopt:
                updated_lines.append(new_vlcopt)
            if new_exthttp:
                updated_lines.append(new_exthttp)
        else:
            updated_lines.append(line)
            i += 1

    with open("template.m3u", "w") as file:
        file.writelines(updated_lines)

# --- Step 2: Fancode Section Update ---
def update_fancode():
    def hash_list(lines): return hashlib.md5("\n".join(lines).encode()).hexdigest()

    fancode_url = "https://tv.onlinetvbd.com/fancode/playlist/playlist.m3u"
    fancode_data = requests.get(fancode_url).text
    fancode_lines = []

    lines = fancode_data.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF:"):
            if 'group-title="' in line:
                line = re.sub(r'group-title=".*?"', 'group-title="Fancode Live"', line)
            else:
                line = line.replace('#EXTINF:', '#EXTINF: group-title="Fancode Live",')
            fancode_lines.append(line.strip())
            if i + 1 < len(lines) and lines[i + 1].startswith("http"):
                fancode_lines.append(lines[i + 1].strip())
                i += 1
        i += 1

    with open("template.m3u", "r") as file:
        template_lines = file.readlines()

    other_lines = []
    old_fancode = []
    i = 0
    while i < len(template_lines):
        line = template_lines[i]
        if line.startswith("#EXTINF:") and 'Fancode Live' in line:
            old_fancode.append(line.strip())
            if i + 1 < len(template_lines) and template_lines[i + 1].startswith("http"):
                old_fancode.append(template_lines[i + 1].strip())
                i += 1
        else:
            other_lines.append(line.rstrip())
        i += 1

    if hash_list(old_fancode) != hash_list(fancode_lines):
        with open("template.m3u", "w") as f:
            f.writelines([line + '\n' for line in other_lines])
            f.write('\n'.join(fancode_lines) + '\n')
        print("Fancode আপডেট হয়েছে।")
    else:
        print("Fancode অপরিবর্তিত।")

# --- Step 3: API Section Update ---
def update_api_channels():
    def fetch_api():
        url = "https://otapp.store/rest-api//v130/all_tv_channel_by_category"
        headers = {
            "API-KEY": "ottbangla@android",
            "Authorization": "Basic YWRtaW46MTIzNA==",
            "Host": "otapp.store",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/4.9.0"
        }
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()

    def generate_lines(data):
        lines = []
        for cat in data:
            group = cat.get('title', 'Unknown')
            for ch in cat.get('channels', []):
                name = ch.get('tv_name', '').strip()
                if name.lower() in ignore_names or not ch.get('stream_url', ''):
                    continue
                lines.append(f'#EXTINF:-1 tvg-id="{ch.get("live_tv_id")}" tvg-name="{name}" tvg-logo="{ch.get("thumbnail_url")}" group-title="{group}",{name}')
                lines.append(ch['stream_url'])
        return lines

    def hash_list(lines): return hashlib.md5("\n".join(lines).encode()).hexdigest()

    api_data = fetch_api()
    new_api_lines = generate_lines(api_data)

    with open("template.m3u", "r") as f:
        template_lines = f.readlines()

    other_lines = []
    old_api = []
    i = 0
    while i < len(template_lines):
        line = template_lines[i]
        is_api = False
        if line.startswith("#EXTINF:") and 'group-title=' in line and 'Fancode Live' not in line:
            name = re.search(r',(.+)', line)
            if name and name.group(1).strip().lower() not in ignore_names:
                is_api = True
        if is_api:
            old_api.append(line.strip())
            if i + 1 < len(template_lines) and template_lines[i + 1].startswith("http"):
                old_api.append(template_lines[i + 1].strip())
                i += 1
        else:
            other_lines.append(line.rstrip())
        i += 1

    if hash_list(old_api) != hash_list(new_api_lines):
        with open("template.m3u", "w") as f:
            f.writelines([l + '\n' for l in other_lines])
            f.write('\n'.join(new_api_lines) + '\n')
        print("API চ্যানেল আপডেট হয়েছে।")
    else:
        print("API চ্যানেল অপরিবর্তিত।")

# --- Step 4: Final Output ---
def generate_final_file():
    input_file = 'template.m3u'
    output_file = 'ottrxs.m3u'
    bd_time = datetime.utcnow() + timedelta(hours=6)
    hour = bd_time.hour

    if 5 <= hour < 12:
        msg = "🥱Good morning☀️👉Vip Ip Tv By Reyad Hossain🇧🇩"
    elif 12 <= hour < 18:
        msg = "☀️Good Afternoon👉Vip Ip Tv By Reyad Hossain🇧🇩"
    else:
        msg = "🌙Good Night👉Vip Ip Tv By Reyad Hossain🇧🇩"

    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for i, line in enumerate(infile):
            if i == 0 and line.startswith("#EXTM3U"):
                outfile.write(f'#EXTM3U billed-msg="{msg}"\n')
            else:
                outfile.write(line)

# --- Run All Tasks ---
safe_run("Cartoon Network HD", update_cartoon_network)
safe_run("Fancode", update_fancode)
safe_run("API", update_api_channels)
safe_run("Final Output", generate_final_file)