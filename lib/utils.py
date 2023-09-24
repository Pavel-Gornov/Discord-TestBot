import multiprocessing
from typing import Callable
import datetime
from storage import DEFULT_LANG, LANGS

import discord


def run_until(seconds: int, func: Callable, *args):
    """Run a function until timeout in seconds reached."""
    with multiprocessing.Pool(processes=2) as pool:
        result = pool.apply_async(func, [*args])
        try:
            result.get(timeout=seconds)
            return result.get()
        except multiprocessing.TimeoutError:
            pass


def makeDSTimestamp(year, month, day, hour, minute, second, timezone, mode):
    dt = datetime.datetime(year, month, day, hour, minute, second,
                           tzinfo=datetime.timezone(datetime.timedelta(hours=timezone)))
    return f"<t:{int(dt.timestamp())}:{mode[0]}>"


# TODO: Добавить настройки языка сервера и использовать их в этой функции.
def get_guild_lang(guild: discord.Guild) -> str:
    if not guild or guild.preferred_locale not in LANGS:
        return DEFULT_LANG
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
