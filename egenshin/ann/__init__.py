import requests
import nonebot
from bs4 import BeautifulSoup
from ..util import *

api_url = 'https://hk4e-api-static.mihoyo.com/common/hk4e_cn/announcement/api/'
api_params = '?game=hk4e&game_biz=hk4e_cn&lang=zh-cn&bundle_id=hk4e_cn&platform=pc&region=cn_gf01&level=55&uid=105293904'
ann_content_url = '%sgetAnnContent%s' % (api_url, api_params)
ann_list_url = '%sgetAnnList%s' % (api_url, api_params)


class ann:
    ann_list_data = []
    ann_content_data = []

    def __init__(self):
        pass

    async def get_ann_content(self):
        res = dict_to_object(json.loads(requests.get(ann_content_url, timeout=10).text))
        if res.retcode == 0:
            self.ann_content_data = res.data.list
        return self.ann_content_data

    async def get_ann_list(self):
        res = dict_to_object(json.loads(requests.get(ann_list_url, timeout=10).text))
        if res.retcode == 0:
            self.ann_list_data = res.data.list
        return self.ann_list_data

    async def get_ann_ids(self):
        await self.get_ann_list()
        if not self.ann_list_data:
            return []
        ids = []
        for label in self.ann_list_data:
            ids += [x['ann_id'] for x in label['list']]
        return ids

    async def ann_list_msg(self):
        await self.get_ann_list()
        if not self.ann_list_data:
            return '获取游戏公告失败,请检查接口是否正常'
        msg = ''
        for data in self.ann_list_data:
            msg += '%s:\n' % data['type_label']
            data_list = [x for x in data['list'] if not x['ann_id'] in config.setting.ann_block]
            msg += '\n'.join(map(lambda x: '%s %s' % (x['ann_id'], x['title']), data_list))
            msg += '\n'
        msg += '\n请输入前面的数字ID进行查看,例: %s0000' % config.comm.ann_detail
        return msg

    async def ann_detail_msg(self, ann_id):
        await self.get_ann_content()
        if not self.ann_content_data:
            return '获取游戏公告失败,请检查接口是否正常'
        content = filter_list(self.ann_content_data, lambda x: x['ann_id'] == ann_id)
        if not content:
            return '没有找到对应的公告ID'
        soup = BeautifulSoup(content[0]['content'], 'lxml')
        banner = content[0]['banner']
        ann_img = str(MessageSegment.image(banner)) if banner else ''
        for a in soup.find_all('a'):
            href = a.get('href')
            a.string += ' (%s)' % re.search(r'https?.+', re.sub(r'[;()\']', '', href)).group()

        for img in soup.find_all('img'):
            img.string = str(MessageSegment.image(img.get('src')))

        msg_list = [BeautifulSoup(x.get_text('\n').replace('<<', ''), 'lxml').get_text() for x in soup.find_all('p')]
        msg_list.append(ann_img)
        return '\n'.join(msg_list)


ann_db = init_db(config.cache_dir, 'ann.sqlite')


def sub_ann(group):
    sub_list = ann_db.get('sub', [])
    sub_list.append(group)
    ann_db['sub'] = list(set(sub_list))
    return '成功订阅原神公告'


def unsub_ann(group):
    sub_list = ann_db.get('sub', [])
    sub_list.remove(group)
    ann_db['sub'] = sub_list
    return '成功取消订阅原神公告'


async def check_ann_state():
    print('定时任务: 原神公告查询..')
    ids = ann_db.get('ids', [])
    sub_list = ann_db.get('sub', [])
    if not sub_list:
        print('没有群订阅, 取消获取数据')
        return
    if not ids:
        ids = await ann().get_ann_ids()
        if not ids:
            print('获取原神公告ID列表错误,请检查接口')
        ann_db['ids'] = ids
        print('初始成功, 将在下个轮询中更新.')
        return
    new_ids = await ann().get_ann_ids()

    new_ann = [i for i in new_ids if i not in ids]
    if not new_ann:
        print('没有最新公告')
        return

    detail_list = []
    for ann_id in new_ann:
        detail_list.append(await ann().ann_detail_msg(ann_id))

    for group in sub_list:
        for msg in detail_list:
            await bot.send_group_msg(group_id=group, message=msg)

    print('推送完毕, 更新数据库')
    ann_db['ids'] = new_ids


if config.setting.ann_cron_enable:
    @nonebot.scheduler.scheduled_job(
        'cron',
        minute=f"*/{config.setting.ann_cron_time}"
    )
    async def _():
        await check_ann_state()
