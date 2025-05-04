import os
import requests
import re
import hashlib
from datetime import datetime, timedelta

# --- Settings ---
ignore_names = {
    name.lower() for name in [
        "sony pal hd", "sony pix hd", "ssc sport 1", "sony sab hd", "nick hindi", "atn bangla",
        "sony aath", "jamuna tv", "independent tv", "dbc news", "ekattor tv", "somoy news tv",
        "atn news", "gazi tv hd", "channel 9", "btv news", "btv ctg", "ntv", "channel i",
        "sony bbc earth hd", "disney hindi-2", "sony sports ten 1", "sony sports ten 2",
        "sony sports ten 3", "sony sports ten 4", "sony sports ten 5", "sony sports ten 1 hd",
        "sony sports ten 2 hd", "sony sports ten 3 hd", "sony sports ten 4 hd",
        "sony sports ten 5 hd", "ptv sports", "sony yay hindi", "sony max hd",

        "team rxs", "nick pluto tv", "disney xd marathon", "disney xd", "mr bean",
        "cartoon network english", "cartoon network hd",
        "nick hd plus", "cn-pak", "psl", "aakaash", "nat geo bangla", "hbo", "hbo hits", "hbo family",
        "hbo signature", "cinemax", "movies now", "ssc sport 2", "ssc sport 3", "ssc sport 4",
        "ssc sport 5", "ssc sport extra 1", "ssc sport extra 2", "ssc sport extra 3",
        "bein sports mena english 1", "bein sports mena english 2", "bein sports mena english 3",
        "bein sports mena 1", "bein sports mena 2", "bein sports mena 3", "bein sports mena 4",
        "bein sports mena 5", "bein sports mena 6", "bein sports mena 7", "bein sports mena 8",
        "bein sports mena 9", "bein sports xtra 1", "bein sports xtra 2", "tnt sports 1 uk",
        "tnt sports 2 uk", "tnt sports 3 uk", "tnt sports 4 uk", "tnt brazil",
        "tnt sports argentina", "tnt sports hd chile", "tnt usa", "dazn 1 bar de",
        "dazn 2 bar de", "dazn 1 spain", "dazn 2 spain", "dazn 3 spain", "dazn 4 spain",
        "dazn f1 es", "dazn laliga", "dazn laliga 2", "star movies select hd", "songsad tv",
        "star plus hd", "star jalsha sd", "wb tv", "fight tv premium", "movies action", "join tg @teamrxs"
    ]
}

def safe_run(section_name, func):
    try:
        func()
    except Exception as e:
        print(f"[{section_name}] তে সমস্যা হয়েছে: {e}")

# --- Step 1: Cartoon Network HD Header Update ---
def update_channels(channel_names):
    source_url = "https://raw.githubusercontent.com/byte-capsule/Toffee-Channels-Link-Headers/main/toffee_OTT_Navigator.m3u"
    response = requests.get(source_url)
    source_data = response.text

    with open("template.m3u", "r") as file:
        lines = file.readlines()

    updated_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # ছোট/বড় হাত এক করে মিল খোঁজা
        matched_channel = next((ch for ch in channel_names if ch.lower() in line.lower()), None)

        if matched_channel:
            # চ্যানেলের নতুন তথ্য source থেকে বের করা
            pattern = re.compile(
                rf'#EXTINF:-1.*?,\s*{re.escape(matched_channel)}\s*\n(#EXTVLCOPT:.*\n)?(#EXTHTTP:.*\n)?(https?://.*)',
                re.MULTILINE | re.IGNORECASE
            )
            match = pattern.search(source_data)

            if match:
                new_vlcopt = match.group(1) or ''
                new_exthttp = match.group(2) or ''
                updated_lines.append(line)
                i += 1
                # পুরাতন EXT অপশন স্কিপ করে
                if i < len(lines) and lines[i].startswith("#EXTVLCOPT:"):
                    i += 1
                if i < len(lines) and lines[i].startswith("#EXTHTTP:"):
                    i += 1
                if new_vlcopt:
                    updated_lines.append(new_vlcopt)
                if new_exthttp:
                    updated_lines.append(new_exthttp)
            else:
                print(f"{matched_channel} খুঁজে পাওয়া যায়নি।")
                updated_lines.append(line)
                i += 1
        else:
            updated_lines.append(line)
            i += 1

    with open("template.m3u", "w") as file:
        file.writelines(updated_lines)

# এখানে শুধু নাম অ্যাড করলেই চলবে
channel_list = [
    "Cartoon Network HD",
    "PSL"
]

update_channels(channel_list)

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
