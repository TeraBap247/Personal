import os
import requests
import re
from datetime import datetime, timedelta

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
