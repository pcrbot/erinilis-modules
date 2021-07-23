from nonebot import Message
from urllib.parse import urlparse, parse_qs, unquote
from . import util
from .gacha_log import gacha_log

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
        authkey = unquote(authkey)
        log = gacha_log(self.qq, authkey, region)
        user_info = await log.get_player_info()
        if not user_info:
            return '绑定失败,请检查链接是否能打开'

        info = db.get(self.qq, {})
        info['authkey'] = authkey
        info['region'] = region
        db[self.qq] = info

        msg = """卡池绑定成功!
UID:{uid}
昵称:{nickname}
等级:{level}

可以使用命令:
{comm1}
{comm2}"""

        return msg.format(uid=user_info['user_id'],
                          nickname=user_info['nickname'],
                          level=user_info['level'],
                          comm1=config.comm.gachalog,
                          comm2=config.comm.gacha_statistics
                          )
