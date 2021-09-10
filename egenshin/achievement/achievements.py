import json
import re
from datetime import timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from hoshino import aiorequests
from ..util import cache, get_path, gh_json

local_dir = Path(get_path('achievement'))


def remove_special_char(s):
    special_char = r'[ 「」…！!，,。.、？?《》·♬Ⅱ—“”-]'
    return re.sub(special_char, '', s)

with open(local_dir / 'unactuated.json', 'r', encoding="utf-8") as fp:
    UNACTUATED = [remove_special_char(x) for x in json.load(fp)]

@cache(ttl=timedelta(hours=10))
async def gh_unactuated():
    return await gh_json('achievement/unactuated.json')


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
    for name, description, reward, version in zip(name, description, reward, version):
        if '(test)' in name:
            continue
        key_name = remove_special_char(name)
        if key_name in UNACTUATED:
            continue
        

        result[key_name] = dict(name=name,
                                description=description,
                                reward=reward,
                                version=version)
    return result
