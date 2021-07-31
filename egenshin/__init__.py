from . import util
from .ann import *
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
    is_super_admin = ctx.user_id in _bot.config.SUPERUSERS
    is_admin = util.is_group_admin(ctx) or is_super_admin

    # ---------------- 原神公告 ----------------

    # 原神公告
    keyword = util.get_msg_keyword(config.comm.ann_list, msg, True)
    if isinstance(keyword, str) and keyword == '':
        await _bot.send(ctx, await ann().ann_list_msg())

    # 原神公告详情
    keyword = util.get_msg_keyword(config.comm.ann_detail, msg, True)
    if keyword and keyword.isdigit():
        await _bot.send(ctx, await ann().ann_detail_msg(int(keyword)))

    # 订阅原神公告
    keyword = util.get_msg_keyword(config.comm.sub_ann, msg, True)
    if isinstance(keyword, str) and config.setting.ann_cron_enable:
        if not config.setting.ann_enable_only_admin:
            await _bot.send(ctx, sub_ann(ctx.group_id))
        elif is_admin:
            await _bot.send(ctx, sub_ann(ctx.group_id))
        else:
            await _bot.send(ctx, '你没有权限开启原神公告推送')

    # 取消订阅原神公告
    keyword = util.get_msg_keyword(config.comm.unsub_ann, msg, True)
    if isinstance(keyword, str):
        if not config.setting.ann_enable_only_admin:
            await _bot.send(ctx, unsub_ann(ctx.group_id))
        elif is_admin:
            await _bot.send(ctx, unsub_ann(ctx.group_id))
        else:
            await _bot.send(ctx, '你没有权限取消原神公告推送')

    # 取消公告红点
    keyword = util.get_msg_keyword(config.comm.consume_remind, msg, True)
    if keyword and keyword.isdigit():
        await _bot.send(ctx, await consume_remind(keyword))

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
