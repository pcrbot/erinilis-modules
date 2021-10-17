class Error_Message(Exception):
    def __init__(self, message=''):
        self.message = message

    def __repr__(self):
        return self.message

class Cookie_Error(Error_Message):
    def __repr__(self):
        t = '''
* 注意, 这个插件需要获取账号的令牌, 谨慎授权

1. 打开米游社(https://bbs.mihoyo.com/ys/)
2. 登录游戏账号
3. F12打开控制台
4. 输入以下代码运行
javascript:(()=>{_=(name)=>{for(i in(r=document.cookie.split("; "))){arr=r[i].split("=");if(arr[0]==name)return arr[1]}};alert(_("account_id")+","+_("cookie_token"))})();
5. 复制提示的内容, 私聊发给机器人
私聊格式为

原神便笺绑定xxxxxxxxxxxxxx

其中xxxxxxxxxxxxxx是复制的内容
        '''
        return t.rstrip()


class Login_Error(Error_Message):
    pass