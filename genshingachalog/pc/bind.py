import os
import re
import yaml
import winreg
import ctypes
import signal
import asyncio
import requests
import urllib.parse
import mitmproxy.http
from sys import exit
from pathlib import Path
from mitmproxy.options import Options
from mitmproxy.proxy.config import ProxyConfig
from mitmproxy.proxy.server import ProxyServer
from mitmproxy.tools.dump import DumpMaster


# 设定代理,enable:是否开启,proxyIp:代理服务器ip及端口,IgnoreIp:忽略代理的ip或网址
def set_proxy(enable, proxyIp, IgnoreIp):
    xpath = "Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    INTERNET_OPTION_REFRESH = 37
    INTERNET_OPTION_SETTINGS_CHANGED = 39
    internet_set_option = ctypes.windll.Wininet.InternetSetOptionW
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, xpath, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, enable)
        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxyIp)
        winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, IgnoreIp)
        internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)
        internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
    except Exception as e:
        print("ERROR: " + str(e.args))


# 开启，定义代理服务器ip及端口，忽略ip内容(分号分割)
def enable_proxy():
    proxyIP = "127.0.0.1:%s" % config.proxy_port
    IgnoreIp = "172.*;192.*;"
    set_proxy(1, proxyIP, IgnoreIp)


# 关闭清空代理
def disable_proxy():
    set_proxy(0, "", "")


class Dict(dict):
    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, attr, value):
        self[attr] = value


def dict_to_object(dict_obj):
    if not isinstance(dict_obj, dict):
        return dict_obj
    inst = Dict()
    for k, v in dict_obj.items():
        inst[k] = dict_to_object(v)
    return inst


def get_config():
    try:
        file = open(os.path.join(os.path.dirname(__file__), "config.yml"), 'r', encoding="utf-8")
        return dict_to_object(yaml.load(file.read(), Loader=yaml.FullLoader))
    except FileNotFoundError:
        return {}


def input_num(msg: str):
    num = input(msg)
    if not num.isdigit():
        print('只能输入数字')
        return input_num(msg)
    return num


def handle_bind(url):
    if not url:
        return
    print('正在发送数据到服务器绑定.')
    qs = urllib.parse.parse_qs(url)
    if not qs.get('authkey'):
        print('参数错误. 请重新获取')
        exit()
    authkey = qs['authkey'][0]
    region = qs['region'][0]
    server = f'http://{config.server}/genshin/gachalog/bind'
    res = requests.get(f'{server}?region={region}&qq={qq}&authkey={urllib.parse.quote(authkey)}', timeout=30).text
    print(res)
    # m.shutdown()
    print('可以关闭软件了, 如果网页打不开请重新打开软件使用 2.清除代理')
    # disable_proxy()
    input()


class Addon(object):
    success = False

    def __init__(self):
        pass

    def request(self, flow: mitmproxy.http.HTTPFlow):
        if "mihoyo.com/event/gacha_info/api/getGachaLog" in flow.request.url:
            handle_bind(flow.request.url)
            self.success = True
        elif not self.success:
            print('正在寻找数据中...')

    def response(self, flow: mitmproxy.http.HTTPFlow):
        if "mihoyo.com/event/gacha_info/api/getGachaLog" in flow.request.url:
            pass
        if "webstatic.mihoyo.com/hk4e/event/e20190909gacha/index.html" in flow.request.url:
            flow.response.set_text('''
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><link href="1_c6b5f724d77058182555.css" rel="stylesheet"><link href="bundle_a9a7016b97405af09682.css" rel="stylesheet"></head>
<body>
  <div>
    <div align="center" vertical-align="middle"><h1>绑定成功,可以关闭绑定软件了, 同时也可以到群内使用卡池查询功能!</h1></div>
  </div>
  <div id="frame" style="display:none">
    <div id="content"></div>
  </div>
  <script id="vconsole" type="text/javascript" data-src="https://webstatic.mihoyo.com/dora/lib/vconsole/3.2.0/vconsole.min.js"></script>
  <script type="text/javascript" src="vendors_079608b5a9e913c8e1fe.js"></script><script type="text/javascript" src="bundle_536bfc3fc05fa0ec9790.js"></script>
</body>
</html>
            ''')


def from_log_file():
    log_file = Path(os.getenv('LOCALAPPDATA') + 'Low') / 'miHoYo' / '原神' / 'output_log.txt'
    if not log_file.exists():
        print('错误.找不到本地日志文件')
        os.system('pause')
        exit()
    with log_file.open() as f:
        log = f.read()
    url = re.search(r'.+gacha/index.html?(.+)', log)
    if not url:
        print('请在游戏内先F3打开抽卡页面后,点击下面的历史记录后在继续')
        os.system('pause')
        from_log_file()
    handle_bind(url.group(1))


def menu():
    print('1.绑定原神卡池记录')
    print('2.清除代理(上不了网使用这个)')
    print('3.从本地日志获取(作用同1,不同的是不需要对网络进行代理)')

    return input_num('选择一个来执行:')


if __name__ == "__main__":
    config = get_config()
    config.setdefault('select', 0)
    config.setdefault('QQ', 0)
    config.setdefault('server', '')  # 如果作为单独的程序不需要配置文件可以直接把服务器地址填到这里
    config.setdefault('proxy_port', 6454)
    config = dict_to_object(config)
    if not config.server:
        print('请在配置文件设置服务器地址')
        exit()
    select = config.select
    if not select:
        select = menu()

    if str(select) == '1':
        print('此程序仅设置Internet局域网代理 可能会被拦截,请允许.')
        print('不要启动加速器或者其它代理程序.')
        qq = config.QQ
        if not qq:
            qq = input_num('输入一个QQ号进行绑定:')

        print('正在设置代理..')

        enable_proxy()
        options = Options(listen_host="0.0.0.0", listen_port=config.proxy_port, http2=True)
        m = DumpMaster(options, with_termlog=False, with_dumper=False)
        m.server = ProxyServer(ProxyConfig(options))
        m.addons.add(Addon())

        try:
            loop = asyncio.get_event_loop()
            try:
                loop.add_signal_handler(signal.SIGINT, getattr(m, "prompt_for_exit", m.shutdown))
                loop.add_signal_handler(signal.SIGTERM, m.shutdown)
            except NotImplementedError:
                pass


            async def wakeup():
                while True:
                    await asyncio.sleep(0.2)


            asyncio.ensure_future(wakeup())
            print('请打开原神的抽卡页面,点击历史记录,刷新或者翻页获取.')
            print('卡半天可以尝试到浏览器刷新一下页面 出现未信任连接即可到游戏内刷新.')
            print("等待链接刷新...")
            m.run()

        except (KeyboardInterrupt, RuntimeError):
            print("清除代理")
            disable_proxy()
            print("成功")
        except TypeError:
            pass

    if select == '2':
        disable_proxy()
        print('清除代理成功')
        os.system('pause')

    if select == '3':
        qq = config.QQ
        if not qq:
            qq = input_num('输入一个QQ号进行绑定:')
        from_log_file()
