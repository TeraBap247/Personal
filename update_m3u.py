import os
import re
import hashlib
import requests
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

# =============== SETTINGS ===============
HTTP_TIMEOUT = 20
UA_STR = 'oxoo/1.3.9.d (Linux;Android 13) ExoPlayerLib/2.14.1'

ignore_names = {
    name.lower() for name in [
        "sony kal", "Star Movies 2", "sony pix hd", "ssc sport 1", "sony sab hd", "atn bangla",
        "sony aath hd", "dbc news", "ekattor tv", "somoy news tv", "atn news", "gazi tv hd",
        "independent tv", "jamuna tv", "channel 9", "btv news", "btv ctg", "channel i",
        "sony bbc earth hd", "astro cricket", "fashion tv", "disney hindi-2", "nexus tv",
        "sony sports ten 1", "sony sports ten 2", "boomerang", "willow cricket", "zee bangla sd",
        "sony sports ten 5", "sony sports ten 1 hd", "sony sports ten 2 hd", "sony sports ten 3 hd",
        "sony sports ten 4 hd", "sony sports ten 5 hd", "ptv sports", "sony yay hindi", "sony max hd",
        "team rxs", "nick pluto tv", "ott bangla live tv", "disney xd marathon", "disney xd",
        "mr bean", "cartoon network english", "cartoon network hd", "cn-pak", "psl vip", "aakaash",
        "nat geo bangla", "hbo", "hbo hits", "apple tv", "hbo family", "hbo signature", "cinemax",
        "movies now", "ssc sport 2", "ssc sport 3", "ssc sport 4", "ssc sport 5", "ssc sport extra 1",
        "ssc sport extra 2", "ssc sport extra 3", "bein sports mena english 1", "bein sports mena english 2",
        "bein sports mena english 3", "bein sports mena 1", "bein sports mena 2", "bein sports mena 3",
        "bein sports mena 4", "bein sports mena 5", "bein sports mena 6", "bein sports mena 7",
        "bein sports mena 8", "bein sports mena 9", "bein sports xtra 1", "bein sports xtra 2",
        "tnt sports 1", "tnt sports 2", "tnt sports 3", "tnt sports 4", "tnt brazil",
        "dazn 1 hd", "dazn 2 hd", "dazn 3 hd", "dazn 4 hd", "star movies select hd", "songsad tv",
        "star plus hd", "star jalsha sd", "wb tv", "fight tv premium", "movies action", "join tg @teamrxs",
        "sananda tv", "zee anmol cinema", "star gold thrills", "zee cinema hd",
        "colors cineplex bollywood", "colors cineplex hd", "sony wah", "colors infinity hd",
        "biswa bangla 24", "alpona tv", "deshi tv", "deshe bideshe", "channel 52 usa", "matri bhumi",
        "movie plus", "magic bangla tv", "btv world", "nan tv", "s tv bangla", "rajdahni tv",
        "deepto tv", "channel s bd", "rtv", "movie bangla", "ekhon tv", "global tv", "ananda tv",
        "sa tv", "asian tv", "bijoy tv", "mohona tv", "my tv", "desh tv", "boishakhi tv", "ntv",
        "ekushey tv", "bangla vision", "news 24", "channel 24", "dw news", "bbc news", "al jazeera",
        "zee 24 ghanta", "cnn", "peace tv bangla", "peace tv urdu hd", "madani channel hd",
        "makkah live quran tv", "madina live tv sunnah tv", "channel 5", "music bangla",
        "padma cable vision tv", "sangeet bangla", "zoom", "mastiii", "9xm", "music india", "b4u music",
        "investigation discovery", "tlc hd", "travelxp hd hindi", "discovery channel bengali",
        "discovery science", "discovery turbo", "animal planet hd world", "discovery", "zee bangla hd",
        "super hungama tv", "rongeen tv", "cartoon network", "pogo", "discovery kids", "tara tv",
        "bangla plus", "mon tv bangla", "aamar digital", "aamar bangla channel", "enterr10 bangla",
        "star gold romance", "star gold select", "star gold", "star bharat", "hum tv", "dangal 2",
        "goldmines movies", "goldmines bollywood", "goldmines", "mtv india", "sony max2", "and pictures hd",
        "b4u movies", "shemaroo tv", "rishtey", "sony hd (set hd)", "dangal", "colors hd", "zee tv hd",
        "tyc sports argentina", "ten sports", "a sports", "t sports", "red bull tv", "eurosport",
        "fox sports 2", "star sports 2 hd", "star sports 1 hd", "star sport select 2", "star sport select 1",
        "zee anmol cinema 2", "colors cineplex superhit", "channel a1", "nagorik tv", "news18 bangla news",
        "tlc hindi", "ott bangla live tv", "travelxp bangla", "sony pal", "psl", "tata ipl t sports",
        "tata ipl 2025", "gubbare tv", "cartoon network hindi", "pogo hindi", "bein sports", "sony aath",
        "sony sab", "zee cinema", "sony max", "discovery kids 2", "and prive hd", "shemaroo umang", "espn"
    ]
}

