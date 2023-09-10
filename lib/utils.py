import multiprocessing
from typing import Callable
import datetime


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
