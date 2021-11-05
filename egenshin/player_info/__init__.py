from hoshino import MessageSegment, Service, priv
from nonebot.message import CanceledException
from ..util import get_config, support_private
from . import info_card, query
from .cookies import Genshin_Cookies
from ..imghandler import text_image

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


async def handle(bot, ev):
    uid = ev.message.extract_plain_text().strip()
    if uid and not uid.isdigit():
        await bot.finish(ev, '游戏UID不合法')

    qid = ev.user_id
    nickname = ev['sender']['nickname']
    m = ev.message
    if m and m[0]['type'] == 'at':
        uid = ''
        qid = m[0]['data']['qq']
        qq_info = await bot.get_group_member_info(group_id=ev.group_id,
                                                  user_id=qid)
        nickname = qq_info['nickname']
    if not uid:
        uid = query.get_uid_by_qid(qid)
        if not uid:
            await bot.finish(
                ev,
                '请在原有指令后面输入游戏uid,只需要输入一次就会记住下次直接使用{comm}获取就好\n例如:{comm}105293904'
                .format(comm='ys#'))
    query.save_uid_by_qid(qid, uid)
    raw_data = await query.info(uid=uid, qid=qid, group_id=ev.group_id)

    if isinstance(raw_data, str):
        await bot.finish(ev, raw_data)

    return uid, qid, nickname, raw_data


@support_private(sv)
@sv.on_prefix('ys#')
async def main(bot, ev):
    if ev.detail_type == 'private':
        await bot.send(ev, '这个功能只能在授权的群内使用~')
        return
    try:
        uid, qid, nickname, raw_data = await handle(bot, ev)

        im = await info_card.draw_info_card(uid=uid,
                                            qid=qid,
                                            nickname=nickname,
                                            raw_data=raw_data.data,
                                            max_chara=12,
                                            group_id=ev.group_id)

        await bot.send(ev, MessageSegment.image(im), at_sender=True)
    except CanceledException:
        pass
    except Exception as e:
        await bot.send(ev, repr(e), at_sender=True)


@support_private(sv)
@sv.on_prefix('ysa#')
async def main(bot, ev):
    if ev.detail_type == 'private':
        await bot.send(ev, '这个功能只能在授权的群内使用~')
        return
    try:
        uid, qid, nickname, raw_data = await handle(bot, ev)

        im = await info_card.draw_info_card(uid=uid,
                                            qid=qid,
                                            nickname=nickname,
                                            raw_data=raw_data.data,
                                            max_chara=None,
                                            group_id=ev.group_id)

        await bot.send(ev, MessageSegment.image(im), at_sender=True)

    except CanceledException:
        pass
    except Exception as e:
        await bot.send(ev, repr(e), at_sender=True)


@support_private(sv)
@sv.on_prefix('添加令牌')
async def add_cookie(bot, ev):
    try:
        if ev.detail_type == 'group':
            await bot.send(ev,'请撤回, 这个功能只能私聊使用~')
            return

        text = ev.message.extract_plain_text().strip()
        await Genshin_Cookies().raw_text_add_group(text)

    except CanceledException:
        pass
    except Exception as e:
        await bot.send(ev, MessageSegment.image(await text_image(repr(e))), at_sender=True)
