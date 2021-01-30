import base64
import json
import math
import re
import requests
import urllib.parse
from io import BytesIO
import matplotlib.pyplot as plt
from enum import Enum
from . import util

config = util.get_config()
db = util.init_db(config.cache_dir)


class GACHA_TYPE(Enum):
    activity = 301  # 限定卡池
    weapon = 302  # 武器卡池
    permanent = 200  # 常驻卡池


def gacha_type_by_name(name):
    if re.search(r'^[限活][定动]池?$', name, re.I):
        return GACHA_TYPE.activity.value
    if re.search(r'^[武][器]池?$', name, re.I):
        return GACHA_TYPE.weapon.value
    if re.search(r'^[常普][驻通规]池?$', name, re.I):
        return GACHA_TYPE.permanent.value
    return 0


def get_item_list():
    url = 'https://webstatic.mihoyo.com/hk4e/gacha_info/%s/items/%s.json' % ('cn_gf01', 'zh-cn')
    return util.dict_to_object(json.loads(requests.get(url, timeout=30).text))


items = get_item_list()


class gacha_log:
    qq: str
    authkey: str
    size: int

    def __init__(self, qq: str, authkey: str, region='cn_gf01', size=20):
        self.qq = qq
        self.authkey = authkey
        self.size = size
        self.region = region

    def get_api(self,
                service='getGachaLog',
                page=1,
                gacha_type=301,
                ):
        params = dict()
        params['authkey_ver'] = 1
        params['lang'] = 'zh-cn'
        params['region'] = self.region
        params['authkey'] = self.authkey
        params['size'] = self.size
        params['page'] = page
        params['gacha_type'] = gacha_type
        url = f'{config.api}{service}?{urllib.parse.urlencode(params)}'
        res = util.dict_to_object(json.loads(requests.get(url, timeout=30).text))
        if res.message == 'authkey valid error':
            print('authkey 错误')
            return False
        if not res.data:
            print(res.message)
            return False
        return res.data

    async def get_logs(self, gacha_type, _filter=None):
        item_list = []
        _flag = False
        for page in range(1, 9999):
            clist = self.get_api(page=page, gacha_type=gacha_type).list
            if not clist:
                break
            for data in clist:
                item_info = util.filter_list(items, lambda x: x['item_id'] == data['item_id'])
                if not len(item_info):
                    item_info = [{
                        "item_id": data['item_id'],
                        "name": "unknown",
                        "item_type": "unknown",
                        "rank_type": "unknown"
                    }]
                item_info = item_info[0]
                item_info['time'] = data['time']
                item_list.append(item_info)
                if _filter:
                    _flag = _filter(item_info)
                    if _flag:
                        break
            if _flag:
                break
        return item_list

    async def last5star(self, gacha_type):
        item_list = await self.get_logs(gacha_type, lambda item_info: item_info['rank_type'] == '5')
        if not item_list:
            return '还没有抽过'
        return '距离上一个%s一共抽了%s发' % (item_list[-1:][0]['name'], len(item_list) - 1)

    async def current(self):
        activity_gacha = await self.last5star(GACHA_TYPE.activity.value)
        weapon_gacha = await self.last5star(GACHA_TYPE.weapon.value)
        permanent_gacha = await self.last5star(GACHA_TYPE.permanent.value)

        msg = '查询的记录有1小时左右的延迟\n\n'
        msg += '限定池%s\n' % activity_gacha
        msg += '武器池%s\n' % weapon_gacha
        msg += '常规池%s' % permanent_gacha

        return msg

    async def get_config_list(self):
        data = self.get_api('getConfigList')
        return data.gacha_type_list if data else False

    async def check_authkey(self):
        return await self.get_config_list()

    async def gacha_statistics(self, gacha_type_name):
        gacha_type = gacha_type_by_name(gacha_type_name)
        if not gacha_type:
            return
        logs = await self.get_logs(gacha_type)

        data = list(map(lambda x: x if x['rank_type'] == '5' else 0, logs))
        input_values = []
        squares = []
        pulls = 0
        data.reverse()
        for item in data:
            pulls += 1
            if not item:
                continue
            squares.append(pulls)
            input_values.append('%s(%s)' % (item['name'], pulls))
            pulls = 0
        input_values.append('%s(%s)' % ('目前', pulls))
        squares.append(pulls)

        plt.plot(input_values, squares, label='一共%s个5星' % (len(input_values) - 1))
        plt.legend()
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        all_pulls_num = len(logs) - pulls

        if not len(input_values) - 1:
            total_probability = 0
        else:
            total_probability = ((len(input_values) - 1) / all_pulls_num) * 100
        plt.title('%s(%s次5星出货概率为%.2f%%)' % (gacha_type_name, all_pulls_num, total_probability), fontsize=24)

        max_pulls = 74

        probability = 0.6

        if pulls > max_pulls:
            probability = probability + (pulls - max_pulls) * 5.3
            probability_str = "当前%s抽,下一抽大概有%.2f%%几率获得5星" % (pulls, probability)
        else:
            mp = max_pulls - pulls
            probability_str = '74抽前抽%s次有%.2f%%几率出现5星' % (mp, round((1 - math.pow(0.994, mp)) * 100, 2))

        plt.xlabel(probability_str, fontsize=14)

        buf = BytesIO()
        plt.savefig(buf, format='PNG', dpi=100)
        plt.close()
        base64_str = base64.b64encode(buf.getvalue()).decode()
        return 'base64://' + base64_str
