from nonebot import *
from hoshino import Service
from .service import switcher
from . import util, gacha_log
from .bind import bind

sv = Service('gachalog')

_bot = get_bot()
app = _bot.server_app
app.register_blueprint(switcher)

# 初始化配置文件
config = util.get_config()
db = util.init_db(config.cache_dir)

bind_help = """
1.请在游戏内打开派蒙界面(esc)
2.点击反馈,pc端会打开浏览器
3.复制浏览器上的链接地址后使用 {comm} 进行绑定
手机端打开反馈后进行断网再刷新,会显示网页无法打开,把里面的内容全选复制就可
例: {comm}https://webstatic.mi....
"""


@sv.on_message('group')
async def gachalog_main(*params):
    bot, ctx = (_bot, params[0]) if len(params) == 1 else params

    msg = str(ctx['message']).strip()
    keyword = util.get_msg_keyword(config.comm.gachalog, msg, True)
    if isinstance(keyword, str):
        await get_log(ctx)

    keyword = util.get_msg_keyword(config.comm.gacha_statistics, msg, True)
    if isinstance(keyword, str):
        await gacha_statistics(ctx)

    keyword = util.get_msg_keyword(config.comm.bind, msg, True)
    if keyword:
        await _bot.send(ctx, await bind(ctx.user_id, keyword).save(), at_sender=True)


async def check_bind(ctx) -> gacha_log:
    uid = ctx.user_id
    log_db = db.get(uid, {})
    if not log_db:
        await _bot.send(ctx, bind_help.format(comm=config.comm.bind))
        return
    gl = gacha_log.gacha_log(uid, log_db['authkey'], log_db.get('region'))
    return gl


async def get_log(ctx):
    log = await check_bind(ctx)
    if not log:
        return
    if not await log.check_authkey():
        await _bot.send(ctx, '凭证已过期,请重新获取\n' + bind_help.format(comm=config.comm.bind))
        return
    await _bot.send(ctx, await log.current(), at_sender=True)


async def gacha_statistics(ctx):
    log = await check_bind(ctx)
    if not log:
        return
    is_expired = not await log.check_authkey()
    msg = ''
    if is_expired:
        msg += '凭证已过期, 仅能查询上一次的结果 \n'

    await _bot.send(ctx, msg + '正在处理 请稍等')
    await _bot.send(ctx, await log.update_xlsx(ctx.user_id, is_expired), at_sender=True)
