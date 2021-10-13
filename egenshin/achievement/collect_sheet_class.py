import re
from dataclasses import dataclass


__all__ = [
    'remove_special_char', 'Achievements_Info', 'Achievements20_Info',
    'Achievements21_Info', 'Achievements22_Info'
]


def remove_special_char(s):
    special_char = r'[+ 「」…！!，,。.、？?《》·♬Ⅱ—“”-]'
    return re.sub(special_char, '', s)


class Base:
    def __str__(self):
        return remove_special_char(self.name)

    @property
    def is_daily_quest(self):
        return '每日' in self.type

    @property
    def is_main_quest(self):
        return '魔神' in self.type

    @property
    def is_world_quest(self):
        return '世界任务' in self.type

    @property
    def is_prestige_quest(self):
        return '声望' in self.type

    @property
    def is_world_explore(self):
        return '大世界' in self.type

    @property
    def is_battle(self):
        return '战斗相关' in self.type

    @property
    def is_cooking(self):
        return '料理相关' in self.type

# @dataclass
# class Unactuated_Info:
#     code: str
#     version: str
#     is_hide: str
#     top_type: str
#     name: str
#     desc: str
#     type: str
#     remark: str
#     neta: str


@dataclass
class Achievements_Info(Base):
    id: str
    code: str
    version: str
    is_hide: str
    top_type: str
    name: str
    desc: str
    type: str
    rarity: str
    reward: str
    remark: str
    neta: str

@dataclass
class Achievements20_Info(Base):
    code: str
    version: str
    is_hide: str
    top_type: str
    name: str
    desc: str
    type: str
    rarity: str
    reward: str
    remark: str

@dataclass
class Achievements21_Info(Base):
    code: str
    version: str
    is_hide: str
    top_type: str
    name: str
    desc: str
    type: str
    rarity: str
    reward: str
    remark: str
    neta: str
    
@dataclass
class Achievements22_Info(Base):
    code: str
    version: str
    is_hide: str
    top_type: str
    name: str
    desc: str
    type: str
    rarity: str
    reward: str
    remark: str
    neta: str