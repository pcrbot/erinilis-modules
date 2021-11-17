class Error_Message(Exception):
    def __init__(self, message=''):
        self.message = message

    def __repr__(self):
        return self.message

class Cookie_Error(Error_Message):
    def __repr__(self):
        t = '''
* 这个插件需要获取账号cookie, 外泄有可能导致您的账号遭受损失, 请注意相关事项再进行绑定, 造成一切损失由用户自行承担
* 修改密码可以直接使其失效

0. 确保ys#的是自己的uid
1. 打开米游社(https://bbs.mihoyo.com/ys/)
2. 登录游戏账号
3. F12打开控制台
4. 输入以下代码运行
javascript:(()=>{_=(n)=>{for(i in(r=document.cookie.split(";"))){var arr=r[i].split("=");if(arr[0].trim()==n)return arr[1];}};c=_("cookie_token")||alert('请重新登录');m=_("account_id")+","+c;c&&confirm('确定复制到剪切板?:'+m)&&copy(m)})();
5. 复制提示的内容, 私聊发给机器人
私聊格式为

yss绑定0000000,xxxxxxxxxxxx

其中0000000,xxxxxxxxxxxx是复制的内容

如果你想查看另外个方法可以发送 yss?2
* 同时兼容手机端
        '''
        return t.rstrip()

class Cookie_Error_tampermonkey(Error_Message):
    def __repr__(self):
        t = '''
如果你是PC端,浏览器需要安装tampermonkey插件(https://www.tampermonkey.net/)
如果你是手机端,可以下载油猴浏览器(http://www.youhouzi.cn/),并且在右下角打开菜单 [打开电脑模式] ,之后在[脚本管理]->[启用脚本功能]

然后打开链接安装脚本 https://greasyfork.org/scripts/435553-%E7%B1%B3%E6%B8%B8%E7%A4%BEcookie/code/%E7%B1%B3%E6%B8%B8%E7%A4%BEcookie.user.js

就可以访问米游社进行登录了
提示复制的内容可以直接私聊发给机器人

私聊格式为

yss绑定0000000,xxxxxxxxxxxx

其中0000000,xxxxxxxxxxxx是复制的内容
        '''
        return t.rstrip()

class Login_Error(Error_Message):
    pass