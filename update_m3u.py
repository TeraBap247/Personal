import os
import requests
import re
from datetime import datetime, timedelta
import hashlib

# --- Step 1: Download source .m3u file from external repo ---

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

    # --- Step 2.5: Conditionally update Fancode Live channels ---

    def hash_channel_list(lines):
        return hashlib.md5("\n".join(lines).encode()).hexdigest()

    fancode_url = "https://tv.onlinetvbd.com/fancode/playlist/playlist.m3u"
    fancode_response = requests.get(fancode_url)
    fancode_data = fancode_response.text

    # Extract new Fancode channels
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

    # Read current template and extract old Fancode channels
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
        print("Fancode channels changed. Updating template.m3u...")
        with open("template.m3u", "w") as file:
            file.writelines([line + '\n' for line in cleaned_template])
            file.write('\n'.join(new_fancode_lines).rstrip() + '\n')
    else:
        print("Fancode channels unchanged. No update needed.")

    # --- Step 4: Create ottrxs.m3u from updated template.m3u ---

    input_file = 'template.m3u'
    output_file = 'ottrxs.m3u'

    # বাংলাদেশ সময় নির্ণয় (UTC +6)
    bd_time = datetime.utcnow() + timedelta(hours=6)
    current_hour = bd_time.hour

    # শুভেচ্ছা বার্তা
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
else:
    print("Channel not found in source.")
