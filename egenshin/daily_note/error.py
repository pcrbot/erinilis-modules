class Error_Message(Exception):
    def __init__(self, message=''):
        self.message = message

    def __repr__(self):
        return self.message

class Cookie_Error(Error_Message):
    def __repr__(self):
        t = '''
1. 打开米游社(https://bbs.mihoyo.com/ys/)
2. 登录游戏账号
3. F12打开控制台
4. 输入以下代码运行
javascript:(()=>{_=(n)=>document.cookie.match(`[;\s+]?${n}=([^;]*)`)?.pop();alert(_("account_id")+","+_("cookie_token"))})();
5. 复制提示的内容, 私聊发给机器人
私聊格式为

原神便笺绑定xxxxxxxxxxxxxx

其中xxxxxxxxxxxxxx是复制的内容
        '''
        return t.rstrip()


class Login_Error(Error_Message):
    pass