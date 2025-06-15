import os
import requests
import re
import hashlib
from datetime import datetime, timedelta

# --- Settings ---
toffee_channels = {
    name.lower() for name in [
        "cartoon network", "pogo",
        "discovery kid", "cartoon network hd", "psl vip"
    ]
}

def safe_run(section_name, func):
    try:
        func()
    except Exception as e:
        print(f"[{section_name}] তে সমস্যা হয়েছে: {e}")

# --- Step 1: Toffee Channel Section Update ---
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
        matched_channel = next(
            (ch for ch in channel_names if ch.lower() in line.lower()), None
        )

        if matched_channel and matched_channel.lower() in toffee_channels:
            pattern = re.compile(
                rf'#EXTINF:-1.*?,\s*{re.escape(matched_channel)}\s*\n(#EXTVLCOPT:.*\n)?(#EXTHTTP:.*\n)?(https?://.*)',
                re.MULTILINE | re.IGNORECASE
            )
            match = pattern.search(source_data)

            if match:
                new_vlcopt = match.group(1) or ''
                new_exthttp = match.group(2) or ''
                new_url = match.group(3)

                updated_lines.append(line)
                i += 1
                if i < len(lines) and lines[i].startswith("#EXTVLCOPT:"):
                    i += 1
                if i < len(lines) and lines[i].startswith("#EXTHTTP:"):
                    i += 1
                updated_lines.extend([new_vlcopt, new_exthttp, new_url + '\n'])
            else:
                print(f"{matched_channel} খুঁজে পাওয়া যায়নি।")
                updated_lines.append(line)
                i += 1
        else:
            updated_lines.append(line)
            i += 1

    with open("template.m3u", "w") as file:
        file.writelines(updated_lines)

# --- Step 2: Fancode Section Update ---
def update_fancode():
    def hash_list(lines):
        return hashlib.md5("\n".join(lines).encode()).hexdigest()

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

# --- Step 3: Final Output ---
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
safe_run("Toffee Channels", lambda: update_channels([
    "Cartoon Network", "Pogo",
    "Discovery Kid", "Cartoon Network HD", "PSL VIP"
]))
safe_run("Fancode", update_fancode)
safe_run("Final Output", generate_final_file)