import json
import base64
import aiofiles
import asyncio
import datetime
from hoshino import aiorequests
from urllib.parse import urlencode
from .util import Dict, get_config, cache

config = get_config().setting

TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'
OCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"


async def fetch_token(API_KEY=None, SECRET_KEY=None):
    params = {
        'grant_type': 'client_credentials',
        'client_id': API_KEY or config.baidu_ocr.API_KEY,
        'client_secret': SECRET_KEY or config.baidu_ocr.SECRET_KEY
    }
    post_data = urlencode(params).encode('utf-8')
    req = await aiorequests.post(TOKEN_URL, post_data, timeout=10)
    result = json.loads(await req.text)

    if ('access_token' in result.keys() and 'scope' in result.keys()):
        if not 'brain_all_scope' in result['scope'].split(' '):
            raise Exception('please ensure has check the ability')
        return result['access_token']
    else:
        raise Exception('please overwrite the correct API_KEY and SECRET_KEY')


async def ocr_text(img_path=None, img_url=None):
    if not any([img_path, img_url]):
        raise Exception('img_path or img_url is None.')

    token = await fetch_token()
    image_url = OCR_URL + "?access_token=" + token
    file_content = None
    if img_path:
        async with aiofiles.open(img_path, 'rb') as fp:
            file_content = await fp.read()
    else:
        req = await aiorequests.get(img_url)
        file_content = await req.content

    post_data = urlencode({'image': base64.b64encode(file_content)})
    result = await aiorequests.post(image_url, post_data, timeout=10)
    json_data = await result.json(object_hook=Dict)
    err = json_data.get('error_code')
    if err and err == 18:  # QPS
        await asyncio.sleep(1)
        return await ocr_text(img_path=img_path, img_url=img_url)
    elif err:
        # https://cloud.baidu.com/doc/OCR/s/dk3h7y5vr
        raise Exception(json_data.error_msg)

    return json_data