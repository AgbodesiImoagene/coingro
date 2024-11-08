"""
Various tool functions for Coingro and scripts
"""
import gzip
import logging
import os
import re
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Iterator, List, Optional, TypeVar, cast, overload
from typing.io import IO
from urllib.parse import urlparse

import rapidjson

from coingro.constants import DECIMAL_PER_COIN_FALLBACK, DECIMALS_PER_COIN, RETRY_COUNT, RETRY_TIME
from coingro.exceptions import RetryableOrderError, TemporaryError

logger = logging.getLogger(__name__)


def decimals_per_coin(coin: str):
    """
    Helper method getting decimal amount for this coin
    example usage: f".{decimals_per_coin('USD')}f"
    :param coin: Which coin are we printing the price / value for
    """
    return DECIMALS_PER_COIN.get(coin, DECIMAL_PER_COIN_FALLBACK)


def round_coin_value(
    value: float, coin: str, show_coin_name=True, keep_trailing_zeros=False
) -> str:
    """
    Get price value for this coin
    :param value: Value to be printed
    :param coin: Which coin are we printing the price / value for
    :param show_coin_name: Return string in format: "222.22 USDT" or "222.22"
    :param keep_trailing_zeros: Keep trailing zeros "222.200" vs. "222.2"
    :return: Formatted / rounded value (with or without coin name)
    """
    val = f"{value:.{decimals_per_coin(coin)}f}"
    if not keep_trailing_zeros:
        val = val.rstrip("0").rstrip(".")
    if show_coin_name:
        val = f"{val} {coin}"

    return val


def shorten_date(_date: str) -> str:
    """
    Trim the date so it fits on small screens
    """
    new_date = re.sub("seconds?", "sec", _date)
    new_date = re.sub("minutes?", "min", new_date)
    new_date = re.sub("hours?", "h", new_date)
    new_date = re.sub("days?", "d", new_date)
    new_date = re.sub("^an?", "1", new_date)
    return new_date


def file_dump_json(
    filename: Path,
    data: Any,
    is_zip: bool = False,
    log: bool = True,
    pretty_print: bool = False,
    nan: bool = False,
) -> None:
    """
    Dump JSON data into a file
    :param filename: file to create
    :param is_zip: if file should be zip
    :param data: JSON Data to save
    :return:
    """
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)

    wm = rapidjson.WM_PRETTY if pretty_print else rapidjson.WM_COMPACT
    nm = rapidjson.NM_NAN if nan else rapidjson.NM_NATIVE

    if is_zip:
        if filename.suffix != ".gz":
            filename = filename.with_suffix(".gz")
        if log:
            logger.info(f'dumping json to "{filename}"')

        with gzip.open(filename, "w") as fpz:
            rapidjson.dump(data, fpz, default=str, number_mode=nm, write_mode=wm, indent=4)
    else:
        if log:
            logger.info(f'dumping json to "{filename}"')
        with open(filename, "w") as fp:
            rapidjson.dump(data, fp, default=str, number_mode=nm, write_mode=wm, indent=4)

    logger.debug(f'done json to "{filename}"')


def file_dump_joblib(filename: Path, data: Any, log: bool = True) -> None:
    """
    Dump object data into a file
    :param filename: file to create
    :param data: Object data to save
    :return:
    """
    import joblib

    if log:
        logger.info(f'dumping joblib to "{filename}"')
    with open(filename, "wb") as fp:
        joblib.dump(data, fp)
    logger.debug(f'done joblib dump to "{filename}"')


def json_load(datafile: IO) -> Any:
    """
    load data with rapidjson
    Use this to have a consistent experience,
    set number_mode to "NM_NATIVE" for greatest speed
    """
    return rapidjson.load(datafile, number_mode=rapidjson.NM_NATIVE)


def file_load_json(file):

    if file.suffix != ".gz":
        gzipfile = file.with_suffix(file.suffix + ".gz")
    else:
        gzipfile = file
    # Try gzip file first, otherwise regular json file.
    if gzipfile.is_file():
        logger.debug(f"Loading historical data from file {gzipfile}")
        with gzip.open(gzipfile) as datafile:
            pairdata = json_load(datafile)
    elif file.is_file():
        logger.debug(f"Loading historical data from file {file}")
        with open(file) as datafile:
            pairdata = json_load(datafile)
    else:
        return None
    return pairdata


def pair_to_filename(pair: str) -> str:
    for ch in ["/", " ", ".", "@", "$", "+", ":"]:
        pair = pair.replace(ch, "_")
    return pair


