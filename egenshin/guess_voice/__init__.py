import asyncio
from pathlib import Path
from .. import util
from hoshino import Service, get_bot, MessageSegment
from .download_data import update_voice_data
from .handler import Guess

sv = Service('genshin-guess-voice')

config = util.get_config('guess_voice/config.yml')

_bot = get_bot()


@sv.on_message('group')
async def main(*params):
    bot, ctx = (_bot, params[0]) if len(params) == 1 else params
    msg = str(ctx['message']).strip()
    guess = Guess(ctx.group_id, time=config.setting.time)

    # 排行榜
    show_rank = util.get_msg_keyword(config.comm.rank, msg, True)
    if isinstance(show_rank, str):
        return await _bot.send(ctx, guess.get_rank())

    # 开始游戏
    start = util.get_msg_keyword(config.comm.start, msg, True)
    if isinstance(start, str):
        if not start:
            start = '中'
        if not (start in list('中日英韩')):
            return await _bot.send(ctx, '参数不正确呢')

        if not (Path(__file__).parent / 'data' / start).exists():
            await _bot.send(ctx, '资源尚未初始化')
            print('资源文件不存在,请运行download_data.py文件获取呢')
            return

        if guess.is_start():
            return await _bot.send(ctx, '游戏正在进行中哦.')

        await _bot.send(ctx, '即将发送一段语音,将在%s秒后公布答案' % config.setting.time)
        await asyncio.sleep(1)
        await _bot.send(ctx, guess.start(list(start)))
    # 加入答案
    if guess.is_start():
        guess.add_answer(ctx.user_id, msg)

    # 获取单个语音
    get_voice = util.get_msg_keyword(config.comm.get_random_voice, msg, True)
    if get_voice:
        path = guess.get_random_voice(get_voice)
        if not path:
            return await _bot.send(ctx, '没有找到 %s 的语音呢' % get_voice)

        await _bot.send(ctx, MessageSegment.record(f'file:///{util.get_path("guess_voice", path)}'))
    # 获取单个语音
    get_voice = util.get_msg_keyword(config.comm.get_random_voice_jp, msg, True)
    if get_voice:
        path = guess.get_random_voice(get_voice, '日')
        if not path:
            return await _bot.send(ctx, '没有找到 %s 的语音呢' % get_voice)

        await _bot.send(ctx, MessageSegment.record(f'file:///{util.get_path("guess_voice", path)}'))
