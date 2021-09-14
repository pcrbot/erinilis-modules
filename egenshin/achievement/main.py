import copy
import json
import re
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import List

import zhconv

from ..baidu_ocr import ocr_text
from ..player_info.query import get_uid_by_qid
from ..util import cache, get_config, get_path, gh_json, init_db, process
from .collect_sheet import remove_special_char, achievements_sheet
from .proxy_url import proxy_url

config = get_config()
db = init_db(config.cache_dir, 'achievement.sqlite')
local_dir = Path(get_path('achievement'))

with open(local_dir / 'fix_word.json', 'r', encoding="utf-8") as fp:
    FIX_WORD = json.load(fp)


@cache(ttl=timedelta(hours=24))
async def gh_fix_word():
    return await gh_json('achievement/fix_word.json')


@dataclass
class Info:
    uid: int = 0
    completed: List[str] = field(default_factory=list)


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

        self.run = process(self.info.uid).start()

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
        try:
            all_achievement = await achievements_sheet()
            all_keys = all_achievement.keys()
            completed = set(self.info.completed)
            old_completed_len = len(completed)
            ocr_success = []
            for img_url in img_list:
                result = await ocr_text(img_url=img_url)
                ocr_count = 0
                for word in result.words_result:
                    word = word.words.strip()
                    word = zhconv.convert(word, 'zh-hans').strip('“”') # 转换简体字
                    local_fix = FIX_WORD.get(word)

                    if not local_fix: # 如果本地没有修复的词, 就使用github上的
                        gh_fix = await gh_fix_word()
                        word = gh_fix.get(word, word)
                    else:
                        word = local_fix

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
                        ocr_count += 1
                        completed.add(all_achievement[word_filter[0]].name)
                ocr_success.append(ocr_count)
            self.info.completed = list(completed)

            await self.save_data(self.info.__dict__)

            self.run.ok()
            return ocr_success, len(self.info.completed) - old_completed_len
        except Exception as e:
            self.run.ok()
            raise e

    async def from_proxy_url(self, url_list):
        try:
            img_list, failed_list = await proxy_url(url_list)
            ocr_success, added_len = await self.form_img_list(img_list)
            return failed_list, ocr_success, added_len
        except Exception as e:
            self.run.ok()
            raise e

    @property
    async def unfinished(self):
        try:
            all_achievement = copy.copy(await achievements_sheet())
            all_keys = all_achievement.keys()

            for name in self.info.completed:
                name = remove_special_char(name)
                if name in all_keys:
                    del all_achievement[name]
            self.run.ok()
            return all_achievement.values()
        except Exception as e:
            self.run.ok()
            raise e
