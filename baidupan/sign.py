import requests
import time
import json

from . import util, api

config = util.get_config()


def __sign2__(j, r):
    a = list(range(256))
    p = list(range(256))
    o = []
    v = len(j)
    for q in range(0, 256):
        qv = q % v
        a[q] = ord(j[qv:qv + 1][0])
        p[q] = int(q)
    u = 0
    for q in range(0, 256):
        u = (u + p[q] + a[q]) % 256
        t = p[q]
        p[q] = p[u]
        p[u] = t
    i = u = 0
    for q in range(0, len(r)):
        i = (i + 1) % 256
        u = (u + p[i]) % 256
        t = p[i]
        p[i] = p[u]
        p[u] = t
        k = p[((p[i] + p[u]) % 256)]
        o.append(chr(ord(r[q]) ^ k))
    return o


def __sign2base64__(t):
    s = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    a = len(t)
    r = 0
    e = ""
    while a > r:
        o = 255 & ord(t[r])
        r += 1
        if r == a:
            e += s[o >> 2]
            e += s[(3 & o) << 4]
            e += "=="
            break
        n = ord(t[r])
        r += 1
        if r == a:
            e += s[o >> 2]
            e += s[(3 & o) << 4 | (240 & n) >> 4]
            e += s[(15 & n) << 2]
            e += "="
            break
        i = ord(t[r])
        r += 1
        e += s[o >> 2]
        e += s[(3 & o) << 4 | (240 & n) >> 4]
        e += s[(15 & n) << 2 | (192 & i) >> 6]
        e += s[63 & i]
    return e


sign = ''
timestamp = 0


def gen_sign():
    url = 'https://pan.baidu.com/api/gettemplatevariable?app_id=250528&channel=chunlei&clienttype=0&fields=[%22sign1%22,%22sign2%22,%22sign3%22,%22timestamp%22]&web=1'
    text = requests.get(url, headers=api.get_randsk_headers(), timeout=30).text
    info = json.loads(text[3:])

    if not info['errno'] == 0:
        return False, 0
    global sign, timestamp

    result = util.dict_to_object(info['result'])
    sign = __sign2__(result.sign3, result.sign1)
    sign = __sign2base64__(''.join([str(i) for i in sign]))
    timestamp = result.timestamp
    return sign, timestamp


def get_sign():
    if timestamp + config.rules.sign_cache_time * 60 * 60 < time.time() or timestamp == 0:
        print('刷新sign')
        return gen_sign()
    return sign, timestamp
