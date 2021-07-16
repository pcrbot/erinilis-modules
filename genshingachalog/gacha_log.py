import base64
import requests
import json
import math
import re
import urllib.parse
from io import BytesIO
import matplotlib.pyplot as plt
from enum import Enum
from hoshino import aiorequests
from nonebot import MessageSegment
from . import util
from .xlsx_handler import write_xlsx

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

    async def get_api(self,
                      service='getGachaLog',
                      page=1,
                      gacha_type=301,
                      end_id=0
                      ):
        params = dict()
        params['authkey_ver'] = 1
        params['lang'] = 'zh-cn'
        params['region'] = self.region
        params['authkey'] = self.authkey
        params['size'] = self.size
        params['page'] = page
        params['gacha_type'] = gacha_type
        if end_id:
            params['end_id'] = end_id
        url = f'{config.api}{service}?{urllib.parse.urlencode(params)}'
        res = await aiorequests.get(url, timeout=30)
        res = util.dict_to_object(json.loads(await res.text))
        if res.message == 'authkey valid error':
            print('authkey 错误')
            return False
        if not res.data:
            print(res.message)
            return False
        return res.data

    async def get_logs(self, gacha_type, _filter=None, history=None):
        item_list = []
        _flag = False
        end_id = 0
        add_history = False
        history_player_uid = ""
        if history:
            history_player_uid = await self.get_player_uid(history)
        for page in range(1, 9999):
            if add_history:
                break
            clist = (await self.get_api(page=page, gacha_type=gacha_type, end_id=end_id)).list
            if not clist:
                break

            player_uid = await self.get_player_uid(clist)
            if history_player_uid != player_uid:  # 如果 历史记录不匹配 则不使用之前的记录
                history = None

            end_id = clist[-1]['id']
            for data in clist:
                if history and history[0]['id'] == data['id']:
                    item_list = item_list + history
                    add_history = True
                    break
                item_list.append(data)
                if _filter:
                    _flag = _filter(data)
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
        data = await self.get_api('getConfigList')
        return data.gacha_type_list if data else False

    async def check_authkey(self):
        return bool(await self.get_config_list())

    async def get_player_info(self):
        params = dict()
        params['im_out'] = True
        params['sign_type'] = 2
        params['auth_appid'] = 'im_ccs'
        params['authkey_ver'] = 1
        params['win_direction'] = 'portrait'
        params['lang'] = 'zh-cn'
        params['device_type'] = 'pc'
        params['ext'] = '%7B%7D'
        params['game_version'] = 'CNRELWin1.6.0_R3557509_S3266913_D3526661'
        params['authkey'] = self.authkey
        params['game_biz'] = 'hk4e_cn'
        url = f'https://api-takumi.mihoyo.com/common/im/userClient/initUserChat?{urllib.parse.urlencode(params)}'
        res = await aiorequests.post(url, json={
            "device": 'Mozilla',
            "language": 'zh-cn',
            "system_info": 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
        }, timeout=30)
        res = util.dict_to_object(json.loads(await res.text))
        data = res.get('data')
        if not data:
            return None
        return data

    async def get_player_uid(self, clist=None):
        if not clist:
            clist = (await self.get_api(gacha_type=GACHA_TYPE.activity.value)).list
            if not clist:
                return None
        return clist[0]['uid']

    async def update_xlsx(self, uid, is_expired_authkey=False):
        user = db.get(uid, {})
        logs = None
        if is_expired_authkey:
            # 如果凭证过期的话 直接从数据库拿缓存
            logs = user.get(str(GACHA_TYPE.activity.value))
            if not logs:
                return '你尚未获取过卡池记录,请重新绑定刷新数据'
        else:
            for gacha_type in GACHA_TYPE:
                gacha_type = gacha_type.value
                data = await self.get_logs(gacha_type, history=user.get(str(gacha_type), []))
                user[str(gacha_type)] = data
                if not logs:
                    logs = data
            db[uid] = user

        player_uid = await self.get_player_uid(logs)
        await write_xlsx(user)
        msg = is_expired_authkey and '缓存数据' or '数据已更新'
        urls = '\n'.join([f'{url}?uid={player_uid}' for url in config.gacha_analyzer_webs])
        return f'{msg}, 请访问: \n{urls}'

    # 暂时弃用 直接使用网页版本的
    async def gacha_statistics(self, uid, gacha_type_name):
        gacha_type = gacha_type_by_name(gacha_type_name)
        if not gacha_type:
            return
        user = db.get(uid, {})
        logs = await self.get_logs(gacha_type, history=user.get(str(gacha_type), []))
        user[str(gacha_type)] = logs
        db[uid] = user
        # logs = user.get(str(gacha_type)) # debug
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

        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        def split_list(arr, n=8):
            return [arr[i:i + n] for i in range(0, len(arr), n)]

        input_values_arr = split_list(input_values)
        squares_arr = split_list(squares)
        msg = []
        for index, item in enumerate(input_values_arr):
            total_val = len(item) - 1 if len(input_values_arr) - 1 == index else len(item)
            plt.plot(item, squares_arr[index], label='一共%s个5星' % total_val)
            plt.legend()
            if index == len(input_values_arr) - 1:
                all_pulls_num = len(logs) - pulls
                if not len(input_values) - 1:
                    total_probability = 0
                else:
                    total_probability = ((len(input_values) - 1) / all_pulls_num) * 100
                plt.title('%s(%s次5星出货概率为%.2f%%)' % (gacha_type_name, all_pulls_num, total_probability), fontsize=24)

                max_pulls = 74
                if gacha_type == GACHA_TYPE.weapon.value:
                    max_pulls -= 10

                probability = 0.6

                if pulls > max_pulls:
                    probability = probability + (pulls - max_pulls) * 5.3
                    probability_str = "当前%s抽,下一抽大概有%.2f%%几率获得5星" % (pulls, probability)
                else:
                    mp = max_pulls - pulls
                    probability_str = '%s抽前抽%s次有%.2f%%几率出现5星' % (
                        max_pulls, mp, round((1 - math.pow(0.994, mp)) * 100, 2))
                plt.xlabel(probability_str, fontsize=14)
            else:
                plt.title('前一组记录(%s)' % index, fontsize=24)

            buf = BytesIO()
            plt.savefig(buf, format='PNG', dpi=150)
            plt.close()
            base64_str = base64.b64encode(buf.getvalue()).decode()
            msg.append(MessageSegment.image('base64://' + base64_str))
        msg.reverse()
        return msg
