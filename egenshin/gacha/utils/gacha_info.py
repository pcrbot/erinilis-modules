from ...util import Dict
from hoshino import aiorequests

BASE_URL = 'https://webstatic.mihoyo.com/hk4e/gacha_info/cn_gf01/%s'


async def gacha_info_list():
    res = await aiorequests.get(BASE_URL % 'gacha/list.json')
    json_data = await res.json(object_hook=Dict)

    if json_data.retcode != 0:
        raise Exception(json_data.message)

    return json_data.data.list


async def gacha_info(gacha_id):
    res = await aiorequests.get(BASE_URL % gacha_id + '/zh-cn.json')

    if res.status_code != 200:
        raise Exception("error gacha_id: %s" % gacha_id)

    return await res.json(object_hook=Dict)
