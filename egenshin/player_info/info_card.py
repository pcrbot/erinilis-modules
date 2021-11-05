# 以下界面来自明见佬

import datetime
import os
from io import BytesIO
from pathlib import Path

from ..imghandler import *
from ..util import cache, get_font, get_path, pil2b64, require_file
from . import query

assets_dir = Path(get_path('assets'))

info_bg = Image.open(assets_dir / 'player_info' / "原神资料卡.png")
weapon_bg = Image.open(assets_dir / 'player_info' / "weapon_bg.png")
weapon_icon_dir = assets_dir / 'player_info' / 'weapon'
abyss_star_bg = Image.open(assets_dir / 'player_info' / "深渊星数.png").convert('RGBA')

weapon_card_bg = {}
for i in range(1 ,6):
    weapon_card_bg[i] = Image.open(assets_dir / 'player_info' / f"{i}星武器.png")


QQ_Avatar = True  # 是否使用QQ头像

# 以下2个选项控制显示深渊星数 已经角色武器信息, 可能会使用额外的cookie次数
# 已知每个cookie能查询30次, 查询基本信息为一次, 深渊信息为一次, 武器信息为一次
# 下列2个变量都为True时 查询次数为3次
SHOW_SPIRAL_ABYSS_STAR = True # 是否显示深渊信息
SHOW_WEAPON_INFO = True # 是否显示武器信息

CHARA_CARD = assets_dir / "chara_card"
CHARA = assets_dir / 'player_info'


async def avatar_card(avatar_id, level, constellation, fetter, detail_info):
    '''
    生成角色缩略信息卡

    avatar_id：角色id

    level：经验等级

    constellation：命之座等级

    fetter：好感度等级
    '''
    card = Image.open(os.path.join(CHARA_CARD, f'{avatar_id}.png'))
    draw_text_by_line(card, (0, 235), f'Lv.{level}', get_font(35), '#475463', 226, True)
    if constellation > 0:
        i_con = Image.open(os.path.join(CHARA, f'命之座{constellation}.png'))
        card = easy_alpha_composite(card, i_con, (160, -5))

    i_fet = Image.open(os.path.join(CHARA, f'好感度{fetter}.png'))
    card = easy_alpha_composite(card, i_fet, (0, 165))

    # 显示详细信息
    if detail_info:
        # 武器信息
        weapon_info = detail_info.weapon
        new_card = Image.new("RGBA", (card.width, card.height + weapon_bg.height))
        new_card = easy_alpha_composite(new_card, card, (0, 0))

        # 武器背景
        weapon_card = weapon_bg.copy()
        new_weapon_card_bg = weapon_card_bg[weapon_info.rarity].copy()
        # 武器等级


        weapon_card = easy_alpha_composite(weapon_card, new_weapon_card_bg, (4, 3))
        # 获取武器图标
        file_url = weapon_info.icon
        file_name = Path(file_url).name
        weapon_icon_img = await require_file(file=weapon_icon_dir / file_name, url=file_url)
        weapon_icon = Image.open(BytesIO(weapon_icon_img)).convert("RGBA").resize((56, 65), Image.LANCZOS)
        weapon_card = easy_alpha_composite(weapon_card, weapon_icon, (9, 6))

        # 武器名称 精炼
        name_img = Image.new("RGBA", (weapon_bg.width - new_weapon_card_bg.width, weapon_bg.height))
        draw_text_by_line(name_img, (96.86, 9.71), weapon_info.name, get_font(18), '#475463', 226, True)

        draw_text_by_line(name_img, (132.48, 34.01), f'Lv.{weapon_info.level}', get_font(14), '#475463', 226, True)

        affix_name = weapon_info.affix_level == 5 and 'MAX' or f'{weapon_info.affix_level}阶'
        draw_text_by_line(name_img, (120, 53.39), f'精炼{affix_name}', get_font(18), '#cc9966', 226, True)

        weapon_card = easy_alpha_composite(weapon_card, name_img, (new_weapon_card_bg.width, 0))


        # 复制到新的卡片上
        new_card = easy_alpha_composite(new_card, weapon_card, (0, card.height))

        card = new_card


    return card

async def gen_detail_info(uid ,character_ids, qid, group_id=None):
    info = await query.character(uid=uid, character_ids=character_ids, qid=qid, group_id=group_id)
    if info.retcode == 10102:
        raise Exception("武器信息读取失败, 请打开米游社,我的-个人主页-管理-公开信息")
    return {x.id: x for x in info.data.avatars}



