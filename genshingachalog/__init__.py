from nonebot import *
from hoshino import Service  # 如果使用hoshino的分群管理取消注释这行
from .service import switcher
from . import util, gacha_log

#
sv = Service('gachalog')  # 如果使用hoshino的分群管理取消注释这行

_bot = get_bot()
app = _bot.server_app
app.register_blueprint(switcher)

# 初始化配置文件
config = util.get_config()
db = util.init_db(config.cache_dir)


@sv.on_message('group')
# @_bot.on_message  # nonebot使用这
async def gachalog_main(*params):
    bot, ctx = (_bot, params[0]) if len(params) == 1 else params

    msg = str(ctx['message']).strip()
    keyword = util.get_msg_keyword(config.comm.gachalog, msg, True)
    if isinstance(keyword, str):
        await get_log(ctx)

    keyword = util.get_msg_keyword(config.comm.gacha_statistics, msg, True)
    if keyword:
        await gacha_statistics(ctx, keyword)


async def check_bind(ctx) -> gacha_log:
    uid = ctx.user_id
    log_db = db.get(uid, {})
    if not log_db:
        await _bot.send(ctx, '你还没有绑定')
        return
    gl = gacha_log.gacha_log(uid, log_db['authkey'], log_db.get('region'))
    if not await gl.check_authkey():
        await _bot.send(ctx, '凭证已过期,请重新获取')
        return

    return gl


async def get_log(ctx):
    log = await check_bind(ctx)
    if not log:
        return
    await _bot.send(ctx, await log.current(), at_sender=True)


async def gacha_statistics(ctx, keyword):
    log = await check_bind(ctx)
    if not log:
        return
    await _bot.send(ctx, '正在处理 请稍等')
    await _bot.send(ctx, await log.gacha_statistics(ctx.user_id, keyword), at_sender=True)
