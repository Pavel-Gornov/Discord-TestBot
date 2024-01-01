import json
import datetime
from settings import DEFAULT_LANG, LANGS
from enum import Enum
import discord


class Color(Enum):
    BOT = 0xFFF7ED
    SUCCESS = 0x66bb6a
    ERROR = 0xf03431


def load_local():
    with open("locale.json", mode="r", encoding="utf-8") as f:
        return json.load(f)


LOCAL = load_local()


def tbsl(string_id: str, local=None):
    if local is None:
        return LOCAL.get(string_id, None)
    if string_id in LOCAL.keys():
        s = LOCAL.get(string_id)
        if local in s.keys():
            return s.get(local, "")
        return s.get(DEFAULT_LANG, "")
    return ""


def makeDSTimestamp(year, month, day, hour, minute, second, timezone, mode):
    dt = datetime.datetime(year, month, day, hour, minute, second,
                           tzinfo=datetime.timezone(datetime.timedelta(hours=timezone)))
    return f"<t:{int(dt.timestamp())}:{mode[0]}>"


# TODO: Добавить настройки языка сервера и использовать их в этой функции.
def get_guild_lang(guild: discord.Guild) -> str:
    if not guild or guild.preferred_locale not in LANGS:
        return DEFAULT_LANG
    return guild.preferred_locale


def is_emoji(string):
    range_min = 127744
    range_max = 129782
    range_min_2 = 126980
    range_max_2 = 127569
    range_min_3 = 169
    range_max_3 = 174
    range_min_4 = 8205
    range_max_4 = 12953
    if string:
        for a_char in string:
            char_code = ord(a_char)
            if range_min <= char_code <= range_max:
                return True
            elif range_min_2 <= char_code <= range_max_2:
                return True
            elif range_min_3 <= char_code <= range_max_3:
                return True
            elif range_min_4 <= char_code <= range_max_4:
                return True
        return False
    else:
        return False
