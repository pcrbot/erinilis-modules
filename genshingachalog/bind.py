from nonebot import Message
from urllib.parse import urlparse, parse_qs, unquote
from . import util

config = util.get_config()
db = util.init_db(config.cache_dir)


class bind:
    raw = ''
    qq = 0

    def __init__(self, qq, bind_msg: str):
        self.raw = bind_msg.strip()
        self.qq = qq

    async def save(self):
        msg = Message(self.raw)[0]
        if msg.type != 'text':
            return '参数只允许文本'

        query = urlparse(self.raw).query
        if not query:
            return '链接不正确'
        query = {k: v[0] for k, v in parse_qs(query).items()}
        authkey = query.get('authkey')
        region = query.get('region', 'cn_gf01')
        if not authkey:
            return '缺少必要参数(authkey)'

        info = db.get(self.qq, {})
        info['authkey'] = unquote(authkey)
        info['region'] = region
        db[self.qq] = info
        return '绑定成功'
