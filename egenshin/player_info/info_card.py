# 以下界面来自明见佬

import os
import datetime

from pathlib import Path
from ..util import pil2b64, get_path, cache, get_font
from ..imghandler import *
from . import query

assets_dir = Path(get_path('assets'))

info_bg = Image.open(assets_dir / 'player_info' / "原神资料卡.png")

QQ_Avatar = True  # 是否使用QQ头像

MAX_CHARA = 12  # 最大允许显示角色数量

CHARA_CARD = assets_dir / "chara_card"
CHARA = assets_dir / 'player_info'


async def avatar_card(avatar_id, level, constellation, fetter):
    '''
    生成角色缩略信息卡

    avatar_id：角色id

    level：经验等级

    constellation：命之座等级

    fetter：好感度等级
    '''
    card = Image.open(os.path.join(CHARA_CARD, f'{avatar_id}.png'))
    draw_text_by_line(card, (0, 235), f'Lv.{level}', get_font(35), '#475463', 226, True)
    i_con = Image.open(os.path.join(CHARA, f'命之座{constellation}.png'))
    i_fet = Image.open(os.path.join(CHARA, f'好感度{fetter}.png'))
    card = easy_alpha_composite(card, i_con, (160, -5))
    card = easy_alpha_composite(card, i_fet, (0, 165))
    return card


@cache(ttl=datetime.timedelta(minutes=30), arg_key='uid')
async def draw_info_card(uid, qid, nickname, raw_data):
    '''
    绘制玩家资料卡
    '''

    stats = query.stats(raw_data.stats, True)
    world_explorations = {}
    for w in raw_data.world_explorations:
        world_explorations[w.name] = w

    char_data = raw_data.avatars

    for k in raw_data.avatars:
        if k['name'] == '旅行者':
            k['rarity'] = 3

    char_data.sort(key=lambda x: (-x['rarity'], -x['actived_constellation_num'], -x['level']))  # , -x['fetter']

    # 头像
    if QQ_Avatar:
        url = f'https://q1.qlogo.cn/g?b=qq&nk={qid}&s=640'
        avatar = await get_pic(url, (256, 256))
    else:
        cid = char_data[0]['id']
        avatar = Image.open(assets_dir / "avatar" / f"{cid}.png")
    card_bg = Image.new('RGB', (1080, 1820), '#d19d78')
    easy_paste(card_bg, avatar, (412, 140))
    easy_paste(card_bg, info_bg, (0, 0))
    text_draw = ImageDraw.Draw(card_bg)
    # UID
    text_draw.text((812, 10), f'UID：{uid}', '#ffffff', get_font(30))
    # 用户昵称
    draw_text_by_line(card_bg, (0, 528), nickname[:10], get_font(40), '#786a5d', 450, True)
    # 成就数量
    text_draw.text((238, 768), stats.achievement.__str__(), '#475463', get_font(60))
    # 深境螺旋
    text_draw.text((769, 768), stats.spiral_abyss, '#475463', get_font(60))
    # 活跃天数
    text_draw.text((350, 1032), stats.active_day.__str__(), '#caae93', get_font(36))
    # 获得角色
    text_draw.text((350, 1086), stats.avatar.__str__(), '#caae93', get_font(36))
    # 开启锚点
    text_draw.text((350, 1142), stats.way_point.__str__(), '#caae93', get_font(36))
    # 探索秘境
    text_draw.text((350, 1197), stats.domain.__str__(), '#caae93', get_font(36))
    # 普通宝箱
    text_draw.text((860, 1032), stats.common_chest.__str__(), '#caae93', get_font(36))
    # 精致宝箱
    text_draw.text((860, 1086), stats.exquisite_chest.__str__(), '#caae93', get_font(36))
    # 珍贵宝箱
    text_draw.text((860, 1142), stats.precious_chest.__str__(), '#caae93', get_font(36))
    # 华丽宝箱
    text_draw.text((860, 1197), stats.luxurious_chest.__str__(), '#caae93', get_font(36))
    # 蒙德
    world = world_explorations['蒙德']
    text_draw.text((370, 1370), str(world.exploration_percentage / 10) + '%', '#d4aa6b', get_font(32))
    text_draw.text((370, 1414), 'Lv.' + str(world.level), '#d4aa6b', get_font(32))
    text_draw.text((370, 1456), stats.anemoculus.__str__(), '#d4aa6b', get_font(32))
    # 璃月
    world = world_explorations['璃月']
    text_draw.text((896, 1370), str(world.exploration_percentage / 10) + '%', '#d4aa6b', get_font(32))
    text_draw.text((896, 1414), 'Lv.' + str(world.level), '#d4aa6b', get_font(32))
    text_draw.text((896, 1456), stats.geoculus.__str__(), '#d4aa6b', get_font(32))
    # 雪山
    world = world_explorations['龙脊雪山']
    text_draw.text((350, 1555), str(world.exploration_percentage / 10) + '%', '#d4aa6b', get_font(32))
    text_draw.text((350, 1612), 'Lv.' + str(world.level), '#d4aa6b', get_font(32))
    # 稻妻
    world = world_explorations['稻妻']
    text_draw.text((880, 1543), str(world.exploration_percentage / 10) + '%', '#d4aa6b', get_font(24))
    text_draw.text((880, 1576), 'Lv.' + str(world.level), '#d4aa6b', get_font(24))
    text_draw.text((880, 1606), 'Lv.' + str(world.offerings[0].level), '#d4aa6b', get_font(24))
    text_draw.text((880, 1639), stats.electroculus.__str__(), '#d4aa6b', get_font(24))

    avatar_cards = []

    for chara in char_data[:MAX_CHARA]:
        card = await avatar_card(chara['id'], chara["level"], chara["actived_constellation_num"], chara["fetter"])
        avatar_cards.append(card)

    chara_bg = Image.new('RGB', (1080, math.ceil(len(avatar_cards) / 4) * 315), '#f0ece3')
    chara_img = image_array(chara_bg, avatar_cards, 4, 35, 0)

    info_card = Image.new('RGBA', (1080, card_bg.size[1] + chara_img.size[1]))
    easy_paste(info_card, card_bg.convert('RGBA'), (0, 0))
    easy_paste(info_card, chara_img.convert('RGBA'), (0, card_bg.size[1]))

    return pil2b64(info_card)
