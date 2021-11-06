import math
from PIL import Image, ImageDraw, ImageFont, ImageOps
from hoshino import aiorequests
from io import BytesIO
from .util import get_font, pil2b64


async def get_pic(url, size=None, *args, **kwargs) -> Image:
    """
    从网络获取图片，格式化为RGBA格式的指定尺寸
    """
    resp = await aiorequests.get(url, stream=True, *args, **kwargs)
    if resp.status_code != 200:
        return None
    pic = Image.open(BytesIO(await resp.content))
    pic = pic.convert("RGBA")
    if size is not None:
        pic = pic.resize(size, Image.LANCZOS)
    return pic


def easy_paste(im: Image, im_paste: Image, pos=(0, 0), direction="lt"):
    """
    inplace method
    快速粘贴, 自动获取被粘贴图像的坐标。
    pos应当是粘贴点坐标，direction指定粘贴点方位，例如lt为左上
    """
    x, y = pos
    size_x, size_y = im_paste.size
    if "d" in direction:
        y = y - size_y
    if "r" in direction:
        x = x - size_x
    if "c" in direction:
        x = x - int(0.5 * size_x)
        y = y - int(0.5 * size_y)
    im.paste(im_paste, (x, y, x + size_x, y + size_y), im_paste)


def easy_alpha_composite(im: Image,
                         im_paste: Image,
                         pos=(0, 0),
                         direction="lt") -> Image:
    '''
    透明图像快速粘贴
    '''
    base = Image.new("RGBA", im.size)
    easy_paste(base, im_paste, pos, direction)
    base = Image.alpha_composite(im, base)
    return base


def draw_text_by_line(img,
                      pos,
                      text,
                      font,
                      fill,
                      max_length,
                      center=False,
                      line_space=None):
    """
    在图片上写长段文字, 自动换行
    max_length单行最大长度, 单位像素
    line_space  行间距, 单位像素, 默认是字体高度的0.3倍
    """
    x, y = pos
    _, h = font.getsize("X")
    if line_space is None:
        y_add = math.ceil(1.3 * h)
    else:
        y_add = math.ceil(h + line_space)
    draw = ImageDraw.Draw(img)
    row = ""  # 存储本行文字
    length = 0  # 记录本行长度
    for character in text:
        w, h = font.getsize(character)  # 获取当前字符的宽度
        if length + w * 2 <= max_length:
            row += character
            length += w
        else:
            row += character
            if center:
                font_size = font.getsize(row)
                x = math.ceil((img.size[0] - font_size[0]) / 2)
            draw.text((x, y), row, font=font, fill=fill)
            row = ""
            length = 0
            y += y_add
    if row != "":
        if center:
            font_size = font.getsize(row)
            x = math.ceil((img.size[0] - font_size[0]) / 2)
        draw.text((x, y), row, font=font, fill=fill)


def image_array(canvas, image_list, col, space=0, top=0):
    '''
    循环贴图到画布

    canvas：画布

    image_list：图片列表，应大小一致

    col：竖列数量

    space：图片间距

    top：顶部间距
    '''
    num = list(range(len(image_list)))
    column = 0
    x = 0
    y = 0
    for i, image in zip(num, image_list):
        i += 1
        rows = math.ceil(i / col) - 1
        x = column * (image.size[0] + space)
        y = top + rows * (image.size[1] + space)
        column += 1
        if column == col:
            column = 0
        if i == len(image_list):
            x = col * (image.size[0] + space) - space
            y += image.size[1]
    list_canvas = Image.new('RGBA', (x, y), (255, 255, 255, 0))
    column = 0
    for i, image in zip(num, image_list):
        i += 1
        rows = math.ceil(i / col) - 1
        x = column * (image.size[0] + space)
        y = top + rows * (image.size[1] + space)
        column += 1
        easy_paste(list_canvas, image, (x, y))
        if column == col:
            column = 0
    easy_paste(canvas, list_canvas, (math.ceil(
        (canvas.size[0] - list_canvas.size[0]) / 2), 0))
    return canvas

w65 = get_font(26, w=65)

def get_duanluo(text):
    txt = Image.new('RGBA', (600, 800), (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt)
    # 所有文字的段落
    duanluo = ""
    max_width = 1080
    # 宽度总和
    sum_width = 0
    # 几行
    line_count = 1
    # 行高
    line_height = 0
    for char in text:
        width, height = draw.textsize(char, w65)
        sum_width += width
        if sum_width > max_width: # 超过预设宽度就修改段落 以及当前行数
            line_count += 1
            sum_width = 0
            duanluo += '\n'
        duanluo += char
        line_height = max(height, line_height)
    if not duanluo.endswith('\n'):
        duanluo += '\n'
    return duanluo, line_height, line_count

def split_text(content):
    # 按规定宽度分组
    max_line_height, total_lines = 0, 0
    allText = []
    for text in content.split('\n'):
        duanluo, line_height, line_count = get_duanluo(text)
        max_line_height = max(line_height, max_line_height)
        total_lines += line_count
        allText.append((duanluo, line_count))
    line_height = max_line_height
    total_height = total_lines * line_height
    drow_height = total_lines * line_height
    return allText, total_height, line_height, drow_height

async def text_image(raw_str: str):
    drow_height = 0
    msg_list = raw_str.split('\n')
    for msg in msg_list:
        if msg.strip().endswith(('jpg', 'png')):
            img = await get_pic(msg.strip())
            img_height = img.size[1]
            if img.width > 1080:
                img_height = int(img.height * 0.6)
            drow_height += img_height + 40
        else:
            x_drow_duanluo, x_drow_note_height, x_drow_line_height, x_drow_height = split_text(msg)
            drow_height += x_drow_height
            
    im = Image.new("RGB", (1080, drow_height), '#f9f6f2')
    draw = ImageDraw.Draw(im)
    # 左上角开始
    x, y = 0, 0
    for msg in msg_list:
        if msg.strip().endswith(('jpg', 'png')):
            img = await get_pic(msg.strip())
            if img.width > im.width:
                img = img.resize((int(img.width * 0.6), int(img.height * 0.6)))
            easy_paste(im, img, (0, y))
            y += img.size[1] + 40
        else:
            drow_duanluo, drow_note_height, drow_line_height, drow_height = split_text(msg)
            for duanluo, line_count in drow_duanluo:
                draw.text((x, y), duanluo, fill=(0, 0, 0), font=w65)
                y += drow_line_height * line_count
                
    _x, _y = w65.getsize("囗")
    padding = (_x, _y, _x, _y)
    im = ImageOps.expand(im, padding, '#f9f6f2')

    return pil2b64(im)