# =============== UTILS ===============
def safe_run(section, fn):
    try:
        fn()
    except Exception as e:
        print(f"[{section}] তে সমস্যা হয়েছে: {e}")

def read_lines(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().splitlines()

def write_lines(path, lines):
    # normalize newline to '\n'
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip("\n") + "\n")

def iter_blocks(lines):
    """
    Yield channel blocks: (start_idx, end_idx_exclusive, extinf, headers(list), url or '')
    A block starts at #EXTINF and continues through optional #EXTVLCOPT/#EXTHTTP lines to the URL line.
    """
    i, n = 0, len(lines)
    while i < n:
        if lines[i].startswith("#EXTINF:"):
            start = i
            extinf = lines[i]
            i += 1
            headers = []
            while i < n and (lines[i].startswith("#EXTVLCOPT:") or lines[i].startswith("#EXTHTTP:")):
                headers.append(lines[i])
                i += 1
            url = ""
            if i < n and lines[i].startswith("http"):
                url = lines[i]
                i += 1
            end = i
            yield (start, end, extinf, headers, url)
        else:
            i += 1

def get_name_from_extinf(extinf_line):
    # After last comma
    m = re.search(r',\s*(.+?)\s*$', extinf_line.strip())
    return m.group(1).strip() if m else ""

def has_attr(extinf_line, key, value=None):
    # Match key="value" or key=... in the EXTINF attributes area
    # attributes assumed between "#EXTINF:-1" and ","
    m = re.match(r'^#EXTINF:[^,]*', extinf_line)
    head = m.group(0) if m else ""
    if value is None:
        return re.search(rf'\b{re.escape(key)}\b', head) is not None
    return re.search(rf'\b{re.escape(key)}\s*=\s*"(?:{re.escape(value)})"', head) is not None

def set_attr(extinf_line, key, value):
    # Insert or replace key="value" inside EXTINF header (before the final comma)
    if "," not in extinf_line:
        return extinf_line
    head, tail = extinf_line.split(",", 1)
    if re.search(rf'\b{re.escape(key)}\s*=', head):
        head = re.sub(rf'(\b{re.escape(key)}\s*=\s*")[^"]*(")', rf'\1{value}\2', head)
    else:
        head = head.replace("#EXTINF:-1", f'#EXTINF:-1 {key}="{value}"')
    return f"{head},{tail}"

def normalize_extinf_group_title(extinf_line, group_title):
    # Ensure group-title is exactly set to given value
    if re.search(r'group-title\s*=\s*"', extinf_line):
        return re.sub(r'group-title\s*=\s*"(.*?)"', f'group-title="{group_title}"', extinf_line)
    else:
        return set_attr(extinf_line, "group-title", group_title)

def remove_blocks_by_predicate(lines, predicate):
    """Remove all blocks for which predicate(extinf, headers, url) returns True."""
    to_remove = set()
    for start, end, extinf, headers, url in iter_blocks(lines):
        if predicate(extinf, headers, url):
            to_remove.update(range(start, end))
    return [line for idx, line in enumerate(lines) if idx not in to_remove]

