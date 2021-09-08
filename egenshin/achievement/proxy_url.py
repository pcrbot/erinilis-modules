import re
from hoshino import aiorequests
from ..util import Dict

async def proxy_url(url_list):
    img_list = []
    failed_list = []
    for url in url_list:
        match_ibb = re.search(r'^https://ibb.co/(\S+)$', url)
        match_imgtu = re.search(r'^https://imgtu.com/i/(\S+)$', url)

        if match_ibb:
            code = match_ibb.group(1)
            res = await aiorequests.get(
                f'https://ibb.co/{code}/oembed.json')
            if res.status_code == 200:
                json_data = await res.json(object_hook=Dict)
                img_list.append(json_data.url)
            else:
                failed_list.append(url)

        if match_imgtu:
            code = match_imgtu.group(1)
            res = await aiorequests.get(
                f'https://imgtu.com/oembed/?url=https%3A%2F%2Fimgtu.com%2Fi%2F{code}&format=json'
            )
            if res.status_code == 200:
                json_data = await res.json(object_hook=Dict)
                img_list.append(
                    json_data.thumbnail_url.replace('.md', ''))
            else:
                failed_list.append(url)

    return img_list, failed_list