def format_ms_time(date: int) -> str:
    """
    convert MS date to readable format.
    : epoch-string in ms
    """
    return datetime.fromtimestamp(date / 1000.0).strftime("%Y-%m-%dT%H:%M:%S")


def deep_merge_dicts(source, destination, allow_null_overrides: bool = True):
    """
    Values from Source override destination, destination is returned (and modified!!)
    Sample:
    >>> a = { 'first' : { 'rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            deep_merge_dicts(value, node, allow_null_overrides)
        elif value is not None or allow_null_overrides:
            destination[key] = value

    return destination


def round_dict(d, n):
    """
    Rounds float values in the dict to n digits after the decimal point.
    """
    return {k: (round(v, n) if isinstance(v, float) else v) for k, v in d.items()}


def safe_value_fallback(obj: dict, key1: str, key2: str, default_value=None):
    """
    Search a value in obj, return this if it's not None.
    Then search key2 in obj - return that if it's not none - then use default_value.
    Else falls back to None.
    """
    if key1 in obj and obj[key1] is not None:
        return obj[key1]
    else:
        if key2 in obj and obj[key2] is not None:
            return obj[key2]
    return default_value


def safe_value_fallback2(dict1: dict, dict2: dict, key1: str, key2: str, default_value=None):
    """
    Search a value in dict1, return this if it's not None.
    Fall back to dict2 - return key2 from dict2 if it's not None.
    Else falls back to None.

    """
    if key1 in dict1 and dict1[key1] is not None:
        return dict1[key1]
    else:
        if key2 in dict2 and dict2[key2] is not None:
            return dict2[key2]
    return default_value


def plural(num: float, singular: str, plural: Optional[str] = None) -> str:
    return singular if (num == 1 or num == -1) else plural or singular + "s"


def render_template(templatefile: str, arguments: dict = {}) -> str:

    from jinja2 import Environment, PackageLoader, select_autoescape

    env = Environment(
        loader=PackageLoader("coingro", "templates"), autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template(templatefile)
    return template.render(**arguments)


def render_template_with_fallback(
    templatefile: str, templatefallbackfile: str, arguments: dict = {}
) -> str:
    """
    Use templatefile if possible, otherwise fall back to templatefallbackfile
    """
    from jinja2.exceptions import TemplateNotFound

    try:
        return render_template(templatefile, arguments)
    except TemplateNotFound:
        return render_template(templatefallbackfile, arguments)


def chunks(lst: List[Any], n: int) -> Iterator[List[Any]]:
    """
    Split lst into chunks of the size n.
    :param lst: list to split into chunks
    :param n: number of max elements per chunk
    :return: None
    """
    for chunk in range(0, len(lst), n):
        yield (lst[chunk : chunk + n])


def parse_db_uri_for_logging(uri: str):
    """
    Helper method to parse the DB URI and return the same DB URI with the password censored
    if it contains it. Otherwise, return the DB URI unchanged
    :param uri: DB URI to parse for logging
    """
    parsed_db_uri = urlparse(uri)
    if not parsed_db_uri.netloc:  # No need for censoring as no password was provided
        return uri
    pwd = parsed_db_uri.netloc.split(":")[1].split("@")[0]
    return parsed_db_uri.geturl().replace(f":{pwd}@", ":*****@")


F = TypeVar("F", bound=Callable[..., Any])


# Type shenanigans
@overload
def retrier(_func: F) -> F:
    ...


@overload
def retrier(*, retries=RETRY_COUNT, sleep_time: float = RETRY_TIME) -> Callable[[F], F]:
    ...


def retrier(
    _func: Optional[F] = None, *, retries: int = RETRY_COUNT, sleep_time: float = RETRY_TIME
):
    def decorator(f: F) -> F:
        @wraps(f)
        def wrapper(*args, **kwargs):
            count = kwargs.pop("count", retries)
            try:
                return f(*args, **kwargs)
            except (TemporaryError, RetryableOrderError) as ex:
                msg = f'{f.__name__}() returned exception: "{ex}". '
                if count > 0:
                    logger.warning(msg + f"Retrying still for {count} times.")
                    count -= 1
                    kwargs.update({"count": count})
                    time.sleep(sleep_time)
                    return wrapper(*args, **kwargs)
                else:
                    logger.warning(msg + "Giving up.")
                    raise ex

        return cast(F, wrapper)

    # Support both @retrier and @retrier(retries=2, sleep_time=5) syntax
    if _func is None:
        return decorator
    else:
        return decorator(_func)
