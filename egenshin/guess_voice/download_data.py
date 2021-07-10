# -*- coding: UTF-8 -*-
"""
该脚本可以直接获取wiki上的语音文件 并保存进数据库中
"""

import asyncio
import requests
import json
import os

from sqlitedict import SqliteDict
from pathlib import Path
from bs4 import BeautifulSoup

OUT_PUT = Path(__file__).parent / 'data'

BASE_URL = 'https://wiki.biligame.com/ys/'

API = {
    'character_list': '角色',
    'voice': '%s语音'
}

config = {
    # 中 日 英 韩
    'voice_language': ['中', '日']
}


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
    html = requests.get(BASE_URL + API['character_list']).text
    soup = BeautifulSoup(html, 'lxml')
    char_list = soup.find(attrs={'class': 'resp-tab-content', 'style': 'display:block;'})
    char_list = char_list.find_all(attrs={'class': 'center'})
    res = list(set(map(lambda x: x.find('a').attrs['title'], char_list)))
    res.sort()
    return res


# 获取角色语音
async def get_voice_info(character_name: str):
    print('获取数据: %s' % character_name)
    html = requests.get(BASE_URL + API['voice'] % character_name).text
    soup = BeautifulSoup(html, 'lxml')
    if soup.find(text='本页面目前没有内容。您可以在其他页面中'):
        return None
    voice_list = soup.find_all(attrs={'class': 'visible-md'})[2:]
    info_list = []
    for item in voice_list:
        item_tab = item.find_all(attrs={'class': ''})[1:]
        if isinstance(item_tab[1].next, str):
            print('...别管龙哥了')
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
        res = requests.get(url, timeout=30)
    except requests.exceptions.ConnectionError:
        raise
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(res.content)


async def update_voice_data():
    # 获取全部人物列表
    char_list = await get_character_list()
    for char in char_list:
        info = await get_voice_info(char)
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
                out_path = OUT_PUT / language / char / Path(url).name
                out = str(out_path)
                if not out_path.exists():
                    await download(url, out)

                if language == '中':
                    chn = out
                elif language == '日':
                    jap = out
                elif language == '英':
                    eng = out
                elif language == '韩':
                    kor = out

                print('下载成功: %s -> %s' % (char, out))

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


def run_init():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(update_voice_data())
    loop.close()


if __name__ == '__main__':
    run_init()
