import json
import requests

from . import util

setting = util.get_config().setting


def short(url: str):
    if not setting.short_url_enable or not url:
        return url

    data = {
        'url': url
    }
    proxy = {}
    if setting.proxy_enable:
        proxy = {
            "http": setting.proxy_url,
            "https": setting.proxy_url
        }

    try:
        res = json.loads(requests.post(setting.short_api,
                                       json=data,
                                       headers=setting.short_headers,
                                       timeout=30,
                                       proxies=proxy
                                       ).text, object_hook=util.Dict)
    except TimeoutError:
        print('short url time out')
        return url

    if setting.short_error and res[setting.short_error] == setting.short_error_value:
        print('short url error: %s' % res.msg)
        return url

    return res[setting.short_json_str]
