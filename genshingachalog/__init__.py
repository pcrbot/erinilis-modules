import re
from nonebot import *
from hoshino import Service, aiorequests
from .service import switcher
from . import util, gacha_log
from .bind import bind
from ..egenshin.util import support_private

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

@support_private(sv)
@sv.on_prefix(('原神卡池进度' , '卡池进度'))
async def gachalog(bot, ev):
    await get_log(ev)
    
    
@support_private(sv)
@sv.on_prefix(('原神卡池统计' , '卡池统计'))
async def gachalog(bot, ev):
    await gacha_statistics(ev)


@support_private(sv)
@sv.on_prefix(('原神卡池绑定' , '卡池绑定'))
async def gacha_bind(bot, ev):
    msg = ev.message.extract_plain_text().strip()
    await bot.send(ev, await bind(ev.user_id, msg).save(), at_sender=True)


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
        await _bot.send(
            ctx, '凭证已过期,请重新获取\n' + bind_help.format(comm=config.comm.bind))
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
    await _bot.send(ctx, await log.update_xlsx(is_expired), at_sender=True)


@sv.on_notice('group_upload')
async def main(session: NoticeSession):
    ctx = session.ctx
    file = ctx.file
    uid = ctx.user_id

    if not re.search(r'gacha-list-.+\.json', file['name']):
        return

    await session.send('检测到卡池记录文件.正在导入数据', at_sender=True)
    if file['size'] / 1024 / 1024 > 5:
        await session.send('档案过大,确保正确的文件,后请联系作者修改限制', at_sender=True)
        return

    res = await aiorequests.get(file['url'], timeout=30)
    json_data = await res.json(object_hook=util.Dict)

    gacha_data = sum(json_data.result, [])
    keys = ['time', 'name', 'item_type', 'rank_type']
    raw_data = list(
        map(lambda x: list(reversed([dict(zip(keys, i)) for i in x])),
            gacha_data[1::2]))

    gacha_data = dict(zip(gacha_data[::2], raw_data))

    log_db = db.get(uid, {})
    if not log_db:
        region = 'cn_gf01'
        if json_data.uid[0] == "5":
            region = 'cn_qd01'
        gacha_data = {'authkey': "", 'region': region}
        gacha_data.update(gacha_data)
        db[uid] = gacha_data
        await session.send('导入成功~', at_sender=True)
    else:
        lg = gacha_log.gacha_log(uid, log_db['authkey'], log_db.get('region'))
        try:
            count = await lg.merge_gacha_json(json_data.uid, gacha_data)
            await session.send('合并成功~ 一共导入了%s条数据' % count, at_sender=True)
        except Exception as e:
            await session.send(e.args[0], at_sender=True)
