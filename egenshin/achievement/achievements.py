import re
from datetime import timedelta
from bs4 import BeautifulSoup
from ..util import cache
from hoshino import aiorequests


def remove_special_char(s):
    special_char = r'[ 「」…！!，,。.、？?《》·♬Ⅱ—]'
    return re.sub(special_char, '', s)


@cache(ttl=timedelta(hours=24))
async def all_achievements():
    url = f'https://genshin.honeyhunterworld.com/db/achiev/ac_1/?lang=CHS'
    res = await aiorequests.get(url)
    res = BeautifulSoup(await res.text, features="lxml")
    name = map(
        lambda row: row.text,
        res.select(
            'table.art_stat_table > tr:nth-child(n) > td:nth-child(3) > a'))

    description = map(
        lambda row: row.text,
        res.select(
            'table.art_stat_table > tr:nth-child(n+2) > td:nth-child(4)'))

    reward = map(
        lambda row: row.text[2:],
        res.select(
            'table.art_stat_table > tr:nth-child(n+2) > td:nth-child(6)'))

    version = map(
        lambda row: row.text,
        res.select(
            'table.art_stat_table > tr:nth-child(n+2) > td:nth-child(7)'))

    result = {}
    for name, description, reward, version in zip(name, description, reward,
                                                  version):
        if '(test)' in name:
            continue
        result[remove_special_char(name)] = dict(name=name,
                                                 description=description,
                                                 reward=reward,
                                                 version=version)
    return result