import os
import requests
import re
import hashlib
from datetime import datetime
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None

# --- Settings ---
ignore_names = {
    name.lower() for name in [
        "sony kal", "Star Movies 2", "sony pix hd", "ssc sport 1", "sony sab hd", "atn bangla",
        "sony aath hd", "dbc news", "ekattor tv", "somoy news tv",
        "atn news", "gazi tv hd", "independent tv", "jamuna tv", "channel 9", "btv news", "btv ctg", "channel i",
        "sony bbc earth hd", "astro cricket", "fashion tv", "disney hindi-2", "nexus tv", "sony sports ten 1", "sony sports ten 2",
        "boomerang", "willow cricket", "zee bangla sd", "sony sports ten 5", "sony sports ten 1 hd",
        "sony sports ten 2 hd", "sony sports ten 3 hd", "sony sports ten 4 hd", "sony sports ten 5 hd", "ptv sports",
        "sony yay hindi", "sony max hd", "team rxs", "nick pluto tv", "ott bangla live tv", "disney xd marathon",
        "disney xd", "mr bean", "cartoon network english", "cartoon network hd", "cn-pak", "psl vip",
        "aakaash", "nat geo bangla", "hbo", "hbo hits", "apple tv", "hbo family", "hbo signature", "cinemax",
        "movies now", "ssc sport 2", "ssc sport 3", "ssc sport 4", "ssc sport 5", "ssc sport extra 1",
        "ssc sport extra 2", "ssc sport extra 3", "bein sports mena english 1", "bein sports mena english 2",
        "bein sports mena english 3", "bein sports mena 1", "bein sports mena 2", "bein sports mena 3",
        "bein sports mena 4", "bein sports mena 5", "bein sports mena 6", "bein sports mena 7", "bein sports mena 8",
        "bein sports mena 9", "bein sports xtra 1", "bein sports xtra 2", "tnt sports 1", "tnt sports 2",
        "tnt sports 3", "tnt sports 4", "tnt brazil", "dazn 1 hd", "dazn 2 hd", "dazn 3 hd", "dazn 4 hd",
        "star movies select hd", "songsad tv", "star plus hd", "star jalsha sd", "wb tv", "fight tv premium",
        "movies action", "join tg @teamrxs", "sananda tv", "zee anmol cinema", "star gold thrills",
        "zee cinema hd", "colors cineplex bollywood", "colors cineplex hd",
        "sony wah", "colors infinity hd", "biswa bangla 24", "alpona tv", "deshi tv", "deshe bideshe",
        "channel 52 usa", "matri bhumi", "movie plus", "magic bangla tv", "btv world", "nan tv", "s tv bangla",
        "rajdahni tv", "deepto tv", "channel s bd", "rtv", "movie bangla", "ekhon tv", "global tv", "ananda tv", "sa tv", "asian tv", "bijoy tv", "mohona tv", "my tv", "desh tv",
        "boishakhi tv", "ntv", "ekushey tv", "bangla vision", "news 24", "channel 24", "dw news", "bbc news",
        "al jazeera", "zee 24 ghanta", "cnn", "peace tv bangla", "peace tv urdu hd", "madani channel hd",
        "makkah live quran tv", "madina live tv sunnah tv", "channel 5", "music bangla", "padma cable vision tv",
        "sangeet bangla", "zoom", "mastiii", "9xm", "music india", "b4u music", "investigation discovery",
        "tlc hd", "travelxp hd hindi", "discovery channel bengali", "discovery science",
        "discovery turbo", "animal planet hd world", "discovery",
        "zee bangla hd", "super hungama tv", "rongeen tv",
        "cartoon network", "pogo", "discovery kids", "tara tv", "bangla plus", "mon tv bangla", "aamar digital",
        "aamar bangla channel", "enterr10 bangla", "star gold romance", "star gold select",
        "star gold", "star bharat", "hum tv", "dangal 2", "goldmines movies", "goldmines bollywood", "goldmines",
        "mtv india", "sony max2", "and pictures hd", "b4u movies", "shemaroo tv", "rishtey",
        "sony hd (set hd)", "dangal", "colors hd", "zee tv hd", "tyc sports argentina", "ten sports", "a sports",
        "t sports", "red bull tv", "eurosport", "fox sports 2", "star sports 2 hd", "star sports 1 hd",
        "star sport select 2", "star sport select 1", "zee anmol cinema 2",
        "colors cineplex superhit", "channel a1", "nagorik tv", "news18 bangla news", "tlc hindi",
        "ott bangla live tv", "travelxp bangla", "sony pal", "psl", "tata ipl t sports", "tata ipl 2025",
        "gubbare tv", "cartoon network hindi", "pogo hindi", "bein sports", "sony aath", "sony sab", "zee cinema", "sony max",
        "discovery kids 2", "and prive hd", "shemaroo umang", "espn"
    ]
}

