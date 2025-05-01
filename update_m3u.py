import os
from datetime import datetime, timedelta

# ইনপুট ও আউটপুট ফাইলের নাম
input_file = 'template.m3u'
output_file = 'ottrxs.m3u'

# বাংলাদেশ সময় নির্ণয় (UTC +6)
bd_time = datetime.utcnow() + timedelta(hours=6)
current_hour = bd_time.hour

# সময় অনুযায়ী শুভেচ্ছা বার্তা নির্ধারণ
if 5 <= current_hour < 12:
    billed_msg = "🥱Good morning☀️👉Vip Ip Tv By Reyad Hossain🇧🇩"
elif 12 <= current_hour < 18:
    billed_msg = "☀️Good Afternoon👉Vip Ip Tv By Reyad Hossain🇧🇩"
else:
    billed_msg = "🌙Good Night👉Vip Ip Tv By Reyad Hossain🇧🇩"

# ফাইল পড়া ও নতুন ফাইলে লেখা
with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    first_line_written = False
    for line in infile:
        # প্রথম লাইন যদি #EXTM3U হয়, তাহলে টাইম অনুযায়ী মেসেজ বসানো হবে
        if not first_line_written and line.startswith("#EXTM3U"):
            outfile.write(f'#EXTM3U billed-msg="{billed_msg}"\n')
            first_line_written = True
        elif line.startswith("http") and (".m3u8" in line or ".mpd" in line):
            # টোকেন ছাড়াই URL টি পরিষ্কার করে লেখা
            outfile.write(line.strip() + "\n")
        else:
            # অন্যান্য সব লাইন অপরিবর্তিত রেখে লেখা
            outfile.write(line)
