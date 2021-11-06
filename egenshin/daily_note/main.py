from dataclasses import dataclass
from http.cookies import SimpleCookie
from typing import List

from apscheduler.triggers.date import DateTrigger
from nonebot import scheduler

from ..player_info import query
from ..util import init_db
from .error import *

Account_Error = query.Account_Error

remind_db = init_db('daily_note/data', 'remind.sqlite')


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
    def __init__(self, qid, cookie_raw=None, group_id=None):
        self.qid = qid
        self.group_id = group_id

        self.cookie = query.get_cookie_by_qid(qid)

        if not any([cookie_raw, self.cookie]):
            raise Cookie_Error()

        if cookie_raw and ',' not in cookie_raw:
            raise Error_Message(
                'cookie格式错误, 请参考说明, 正确的格式应为 100000000,Xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
            )

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
        try:
            json_data = await query.daily_note(self.uid, self.cookie_raw)
        except Exception as e:
            raise Login_Error(repr(e) + '\n 如果已确认打开可能是获取的cookie不正确')

        if json_data.retcode == 10102:
            raise Login_Error('UID[%s]请先在米游社角色信息那打开实时便笺功能' % self.uid)
        if json_data.retcode != 0:
            raise Login_Error(json_data.message)

        query.save_cookie(self.qid, self.cookie_raw)
        return Daily_Note_Info(**json_data.data)

    def get_remind_key(self):
        return '%s_%s' % (self.qid, self.uid)

    async def remind(self, on=True):
        db_key = self.get_remind_key()
        if on:
            remind_db[db_key] = {
                'qid': self.qid,
                'uid': self.uid,
                'group_id': self.group_id
            }
            return '已打开提醒功能'
        else:
            del remind_db[db_key]
            return '已关闭提醒功能'

    async def remind_job(self):

        # job_id = f'egenshin_remind_job_{self.uid}'

        # scheduler.add_job(self.remind_job, trigger=DateTrigger(notify_time),
        #                   id=job_id,
        #                   misfire_grace_time=60,
        #                   coalesce=True,
        #                   jobstore='default',
        #                   max_instances=1)
        pass


# @scheduler.scheduled_job('cron', minute=f"*/5")
# async def update_resin():
#     # 为设置提醒的用户刷新树脂
#     pass

