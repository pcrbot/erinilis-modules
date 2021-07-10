import os
import random
import datetime
import json
import hoshino
from apscheduler.triggers.date import DateTrigger
from typing import List
from nonebot import MessageSegment, scheduler, get_bot
from hoshino.util import escape

from .. import util

dir_data = os.path.join(os.path.dirname(__file__), 'data')

data_path = os.path.join(os.path.dirname(__file__), 'voice')

if not os.path.exists(dir_data):
    os.makedirs(dir_data)

user_db = util.init_db('guess_voice/data', 'user.sqlite')
voice_db = util.init_db('guess_voice/data', 'voice.sqlite')
process = {}

with open(os.path.join(os.path.dirname(__file__), 'character.json'), 'r', encoding="utf-8") as f:
    character_json: dict = json.loads(f.read())


def get_voice_by_language(data, language_name):
    if language_name == '中':
        return data['chn']
    elif language_name == '日':
        return data['jap']
    elif language_name == '英':
        return data['eng']
    elif language_name == '韩':
        return data['kor']


def char_name_by_name(name):
    names = character_json.keys()
    # 是否就是正确的名字
    if name in names:
        return name
    #
    for item in names:
        nickname = character_json[item]
        if name in nickname:
            return item
    return ''


def get_random_voice(name, language='中'):
    voice_list = voice_db.get(char_name_by_name(name))
    if not voice_list:
        return
    temp_voice_list = []
    for v in voice_list:
        voice_path = get_voice_by_language(v, language)
        if voice_path:
            temp_voice_list.append(voice_path)
    if not temp_voice_list:
        return
    path = os.path.join(data_path, random.choice(temp_voice_list))
    return path


class Guess:
    time: int
    group_id: int
    group = {}

    def __init__(self, group_id: int, time=30):
        self.time = time
        self.group_id = group_id
        self.group = process.get(self.group_id)

    def is_start(self):
        if not self.group:
            return False
        return self.group['start']

    def start(self, language: List[str] = None):
        if not language:
            language = ['中']
        # 随机一个语言
        language = random.choice(language)
        # 随机选择一个语音
        answer = random.choice(list(voice_db.keys()))
        #print('正确答案为: %s' % answer)
        temp_voice_list = []

        for v in voice_db[answer]:
            if not (answer in v['text']):
                voice_path = get_voice_by_language(v, language)
                if voice_path:
                    temp_voice_list.append(voice_path)

        if not temp_voice_list:
            hoshino.logger.info('随机到了个哑巴,, 重新随机.. 如果反复出现这个 你应该检查一下数据库')
            return self.start([language])

        voice_path = random.choice(temp_voice_list)
        # 记录答案
        process[self.group_id] = {
            'start': True,
            'answer': answer,
            'ok': set()
        }

        job_id = str(self.group_id)
        if scheduler.get_job(job_id, 'default'):
            scheduler.remove_job(job_id, 'default')

        now = datetime.datetime.now()
        notify_time = now + datetime.timedelta(seconds=self.time)
        scheduler.add_job(self.end_game, trigger=DateTrigger(notify_time),
                          id=job_id,
                          misfire_grace_time=60,
                          coalesce=True,
                          jobstore='default',
                          max_instances=1)

        path = os.path.join(data_path, voice_path)

        return MessageSegment.record(f'file:///{path}')

    async def end_game(self):
        self.group = process.get(self.group_id)

        ok_list = list(process[self.group_id]['ok'])
        if not ok_list:
            msg = '还没有人猜中呢'
        else:
            msg = '回答正确的人: ' + ' '.join([str(MessageSegment.at(qq)) for qq in ok_list])
        msg = '正确答案是 %s\n%s' % (self.group['answer'], msg)
        await get_bot().send_group_msg(group_id=self.group_id, message=msg)

        # 清理记录
        process[self.group_id] = {}

        # 记录到数据库给之后奖励做处理
        user_group = user_db.get(self.group_id, {})
        if not user_group:
            user_db[self.group_id] = {}

        for user in ok_list:
            info = user_group.get(str(user), {'count': 0})
            info['count'] += 1
            user_group[user] = info
        user_db[self.group_id] = user_group

    # 只添加正确的答案
    async def add_answer(self, qq: int, msg: str):
        if char_name_by_name(msg) == self.group['answer']:
            process[self.group_id]['ok'].add(qq)
            scheduler.remove_job(str(self.group_id), 'default')
            await self.end_game()

    # 获取排行榜
    async def get_rank(self,bot,ev):
        user_list = user_db.get(self.group_id, {})

        user_list = sorted(user_list.items(), key=lambda v: v[1]['count'])
        user_list.reverse()
        num = 0
        msg = '本群猜语音排行榜:\n'
        for user, data in user_list[:10]:
            user = await bot.get_group_member_info(group_id=ev['group_id'],user_id=user)
            num += 1
            msg += f"第{num}名: {escape(user['card'])}, 猜对{data['count']}次\n"
        return msg