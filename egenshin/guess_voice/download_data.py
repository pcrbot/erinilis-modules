# -*- coding: UTF-8 -*-
"""
该脚本可以直接获取wiki上的语音文件 并保存进数据库中
"""

import json
import os
from datetime import timedelta
from pathlib import Path

import hoshino
from bs4 import BeautifulSoup
from hoshino import aiorequests
from sqlitedict import SqliteDict

from ..util import Dict, cache

OUT_PUT = Path(__file__).parent / 'voice'

BASE_URL = 'https://wiki.biligame.com/ys/'

API = {'character_list': '角色', 'voice': '%s语音'}

config = {
    # 日 英 韩
    'voice_language': ['日', '英', '韩']
}

dir_data = os.path.join(os.path.dirname(__file__), 'data')

if not os.path.exists(dir_data):
    os.makedirs(dir_data)


############
def get_path(*paths):
    return os.path.join(os.path.dirname(__file__), *paths)


def init_db(db_dir, db_name='db.sqlite') -> SqliteDict:
    return SqliteDict(get_path(db_dir, db_name),
                      encode=json.dumps,
                      decode=json.loads,
                      autocommit=True)


db = init_db('data', 'voice.sqlite')


############

# 获取角色列表
async def get_character_list():
    html = await aiorequests.get(BASE_URL + API['character_list'])
    soup = BeautifulSoup(await html.text, 'lxml')
    char_list = soup.find(attrs={
        'class': 'resp-tab-content',
        'style': 'display:block;'
    })
    char_list = char_list.find_all(attrs={'class': 'center'})
    res = list(set(map(lambda x: x.find('a').attrs['title'], char_list)))
    res.sort()
    return res


# 获取角色语音
async def get_voice_info(character_name: str):
    hoshino.logger.info('获取数据: %s' % character_name)
    html = await aiorequests.get(BASE_URL + API['voice'] % character_name)
    soup = BeautifulSoup(await html.text, 'lxml')
    if soup.find(text='本页面目前没有内容。您可以在其他页面中'):
        return None
    voice_list = soup.find_all(attrs={'class': 'visible-md'})[2:]
    info_list = []
    for item in voice_list:
        item_tab = item.find_all(attrs={'class': ''})[1:]
        if isinstance(item_tab[1].next, str):
            return info_list
        info_list.append({
            'title': item_tab[0].text,
            'text': item_tab[5].text,
            '中': item_tab[1].next.attrs.get('data-src', ''),
            '日': item_tab[2].next.attrs.get('data-src', ''),
            '英': item_tab[3].next.attrs.get('data-src', ''),
            '韩': item_tab[4].next.attrs.get('data-src', ''),
        })
    return info_list


# 下载音频文件到本地
async def download(url, path):
    try:
        res = await aiorequests.get(url, timeout=30)
    except aiorequests.exceptions.ConnectionError:
        raise
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(await res.content)


async def update_voice_data():
    # 获取全部人物列表
    char_list = await get_character_list()
    for char in char_list:
        info = await get_voice_info(char)
        if not info:
            continue
        data = []
        for v in info:
            chn = ''
            jap = ''
            eng = ''
            kor = ''
            for language in config['voice_language']:
                url = v[language]
                if not url:
                    continue
                path = str(Path() / language / char / Path(url).name)
                out_path = OUT_PUT / path
                out = str(out_path)
                if not out_path.exists():
                    await download(url, out)

                if language == '中':
                    chn = path
                elif language == '日':
                    jap = path
                elif language == '英':
                    eng = path
                elif language == '韩':
                    kor = path

                hoshino.logger.info('下载成功: %s -> %s' % (char, path))

            data.append({
                'title': v['title'],
                'text': v['text'],
                'chn': chn,
                'jap': jap,
                'eng': eng,
                'kor': kor
            })
        # 存入数据库
        db[char] = data


@cache(ttl=timedelta(hours=24))
async def voice_list_by_mys():
    try:
        url = 'https://api-static.mihoyo.com/common/blackboard/ys_obc/v1/home/content/list?app_sn=ys_obc&channel_id=80'
        res = await aiorequests.get(url, timeout=30)
    except aiorequests.exceptions.ConnectionError:
        raise
    json_data = await res.json(object_hook=Dict)
    if json_data.retcode:
        raise Exception(json_data.message)
    try:
        data_list = json_data.data.list[0].children[2].list
    except KeyError as e:
        raise Exception('获取语音列表失败, 请联系作者修复')

    return {x['title'].split()[0]: x for x in data_list}


async def voice_detail_by_mys(content_id):
    try:
        url = 'https://bbs.mihoyo.com/ys/obc/content/%s/detail?bbs_presentation_style=no_header' % content_id
        res = await aiorequests.get(url, timeout=30)
    except aiorequests.exceptions.ConnectionError:
        raise
    soup = BeautifulSoup(await res.content, 'lxml')
    paragraph_box = soup.select('.obc-tmpl__paragraph-box')

    return [{
        'text': x.get_text(),
        'chn': x.find('source').attrs['src']
    } for x in paragraph_box]
