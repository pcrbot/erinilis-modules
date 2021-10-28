import datetime
from pathlib import Path

from ..imghandler import *
from ..util import get_font, get_path, pil2b64
from .main import Daily_Note_Info

default_text_color = '#78818b'
success_text_color = '#669999'

assets_dir = Path(get_path('assets')) / 'daily_note'
box_bg = Image.open(assets_dir / "bg.png")
expedition_box = Image.open(assets_dir / "expeditions_item.png")
expedition_box_ok = Image.open(assets_dir / "expeditions_item_ok.png")
why_not_expedition = Image.open(assets_dir / "你怎么不派遣.png")

def in_time(time_str1, time_str2):
    now = datetime.datetime.now()
    day = str(now.date())
    t1 = datetime.datetime.strptime(day + time_str1, '%Y-%m-%d%H:%M')
    t2 = datetime.datetime.strptime(day + time_str2, '%Y-%m-%d%H:%M')
    if t2 < t1:
        return True
    return now > t1 and now < t2


async def get_time_icon():
    morning = ('6:00', '11:00', '早晨.png')
    noon = ('11:00', '17:00', '中午.png')
    dusk = ('17:00', '19:00', '黄昏.png')
    night = ('19:00', '6:00', '夜晚.png')
    for t1, t2, png in [morning, noon, dusk, night]:
        if in_time(t1, t2):
            return Image.open(assets_dir / png)
    raise Exception('unknown time')


async def gen_expedition_items(expeditions):
    for exp in expeditions:
        remained_time = int(exp['remained_time'])
        avatar = await get_pic(exp['avatar_side_icon'], (49, 60))

        if exp['status'] == 'Finished':
            bg = expedition_box_ok.copy()
            s = '已完成!'
            ok = True
        else:
            bg = expedition_box.copy()
            mm, ss = divmod(remained_time, 60)
            hh, mm = divmod(mm, 60)
            s = "剩余%d小时%02d分%02d秒" % (hh, mm, ss)
            ok = False

        draw_text_by_line(bg, (0, 49.88), s, get_font(49), ok and success_text_color or default_text_color, 881, True)
        yield (avatar, bg.resize((273, 76)))


async def draw_info_card(info: Daily_Note_Info):
    now = datetime.datetime.now()

    bg = Image.new('RGB', (box_bg.width, box_bg.height), '#f1ece6')
    easy_paste(bg, box_bg.copy())

    now_str = now.strftime(" %m月%d日\n%H:%M:%S")
    draw_text_by_line(bg, (219.38, 59.79), now_str, get_font(21), default_text_color, 881)
    easy_paste(bg, await get_time_icon(), (84, 30))

    # 树脂完全回复时间
    resin_recovery_time = now + datetime.timedelta(seconds=int(info.resin_recovery_time))
    resin_recovery_time_day = resin_recovery_time.day > now.day and '明天'  or '今天'
    resin_recovery_str = f'将于{resin_recovery_time_day} {resin_recovery_time.strftime("%H:%M:%S")} 完全回复'
    draw_text_by_line(bg, (173.09, 150.2), resin_recovery_str, get_font(16), default_text_color, 881)

    # 树脂
    resin_str = f'{info.current_resin}/{info.max_resin}'
    draw_text_by_line(bg, (233.55, 196.93), resin_str, get_font(36), default_text_color, 881)

    # 每日
    ok = False
    task_str = f'{info.finished_task_num}/{info.total_task_num}'
    if info.finished_task_num == info.total_task_num:
        task_str = '完成'
        ok = True
    draw_text_by_line(bg, (253, 327), task_str, get_font(36), ok and success_text_color or default_text_color, 881)

    # 周本
    ok = False
    resin_discount_str = f'{info.remain_resin_discount_num}/{info.resin_discount_num_limit}'
    if info.remain_resin_discount_num == 0:
        resin_discount_str = '完成'
        ok = True
    draw_text_by_line(bg, (253, 452), resin_discount_str, get_font(36), ok and success_text_color or default_text_color, 881)



    if info.expeditions:
        # 探索
        first_expeditions_time = int(min([x['remained_time'] for x in info.expeditions]))
        first_expeditions_time = now + datetime.timedelta(seconds=first_expeditions_time)
        first_expeditions_time_day = first_expeditions_time.day > now.day and '明天'  or '今天'
        first_expeditions_str = f'最快{first_expeditions_time_day} {first_expeditions_time.strftime("%H:%M:%S")} 派遣完成'
        draw_text_by_line(bg, (600, 74), first_expeditions_str, get_font(18), default_text_color, 881)

        bg = bg.convert("RGBA")
        exp_index = 114
        async for avatar, exp_bg in gen_expedition_items(info.expeditions):
            bg = easy_alpha_composite(bg, avatar, (538, exp_index))
            bg = easy_alpha_composite(bg, exp_bg, (587, exp_index))

            exp_index += 72
            
    else:
        easy_paste(bg, why_not_expedition, (579, 125))



    return pil2b64(bg)
