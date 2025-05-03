import os
import requests
import re
from datetime import datetime, timedelta
import hashlib
import json

# --- ধাপ ১: বাইরের সোর্স থেকে .m3u ফাইল ডাউনলোড ---
source_url = "https://raw.githubusercontent.com/byte-capsule/Toffee-Channels-Link-Headers/main/toffee_OTT_Navigator.m3u"
response = requests.get(source_url)
source_data = response.text

# --- Step 2: Extract the specific channel block ---

channel_name = "Cartoon Network HD"

pattern = re.compile(
    rf'#EXTINF:-1.*?,\s*{re.escape(channel_name)}\s*\n(#EXTVLCOPT:.*\n)?(#EXTHTTP:.*\n)?(https?://.*)',
    re.MULTILINE
)
match = pattern.search(source_data)

if match:
    new_vlcopt = match.group(1) or ''
    new_exthttp = match.group(2) or ''

    # --- Step 3: Read template.m3u and update only user-agent and cookie for that channel ---

    with open("template.m3u", "r") as file:
        lines = file.readlines()

    updated_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if channel_name in line:
            updated_lines.append(line)  # #EXTINF
            i += 1

            # Remove old EXT lines if they exist
            if i < len(lines) and lines[i].startswith("#EXTVLCOPT:"):
                i += 1
            if i < len(lines) and lines[i].startswith("#EXTHTTP:"):
                i += 1

            # Always write new lines from source
            if new_vlcopt:
                updated_lines.append(new_vlcopt)
            if new_exthttp:
                updated_lines.append(new_exthttp)
        else:
            updated_lines.append(line)
            i += 1

    with open("template.m3u", "w") as file:
        file.writelines(updated_lines)

# --- ধাপ ৩: Fancode Live চ্যানেল শর্তসাপেক্ষে আপডেট ---
try:
    def hash_channel_list(lines):
        return hashlib.md5("\n".join(lines).encode()).hexdigest()

    fancode_url = "https://tv.onlinetvbd.com/fancode/playlist/playlist.m3u"
    fancode_response = requests.get(fancode_url)
    fancode_data = fancode_response.text

    new_fancode_lines = []
    lines = fancode_data.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF:"):
            if 'group-title="' in line:
                line = re.sub(r'group-title=".*?"', 'group-title="Fancode Live"', line)
            else:
                line = line.replace('#EXTINF:', '#EXTINF: group-title="Fancode Live",')
            new_fancode_lines.append(line.strip())
            if i + 1 < len(lines) and lines[i + 1].startswith("http"):
                new_fancode_lines.append(lines[i + 1].strip())
                i += 1
        i += 1

    new_hash = hash_channel_list(new_fancode_lines)

    with open("template.m3u", "r") as file:
        template_lines = file.readlines()

    cleaned_template = []
    existing_fancode_lines = []
    i = 0
    while i < len(template_lines):
        line = template_lines[i]
        if line.startswith("#EXTINF:") and 'group-title="Fancode Live"' in line:
            existing_fancode_lines.append(line.strip())
            if i + 1 < len(template_lines) and template_lines[i + 1].startswith("http"):
                existing_fancode_lines.append(template_lines[i + 1].strip())
                i += 1
        else:
            cleaned_template.append(line.rstrip())
        i += 1

    old_hash = hash_channel_list(existing_fancode_lines)

    if new_hash != old_hash:
        with open("template.m3u", "w") as file:
            file.writelines([line + '\n' for line in cleaned_template])
            file.write('\n'.join(new_fancode_lines).rstrip() + '\n')
        print("Fancode চ্যানেল আপডেট হয়েছে।")
    else:
        print("Fancode চ্যানেল অপরিবর্তিত।")
except Exception as e:
    print(f"Fancode আপডেটে সমস্যা হয়েছে: {e}")
    
# --- ধাপ ৪: API থেকে চ্যানেল এনে template আপডেট ---
try:
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
    data = res.json()

    ignore_channels = [
        "Sony Pal HD", "Sony PIX HD", "SSC Sport 1", "Sony SAB HD", "Nick Hindi",
        "ATN Bangla", "Sony aath", "Jamuna TV", "Independent Tv", "DBC News",
        "Ekattor TV", "Somoy News TV", "ATN News", "Gazi TV HD", "Channel 9",
        "BTV News", "BTV CTG", "NTV", "Channel I", "Sony BBC Earth HD",
        "Disney Hindi-2", "Sony Sports Ten 1", "Sony Sports Ten 2",
        "Sony Sports Ten 3", "Sony Sports Ten 4", "Sony Sports Ten 5",
        "Sony Sports Ten 1 HD", "Sony Sports Ten 2 HD", "Sony Sports Ten 3 HD",
        "Sony Sports Ten 4 HD", "Sony Sports Ten 5 HD"
    ]
    ignore_channels = [name.lower() for name in ignore_channels]

    # template ফাইল থেকে লাইনের তালিকা পড়ে নাও
    with open("template.m3u", "r", encoding="utf-8") as f:
        template_lines = f.read().splitlines()

    # পুরাতন চ্যানেল map করে রাখো (name.lower(): index of EXTINF)
    existing_map = {}
    i = 0
    while i < len(template_lines):
        if template_lines[i].startswith("#EXTINF:"):
            match = re.search(r",\s*(.+)$", template_lines[i])
            if match:
                name = match.group(1).strip().lower()
                existing_map[name] = i
            i += 2
        else:
            i += 1

    updated = 0
    added = 0

    for category in data:
        group = category.get("category_name", "")
        for channel in category.get("tv_list", []):
            name = channel.get("tv_name", "").strip()
            lower_name = name.lower()
            if not name or lower_name in ignore_channels:
                continue

            stream = channel.get("tv_stream_url", "").strip()
            if not stream:
                continue

            if lower_name in existing_map:
                idx = existing_map[lower_name]
                # শুধু stream URL আপডেট করো
                if template_lines[idx + 1] != stream:
                    template_lines[idx + 1] = stream
                    updated += 1
            else:
                # নতুন চ্যানেল অ্যাড করো
                tv_id = channel.get("tv_id", "")
                tv_logo = channel.get("tv_logo", "")
                info_line = f'#EXTINF:-1 tvg-id="{tv_id}" tvg-logo="{tv_logo}" group-title="{group}",{name}'
                template_lines.append(info_line)
                template_lines.append(stream)
                added += 1

    with open("template.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(template_lines) + "\n")

    print(f"{updated} টি চ্যানেলের stream URL আপডেট হয়েছে।")
    print(f"{added} টি নতুন চ্যানেল অ্যাড হয়েছে।")

except Exception as e:
    print(f"OT API আপডেটে সমস্যা হয়েছে: {e}")

# --- ধাপ ৫: ottrxs.m3u তৈরি শুভেচ্ছা বার্তাসহ ---
try:
    input_file = 'template.m3u'
    output_file = 'ottrxs.m3u'

    bd_time = datetime.utcnow() + timedelta(hours=6)
    current_hour = bd_time.hour

    if 5 <= current_hour < 12:
        billed_msg = "☀️ Good morning - Vip Ip Tv By Reyad Hossain 🇧🇩"
    elif 12 <= current_hour < 18:
        billed_msg = "🌤️ Good Afternoon - Vip Ip Tv By Reyad Hossain 🇧🇩"
    else:
        billed_msg = "🌙 Good Night - Vip Ip Tv By Reyad Hossain 🇧🇩"

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
    print("ottrxs.m3u ফাইল সফলভাবে তৈরি হয়েছে।")
except Exception as e:
    print(f"ottrxs.m3u তৈরি করতে সমস্যা হয়েছে: {e}")