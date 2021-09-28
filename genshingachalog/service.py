from quart import request, session, redirect, Blueprint, send_file
import urllib.parse
from pathlib import Path
from . import util
from .verify_user import is_in_group

switcher = Blueprint('genshin_gacha_log', __name__)

config = util.get_config()
db = util.init_db(config.cache_dir)
xlsx_out_dir = Path(util.get_path(config.xlsx_dir, 'gachaExport'))


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
        if not await is_in_group(int(qq)):
            return '这QQ不存在机器人qq群内'

        info = db.get(qq, {})
        info['authkey'] = urllib.parse.unquote(authkey)
        info['region'] = region or 'cn_gf01'
        db[qq] = info
    print(f'%s %s 成功绑定原神卡池记录' % (region, qq))
    return '绑定成功'


@switcher.route('/genshin/gachalog/xlsx/<uid>', methods=['GET'])
async def get_xlsx(uid: str):
    if not uid.isdigit():
        return "uid error", 404
    if not xlsx_out_dir.exists():
        return "no xlsx directory", 404
    filename = uid + '.xlsx'
    if not (xlsx_out_dir / filename).exists():
        return "Invalid file", 404
    response = await send_file(str(xlsx_out_dir / filename))
    response.headers.add('Cache-Control', 'no-cache')
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
