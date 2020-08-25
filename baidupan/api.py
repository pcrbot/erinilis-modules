import requests
import hashlib
import json
import re
from urllib import parse
from nonebot.log import logger
from . import util, share, sign, dupan_link

config = util.get_config()


def get_randsk_headers(randsk=None):
    randsk = f'; BDCLND={randsk}' if randsk else ''
    return {
        'Referer': 'https://pan.baidu.com/disk/home?',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.514.1919.810 Safari/537.36',
        'Cookie': f'BDUSS={config.BDUSS}; STOKEN={config.STOKEN}{randsk}'
    }


# 保存秒传文件 文件md5值
def rapidupload(md5, md5s, size, file_name, dir_name='temp/'):
    url = f'https://pan.baidu.com/api/rapidupload?channel=chunlei&clienttype=0&web=1&app_id=250528&rtype=3'
    data = {
        'path': f'{dir_name}{file_name}',
        'content-md5': md5,
        'slice-md5': md5s,
        'content-length': str(size)
    }
    res = json.loads(requests.post(url, data=data, headers=get_randsk_headers(), timeout=30).text)
    if not res['errno'] == 0:
        return None
    return res['info']


# 根据下载链接获取秒传信息
def get_rapidupload_info(download_link):
    try:
        headers = {
            'user-agent': 'LogStatistic',
            'Cookie': f'BDUSS={config.BDUSS};',
            'Range': 'bytes=0-262143'
        }
        res = requests.get(download_link, headers=headers, timeout=30, allow_redirects=False)
        md5 = res.headers.get('Content-MD5').upper()
        md5s = hashlib.new('md5', res.content).hexdigest().upper()
        size = res.headers.get('x-bs-file-size')
        file_name = re.search(r'filename="(.+)"', res.headers.get('Content-Disposition')).group(1)
        file_name = file_name.encode('raw_unicode_escape').decode('utf-8')
        return md5, md5s, size, file_name
    except:
        return False


def get_real_url_by_dlink(dlink):
    headers = {
        'user-agent': 'LogStatistic',
        'Cookie': f'BDUSS={config.BDUSS};'
    }
    real_link = requests.get(dlink, headers=headers, timeout=30, allow_redirects=False)
    if not real_link.status_code == 302:
        return ''
    return real_link.headers.get('Location')


# 获取度盘内的文件真实下载地址
def get_file_url(fs_id: list):
    sign_str, timestamp = sign.get_sign()
    url = f'https://pan.baidu.com/api/download?type=dlink&channel=chunlei&web=1&app_id=250528&clienttype=0&' \
          f'sign={parse.quote(sign_str)}&timestamp={timestamp}&fidlist=%5B{",".join([str(i) for i in fs_id])}%5D'
    info = util.dict_to_object(json.loads(requests.get(url, headers=get_randsk_headers(), timeout=30).text))
    if not info.errno == 0:
        return []
    url = []
    for dl in info.dlink:
        url.append(get_real_url_by_dlink(dl['dlink']))
    return url


def get_share(keyword, pan_url: str, pwd=None, dir_str=None):
    if not pan_url:
        return '文件无法创建下载链接..'

    tk = '或'.join(config.comm.keyword)
    tip = f'指令格式(用{config.comm.split}分开): {tk}分享链接{config.comm.split}提取码\n'
    tip += f'{tk}https://pan.baidu.com/s/13XHATrvl0pQWx9x3zHjwIg{config.comm.split}6666\n'
    tip += f'支持秒传(PanDL/梦姬/游侠/PCS-Go)链接'
    file_r = dupan_link.parse(keyword)

    if file_r and keyword:
        msg = ''
        for info in file_r:
            is_ok = rapidupload(
                info.md5,
                info.md5s,
                info.size,
                info.name,
                dir_name=config.rules.dulink_temp_dir
            )
            if not is_ok:
                msg += f'{info.name} 获取失败啦\n'
                continue
            logger.info('秒传文件获取成功..')
            # 大于50M 需要分享后处理
            if int(info.size) > 52428800:
                logger.info('文件大于50M 分享后再获取.')
                return get_share('', share.set_share([is_ok['fs_id']]), pwd='erin')
            else:
                url = '\n'.join(get_file_url([is_ok['fs_id']]))
            if not url:
                msg += f'{info.name} 获取下载地址失败啦\n'
                continue
            msg += f'文件名: {info.name}\n'
            msg += f'大小: {util.size_format(int(info.size))}\n'
            msg += f'下载地址: {url}\n'
        return msg

    surl = share.get_surl(pan_url)
    if not surl:
        return f'链接格式不正确啦\n{tip}'

    surl = surl[1:]
    logger.info('网盘分享链接获取成功..')
    randsk = share.verify(surl, pwd)
    if not randsk:
        return f'啊这 提取码错误或者是文件失效\n{tip}'
    logger.info('网盘密码验证成功..')
    yun_data = share.get_yun_data(surl, randsk)
    file_list = share.get_file_list(yun_data.shareid, yun_data.uk, randsk, dir_str=dir_str)

    if not file_list.errno == 0:
        return '文件失效或者分享被取消'
    logger.info('分享列表获取成功..')
    msg = f'发送 {config.comm.help} 查看下载方法\n'

    return msg + share.handle_file_list(file_list, yun_data, randsk)
