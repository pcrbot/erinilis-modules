from pathlib import Path
from pkg_resources import parse_version

from ..imghandler import *
from ..util import get_font, get_game_version, get_path, pil2b64
from .collect_sheet import achievements_sheet
from .achievements import remove_special_char, all_achievements

assets_dir = Path(get_path('assets')) / 'achievement'

list_bg = Image.open(assets_dir / "list_bg.png")
list_bg_line = Image.open(assets_dir / "list_version_line.png")
list_bg_line_red = Image.open(assets_dir / "list_version_line_red.png")
list_bg_w, list_bg_h = list_bg.size

head_img = Image.open(assets_dir / "head.png")
daily_quest_icon = Image.open(assets_dir / "daily_quest.png")  # 每日
main_quest_icon = Image.open(assets_dir / "main_quest.png")  # 魔神
world_quest_icon = Image.open(assets_dir / "world_quest.png")  # 世界
world_explore_icon = Image.open(assets_dir / "world_explore.png")  # 大世界探索
prestige_quest_icon = Image.open(assets_dir / "prestige_quest.png")  # 声望任务
battle_icon = Image.open(assets_dir / "battle.png")  # 战斗相关
cooking_icon = Image.open(assets_dir / "cooking.png")  # 料理相关


async def gen_head(achi_len, all_achi_len, uid, qid, nickname, raw_data):
    achievement_number = raw_data.data.stats.achievement_number
    url = f'http://q.qlogo.cn/headimg_dl?dst_uin={qid}&spec=640&img_type=jpg'
    avatar = await get_pic(url, (180, 180))

    new_head_img = Image.new('RGBA', head_img.size, '#f1ece6')
    easy_paste(new_head_img, avatar, (42, 12))
    easy_paste(new_head_img, head_img.copy(), (0, 0))
    text_draw = ImageDraw.Draw(new_head_img)
    text_draw.text((330, 68), f'UID：{uid}', '#666666', get_font(25))
    draw_text_by_line(new_head_img, (330, 28), nickname[:10], get_font(35),
                      '#786a5d', 450)

    text_draw.text((362, 124), f'天地万象：{achi_len}/{all_achi_len}', '#414d65', get_font(35))
    text_draw.text((910, 66), f'总成就\n  {achievement_number}', '#414d65', get_font(35))

    return new_head_img


async def item_img(name, description, reward, version):
    sheet_data = await achievements_sheet()

    new_bg = list_bg.copy()
    draw_text_by_line(new_bg, (220, 25), name, get_font(28), '#535250', 851)
    draw_text_by_line(new_bg, (220, 70), description, get_font(25), '#b99e8b',
                      851)
    reward_index = 1115
    if len(reward) == 2:
        reward_index -= 5
    draw_text_by_line(new_bg, (reward_index, 85), reward, get_font(21),
                      '#ffffff', 100)

    quest_icon = None
    data_info = sheet_data.get(remove_special_char(name))
    quest_icon_pos = (160, 18)
    if data_info:
        if data_info.is_daily_quest:  # 是否是每日任务
            quest_icon = daily_quest_icon

        elif data_info.is_main_quest:  # 是否是魔神任务
            quest_icon = main_quest_icon

        elif data_info.is_prestige_quest:  # 是否是声望任务
            quest_icon = prestige_quest_icon

        elif data_info.is_world_quest:  # 是否是世界任务
            quest_icon = world_quest_icon
            quest_icon_pos = (166, 18)

        elif data_info.is_world_explore:  # 是否是大世界探索
            quest_icon = world_explore_icon

        elif data_info.is_battle:  # 是否是战斗相关
            quest_icon = battle_icon

        elif data_info.is_cooking:  # 是否是料理相关
            quest_icon = cooking_icon

        if quest_icon:
            easy_paste(new_bg, quest_icon, quest_icon_pos)

    return new_bg


async def item_line(text, red=False):
    new_bg = red and list_bg_line_red.copy() or list_bg_line.copy()
    draw_text_by_line(new_bg, (0, 0), text, get_font(28), '#535250', 881, True)
    return new_bg


async def handle(achievement):
    new_data = {}
    for info in achievement:
        new_list = new_data.get(info['version'], [])
        new_list.append(info)
        new_data[info['version']] = new_list

    return new_data


async def draw_info_card(player, achievement):
    achievement = list(achievement)
    data = await handle(achievement)

    item_index = head_img.size[1] + 40
    bg_h = list_bg_h * len(achievement) + (list_bg_line.size[1] * len(data))
    bg = Image.new('RGB', (list_bg_w + 40, item_index + bg_h), '#f1ece6')

    
    all_achi_len = len(await all_achievements())
    unachi_len = 0
    game_version = parse_version(await get_game_version())
    for version in sorted(data, key=str):
        red = parse_version(version) > game_version
        if red:
            unachi_len += len(data[version])

        easy_paste(bg, await item_line(f'{version} ({len(data[version])})', red), (20, item_index))
        item_index += list_bg_line.size[1]

        for info in data[version]:
            easy_paste(bg, await item_img(**info), (20, item_index))
            item_index += list_bg_h
            
    all_achi_len -= unachi_len
    easy_paste(bg, await gen_head(*((all_achi_len - len(achievement), all_achi_len) + player)), (20, 20))
    
    return pil2b64(bg)
