import time
import json
from pathlib import Path
from datetime import timedelta
from hoshino import aiorequests
from .collect_sheet_class import *
from ..util import Dict, cache, list_split, get_path, gh_json

local_dir = Path(get_path('achievement'))
with open(local_dir / 'unactuated.json', 'r', encoding="utf-8") as fp:
    UNACTUATED = [remove_special_char(x) for x in json.load(fp)]


async def gh_unactuated_word():
    return await gh_json('achievement/unactuated.json')


# 来源 https://docs.qq.com/sheet/DS01hbnZwZm5KVnBB

BASE_URL = 'https://docs.qq.com/dop-api/opendoc?outformat=1&normal=1&preview_token='


def end_point(tab):
    return f'{BASE_URL}&t={int(time.time())}&id=DS01hbnZwZm5KVnBB&tab={tab}'


# 汇总
def get_all_achievements_api():
    keep_head = 2
    keep_row = 0
    return end_point('BB08J3'), keep_head, keep_row, 12, 1, Achievements_Info


# 2.0新增
# def get_all_achievements20_api():
#     keep_head = 1
#     keep_row = 0
#     return end_point('l6oi5q'), keep_head, keep_row, 10, 0, Achievements20_Info


# 2.1新增
# def get_all_achievements21_api():
#     keep_head = 1
#     keep_row = 1
#     return end_point('zc19mx'), keep_head, keep_row, 12, 0, Achievements21_Info

# 2.2新增
def get_all_achievements22_api():
    keep_head = 2
    keep_row = 1
    return end_point('ctb4sr'), keep_head, keep_row, 12, 0, Achievements22_Info


def get_row_value(row):
    info = row.get('2')
    if not info:
        return ''
    return str(row['2'][1])


@cache(ttl=timedelta(hours=24), arg_key='url')
async def request_raw_data(url):
    res = await aiorequests.get(url)
    json_data = await res.json(object_hook=Dict)
    text = json_data.clientVars.collab_client_vars.initialAttributedText.text
    if not text:
        raise Exception('获取数据失败, 很可能是数据源缓存问题, 请稍后再试')
    sheet = text[0][-1][0]['c'][1]
    return [i for i in sheet.values()]


async def request_data(top_type, url, keep_head, keep_row, field_count,
                       ext_field_count, structure):
    gh_unactuated = [remove_special_char(x) for x in await gh_unactuated_word()]
    raw_data = await request_raw_data(url=url)
    sheet_list = list_split(raw_data,
                            field_count + ext_field_count)[keep_head:]
    result = {}
    for row in sheet_list:
        data = structure(*[get_row_value(x)
                           for x in row[:field_count]][keep_row:])



        name = str(data)
        
        if name in UNACTUATED or name in gh_unactuated:
            continue

        if not top_type:
            result[name] = data
        elif top_type == data.top_type:
            result[name] = data

    return result


@cache(ttl=timedelta(hours=24))
async def achievements_sheet(top_type='天地万象'):
    result = {}
    data = await request_data(*((top_type, ) + get_all_achievements_api()))
    # data20 = await request_data(*((top_type, ) + get_all_achievements20_api()))
    # data21 = await request_data(*((top_type, ) + get_all_achievements21_api()))
    data22 = await request_data(*((top_type, ) + get_all_achievements22_api()))

    result.update(data)
    # result.update(data20)
    # result.update(data21)
    result.update(data22)

    return result
