from pathlib import Path
from pkg_resources import parse_version

from ..imghandler import *
from ..util import get_font, get_game_version, get_path, pil2b64

assets_dir = Path(get_path('assets')) / 'achievement'

list_bg = Image.open(assets_dir / "list_bg.png")
list_bg_line = Image.open(assets_dir / "list_version_line.png")
list_bg_line_red = Image.open(assets_dir / "list_version_line_red.png")
list_bg_w, list_bg_h = list_bg.size


async def item_img(name, description, reward, version):
    new_bg = list_bg.copy()
    draw_text_by_line(new_bg, (200, 25), name, get_font(28), '#535250', 881)
    draw_text_by_line(new_bg, (200, 70), description, get_font(25), '#b99e8b', 881)
    reward_index = 1115
    if len(reward) == 2:
        reward_index -= 5
    draw_text_by_line(new_bg, (reward_index, 85), reward, get_font(21), '#ffffff', 100)
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

async def draw_info_card(achievement):
    achievement = list(achievement)
    data = await handle(achievement)

    bg_h = list_bg_h * len(achievement) + (list_bg_line.size[1] * len(data))
    bg = Image.new('RGB', (list_bg_w + 40, bg_h),'#f1ece6')

    game_version = parse_version(await get_game_version())
    item_index = 0
    for version in sorted(data, key=str):
        red = parse_version(version) > game_version

        easy_paste(bg, await item_line(version, red), (20, item_index))
        item_index += list_bg_line.size[1]

        for info in data[version]:
            easy_paste(bg, await item_img(**info), (20, item_index))
            item_index += list_bg_h

    return pil2b64(bg)
