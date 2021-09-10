import time
from dataclasses import dataclass
from datetime import timedelta
from hoshino import aiorequests
from ..util import Dict, cache, list_split
from .achievements import remove_special_char

BASE_URL = 'https://docs.qq.com/dop-api/opendoc?outformat=1&normal=1&preview_token='


def end_point(tab):
    return f'{BASE_URL}&t={int(time.time())}&id=DS01hbnZwZm5KVnBB&tab={tab}'


def get_all_achievements_api():
    return end_point('BB08J3'), 13, Achievements_Info


# def get_unactuated_api():
#     return end_point('nps16r'), 9, Unactuated_Info


def get_row_value(row):
    info = row.get('2')
    if not info:
        return ''
    return str(row['2'][1])


@dataclass
class Achievements_Info:
    id: str
    code: str
    version: str
    is_hide: str
    top_type: str
    name: str
    desc: str
    type: str
    rarity: str
    reward: str
    remark: str
    neta: str

    def __str__(self):
        return remove_special_char(self.name)

    @property
    def is_daily_quest(self):
        return '每日' in self.type
    
    @property
    def is_main_quest(self):
        return '魔神' in self.type
    
    @property
    def is_world_quest(self):
        return '世界任务' in self.type
    
    @property
    def is_prestige_quest(self):
        return '声望' in self.type
    
    @property
    def is_world_explore(self):
        return '大世界' in self.type

    @property
    def is_battle(self):
        return '战斗相关' in self.type
    
    @property
    def is_cooking(self):
        return '料理相关' in self.type

# @dataclass
# class Unactuated_Info:
#     code: str
#     version: str
#     is_hide: str
#     top_type: str
#     name: str
#     desc: str
#     type: str
#     remark: str
#     neta: str

@cache(ttl=timedelta(hours=24))
async def achievements_sheet():
    url, field_count, structure = get_all_achievements_api()

    res = await aiorequests.get(url)
    json_data = await res.json(object_hook=Dict)
    sheet = json_data.clientVars.collab_client_vars.initialAttributedText.text[
        0][-1][0]['c'][1]
    sheet_list = list_split([i for i in sheet.values()], field_count)[2:]
    result = {}
    for row in sheet_list:
        data = structure(*[get_row_value(x) for x in row[:field_count - 1]])
        result[str(data)] = data

    return result
