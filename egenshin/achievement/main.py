import copy
import re
import zhconv
from dataclasses import dataclass, field
from typing import List

from ..baidu_ocr import ocr_text
from ..player_info.query import get_uid_by_qid
from ..util import get_config, init_db, process
from .achievements import all_achievements, remove_special_char
from .proxy_url import proxy_url

config = get_config()
db = init_db(config.cache_dir, 'achievement.sqlite')


@dataclass
class Info:
    uid: int = 0
    completed: List[str] = field(default_factory=list)


FIX_WORD = {
    '碰··碰': '碰·一·碰',
    'SWORDFISHⅡ': 'SWORDFISH Ⅱ',
    'SWORDFISH II': 'SWORDFISH Ⅱ',
    'SWORDFISⅢ': 'SWORDFISH Ⅱ',
    '家里最好的剑': '冢里最好的剑',
    '是时候征服海衹岛了!': '是时候征服海祇岛了!',
    '除了时间什么都没丢': '除了时间什么也没丢',
    'ela vu': 'DejaVu'
}
WORD_REPLACE = {}


class achievement:
    qq: int
    info: Info

    def __init__(self, qq):
        self.qq = str(qq)

        if process(self.qq).is_run():
            raise Exception('正在处理中...')
        uid = get_uid_by_qid(self.qq)
        if not uid:
            raise Exception('请先使用查询游戏UID功能进行绑定')

        info = db.get(self.qq, {}).get(uid)

        self.info = info and Info(**info) or Info(uid=uid)

    async def save_data(self, data):
            if not db.get(self.qq):
                db[self.qq] = {self.info.uid: data}
            else:
                new_data = db[self.qq]
                new_data[self.info.uid] = data
                db[self.qq] = new_data

    async def clear_data(self):
        await self.save_data({})

    async def form_img_list(self, img_list):
        run = process(self.info.uid).start()

        try:
            all_achievement = await all_achievements()
            all_keys = all_achievement.keys()
            completed = set(self.info.completed)

            for img_url in img_list:
                result = await ocr_text(img_url=img_url)

                for word in result.words_result:
                    word = word.words.strip()
                    word = zhconv.convert(word, 'zh-hans').strip('“”')
                    word = FIX_WORD.get(word, word)
                    word = remove_special_char(word)

                    if len(word) == 1:
                        continue

                    if word == '达成':
                        continue

                    match_count = re.search(r'^\d+/\d+$', word)
                    match_date = re.search(r'^\d+/\d+/\d+$', word)
                    if match_count or match_date:
                        continue

                    for v in WORD_REPLACE.items():
                        word = word.replace(*v)

                    word_filter = list(filter(lambda s: word in s, all_keys))
                    if word_filter:
                        completed.add(all_achievement[word_filter[0]]['name'])

            self.info.completed = list(completed)

            await self.save_data(self.info.__dict__)

            run.ok()
        except Exception as e:
            run.ok()
            raise e

    async def from_proxy_url(self, url_list):
        run = process(self.info.uid).start()
        try:
            img_list, failed_list = await proxy_url(url_list)

            await self.form_img_list(img_list)

            return failed_list
        except Exception as e:
            run.ok()
            raise e

    @property
    async def unfinished(self):
        all_achievement = copy.copy(await all_achievements())
        all_keys = all_achievement.keys()

        for name in self.info.completed:
            name = remove_special_char(name)
            if name in all_keys:
                del all_achievement[name]

        return all_achievement.values()
