from typing import List
from dataclasses import dataclass
from http.cookies import SimpleCookie
from ..player_info import query
from .error import *

Account_Error = query.Account_Error


@dataclass
class Daily_Note_expeditions:
    avatar_side_icon: str  # 头像icon
    status: str  # 'Finished' or 'Ongoing' 状态
    remained_time: str  # 剩余时间


@dataclass
class Daily_Note_Info:
    current_resin: int  # 当前树脂
    max_resin: int  # 最大树脂
    resin_recovery_time: str  # 树脂回复时间
    finished_task_num: int  # 完成委托个数
    total_task_num: int  # 全部委托个数
    is_extra_task_reward_received: bool
    remain_resin_discount_num: int  # 周本树脂减半剩余次数
    resin_discount_num_limit: int  # 周本树脂减半次数
    current_expedition_num: int  # 当前派遣数量
    max_expedition_num: int  # 最大派遣数量
    expeditions: List[Daily_Note_expeditions]  # 派遣列表


class Daily_Note():
    def __init__(self, qid, cookie_raw=None):
        self.qid = qid

        self.cookie = query.get_cookie_by_qid(qid)

        if not any([cookie_raw, self.cookie]):
            raise Cookie_Error()

        self.uid = query.get_uid_by_qid(qid)
        if not self.uid:
            raise Error_Message('请先使用ys#绑定')

        self.cookie = SimpleCookie(self.cookie)
        if cookie_raw:
            self.cookie.load(
                dict(zip(['account_id', 'cookie_token'],
                         cookie_raw.split(','))))

        self.cookie_raw = self.cookie.output(header='', sep=';').strip()

    async def get_info(self) -> Daily_Note_Info:
        json_data = await query.daily_note(self.uid, self.cookie_raw)

        if json_data.retcode == 10102:
            raise Login_Error('请先在米游社角色信息那打开实时便笺功能')
        if json_data.retcode != 0:
            raise Login_Error(json_data.message)

        query.save_cookie(self.qid, self.cookie_raw)
        return Daily_Note_Info(**json_data.data)
