import os
import xlsxwriter
from . import util

config = util.get_config()

gacha_type = [
    {
        "id": "4",
        "key": "200",
        "name": "常驻祈愿"
    },
    {
        "id": "14",
        "key": "100",
        "name": "新手祈愿"
    },
    {
        "id": "15",
        "key": "301",
        "name": "角色活动祈愿"
    },
    {
        "id": "16",
        "key": "302",
        "name": "武器活动祈愿"
    }
]

out_dir = util.get_path(config.xlsx_dir, 'gachaExport')
if not os.path.exists(out_dir):
    os.makedirs(out_dir)


async def write_xlsx(data):
    gachaTypes = gacha_type
    gacha_type_ids = [banner["key"] for banner in gachaTypes]
    gachaTypeNames = [key["name"] for key in gachaTypes]
    gachaTypeDict = dict(zip(gacha_type_ids, gachaTypeNames))
    player_uid = data['301'][0]['uid']

    workbook = xlsxwriter.Workbook(os.path.join(out_dir, f'{player_uid}.xlsx'))
    for _id in gacha_type_ids:
        gachaDictList = data.get(_id, [])
        gachaTypeName = gachaTypeDict[_id]
        gachaDictList.reverse()
        header = "时间,名称,类别,星级,总次数,保底内"
        worksheet = workbook.add_worksheet(gachaTypeName)
        content_css = workbook.add_format(
            {"align": "left", "font_name": "微软雅黑", "border_color": "#c4c2bf", "bg_color": "#ebebeb", "border": 1})
        title_css = workbook.add_format(
            {"align": "left", "font_name": "微软雅黑", "color": "#757575", "bg_color": "#dbd7d3", "border_color": "#c4c2bf",
             "border": 1, "bold": True})
        excel_col = ["A", "B", "C", "D", "E", "F"]
        excel_header = header.split(",")
        worksheet.set_column("A:A", 22)
        worksheet.set_column("B:B", 14)
        for i in range(len(excel_col)):
            worksheet.write(f"{excel_col[i]}1", excel_header[i], title_css)
        worksheet.freeze_panes(1, 0)
        idx = 0
        pdx = 0
        i = 0
        for gacha in gachaDictList:
            time = gacha["time"]
            name = gacha["name"]
            item_type = gacha["item_type"]
            rank_type = gacha["rank_type"]
            idx = idx + 1
            pdx = pdx + 1
            excel_data: list = [time, name, item_type, rank_type, idx, pdx]
            excel_data[3] = int(excel_data[3])
            for j in range(len(excel_col)):
                worksheet.write(f"{excel_col[j]}{i + 2}", excel_data[j], content_css)
            if excel_data[3] == 5:
                pdx = 0
            i += 1

        star_5 = workbook.add_format({"color": "#bd6932", "bold": True})
        star_4 = workbook.add_format({"color": "#a256e1", "bold": True})
        star_3 = workbook.add_format({"color": "#8e8e8e"})
        worksheet.conditional_format(f"A2:F{len(gachaDictList) + 1}",
                                     {"type": "formula", "criteria": "=$D2=5", "format": star_5})
        worksheet.conditional_format(f"A2:F{len(gachaDictList) + 1}",
                                     {"type": "formula", "criteria": "=$D2=4", "format": star_4})
        worksheet.conditional_format(f"A2:F{len(gachaDictList) + 1}",
                                     {"type": "formula", "criteria": "=$D2=3", "format": star_3})

    workbook.close()
