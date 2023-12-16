from Token import *
import json


def load_local():
    with open("locale.json", mode="r", encoding="utf-8") as f:
        return json.load(f)


def economy():
    with open("economy.json", mode="r", encoding="utf-8") as f:
        return json.load(f)


GREETINGS_LIST: final = ('Привет', 'Приветствую', 'Рад видеть вас')
COLOR_CODES: final = {"bot": 0xFFF7ED, "success": 0x66bb6a, "error": 0xf03431}
EMOJIS: final = ("🪨", "📜", "✂")
REQUEST_CODES: final = (100, 101, 102, 103,
                        200, 201, 202, 203, 204, 206, 207,
                        300, 301, 302, 303, 304, 305, 307, 308,
                        400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                        411, 412, 413, 414, 415, 416, 417, 418, 420,
                        421, 422, 423, 424, 425, 426, 429, 431, 444, 450, 451, 497,
                        498, 499, 500, 501, 502, 503, 504, 506, 507, 508, 509, 510,
                        511, 521, 522, 523, 525, 599)
SETTINGS: final = {'token': TOKEN, 'bot': BOT_NAME, 'id': BOT_ID, 'prefix': 'd|'}
GUILD_IDS: final = [1076117733428711434, 1055895511359574108]
BOT_ICON_URL: final = "https://media.discordapp.net/attachments/1055896512053399623/1150820899231109271/-.png"
LANGS: final = ("ru", "en-US")
DEFAULT_LANG: final = "ru"
LOCAL: final = load_local()
economy_data = economy()
