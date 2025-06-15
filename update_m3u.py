import os
import requests
import re
import hashlib
from datetime import datetime, timedelta

# --- Settings ---
ignore_names = {
    name.lower() for name in [
        "sony kal", "sony pix hd", "ssc sport 1", "sony sab hd", "nick hindi", "atn bangla",
        "sony aath hd", "jamuna tv", "independent tv", "dbc news", "ekattor tv", "somoy news tv",
        "atn news", "gazi tv hd", "duronto tv", "channel 9", "btv news", "btv ctg", "channel i",
        "sony bbc earth hd", "astro cricket", "fashion tv", "disney hindi-2", "sony sports ten 1", "sony sports ten 2",
        "boomerang", "willow cricket", "zee bangla sd", "sony sports ten 5", "sony sports ten 1 hd",
        "sony sports ten 2 hd", "sony sports ten 3 hd", "sony sports ten 4 hd",
        "sony sports ten 5 hd", "ptv sports", "sony yay hindi", "sony max hd",
        "team rxs", "nick pluto tv", "ott bangla live tv", "disney xd marathon", "disney xd", "mr bean",
        "cartoon network english", "cartoon network hd",
        "nick hd plus", "cn-pak", "psl vip", "aakaash", "nat geo bangla", "hbo", "hbo hits", "apple tv", "hbo family",
        "hbo signature", "cinemax", "movies now", "ssc sport 2", "ssc sport 3", "ssc sport 4",
        "ssc sport 5", "ssc sport extra 1", "ssc sport extra 2", "ssc sport extra 3",
        "bein sports mena english 1", "bein sports mena english 2", "bein sports mena english 3",
        "bein sports mena 1", "bein sports mena 2", "bein sports mena 3", "bein sports mena 4",
        "bein sports mena 5", "bein sports mena 6", "bein sports mena 7", "bein sports mena 8",
        "bein sports mena 9", "bein sports xtra 1", "bein sports xtra 2", "tnt sports 1",
        "tnt sports 2", "tnt sports 3", "tnt sports 4", "tnt brazil",
        "dazn 1 hd",
        "dazn 2 hd", "dazn 3 hd", "dazn 4 hd",
        "star movies select hd", "songsad tv",
        "star plus hd", "star jalsha sd", "wb tv", "fight tv premium", "movies action", "join tg @teamrxs"
    ]
}

def safe_run(section_name, func):
    try:
        func()
    except Exception as e:
        print(f"[{section_name}] তে সমস্যা হয়েছে: {e}")

# --- Step 1: Channel Header Update ---
def update_channels(channel_names):
    source_url = "https://raw.githubusercontent.com/byte-capsule/Toffee-Channels-Link-Headers/main/toffee_OTT_Navigator.m3u"
    response = requests.get(source_url)
    source_data = response.text

    source_lines = source_data.strip().splitlines()
    source_map = {}

    i = 0
    while i < len(source_lines):
        line = source_lines[i]
        if line.startswith("#EXTINF:"):
            name_match = re.search(r',\s*(.+?)\s*$', line)
            if name_match:
                ch_name = name_match.group(1).lower()
                vlcopt, exthttp, url = "", "", ""

                j = i + 1
                while j < len(source_lines) and not source_lines[j].startswith("#EXTINF:"):
                    if source_lines[j].startswith("#EXTVLCOPT:"):
                        vlcopt = source_lines[j]
                    elif source_lines[j].startswith("#EXTHTTP:"):
                        exthttp = source_lines[j]
                    elif source_lines[j].startswith("http"):
                        url = source_lines[j]
                    j += 1

                if url:
                    source_map[ch_name] = (line, vlcopt, exthttp, url)
                i = j
            else:
                i += 1
        else:
            i += 1

    with open("template.m3u", "r") as file:
        lines = file.readlines()

    updated_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        matched_channel = next((ch for ch in channel_names if ch.lower() in line.lower()), None)

        if matched_channel:
            ch_key = matched_channel.lower()
            if ch_key in source_map:
                extinf, vlcopt, exthttp, url = source_map[ch_key]
                updated_lines.append(extinf + "\n")
                if vlcopt:
                    updated_lines.append(vlcopt + "\n")
                if exthttp:
                    updated_lines.append(exthttp + "\n")
                updated_lines.append(url + "\n")

                i += 1
                while i < len(lines) and not lines[i].startswith("#EXTINF:"):
                    i += 1
                continue
            else:
                print(f"{matched_channel} খুঁজে পাওয়া যায়নি।")
        updated_lines.append(line)
        i += 1

    with open("template.m3u", "w") as file:
        file.writelines(updated_lines)

# --- Step 2: Fancode Section Update ---
def update_fancode():
    def hash_list(lines): return hashlib.md5("\n".join(lines).encode()).hexdigest()

    fancode_url = "https://filofilmes.art/fancode/playlist/playlist.m3u"
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

# --- Step 3: Final Output Generation ---
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
channel_list = [
    "Cartoon Network HD",
    "PSL VIP",
    "Cartoon Network",
    "Pogo",
    "Discovery Kids",
    "Discovery",
    "TLC HD"
]

safe_run("Channel Update", lambda: update_channels(channel_list))
safe_run("Fancode", update_fancode)
safe_run("Final Output", generate_final_file)