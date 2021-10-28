import re
from nonebot.message import CanceledException
from hoshino import Message, MessageSegment, Service, priv
from ..player_info import handle as player_info
from ..util import support_private
from .info_card import draw_info_card
from .main import achievement

sv_help = '''
原神成就查漏功能 (用ys#绑定 切换号直接查询另一个就好)
不获取游戏内任何数据,仅仅只是记录玩家完成的成就
方便查看还有什么隐藏成就尚未完成
仅限天地万象!!

如果要删除现有的成就请使用 重置原神成就
重置仅仅是ys#绑定的成就
如果要查看带有攻略请使用 a原神成就

使用方法:

可以直接使用命令后跟n张游戏内的截图来进行更新,例如
原神成就[完成的成就截图1][完成的成就截图2][完成的成就截图3]

*第一次需要全部截完 不用一个个发,可以一次性发完

'''.rstrip()

sv = Service(
    name='原神成就',  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=True,  # 默认启用
    # bundle = '娱乐', #分组归类
    help_=sv_help  # 帮助说明
)

prefix = '原神'


@support_private(sv)
@sv.on_prefix((prefix + '成就', ))
async def achievement_main(bot, ev):
    text = ev.message.extract_plain_text().strip()
    detail = ev.get('detail', False)

    if text in ['help', '帮助', '?', '？']:
        await bot.finish(ev, sv_help, at_sender=True)

    try:
        img_list = []
        proxy_url = []

        for msg in ev.message:
            if msg.type == 'image':
                # 如果直接发了图片
                img_list.append(msg.data['url'])

            if msg.type == 'text':
                # 如果使用图片地址
                for text in msg.data['text'].split('\r\n'):
                    if re.search(r'https?://', text):
                        proxy_url.append(text)

        m = ev.message
        user_id = ev.user_id
        if m and m[0]['type'] == 'at':
            user_id = m[0]['data']['qq']
            if any([img_list, proxy_url]):
                raise Exception('你不能帮别人添加成就...')

        ocr_success = []
        achi = achievement(user_id)
        if img_list:
            await bot.send(ev, '更新当前成就中...', at_sender=True)
            ocr_success, added_len = await achi.form_img_list(img_list)

        if proxy_url:
            await bot.send(ev, '正在获取图片,以及更新成就...', at_sender=True)
            failed_list, ocr_success, added_len = await achi.from_proxy_url(proxy_url)
            failed = '\n'.join(failed_list)
            if failed:
                await bot.send(ev, f'获取失败的图片链接:\n{failed}', at_sender=True)

        if ocr_success:
            ocr_success_msg = ' '.join([f'{i + 1}({x})' for i, x in enumerate(ocr_success)])
            await bot.send(ev,
                           f'本次识别结果增加了{added_len}个记录 过程:图片顺序(识别到的成就个数)\n' +
                           ocr_success_msg,
                           at_sender=True)

        result = await achi.unfinished

        if len(result) < 100:
            player = await player_info(bot, ev)

            im = await draw_info_card(player, result, detail)
            await bot.send(ev, MessageSegment.image(im), at_sender=True)
        else:
            await bot.send(
                ev,
                f'绑定的UID[{achi.info.uid}]记录的成就太少,请补充成就后再查看,发送 原神成就? 查看如何使用',
                at_sender=True)
            
    except CanceledException:
        pass
    except Exception as e:
        await bot.send(ev, e.args[0], at_sender=True)
        raise e


@support_private(sv)
@sv.on_prefix(('重置' + prefix + '成就', ))
async def main(bot, ev):
    try:
        achi = achievement(ev.user_id)
        await achi.clear_data()
        await bot.send(ev, '重置成功', at_sender=True)
    except Exception as e:
        await bot.send(ev, e.args[0], at_sender=True)
        raise e


@support_private(sv)
@sv.on_prefix(('a' + prefix + '成就', ))
async def main(bot, ev):
    ev['detail'] = True
    await achievement_main(bot, ev)
