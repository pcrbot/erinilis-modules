from datetime import timedelta
from bs4 import BeautifulSoup
from hoshino import Service, priv, MessageSegment
from ..util import filter_list, get_next_day, cache
from .utils.gacha_info import gacha_info_list, gacha_info
from .modules.wish import wish, gacha_type_by_name
from .modules.wish_ui import wish_ui

sv_help = '''
[原神十连] 一次10连抽卡
[原神一单] 50连抽卡

[原神十连武器] 10连武器抽卡
[原神十连常驻] 10连常驻抽卡
'''.strip()

sv = Service(
    name='原神抽卡',  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=True,  # 默认启用
    # bundle = '娱乐', #分组归类
    help_=sv_help  # 帮助说明
)

prefix = '原神'

# @sv.on_prefix('原神单抽')
# async def gacha(bot, ev):
#     await check_gacha_data(ev.group_id)
#     wish_info = wish(ev.user_id, gacha_info_data[ev.group_id]['type'], gacha_info_data[ev.group_id]['data']).once()
#     await bot.send(ev, wish_info.data.item_name)


@sv.on_prefix(prefix + '十连')
async def gacha(bot, ev):
    gacha_type, gacha_name, gacha_data = await handle_msg(bot, ev)
    wish_info = await wish(ev.user_id, gacha_type, gacha_data).ten()
    img = await wish_ui.ten_b64_img(wish_info)
    await bot.send(ev, MessageSegment.image(img), at_sender=True)


@sv.on_prefix(prefix + '一单')
async def gacha(bot, ev):
    gacha_type, gacha_name, gacha_data = await handle_msg(bot, ev)
    x5 = []
    for i in range(0, 5):
        x5.append(await wish(ev.user_id, gacha_type, gacha_data).ten())
    img = await wish_ui.ten_b64_img_xn(x5)
    await bot.send(ev, MessageSegment.image(img), at_sender=True)


async def handle_msg(bot, ev):
    msg = ev.message.extract_plain_text().strip() or '限定'
    gacha_type = gacha_type_by_name(msg)
    if not gacha_type:
        await bot.finish(ev, '不存在此卡池: %s' % msg)
    gacha_name, gacha_data = await gacha_pool(gacha_type=gacha_type)
    return gacha_type, gacha_name, gacha_data


@cache(ttl=timedelta(hours=24), arg_key='gacha_type')
async def gacha_pool(gacha_type):
    data = await gacha_info_list()
    gacha_data = filter_list(data, lambda x: x.gacha_type == gacha_type)[0]
    gacha_id = gacha_data.gacha_id
    gacha_name = gacha_data.gacha_name
    gacha_type = gacha_data.gacha_type
    gacha_data = await gacha_info(gacha_id)
    return gacha_name, gacha_data
