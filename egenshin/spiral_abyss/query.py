import datetime
import json
import math
import re
from io import BytesIO
from pathlib import Path

from PIL import Image, PngImagePlugin

from ..util import Dict, cache, get_path, get_font, pil2b64, require_file, gh_json
from ..imghandler import draw_text_by_line, image_array, easy_paste, easy_alpha_composite
from hoshino import aiorequests
from bs4 import BeautifulSoup

BASE_URL = 'https://spiral-abyss.appsample.com'

oLookup = {}
s = 'E8SB{nyYN5HZoPGfRzum9Ccv,Ig7}Q6Ad_2lFVt"xX-skLKaep4U:hOTbJ1ji0DWwr3qM'
b64char = '6{}m23rLthApyWswdzS9kTQbZ_PBGM:CD1fHEXV70JKxo-"NjnFO4q8gaR,lYUcui5Ive'

assets_dir = Path(get_path('assets'))
enemies_img = assets_dir / 'spiral_abyss' / 'enemies'

with open(assets_dir / 'character.json', 'r', encoding="utf-8") as f:
    character: dict = json.loads(f.read(), object_hook=Dict)

# with open(assets_dir / 'spiral_abyss' / 'enemies.json', 'r', encoding="utf-8") as f:
#     enemies: dict = json.loads(f.read(), object_hook=Dict)
@cache(ttl=datetime.timedelta(hours=12))
async def gh_enemies():
    return await gh_json('assets/spiral_abyss/enemies.json')


async def decode(raw_data):
    if not oLookup:
        for i, v in enumerate(b64char):
            oLookup[v] = s[i]
    ret = ''
    for i, v in enumerate(raw_data):
        ret += oLookup.get(raw_data[i], raw_data[i])
    return json.loads(ret, object_hook=Dict)


@cache(ttl=datetime.timedelta(hours=12), arg_key='page')
async def __get_html_soup__(page=''):
    res = await aiorequests.get(BASE_URL + page, timeout=10)
    return BeautifulSoup(await res.content, 'lxml')


async def __get_enemies__(floor='12'):
    pass
    # build_id = await __get_build_id__()
    # res = await aiorequests.get(BASE_URL + f'/_next/static/{build_id}/_buildManifest.js', timeout=10)
    # res = await res.text
    # links = re.findall(r"\(\"\S+\"\)", res)[0][1:-1].split(',')
    # for link in links:
    #     link = link.replace("'", '').replace('"', '')
    #     res = await aiorequests.get(BASE_URL + '/_next/' + link, timeout=10)
    #     res = await res.text
    #     if re.search(r'2\.0', res):
    #         print(link)


@cache(ttl=datetime.timedelta(hours=12))
async def __get_build_id__():
    soup = await __get_html_soup__()
    data = soup.find('script', {"id": "__NEXT_DATA__"}).next
    data = json.loads(data, object_hook=Dict)
    # floorDataRaw = await decode(data.props.pageProps.floorDataRaw)
    # floorRaw = await decode(data.props.pageProps.floorRaw)
    return data.buildId


@cache(ttl=datetime.timedelta(hours=2), arg_key='floor')
async def get_abyss_data(floor):
    json_url = '%s/_next/data/%s/zh/floor-%s.json' % (BASE_URL, await __get_build_id__(), floor or '12')
    res = await aiorequests.get(json_url, timeout=10)
    json_data = await res.json(object_hook=Dict)
    return await decode(json_data.pageProps.FDR)


@cache(ttl=datetime.timedelta(hours=2), arg_key='floor')
async def abyss_use_probability(floor):
    data = await get_abyss_data(floor=floor)

    pr_list = {}
    for char_id in data.deploy_count:
        pr = data.deploy_count[char_id] / data.roles_count[char_id]
        pr_list[char_id] = pr * 100
    col_len = 6
    avatar_cards = []
    for name, pr in sorted(pr_list.items(), key=lambda x: x[1], reverse=True):
        card = Image.open(assets_dir / "chara_card" / f'{name}.png')
        draw_text_by_line(card, (0, 235), f'%s%%' % ('%.2f' % pr), get_font(35), '#475463', 226, True)
        avatar_cards.append(card)
    wh = ((avatar_cards[0].size[0] + 40) * col_len, math.ceil(len(avatar_cards) / col_len) * 315)
    chara_bg = Image.new('RGB', wh, '#f0ece3')
    chara_img = image_array(chara_bg, avatar_cards, col_len, 35, 0)

    info_card = Image.new('RGB', (chara_img.size[0], chara_img.size[1] + 120), '#f0ece3')
    floor = '深境螺旋[第%s层]角色使用率\n' % data.floor
    draw_text_by_line(info_card, (0, 35), floor, get_font(50), '#475463', 1000, True)
    easy_paste(info_card, chara_img.convert('RGBA'), (0, 120))

    info_card.thumbnail((info_card.size[0] * 0.7, info_card.size[1] * 0.7))
    return pil2b64(info_card)


