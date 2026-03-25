"""
build.py  –  Inject fresh data into the HTML template and write index.html
Input:   data/agg_data.json  +  data/subcat_data.json  +  scripts/template.html
Output:  index.html
"""

import json, os
from datetime import datetime, timezone

with open("data/agg_data.json",   encoding="utf-8") as f: AGG    = f.read()
with open("data/subcat_data.json", encoding="utf-8") as f: SUBCAT = f.read()

# Validate
agg = json.loads(AGG)
for brand in ("ajio","myntra"):
    a = agg[brand]
    total = a["total"]
    print(f"{brand}: {total:,} reviews | "
          f"avg {a['avg']}★ | "
          f"pos {a['pos']/total*100:.1f}% "
          f"neg {a['neg']/total*100:.1f}% "
          f"neu {a['neu']/total*100:.1f}%")

with open("scripts/template.html", encoding="utf-8") as f:
    html = f.read()

# Inject data
html = html.replace("__AGG__",    AGG)
html = html.replace("__SUBCAT__", SUBCAT)

# Inject build timestamp
ts = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
html = html.replace("__BUILD_TS__", ts)

with open("index.html","w",encoding="utf-8",errors="replace") as f:
    f.write(html)

print(f"\n✅  index.html written  ({os.path.getsize('index.html')//1024} KB)")
print(f"    Last updated: {ts}")