# @cache(ttl=datetime.timedelta(minutes=30), arg_key='uid')
async def draw_info_card(uid, qid, nickname, raw_data, max_chara=None, group_id=None):
    '''
    绘制玩家资料卡
    '''
    stats = query.stats(raw_data.stats, True)
    world_explorations = {}
    for w in raw_data.world_explorations:
        if isinstance(w['exploration_percentage'], int):
            w.exploration_percentage = str(w['exploration_percentage'] / 10)
            if w.exploration_percentage == '100.0':
                w.exploration_percentage = '100'
        world_explorations[w.name] = w

    char_data = raw_data.avatars

    for k in raw_data.avatars:
        if k['name'] == '旅行者':
            k['rarity'] = 3
        if k['name'] == '埃洛伊':
            k['rarity'] = 3

    char_data.sort(key=lambda x: (-x['rarity'], -x['actived_constellation_num'], -x['level']))  # , -x['fetter']

    # 头像
    if QQ_Avatar:
        url = f'http://q.qlogo.cn/headimg_dl?dst_uin={qid}&spec=640&img_type=jpg'
        avatar = await get_pic(url, (256, 256))
        # url = f'http://q1.qlogo.cn/g?b=qq&nk={qid}&s=640'
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
    text_draw.text((370, 1370), str(world.exploration_percentage) + '%', '#d4aa6b', get_font(32))
    text_draw.text((370, 1414), 'Lv.' + str(world.level), '#d4aa6b', get_font(32))
    text_draw.text((370, 1456), stats.anemoculus.__str__(), '#d4aa6b', get_font(32))
    # 璃月
    world = world_explorations['璃月']
    text_draw.text((896, 1370), str(world.exploration_percentage) + '%', '#d4aa6b', get_font(32))
    text_draw.text((896, 1414), 'Lv.' + str(world.level), '#d4aa6b', get_font(32))
    text_draw.text((896, 1456), stats.geoculus.__str__(), '#d4aa6b', get_font(32))
    # 雪山
    world = world_explorations['龙脊雪山']
    text_draw.text((350, 1555), str(world.exploration_percentage) + '%', '#d4aa6b', get_font(32))
    text_draw.text((350, 1612), 'Lv.' + str(world.level), '#d4aa6b', get_font(32))
    # 稻妻
    world = world_explorations['稻妻']
    text_draw.text((880, 1543), str(world.exploration_percentage) + '%', '#d4aa6b', get_font(24))
    text_draw.text((880, 1576), 'Lv.' + str(world.level), '#d4aa6b', get_font(24))
    text_draw.text((880, 1606), 'Lv.' + str(world.offerings[0].level), '#d4aa6b', get_font(24))
    text_draw.text((880, 1639), stats.electroculus.__str__(), '#d4aa6b', get_font(24))

    # 深渊星数
    if SHOW_SPIRAL_ABYSS_STAR:
        abyss_info = await query.spiralAbyss(uid=uid, qid=qid, group_id=group_id)
        if abyss_info.retcode !=0 :
            raise Exception(abyss_info.message)

        new_abyss_star_bg = abyss_star_bg.copy()
        draw_text_by_line(new_abyss_star_bg, (0, 60), str(abyss_info.data.total_star), get_font(36), '#78818b', 64, True)
        card_bg = easy_alpha_composite(card_bg.convert('RGBA'), new_abyss_star_bg, (925, 710))


    detail_info = None
    detail_info_height = 0
    if max_chara == None and SHOW_WEAPON_INFO:
        detail_info = await gen_detail_info(uid, [x.id for x in raw_data.avatars], qid, group_id)
        detail_info_height = weapon_bg.height

    avatar_cards = []
    for chara in char_data[:max_chara or len(char_data)]:
        card = await avatar_card(chara['id'], chara["level"],
                                 chara["actived_constellation_num"],
                                 chara["fetter"], detail_info
                                 and detail_info[chara['id']])
        avatar_cards.append(card)

    chara_bg = Image.new('RGB', (1080, math.ceil(len(avatar_cards) / 4) *
                                 (315 + detail_info_height)), '#f0ece3')
    chara_img = image_array(chara_bg, avatar_cards, 4, 35, 0)

    info_card = Image.new('RGBA', (1080, card_bg.size[1] + chara_img.size[1]))
    easy_paste(info_card, card_bg.convert('RGBA'), (0, 0))
    easy_paste(info_card, chara_img.convert('RGBA'), (0, card_bg.size[1]))

    return pil2b64(info_card)
