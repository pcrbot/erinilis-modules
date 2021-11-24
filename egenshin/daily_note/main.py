import asyncio
import time
from datetime import timedelta
from http.cookies import SimpleCookie

from apscheduler.triggers.date import DateTrigger
from nonebot import Message, MessageSegment, get_bot, scheduler

from ..player_info import query
from ..util import init_db
from .error import *
from .info_card import draw_info_card
from .typing import Daily_Note_Info

Account_Error = query.Account_Error

remind_db = init_db('daily_note/data', 'remind.sqlite')


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

    async def remind(self, on=True, once_remind=None):
        once_msg = ''
        if once_remind:
            once_remind = int(once_remind)
            once_msg = f' 并且树脂{once_remind}时提醒你'

        db_key = self.get_remind_key()
        if on:
            remind_db[db_key] = {
                'qid': self.qid,
                'uid': self.uid,
                'group_id': self.group_id,
                'once_remind': once_remind
            }
            return '已打开提醒功能' + once_msg
        else:
            del remind_db[db_key]
            return '已关闭提醒功能'


async def iter_new_resin():
    for db_key, info in remind_db.items():
        try:
            json_data = await query.daily_note(info['uid'], qid=info['qid'])
            if json_data.retcode != 0:
                raise Error_Message(json_data.message)
            json_data = Daily_Note_Info(**json_data.data)
            info['db_key'] = db_key
            yield info, json_data
            await asyncio.sleep(1)
        except Exception as e:
            del remind_db[db_key]
            raise Error_Message('获取失败,请重新绑定后再开启 原因: \n' + repr(e))


async def notify_remind_resin(qid, group_id, info):
    bot = get_bot()
    message = MessageSegment.image(await draw_info_card(info))
    try:
        tasks = [bot.send_private_msg(user_id=qid, message=message)]
        await asyncio.gather(*tasks)
    except Exception as e:
        # 私聊发送失败时 则使用群聊
        await bot.send_group_msg(group_id=group_id,
                        message=Message([MessageSegment.at(qid),
                                         message]))


@scheduler.scheduled_job('cron', minute=f"*/8")
async def update_resin():
    # 为设置提醒的用户刷新树脂
    async for db_info, data in iter_new_resin():
        notified = False
        remind_times = set([140, 160])
        once_time = db_info['once_remind']
        if once_time:
            remind_times.add(once_time)

        now = time.time()
        last_notify_time = db_info.get('last_notify_time')
        max_resin = db_info.get('max_resin') and data.current_resin == 160
        
        if last_notify_time and last_notify_time + timedelta(minutes=15).seconds > int(now) or max_resin:
            # 15分钟内不重复通知
            continue

        # 如果树脂需要提醒
        if data.current_resin in remind_times:
            await notify_remind_resin(db_info['qid'], db_info['group_id'], data)
            notified = True
            db_info['max_resin'] = data.current_resin == 160
            
            if once_time and data.current_resin >= once_time:
                db_info['once_remind'] = ''

        # 探索提醒
        # if any([x.status == 'Finished' for x in data.expeditions]):
        #     await notify_remind_resin(db_info['qid'], db_info['group_id'], data)
        #     notified = True

        if notified:
            db_info['last_notify_time'] = int(time.time())
            remind_db[db_info['db_key']] = db_info
