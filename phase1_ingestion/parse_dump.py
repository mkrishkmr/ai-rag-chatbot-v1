import json
from bs4 import BeautifulSoup

with open("dump.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

script = soup.find("script", id="__NEXT_DATA__")
if script:
    data = json.loads(script.string)
    page_props = data.get("props", {}).get("pageProps", {})
    for k in page_props.keys():
        print(f"Prop: {k}")
