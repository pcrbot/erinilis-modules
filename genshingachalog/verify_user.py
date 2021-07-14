import datetime
from nonebot import get_bot
from .util import cache

bot = get_bot()


@cache(ttl=datetime.timedelta(minutes=1))
async def get_all_member_list():
    group_data = {}
    for self_id in bot._wsr_api_clients.keys():
        group = await bot.get_group_list(self_id=self_id)

        for group_info in group:
            group_id = group_info['group_id']
            member_list = await bot.get_group_member_list(group_id=group_id, self_id=self_id)
            group_data[group_id] = [i['user_id'] for i in member_list]
    return sum(list(group_data.values()), [])


async def is_in_group(user: int):
    """
    检验用户qq号是否在bot的群组内
    @param user: qq号
    """
    return user in await get_all_member_list()
