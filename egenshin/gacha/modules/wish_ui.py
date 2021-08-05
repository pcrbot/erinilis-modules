import json
import copy
from pathlib import Path
from PIL import Image, PngImagePlugin
from ...util import filter_list, pil2b64

assets_dir = Path(__file__).parent.parent.parent / 'assets' / 'gacha'

with open(assets_dir / 'type.json', 'r', encoding="utf-8") as fp:
    type_json = json.load(fp)

cache_img = {}
cache_item = {}


class wish_ui:
    data: list
    img: PngImagePlugin.PngImageFile

    def __init__(self, wish_result):
        self.data = isinstance(wish_result, list) and wish_result or [wish_result]
        self.sort_data()
        self.img = wish_ui.get_assets('background.png')

    def sort_data(self):
        new = sorted(self.data, key=lambda x: x.rank, reverse=True)
        c = filter_list(new, lambda x: x.data.item_type == '角色')
        w = filter_list(new, lambda x: x.data.item_type == '武器')
        self.data = c + w

    @staticmethod
    def get_assets(path) -> PngImagePlugin.PngImageFile:
        base_path = assets_dir

        cache = cache_img.get(path)
        if cache:
            return copy.deepcopy(cache)
        else:
            cache_img[path] = Image.open(str(base_path / path))
        return wish_ui.get_assets(path)

    @staticmethod
    def item_bg(rank):
        return wish_ui.get_assets('%s_background.png' % str(rank)).resize((143, 845))

    @staticmethod
    def rank_icon(rank):
        return wish_ui.get_assets('%s_star.png' % str(rank))

    @staticmethod
    async def create_item(rank, item_type, name, element):
        if cache_item.get(name):
            return cache_item[name]
        bg = wish_ui.item_bg(rank)
        item_img = wish_ui.get_assets(Path(item_type) / (name + '.png'))
        rank_img = wish_ui.rank_icon(rank).resize((119, 30))

        if item_type == '角色':
            item_img = item_img.resize((item_img.size[0] + 12, item_img.size[1] + 45))
            item_img.alpha_composite(rank_img, (4, 510))

            item_type_icon = wish_ui.get_assets(Path('元素') / (element + '.png')).resize((80, 80))
            item_img.alpha_composite(item_type_icon, (18, 420))
            bg.alpha_composite(item_img, (3, 125))

        else:
            bg.alpha_composite(item_img, (3, 240))
            bg.alpha_composite(rank_img, (9, 635))

            item_type_icon = type_json.get(name)
            if item_type_icon:
                item_type_icon = wish_ui.get_assets(Path('类型') / (item_type_icon + '.png')).resize((100, 100))

                bg.alpha_composite(item_type_icon, (18, 530))
        cache_item[name] = bg
        return bg

    async def ten(self) -> PngImagePlugin.PngImageFile:
        i = 0
        for wish in self.data:
            i += 1
            rank = wish.rank
            name = wish.data.item_name
            item_type = wish.data.item_type
            element = wish.data.get('item_attr') or type_json[name]
            i_img = await wish_ui.create_item(rank, item_type, name, element)
            self.img.alpha_composite(i_img, (105 + (i_img.size[0] * i), 123))
        self.img.thumbnail((1024, 768))

        img = Image.new("RGB", self.img.size, (255, 255, 255))
        img.paste(self.img, mask=self.img.split()[3])
        return img

    @classmethod
    async def ten_b64_img(cls, wish_result):  # 十连抽
        return pil2b64(await cls(wish_result).ten())

    @classmethod
    async def ten_b64_img_xn(cls, wish_result_xn):
        img = Image.new("RGB", (1024, 575 * len(wish_result_xn)), (255, 255, 255))
        for index, wish_result in enumerate(wish_result_xn):
            item_img = await cls(wish_result).ten()
            img.paste(item_img, (0, 575 * index))

        return pil2b64(img)
