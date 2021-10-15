from hoshino import Service, priv, MessageSegment
from ..util import support_private
from .main import Daily_Note, Error_Message, Account_Error
from .info_card import draw_info_card

sv_help = '''
'''.strip()
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
@sv.on_prefix(('yss', 'yss#', '原神状态', '原神实时', '原神便笺'))
async def main(bot, ev):
    text = ev.message.extract_plain_text().strip()
    cookie_raw = ''
    try:
        if text.startswith('绑定'):
            if ev.detail_type == 'group':
                raise Error_Message('请撤回, 不支持在群内绑定, 请私聊机器人')
            cookie_raw = text[2:]
        info = await Daily_Note(ev.user_id, cookie_raw).get_info()
        im = await draw_info_card(info)
        await bot.send(ev, MessageSegment.image(im), at_sender=True)

    except Error_Message as e:
        await bot.send(ev, repr(e), at_sender=True)
    except Account_Error as e:
        await bot.send(ev, 'cookie信息错误, 请重新检查是否正确', at_sender=True)
