from Token import *
import json


def load_local():
    with open("locale.json", mode="r", encoding="utf-8") as f:
        return json.load(f)


def economy():
    with open("economy.json", mode="r", encoding="utf-8") as f:
        return json.load(f)


COLOR_CODES: final = {"bot": 0xFFF7ED, "success": 0x66bb6a, "error": 0xf03431}
LANGS: final = ("ru", "en-US")
DEFAULT_LANG: final = "ru"
LOCAL: final = load_local()
economy_data = economy()
