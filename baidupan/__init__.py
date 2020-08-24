from nonebot import *
from . import util
from . import api

# from hoshino import Service  # 如果使用hoshino的分群管理取消注释这行

#
# sv = Service('baidupan')  # 如果使用hoshino的分群管理取消注释这行

# 初始化配置文件
config = util.get_config()

# 初始化nonebot
_bot = get_bot()


# @sv.on_message('group')  # 如果使用hoshino的分群管理取消注释这行 并注释下一行的 @_bot.on_message("group")
@_bot.on_message  # nonebot使用这
async def pan_main(*params):
    bot, ctx = (_bot, params[0]) if len(params) == 1 else params

    msg = str(ctx['message']).strip()

    keyword = util.get_msg_keyword(config.comm.keyword, msg, True)
    if keyword:
        return await bot.send(ctx, api.get_share(keyword, *keyword.split(config.comm.split)))

    keyword = util.get_msg_keyword(config.comm.help, msg, True)
    if isinstance(keyword, str):
        return await bot.send(ctx, config.str.help)