# =============== STEP 1: Selected channels refresh from Toffee source ===============
def update_channels(channel_names):
    source_url = "https://raw.githubusercontent.com/BINOD-XD/Toffee-Auto-Update-Playlist/refs/heads/main/toffee_OTT_Navigator.m3u"
    r = requests.get(source_url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    source_data = r.text.splitlines()

    if not os.path.exists("template.m3u"):
        raise FileNotFoundError("template.m3u not found")

    lines = read_lines("template.m3u")
    lower_targets = [c.lower() for c in channel_names]

    # Build quick lookup from source by channel name -> (headers, url)
    src_map = {}
    for _, __, extinf, headers, url in iter_blocks(source_data):
        name = get_name_from_extinf(extinf).strip()
        if not name:
            continue
        src_map[name.lower()] = (headers, url)

    # Rewrite target blocks in template
    out = []
    i, n = 0, len(lines)
    while i < n:
        if lines[i].startswith("#EXTINF:"):
            # peek block
            start_i = i
            block = next(iter_blocks(lines[i:]), None)
            if block:
                b_start, b_end, extinf, headers, url = block
                b_start += i; b_end += i  # adjust to absolute
                name = get_name_from_extinf(extinf).lower()
                if name in lower_targets and name in src_map:
                    # replace headers + url from source
                    new_headers, new_url = src_map[name]
                    out.append(extinf)  # keep original EXTINF line text
                    # remove old headers/url by skipping to b_end
                    # add new headers (from source)
                    for h in new_headers:
                        out.append(h)
                    if new_url:
                        out.append(new_url)
                    i = b_end
                    continue
                else:
                    # keep original block as-is
                    out.extend(lines[start_i:b_end])
                    i = b_end
                    continue
        # non-block line
        out.append(lines[i])
        i += 1

    write_lines("template.m3u", out)

# =============== STEP 2: Fancode section replace (clean) ===============
def update_fancode():
    def hash_list(lines):
        return hashlib.md5("\n".join(lines).encode()).hexdigest()

    fancode_url = "https://tv.noobon.top/playlist/fancode.php"
    r = requests.get(fancode_url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    raw = r.text.splitlines()

    # Build fresh Fancode lines (managed)
    fresh = []
    i = 0
    while i < len(raw):
        line = raw[i].strip()
        if line.startswith("#EXTINF:"):
            # enforce -1 and group-title
            line = re.sub(r'^#EXTINF:-?1', '#EXTINF:-1', line)
            line = normalize_extinf_group_title(line, "Fancode Live")
            line = set_attr(line, "x-origin", "fancode")
            line = set_attr(line, "x-managed", "rxs")
            fresh.append(line)
            if i + 1 < len(raw) and raw[i + 1].startswith("http"):
                fresh.append(raw[i + 1].strip())
                i += 1
        i += 1

    if not os.path.exists("template.m3u"):
        raise FileNotFoundError("template.m3u not found")
    lines = read_lines("template.m3u")

    # Remove any previously managed Fancode blocks, or any block with group-title=Fancode Live
    def is_old_fancode(extinf, headers, url):
        gt = 'group-title="Fancode Live"' in extinf
        managed = has_attr(extinf, "x-origin", "fancode") or has_attr(extinf, "x-managed", "rxs")
        return gt or managed

    cleaned = remove_blocks_by_predicate(lines, is_old_fancode)

    # Compare old vs new Fancode by hash of blocks we removed (best-effort)
    # We can just append fresh Fancode at end for consistency
    new_lines = cleaned + ["# --- BEGIN FANCODE (managed) ---"] + fresh + ["# --- END FANCODE (managed) ---"]
    write_lines("template.m3u", new_lines)
    print("Fancode সেকশন রিফ্রেশ হয়েছে।")

# =============== STEP 3: API section replace (clean, with UA) ===============
def update_api_channels():
    def fetch_api():
        url = "https://otapp.store/rest-api//v130/all_tv_channel_by_category"
        headers = {
            "API-KEY": "ottbangla@android",
            "Authorization": "Basic YWRtaW46MTIzNA==",
            "Host": "otapp.store",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/4.9.0",
        }
        res = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
        res.raise_for_status()
        return res.json()

    api = fetch_api()

    # Build fresh API blocks + collect names for sweeping duplicates
    fresh = []
    api_names = set()
    for cat in api:
        group = (cat.get("title") or "Unknown").strip()
        for ch in cat.get("channels", []):
            name = (ch.get("tv_name") or "").strip()
            stream = (ch.get("stream_url") or "").strip()
            if not name or not stream:
                continue
            if name.lower() in ignore_names:
                continue
            api_names.add(name.lower())
            tvg_id = ch.get("live_tv_id", "")
            logo = ch.get("thumbnail_url", "")
            extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}'
            extinf = set_attr(extinf, "x-origin", "api")
            extinf = set_attr(extinf, "x-managed", "rxs")
            fresh.append(extinf)
            fresh.append(f'#EXTVLCOPT:http-user-agent={UA_STR}')
            # চাইলে EXTHTTP যোগ করতে পারেন:
            # fresh.append(f'#EXTHTTP:{{"User-Agent":"{UA_STR}"}}')
            fresh.append(stream)

    if not os.path.exists("template.m3u"):
        raise FileNotFoundError("template.m3u not found")
    lines = read_lines("template.m3u")

    # 1) পুরোনো managed API ব্লক ডিলিট
    def is_old_managed_api(extinf, headers, url):
        return has_attr(extinf, "x-origin", "api") or has_attr(extinf, "x-managed", "rxs")

    lines = remove_blocks_by_predicate(lines, is_old_managed_api)

    # 2) ফার্স্ট-টাইম মাইগ্রেশনে ডুপ্লিকেট নাম ঝাড়ুন:
    #    যেসব ব্লকের নাম fresh API সেটে আছে এবং x-keep="1" নেই এবং Fancode নয়—সব ডিলিট।
    def is_conflicting_old(extinf, headers, url):
        if 'group-title="Fancode Live"' in extinf:
            return False  # Fancode untouched
        if has_attr(extinf, "x-keep", "1"):
            return False  # user-protected
        name = get_name_from_extinf(extinf).lower()
        return name in api_names

    lines = remove_blocks_by_predicate(lines, is_conflicting_old)

    # 3) নতুন API ব্লক অ্যাড করুন (টেইলে)
    lines += ["# --- BEGIN API (managed) ---"] + fresh + ["# --- END API (managed) ---"]
    write_lines("template.m3u", lines)
    print("API সেকশন রিফ্রেশ হয়েছে।")

# =============== STEP 4: Final output with greeting ===============
def generate_final_file():
    input_file = 'template.m3u'
    output_file = 'ottrxs.m3u'

    if ZoneInfo:
        bd_time = datetime.now(ZoneInfo("Asia/Dhaka"))
    else:
        bd_time = datetime.utcnow() + timedelta(hours=6)

    hour = bd_time.hour
    if 5 <= hour < 12:
        msg = "🥱Good morning☀️👉Vip Ip Tv By Reyad Hossain🇧🇩"
    elif 12 <= hour < 18:
        msg = "☀️Good Afternoon👉Vip Ip Tv By Reyad Hossain🇧🇩"
    else:
        msg = "🌙Good Night👉Vip Ip Tv By Reyad Hossain🇧🇩"

    if not os.path.exists(input_file):
        raise FileNotFoundError("template.m3u not found")

    src = read_lines(input_file)
    out = []
    for i, line in enumerate(src):
        if i == 0 and line.startswith("#EXTM3U"):
            out.append(f'#EXTM3U billed-msg="{msg}"')
        else:
            out.append(line)
    write_lines(output_file, out)
    print("Final M3U তৈরি হয়েছে:", output_file)

# =============== DRIVER ===============
if __name__ == "__main__":
    # যেসব চ্যানেল Toffee সোর্স থেকে রিফ্রেশ করবেন (exact নাম)
    channel_list = [
        "Cartoon Network", "Pogo", "Discovery Kids", "Cartoon Network HD", "PSL VIP", "TLC HD", "Discovery"
    ]

    safe_run("Selected Channel Refresh", lambda: update_channels(channel_list))
    safe_run("Fancode", update_fancode)
    safe_run("API", update_api_channels)
    safe_run("Final Output", generate_final_file)
