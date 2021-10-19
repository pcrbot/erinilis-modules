import asyncio
import os
from .. import util
from hoshino import Service, MessageSegment, priv
from .handler import Guess, get_random_voice
from . import download_data

sv_help = '''
[原神猜语音] 开始原神猜语音
[原神猜语音排行榜] 查看本群原神猜语音的排行榜
[原神语音+角色名] 播放指定角色的随机一条语音 
'''.strip()

sv = Service(
    name='原神猜语音',  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=True,  # 默认启用
    # bundle = '娱乐', #分组归类
    help_=sv_help  # 帮助说明
)

setting_time = 30  # 游戏持续时间

dir_name = os.path.join(os.path.dirname(__file__), 'voice')


async def download_voice(bot, ev):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
        await bot.send(ev, '资源尚未初始化，现在开始下载资源，这需要较长的时间，请耐心等待')
        await download_data.update_voice_data()
        await bot.send(ev, '资源下载完成，请重新发送指令开始游戏')


@sv.on_prefix('原神猜语音')
async def guess_genshin_voice(bot, ev):
    await download_voice(bot, ev)
    keyword = ev.message.extract_plain_text().strip()
    guess = Guess(ev['group_id'], time=setting_time)

    hard_mode = False

    if keyword == '排行榜':
        await bot.finish(ev, await guess.get_rank(bot, ev))
    if keyword in ['中', '中国', '汉语', '中文', '中国话', 'Chinese', 'cn'] or not keyword:
        keyword = '中'
    elif keyword in ['日', '日本', '日语', '霓虹', '日本语', 'Japanese', 'jp']:
        keyword = '日'
    elif keyword in ['韩', '韩国', '韩语', '棒子', '南朝鲜', '南朝鲜语']:
        keyword = '韩'
    elif keyword in ['英', '英文', '英语', '洋文', 'English', 'en']:
        keyword = '英'
    elif keyword in ['2', '难', '困难', '地狱']:
        hard_mode = True
    else:
        await bot.finish(ev, f'没有找到{keyword}的语音')
    if guess.is_start():
        await bot.finish(ev, '游戏正在进行中哦')
    guess.set_start()
    await bot.send(ev, f'即将发送一段原神语音,将在{setting_time}秒后公布答案')
    await asyncio.sleep(1)
    if hard_mode:
        try:
            await bot.send(ev, await guess.start2())
        except Exception as e:
            guess.set_end()
            await bot.send(ev, str(e))
    else:
        await bot.send(ev, await guess.start(keyword.split()))


@sv.on_message('group')
async def on_input_chara_name(bot, ev):
    msg = ev['raw_message']
    guess = Guess(ev['group_id'], time=setting_time)
    if guess.is_start():
        await guess.add_answer(ev['user_id'], msg)


@sv.on_prefix('原神语音')
async def get_genshin_voice(bot, ev):
    name = ev.message.extract_plain_text().strip()
    if name.startswith('日'):
        language = '日'
        name = name[1:]
    else:
        language = '中'
    await download_voice(bot, ev)
    path = await get_random_voice(name, language)
    if not path:
        await bot.finish(ev, f'没有找到{name}的语音呢')
    await bot.send(ev, MessageSegment.record(f'file:///{util.get_path("guess_voice", path)}'))


@sv.on_fullmatch('更新原神语音资源')
async def update_genshin_voice(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER):
        return
    await bot.send(ev, '将在后台开始更新原神语音资源，耐心等待')
    await download_data.update_voice_data()
