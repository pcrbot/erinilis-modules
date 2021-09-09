import re

from hoshino import MessageSegment, Service, priv

from ..imghandler import create_text_img
from ..util import pil2b64
from .info_card import draw_info_card
from .main import achievement

sv_help = '''
原神成就查漏功能 (用ys#绑定 切换号直接查询另一个就好)
不获取游戏内任何数据,仅仅只是记录玩家完成的成就
方便查看还有什么隐藏成就尚未完成
只有未完成的成就数量小于100时才有界面

如果要删除现有的成就请使用 重置原神成就
重置仅仅是ys#绑定的成就

使用方法:

(方法1): 可以直接使用命令后跟n张游戏内的截图来进行更新,例如
原神成就[完成的成就截图1][完成的成就截图2][完成的成就截图3]

(方法2): 可以上传图床然后使用命令跟n个上传的图片地址更新,例如
原神成就
https://imgtu.com/i/h5Rq6x
https://imgtu.com/i/h5RHpR
https://imgtu.com/i/h5Rb11

支持的图床有
https://imgtu.com/
https://ibb.co/
'''.strip()

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


@sv.on_prefix((prefix + '成就', ))
async def main(bot, ev):
    text = ev.message.extract_plain_text().strip()
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

        achi = achievement(user_id)
        if img_list:
            await bot.send(ev, '更新当前成就中...', at_sender=True)
            await achi.form_img_list(img_list)

        if proxy_url:
            await bot.send(ev, '正在获取图片,以及更新成就...', at_sender=True)
            failed = '\n'.join(await achi.from_proxy_url(proxy_url))
            if failed:
                await bot.send(ev, f'获取失败的图片链接:\n{failed}', at_sender=True)

        await bot.send(ev, '正在生成未完成的成就列表...', at_sender=True)

        result = await achi.unfinished

        if len(result) < 100:
            im = await draw_info_card(result)
            await bot.send(ev, MessageSegment.image(im), at_sender=True)
        else:
            im = await create_text_img({
                f"({v['version']}) {v['name']}": v['description']
                for i, v in enumerate(result)
            }.items())
            await bot.send(ev,
                           MessageSegment.image(pil2b64(im)),
                           at_sender=True)

    except Exception as e:
        await bot.send(ev, e.args[0], at_sender=True)
        raise e


@sv.on_prefix(('重置' + prefix + '成就', ))
async def main(bot, ev):
    try:
        achi = achievement(ev.user_id)
        await achi.clear_data()
        await bot.send(ev, '重置成功', at_sender=True)
    except Exception as e:
        await bot.send(ev, e.args[0], at_sender=True)
        raise e