HTTP_TIMEOUT = 20
UA_STR = 'oxoo/1.3.9.d (Linux;Android 13) ExoPlayerLib/2.14.1'

def safe_run(section_name, func):
    try:
        func()
    except Exception as e:
        print(f"[{section_name}] তে সমস্যা হয়েছে: {e}")

# --- Step 1: নির্দিষ্ট চ্যানেলগুলোর হেডার/URL রিফ্রেশ ---
def update_channels(channel_names):
    source_url = "https://raw.githubusercontent.com/BINOD-XD/Toffee-Auto-Update-Playlist/refs/heads/main/toffee_OTT_Navigator.m3u"
    resp = requests.get(source_url, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    source_data = resp.text

    with open("template.m3u", "r", encoding="utf-8") as file:
        lines = file.readlines()

    updated_lines = []
    i = 0
    channel_names_lower = [ch.lower() for ch in channel_names]

    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF:"):
            parts = line.strip().split(',')
            channel_name_in_line = parts[-1].strip().lower() if len(parts) > 1 else ""
            if channel_name_in_line in channel_names_lower:
                idx = channel_names_lower.index(channel_name_in_line)
                original_channel_name = channel_names[idx]

                # EXTINF, optional EXTVLCOPT/EXTHTTP, and URL in source
                pattern = re.compile(
                    rf'#EXTINF:-1.*?,\s*{re.escape(original_channel_name)}\s*\n'
                    r'(?:(#EXTVLCOPT:.*)\n)?'
                    r'(?:(#EXTHTTP:.*)\n)?'
                    r'(https?://[^\s]+)',
                    re.IGNORECASE
                )
                match = pattern.search(source_data)

                if match:
                    new_vlcopt = (match.group(1) or '')
                    new_exthttp = (match.group(2) or '')
                    updated_lines.append(line)  # keep original EXTINF
                    i += 1
                    # skip old optional headers in template
                    while i < len(lines) and (lines[i].startswith("#EXTVLCOPT:") or lines[i].startswith("#EXTHTTP:")):
                        i += 1
                    # write fresh optional headers (if any) — URL লাইন আমরা template থেকে লিখছি না
                    if new_vlcopt:
                        updated_lines.append(new_vlcopt + "\n")
                    if new_exthttp:
                        updated_lines.append(new_exthttp + "\n")
                    # URL: source থেকে নেব না—template-এ URL থাকলে স্কিপ করব
                    if i < len(lines) and lines[i].startswith("http"):
                        # পুরনো URL স্কিপ
                        i += 1
                    # URL ইনসার্ট (source থেকে)
                    updated_lines.append(match.group(3) + "\n")
                else:
                    print(f"{original_channel_name} খুঁজে পাওয়া যায়নি।")
                    updated_lines.append(line)
                    i += 1
            else:
                updated_lines.append(line)
                i += 1
        else:
            updated_lines.append(line)
            i += 1

    with open("template.m3u", "w", encoding="utf-8") as file:
        file.writelines(updated_lines)

# --- Step 2: Fancode সেকশন আপডেট ---
def update_fancode():
    def hash_list(lines): 
        return hashlib.md5("\n".join(lines).encode()).hexdigest()

    fancode_url = "https://tv.noobon.top/playlist/fancode.php"
    r = requests.get(fancode_url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    fancode_data = r.text

    fancode_lines = []
    lines = fancode_data.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            # -- keep -1 if present, and inject/replace group-title safely
            # pattern: #EXTINF:-1 ... ,Name
            # ensure group-title="Fancode Live"
            if 'group-title="' in line:
                line = re.sub(r'group-title=".*?"', 'group-title="Fancode Live"', line)
            else:
                # insert right after '#EXTINF:-1'
                line = re.sub(r'^#EXTINF:-?1', '#EXTINF:-1 group-title="Fancode Live"', line)
            fancode_lines.append(line)
            # next line URL
            if i + 1 < len(lines) and lines[i + 1].startswith("http"):
                fancode_lines.append(lines[i + 1].strip())
                i += 1
        i += 1

    with open("template.m3u", "r", encoding="utf-8") as file:
        template_lines = file.readlines()

    other_lines = []
    old_fancode = []
    i = 0
    while i < len(template_lines):
        line = template_lines[i]
        if line.startswith("#EXTINF:") and 'Fancode Live' in line:
            old_fancode.append(line.strip())
            i += 1
            # collect optional headers if any
            while i < len(template_lines) and (template_lines[i].startswith("#EXTVLCOPT:") or template_lines[i].startswith("#EXTHTTP:")):
                old_fancode.append(template_lines[i].strip())
                i += 1
            # collect URL
            if i < len(template_lines) and template_lines[i].startswith("http"):
                old_fancode.append(template_lines[i].strip())
                i += 1
            continue
        else:
            other_lines.append(line.rstrip("\n"))
            i += 1

    if hash_list(old_fancode) != hash_list(fancode_lines):
        with open("template.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(other_lines).rstrip("\n") + "\n" if other_lines else "")
            f.write("\n".join(fancode_lines) + "\n")
        print("Fancode আপডেট হয়েছে।")
    else:
        print("Fancode অপরিবর্তিত।")

# --- Step 3: API সেকশন আপডেট (আপনার দেওয়া API) ---
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
        res = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
        res.raise_for_status()
        return res.json()

    def generate_lines(data):
        lines = []
        for cat in data:
            group = cat.get('title', 'Unknown')
            for ch in cat.get('channels', []):
                name = (ch.get('tv_name') or '').strip()
                stream = ch.get('stream_url') or ''
                if not name or not stream:
                    continue
                if name.lower() in ignore_names:
                    continue
                tvg_id = ch.get("live_tv_id", "")
                logo = ch.get("thumbnail_url", "")
                lines.append(
                    f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}'
                )
                # --- Always keep UA line for API channels ---
                lines.append(f'#EXTVLCOPT:http-user-agent={UA_STR}')
                # চাইলে EXTHTTP-ও দিতে পারেন:
                # lines.append(f'#EXTHTTP:{{"User-Agent":"{UA_STR}"}}')
                lines.append(stream)
        return lines

    def hash_list(lines): 
        return hashlib.md5("\n".join(lines).encode()).hexdigest()

    api_data = fetch_api()
    new_api_lines = generate_lines(api_data)

    with open("template.m3u", "r", encoding="utf-8") as f:
        template_lines = f.readlines()

    other_lines = []
    old_api = []
    i = 0
    while i < len(template_lines):
        line = template_lines[i]
        is_api_block = False

        if line.startswith("#EXTINF:") and 'group-title=' in line and 'Fancode Live' not in line:
            # read channel name from EXTINF
            name_m = re.search(r',\s*(.+?)\s*$', line.strip())
            ch_name = name_m.group(1).strip() if name_m else ""
            if ch_name and ch_name.lower() not in ignore_names:
                is_api_block = True

        if is_api_block:
            # collect the whole block: EXTINF, optional EXTVLCOPT/EXTHTTP, and URL
            old_api.append(line.strip())
            i += 1
            while i < len(template_lines) and (template_lines[i].startswith("#EXTVLCOPT:") or template_lines[i].startswith("#EXTHTTP:")):
                old_api.append(template_lines[i].strip())
                i += 1
            if i < len(template_lines) and template_lines[i].startswith("http"):
                old_api.append(template_lines[i].strip())
                i += 1
            # consumed; don't add to other_lines
            continue
        else:
            other_lines.append(line.rstrip("\n"))
            i += 1

    if hash_list(old_api) != hash_list(new_api_lines):
        with open("template.m3u", "w", encoding="utf-8") as f:
            if other_lines:
                f.write("\n".join(other_lines).rstrip("\n") + "\n")
            f.write("\n".join(new_api_lines) + "\n")
        print("API চ্যানেল আপডেট হয়েছে।")
    else:
        print("API চ্যানেল অপরিবর্তিত।")

# --- Step 4: Final Output ---
def generate_final_file():
    input_file = 'template.m3u'
    output_file = 'ottrxs.m3u'

    if ZoneInfo:
        bd_time = datetime.now(ZoneInfo("Asia/Dhaka"))
    else:
        # fallback (UTC+6 approx)
        from datetime import timedelta
        bd_time = datetime.utcnow() + timedelta(hours=6)

    hour = bd_time.hour
    if 5 <= hour < 12:
        msg = "🥱Good morning☀️👉Vip Ip Tv By Reyad Hossain🇧🇩"
    elif 12 <= hour < 18:
        msg = "☀️Good Afternoon👉Vip Ip Tv By Reyad Hossain🇧🇩"
    else:
        msg = "🌙Good Night👉Vip Ip Tv By Reyad Hossain🇧🇩"

    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for i, line in enumerate(infile):
            if i == 0 and line.startswith("#EXTM3U"):
                outfile.write(f'#EXTM3U billed-msg="{msg}"\n')
            else:
                outfile.write(line)

# --- Run All Tasks ---
if __name__ == "__main__":
    # যেসব চ্যানেল সোর্স ফাইল থেকে টেনে আনবেন:
    channel_list = [
        "Cartoon Network", "Pogo", "Discovery Kids", "Cartoon Network HD", "PSL VIP", "TLC HD", "Discovery"
    ]

    safe_run("Cartoon Network HD", lambda: update_channels(channel_list))
    safe_run("Fancode", update_fancode)
    safe_run("API", update_api_channels)
    safe_run("Final Output", generate_final_file)
