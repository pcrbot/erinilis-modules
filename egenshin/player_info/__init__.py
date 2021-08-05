from hoshino import Service, priv, MessageSegment
from ..util import init_db, get_config
from . import query, info_card

sv_help = '''
[ys#UID] 查询一个用户信息
'''.strip()

sv = Service(
    name='原神UID查询',  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=True,  # 默认启用
    # bundle = '娱乐', #分组归类
    help_=sv_help  # 帮助说明
)
config = get_config()
db = init_db(config.cache_dir, 'uid.sqlite')


@sv.on_prefix('ys#')
async def main(bot, ev):
    uid = ev.message.extract_plain_text().strip()
    qid = ev.user_id
    m = ev.message
    if m and m[0]['type'] == 'at':
        uid = ''
        qid = m[0]['data']['qq']
    if not uid:
        info = db.get(qid, {})
        if not info:
            await bot.finish(ev, '请在原有指令后面输入游戏uid,只需要输入一次就会记住下次直接使用{comm}获取就好\n例如:{comm}105293904'.format(
                comm='ys#'))
        else:
            uid = info['uid']

    im = await info_card.draw_info_card(uid=uid, qid=qid, nickname=ev['sender']['nickname'])
    await bot.send(ev, MessageSegment.image(im), at_sender=True)

    db[uid] = {'uid': uid}
