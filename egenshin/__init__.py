from . import util
from .material import *
from hoshino import Service  # 如果使用hoshino的分群管理取消注释这行

#
sv = Service('egenshin')  # 如果使用hoshino的分群管理取消注释这行
# 初始化配置文件
config = util.get_config()

# 初始化nonebot
_bot = get_bot()


@sv.on_message('group')  # 如果使用hoshino的分群管理取消注释这行 并注释下一行的 @_bot.on_message("group")
# @_bot.on_message  # nonebot使用这
async def main(*params):
    bot, ctx = (_bot, params[0]) if len(params) == 1 else params
    msg = str(ctx['message']).strip()

    # ---------------- 素材定时提醒 ----------------
    mat = material(ctx.group_id, ctx.user_id)
    # 收集素材
    keyword = util.get_msg_keyword(config.comm.material, msg, True)
    if keyword:
        await _bot.send(ctx, await mat.mark(keyword))
    if keyword == '':
        await _bot.send(ctx, await mat.status())

    # 查看材料
    keyword = util.get_msg_keyword(config.comm.show_material, msg, True)
    if keyword:
        await _bot.send(ctx, await mat.show(keyword))
