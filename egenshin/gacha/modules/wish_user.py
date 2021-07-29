from ...util import init_db, get_config

config = get_config()
DB = init_db(config.cache_dir, 'gacha.sqlite')


class wish_user:
    def __init__(self, uid, gacha_type):
        self.uid = uid
        self.gacha_type = gacha_type
        self._get_data()

    @property
    def count_5(self) -> int:
        return self.get_prob_info().get('count_5', 1)

    @property
    def count_4(self) -> int:
        return self.get_prob_info().get('count_4', 1)

    @count_5.setter
    def count_5(self, count):
        self.update_prob_info({'count_5': count})

    @count_4.setter
    def count_4(self, count):
        self.update_prob_info({'count_4': count})

    @property
    def is_up(self):
        return self.get_prob_info().get('is_up', False)

    @is_up.setter
    def is_up(self, up):
        self.update_prob_info({'is_up': up})

    def inc_count(self, rank):
        key = 'count_' + str(rank)
        inc = self.get_prob_info().get(key, 1)
        self.update_prob_info({key: inc + 1})

    def _get_data(self):
        self.data = DB.get('%s_%s' % (self.uid, self.gacha_type), {})

    def save(self):
        DB['%s_%s' % (self.uid, self.gacha_type)] = self.data

    def get_prob_info(self):
        self._get_data()
        return self.data.get('prob_info', {})

    def set_prob_info(self, obj):
        if self.data.get('prob_info'):
            self.data['prob_info'].update(obj)
        else:
            self.data['prob_info'] = obj

    def update_prob_info(self, obj):
        prob_info = self.get_prob_info()
        prob_info.update(obj)
        self.set_prob_info(prob_info)
        self.save()
