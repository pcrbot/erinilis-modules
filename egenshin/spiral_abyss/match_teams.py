from PIL import Image
from .query import get_abyss_data, use_teams_card
from ..imghandler import draw_text_by_line, easy_paste
from ..util import pil2b64, get_font


def get_best_list_ids(key_str):
    return list(map(int, filter(None, key_str.split('_'))))


def find_list_in_avatar(list_key, avatar_data, match_len=4, min_lvl=60):
    self_char = list(avatar_data.keys())
    match_team = []
    for team in list_key:
        match_ids = set(get_best_list_ids(team))
        match = match_ids & set(self_char)
        if len(match) >= match_len and len(match_ids) == len(match):
            # 判断是否有练度
            if all([avatar_data[x].level > min_lvl for x in match_ids]):
                match_team.append(team)
    return match_team


def find_best_team(list_a, list_b, avatar_data, match_len=4, min_lvl=60):
    match_team = []

    match_a = find_list_in_avatar(list_a, avatar_data, match_len, min_lvl)
    match_b = find_list_in_avatar(list_b, avatar_data, match_len, min_lvl)

    team_b_index_list = []
    for team_a in match_a:
        ids_a = set(get_best_list_ids(team_a))
        for team_b_index, team_b in enumerate(match_b):
            ids_b = set(get_best_list_ids(team_b))
            if len(ids_a & ids_b) == 0 and team_b_index not in team_b_index_list:
                team_b_index_list.append(team_b_index)
                match_team.append((team_a, team_b))
                break

    return match_team


async def recommend_team(floor, avatars, recommend_len=4):
    abyss_data = await get_abyss_data(floor=floor)
    avatar_data = {}
    avatars.sort(key=lambda x: (-x['level'],))
    for item in avatars:
        avatar_data[item.id] = item
    chara_bg = None
    # 首先对最合适的深渊配队进行匹配
    for i in [1, 2, 3]:
        best_a = abyss_data['best_%s_a' % i]
        best_b = abyss_data['best_%s_b' % i]
        match_team = find_best_team(best_a, best_b, avatar_data)
        if not match_team:
            match_team = find_best_team(best_a, best_b, avatar_data, min_lvl=0)
            if not match_team:
                raise Exception('配队失败,匹配不到对应阵容')
        find_team_a, find_team_b = zip(*match_team[0:recommend_len])

        chara_bg = await use_teams_card(floor, find_team_a, find_team_b, i, recommend_len, chara_bg,
                                        crop=False,
                                        avatars=avatar_data)

    info_card = Image.new('RGB', (chara_bg.size[0], chara_bg.size[1] + 120), '#f0ece3')
    floor = '深境螺旋[第%s层] 根据已有角色(%s)的阵容推荐' % (abyss_data.floor, len(avatars))
    draw_text_by_line(info_card, (0, 35), floor, get_font(60), '#475463', 1500, True)
    easy_paste(info_card, chara_bg.convert('RGBA'), (0, 120))

    info_card.thumbnail((info_card.size[0] * 0.7, info_card.size[1] * 0.7))
    return pil2b64(info_card)
