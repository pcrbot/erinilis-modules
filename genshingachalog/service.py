from quart import request, session, redirect, Blueprint
import urllib.parse
from . import util

switcher = Blueprint('switcher', __name__)

config = util.get_config()
db = util.init_db(config.cache_dir)


@switcher.route('/genshin/gachalog/bind', methods=['GET', 'POST'])
async def bind():
    if request.method == "GET":

        qq: str = request.args['qq']
        authkey = request.args['authkey']
        region = request.args.get('region')
        if not qq or not qq.isdigit():
            return 'qq格式错误'
        if not authkey:
            return '参数错误'
        info = db.get(qq, {})
        info['authkey'] = urllib.parse.unquote(authkey)
        info['region'] = region or 'cn_gf01'
        db[qq] = info
    print(f'%s %s 成功绑定原神卡池记录' % (region, qq))
    return '绑定成功'
