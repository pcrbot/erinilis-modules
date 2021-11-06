from ..util import init_db, get_group_info
from . import query


class Message(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        return self.msg


class HelpMessage(Message):
    def __init__(self):
        super().__init__('''
因为米游社限制,所以可以给自己的群增加查询使用次数,不公用
每个账号能添加30次(米游社设定),你可以添加小号增加使用次数
令牌可以输入yss?来查看获取方式

格式 群号,0000000,xxxxxxxxxxxx

例如:
添加令牌 723220342,123456789,kmgyypzreycVTAGbiT6iBQDoQv9iq1WKnfyqiPTX

添加时为了证实有效性内部将会使用一次作为验证
        '''.strip())


class Genshin_Cookies():
    def __init__(self):
        self.db = init_db('player_info/data', 'group_cookie.sqlite')

    async def raw_text_add_group(self, raw_text):
        if not raw_text or raw_text in ['?', '？']:
            raise HelpMessage()

        add_info = raw_text.split(',')
        if not add_info or len(add_info) != 3:
            raise HelpMessage()

        group_id, account_id, cookie_token = tuple(add_info)
        if not any([group_id.isdigit(), account_id.isdigit()]):
            raise Message('群号或者令牌ID错误')

        group_info = await get_group_info(group_id)
        if not group_info:
            raise Message('添加失败, 尚未加入该群')

        raw_cookie = f'account_id={account_id}; cookie_token={cookie_token};'

        # 验证cookie可用性
        try:
            await query.request_data(uid='105293904', user_cookie=raw_cookie)
        except Exception as e:
            raise Message('(%s) 验证失败: %s' % (account_id, str(e)))

        group_cookies = set(self.db.get(group_id, []))
        group_cookies.add(raw_cookie)
        self.db[group_id] = list(group_cookies)
        msg = f'群: {group_info.group_name}({group_id})添加成功~\n'
        msg += f'当前已有{len(group_cookies)}个账号,每天有额外查询{len(group_cookies) * 30}次'
        raise Message(msg)