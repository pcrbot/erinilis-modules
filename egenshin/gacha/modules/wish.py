import random
import re
from enum import Enum

from ...util import dict_to_object
from .wish_user import wish_user


class GACHA_TYPE(Enum):
    activity = 301  # 限定卡池
    weapon = 302  # 武器卡池
    permanent = 200  # 常驻卡池


def gacha_type_by_name(name):
    if re.search(r'^[限活][定动]池?$', name, re.I):
        return GACHA_TYPE.activity.value
    if re.search(r'^[武][器]池?$', name, re.I):
        return GACHA_TYPE.weapon.value
    if re.search(r'^[常普][驻通规]池?$', name, re.I):
        return GACHA_TYPE.permanent.value
    return 0


def is_character_gacha(gacha_type):
    return gacha_type == GACHA_TYPE.activity.value or gacha_type == GACHA_TYPE.permanent.value


def random_int():
    return random.randint(1, 10000)


# 抽卡概率来自https://www.bilibili.com/read/cv10468091
# 角色抽卡概率
def character_probability(rank, count):
    ret = 0
    if rank == 5 and count <= 73:
        ret = 60
    elif rank == 5 and count >= 74:
        ret = 60 + 600 * (count - 73)
    elif rank == 4 and count <= 8:
        ret = 510
    elif rank == 4 and count >= 9:
        ret = 510 + 5100 * (count - 8)
    return ret


# 武器抽卡概率
def weapon_probability(rank, count):
    ret = 0
    if rank == 5 and count <= 62:
        ret = 70
    elif rank == 5 and count <= 62:
        ret = 70 + 700 * (count - 62)
    elif rank == 5 and count >= 74:
        ret = 7770 + 350 * (count - 73)
    elif rank == 4 and count <= 7:
        ret = 600
    elif rank == 4 and count == 8:
        ret = 6600
    elif rank == 4 and count >= 9:
        ret = 6600 + 3000 * (count - 8)
    return ret


class wish:
    user: wish_user

    def __init__(self, uid, gacha_type, gacha_pool):
        self.uid = uid
        self.gacha_pool = gacha_pool
        self.user = wish_user(uid, gacha_type)
        self.gacha_type = gacha_type
        self.probability_fn = is_character_gacha(gacha_type) and character_probability or weapon_probability

    def get_rank(self):
        value = random_int()
        index_5 = self.probability_fn(5, self.user.count_5)
        index_4 = self.probability_fn(4, self.user.count_4) + index_5
        if value <= index_5:
            return 5
        elif value <= index_4:
            return 4
        else:
            return 3

    def is_up(self, rank):
        if self.gacha_type == GACHA_TYPE.permanent.value:
            return False
        elif self.gacha_type == GACHA_TYPE.weapon.value:
            return random_int() <= 7500
        else:
            return random_int() <= 5000 or (rank == 5 and self.user.is_up)

    def once(self):
        # 判定星级
        rank = self.get_rank()
        # 是否为up
        is_up = self.is_up(rank)

        if rank != 5:
            # 不是5星则计数器+1
            self.user.inc_count(5)
            if rank == 4:
                # 如果是4星 则4星计数器重置
                self.user.count_4 = 1
            else:
                self.user.inc_count(4)
        else:
            self.user.count_5 = 1
            self.user.inc_count(4)
            if self.gacha_type == GACHA_TYPE.activity.value or self.gacha_type == GACHA_TYPE.weapon.value:
                # 如果是限定池或者武器池
                self.user.is_up = not is_up

        res = {
            'rank': rank,
            'is_up': is_up,
            'count_5': self.user.count_5,
            'count_4': self.user.count_4
        }
        if rank == 3:
            res['data'] = random.choice(self.gacha_pool.r3_prob_list)
        else:
            if is_up:
                res['data'] = random.choice(self.gacha_pool['r%s_up_items' % rank])
            else:
                res['data'] = random.choice(self.gacha_pool['r%s_prob_list' % rank])

        return dict_to_object(res)

    async def ten(self):
        res = []
        for i in range(0, 10):
            res.append(self.once())
        return res
