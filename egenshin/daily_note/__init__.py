import re

from hoshino import MessageSegment, Service, priv
from nonebot.message import CanceledException

from ..util import support_private
from .info_card import draw_info_card
from .main import Account_Error, Cookie_Error, Daily_Note, Error_Message, Cookie_Error_tampermonkey

sv_help = repr(Cookie_Error())
sv_help2 = repr(Cookie_Error_tampermonkey())

sv = Service(
    name='原神实时便笺',  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=True,  # 默认启用
    bundle='娱乐',  #分组归类
    help_=sv_help  # 帮助说明
)


@support_private(sv)
@sv.on_prefix(('yss', 'yss#', '原神状态', '原神实时', '原神便笺', '原神体力'))
async def main(bot, ev):
    text = ev.message.extract_plain_text().strip()
    if text in ['?', '？']:
        await bot.finish(ev, sv_help, at_sender=True)

    if text in ['?2', '？2']:
        await bot.finish(ev, sv_help2, at_sender=True)

    text = text.replace('，', ',')
    cookie_raw = ''
    try:
        if text.startswith('绑定'):
            if ev.detail_type == 'group':
                raise Error_Message('请撤回, 不支持在群内绑定, 请私聊机器人')
            cookie_raw = text[2:].strip()

        dn = Daily_Note(ev.user_id, cookie_raw, ev.get('group_id'))

        if re.findall(r'[关禁不][闭用要]提醒', text):
            await bot.finish(ev, await dn.remind(False))

        remind_reg = re.findall(r'([开启打]?[启用开]?提醒)(\d+)?', text)

        if remind_reg:
            _, once_remind = remind_reg[0]
            await bot.finish(ev, await dn.remind(once_remind=once_remind))


        im = await draw_info_card(await dn.get_info())
        await bot.send(ev, MessageSegment.image(im), at_sender=True)

    except CanceledException:
        pass
    except Error_Message as e:
        await bot.send(ev, repr(e), at_sender=True)
    except Account_Error as e:
        await bot.send(ev, repr(e), at_sender=True)
