import asyncio
import datetime
from apscheduler.triggers.date import DateTrigger
from ..util import *

material_db = init_db(config.cache_dir, 'material.sqlite')
material_data = get_config('material/data.yml')


class material:
    uid = 0
    group = 0
    name = ''

    def __init__(self, group, uid):
        self.group = group
        self.uid = uid

    def get_job_id(self):
        return '%s%s' % (self.group, self.uid)

    @staticmethod
    async def show(name):
        data = material_data.get(name)
        if not data or not data.text:
            return '木有 %s 材料信息' % name
        return data.text

    async def notify(self):
        data = material_data.get(self.name)
        msg = str(MessageSegment.at(self.uid))
        msg += '你设定的材料(%s)已刷新' % self.name
        if data:
            msg += ', 可以使用 查看材料#%s 查看详细信息' % self.name
        await bot.send_group_msg(group_id=self.group, message=msg)
        self.set_mat_data(None)

    def set_mat_data(self, value):
        job_id = self.get_job_id()
        mat_data = material_db.get(job_id, {})
        mat_data[self.name] = value
        material_db[job_id] = mat_data

    def get_mat_data(self):
        job_id = self.get_job_id()
        mat_data = material_db.get(job_id, {})
        if mat_data and mat_data[self.name]:
            return mat_data[self.name]
        return None

    @staticmethod
    def get_material_time(name):
        time_list = material_data.time
        for time in time_list:
            if name in time_list[time]:
                return time
        return 0

    async def mark(self, name, format_time=None):
        self.name = name
        job_id = self.get_job_id()
        time = self.get_material_time(name)
        custom_time = float(get_msg_keyword(r'\D+', name)[0] or '0')
        if not time and not custom_time:
            return '无法添加收集任务,没有找到此材料信息'
        if custom_time and not time:
            time = custom_time
        now = datetime.datetime.now()
        if format_time:
            notify_time = datetime.datetime.strptime(format_time, '%Y-%m-%d %H:%M:%S')
            if now > notify_time:
                self.set_mat_data(None)
                return
        else:
            notify_time = now + datetime.timedelta(hours=time)

        if scheduler.get_job(job_id, 'default'):
            scheduler.remove_job(job_id, 'default')

        scheduler.add_job(self.notify, trigger=DateTrigger(notify_time),
                          id=job_id,
                          misfire_grace_time=60,
                          coalesce=True,
                          jobstore='default',
                          max_instances=1)

        format_time = notify_time.strftime('%Y-%m-%d %H:%M:%S')

        self.set_mat_data({
            'datetime': format_time,
            'uid': self.uid,
            'group': self.group,
            'name': self.name
        })

        return str(MessageSegment.at(self.uid)) + '将于%s小时后 %s 通知你收集材料' % (time, format_time)

    async def status(self):
        mat_list = material_db.get(self.get_job_id(), {})
        if not mat_list:
            return '你还没有任何设定的材料, 请使用 收集材料#材料名字 进行设定'
        msg = []
        for mat in mat_list:
            data = mat_list[mat]
            if not data:
                continue
            msg.append('材料: %s  刷新时间: %s' % (data['name'], data['datetime']))

        if not msg:
            return '你还没有任何设定的材料, 请使用 收集材料#材料名字 进行设定'

        return '\n'.join(msg)


async def init_material_job():
    if material_db:
        for user in material_db:
            for job in material_db[user]:
                job = material_db[user][job]
                if not job:
                    continue
                mat = material(job['group'], job['uid'])
                await mat.mark(job['name'], job['datetime'])


def run_material_init():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(init_material_job())
    loop.close()


run_material_init()