@cache(ttl=datetime.timedelta(hours=2), arg_key='floor')
async def abyss_use_teams(floor):
    data = await get_abyss_data(floor=floor)
    best_data_len = 3
    chara_bg = None
    for i in [1, 2, 3]:
        avatar_a = list(data['best_%s_a' % i])[0:best_data_len]
        avatar_b = list(data['best_%s_b' % i])[0:best_data_len]

        chara_bg = await use_teams_card(floor, avatar_a, avatar_b, i, best_data_len, chara_bg)

    info_card = Image.new('RGB', (chara_bg.size[0], chara_bg.size[1] + 120), '#f0ece3')
    floor = '深境螺旋[第%s层] 上间/下间 阵容推荐' % data.floor
    draw_text_by_line(info_card, (0, 35), floor, get_font(50), '#475463', 1000, True)
    easy_paste(info_card, chara_bg.convert('RGBA'), (0, 120))

    info_card.thumbnail((info_card.size[0] * 0.7, info_card.size[1] * 0.7))
    return pil2b64(info_card)


def sort_char_ids(ids):
    char = []
    for _id in list(filter(None, ids.split('_'))):
        data = {'id': _id}
        data.update(character[_id])
        char.append(data)
    char.sort(key=lambda x: (-x['rarity'], -int(x['id'])))
    return [x['id'] for x in char]


async def use_teams_card(floor, team_a, team_b, i, data_len=3, chara_bg=None, space=120, crop=True, avatars=None):
    """
    生成一个队伍列表图
    @param team_a: 左边队伍
    @param team_b: 右边队伍
    @param i: 第几层
    @param data_len: 最大能生成几行数据
    @param chara_bg: 贴在那个对象上
    @param space: 左边和右边的间隔为多少
    @param crop: 是否不显示等级
    @param avatars: 输入的人物列表 对应填入等级框
    @return:
    """

    def get_cards(ids):
        avatar_cards = []
        for char_ids in ids:
            for c_id in sort_char_ids(char_ids):
                if not c_id:
                    continue
                card: PngImagePlugin.PngImageFile = Image.open(assets_dir / "chara_card" / f'{c_id}.png')
                if crop:
                    card = card.crop((0, 0, card.size[0], card.size[1] - 55))
                if avatars:
                    avatar_data = avatars[int(c_id)]
                    draw_text_by_line(card, (0, 235), f'Lv.{avatar_data.level}', get_font(35), '#475463', 226, True)
                    i_con = Image.open(assets_dir / "player_info" / f'命之座{avatar_data.actived_constellation_num}.png')
                    card = easy_alpha_composite(card, i_con, (160, -5))

                avatar_cards.append(card)
        temp_size = avatar_cards[0].size
        crop_space = crop and 0 or 30
        bg = Image.new('RGB', ((temp_size[0] + 10) * 4, temp_size[1] * data_len + crop_space + 84), '#f0ece3')
        return image_array(bg, avatar_cards, 4, 10, 0).convert('RGBA')

    async def get_enemy_img():
        enemies = await gh_enemies()
        enemy_a_list = []
        enemy_b_list = []
        floor_i = f'{floor}-{i}'
        enemy_resource = 'https://gim.appsample.net/enemies/'
        for enemy_name in enemies[floor_i].a:
            enemy_filename = enemy_name + '.png'
            pic = Image.open(
                BytesIO(await require_file(enemies_img / enemy_filename, url=enemy_resource + enemy_filename)))
            enemy_a_list.append(pic.convert("RGBA"))
        for enemy_name in enemies[floor_i].b:
            enemy_filename = enemy_name + '.png'
            pic = Image.open(BytesIO(await require_file(enemies_img / enemy_filename, url=enemy_resource + enemy_filename)))
            enemy_b_list.append(pic.convert("RGBA"))

        enemy_bg = Image.new('RGBA', (780, pic.height), '#f0ece3')
        enemy_bg_b = Image.new('RGBA', (780, pic.height), '#f0ece3')
        enemy_a_img = image_array(enemy_bg, enemy_a_list, 10)
        enemy_b_img = image_array(enemy_bg_b, enemy_b_list, 10)
        return enemy_a_img, enemy_b_img

    enemy_a, enemy_b = await get_enemy_img()

    team_a = get_cards(team_a)
    team_b = get_cards(team_b)

    row_item = Image.new('RGB', (team_a.size[0] * 2 + space, team_a.size[1]), '#f0ece3')
    easy_paste(row_item, enemy_a, (0, 0))
    easy_paste(row_item, enemy_b, (team_a.size[0] + space, 0))

    easy_paste(row_item, team_a, (0, 74 + 10))
    easy_paste(row_item, team_b, (team_a.size[0] + space, 74 + 10))



    team_space = 100
    if not chara_bg:
        chara_bg = Image.new('RGB', (
            team_a.size[0] * 2 + space,
            row_item.size[1] * 3 + team_space * 3),
                             '#f0ece3')

    team_item_y = (i - 1) * (row_item.size[1] + team_space) + team_space
    title_y = team_item_y - (team_space * 0.8)
    draw_text_by_line(chara_bg, (0, title_y), f'第{i}间', get_font(50), '#475463', 1000, True)
    easy_paste(chara_bg, row_item.convert('RGBA'), (0, team_item_y))
    return chara_bg
