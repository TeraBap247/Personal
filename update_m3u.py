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
        "Sony Sports Ten 5 HD", "PTV Sports", "Sony Yay Hindi", "Sony MAX HD"
    ]
}

def safe_run(section_name, func):
    try:
        func()
    except Exception as e:
        print(f"[{section_name}] তে সমস্যা হয়েছে: {e}")

# --- Step 1: Update Cartoon Network HD ---
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

# --- Step 2: Update Fancode Channels ---
def update_fancode():
    def hash_channel_list(lines):
        return hashlib.md5("\n".join(lines).encode()).hexdigest()

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

    new_fancode_hash = hash_channel_list(fancode_lines)

    with open("template.m3u", "r") as file:
        template_lines = file.readlines()

    def extract_existing_fancode(template_lines):
        cleaned = []
        fancode_existing = []
        i = 0
        while i < len(template_lines):
            line = template_lines[i]
            if line.startswith("#EXTINF:") and 'group-title="Fancode Live"' in line:
                fancode_existing.append(line.strip())
                if i + 1 < len(template_lines) and template_lines[i + 1].startswith("http"):
                    fancode_existing.append(template_lines[i + 1].strip())
                    i += 1
            else:
                cleaned.append(line.rstrip())
            i += 1
        return cleaned, fancode_existing

    cleaned_template, old_fancode_lines = extract_existing_fancode(template_lines)
    old_fancode_hash = hash_channel_list(old_fancode_lines)

    if new_fancode_hash != old_fancode_hash:
        with open("template.m3u", "w") as f:
            f.writelines([line + '\n' for line in cleaned_template])
            f.write('\n'.join(fancode_lines).strip() + '\n')
        print("Fancode আপডেট হয়েছে।")
    else:
        print("Fancode অপরিবর্তিত।")

# --- Step 3: Update API Channels ---
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

    def generate_extinf_from_api(data):
        lines = []
        for category in data:
            group_title = category.get('title', 'Unknown')
            for channel in category.get('channels', []):
                tv_name = channel.get('tv_name', '').strip()
                if tv_name.lower() in ignore_names:
                    continue
                stream_url = channel.get('stream_url', '')
                if not stream_url:
                    continue
                tv_id = channel.get('live_tv_id', '')
                tv_logo = channel.get('thumbnail_url', '')
                lines.append(f'#EXTINF:-1 tvg-id="{tv_id}" tvg-name="{tv_name}" tvg-logo="{tv_logo}" group-title="{group_title}",{tv_name}')
                lines.append(stream_url)
        return lines

    def extract_existing_api_channels(template_lines):
        cleaned = []
        existing_api = []
        i = 0
        while i < len(template_lines):
            line = template_lines[i]
            if line.startswith("#EXTINF:") and 'group-title=' in line and 'Fancode Live' not in line:
                name_match = re.search(r',(.+)', line)
                if name_match:
                    channel_name = name_match.group(1).strip()
                    if channel_name.lower() in ignore_names:
                        cleaned.append(line.rstrip())
                        if i + 1 < len(template_lines) and template_lines[i + 1].startswith("http"):
                            cleaned.append(template_lines[i + 1].rstrip())
                            i += 1
                    else:
                        existing_api.append(line.strip())
                        if i + 1 < len(template_lines) and template_lines[i + 1].startswith("http"):
                            existing_api.append(template_lines[i + 1].strip())
                            i += 1
                else:
                    cleaned.append(line.rstrip())
            else:
                cleaned.append(line.rstrip())
            i += 1
        return cleaned, existing_api

    def hash_channel_list(lines):
        return hashlib.md5("\n".join(lines).encode()).hexdigest()

    api_data = fetch_api()
    api_extinf_lines = generate_extinf_from_api(api_data)

    with open("template.m3u", "r") as f:
        template_lines = f.readlines()

    cleaned_template, old_api_lines = extract_existing_api_channels(template_lines)
    new_api_hash = hash_channel_list(api_extinf_lines)
    old_api_hash = hash_channel_list(old_api_lines)

    if new_api_hash != old_api_hash:
        with open("template.m3u", "w") as f:
            f.writelines([line + '\n' for line in cleaned_template])
            f.write('\n'.join(api_extinf_lines).strip() + '\n')
        print("API চ্যানেল আপডেট হয়েছে।")
    else:
        print("API চ্যানেল অপরিবর্তিত।")

# --- Step 4: Generate Final File ---
def generate_final_file():
    input_file = 'template.m3u'
    output_file = 'ottrxs.m3u'
    bd_time = datetime.utcnow() + timedelta(hours=6)
    current_hour = bd_time.hour

    if 5 <= current_hour < 12:
        billed_msg = "🥱Good morning☀️👉Vip Ip Tv By Reyad Hossain🇧🇩"
    elif 12 <= current_hour < 18:
        billed_msg = "☀️Good Afternoon👉Vip Ip Tv By Reyad Hossain🇧🇩"
    else:
        billed_msg = "🌙Good Night👉Vip Ip Tv By Reyad Hossain🇧🇩"

    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        first_line_written = False
        for line in infile:
            if not first_line_written and line.startswith("#EXTM3U"):
                outfile.write(f'#EXTM3U billed-msg="{billed_msg}"\n')
                first_line_written = True
            elif line.startswith("http") and (".m3u8" in line or ".mpd" in line):
                outfile.write(line.strip() + "\n")
            else:
                outfile.write(line)

# Run all in protected blocks
safe_run("Cartoon Network HD", update_cartoon_network)
safe_run("Fancode", update_fancode)
safe_run("API", update_api_channels)
safe_run("Final Output", generate_final_file)