import myfitnesspal

import json
import datetime
import shelve
import threading
from collections import namedtuple, OrderedDict

MFP_Stats = namedtuple('MFP_Stats', 'calories_consumed weight exercise_minutes')

import logging
logger = logging.getLogger('BatHome')

class MFP_Crawler(object):
    def __init__(self, flask_app, local_cache_fname, usr, pwd,
                    prev_days, ignore_cache_day_count=2):
        """ ignore_cache_day_count -> previous days to ignore from cache. Eg: if
        ignore_cache_day_count = 2 then the last 2 days will always be read from MFP,
        even if they are cached. Useful in case the last few days get updated """
        self.local_cache_fname = local_cache_fname
        self.usr = usr
        self.pwd = pwd
        self.ignore_cache_day_count = ignore_cache_day_count
        self.default_update_days = prev_days

        self._startup_thread = threading.Thread(target=self.update_stats)
        self._startup_thread.start()

        @flask_app.route('/mfp/stats')
        def flask_mfp_stats():
            return json.dumps(self.json_stats())

        @flask_app.route('/mfp/refresh')
        @flask_app.route('/mfp/refresh/<days>days')
        def flask_mfp_update_stats(days=None):
            if days is None:
                days = self.default_update_days
            self.update_stats(int(days))
            return "OK"

    def update_stats(self, prev_days=None):
        if prev_days is None:
            prev_days = self.default_update_days

        self._stats = self._get_stats(self.ignore_cache_day_count, prev_days)

    def stats(self):
        if self._startup_thread is not None:
            self._startup_thread.join()
            self._startup_thread = None

        return self._stats

    def json_stats(self):
        stats = self.stats()
        js = {}
        for day in stats:
            js[str(day)] = {'calories': stats[day].calories_consumed,
                            'weight': stats[day].weight,
                            'exercise_minutes': stats[day].exercise_minutes}
        return js

    @staticmethod
    def _get_mfp_prev_dates(n):
        def getdate(prev_day_n):
            return datetime.date.today() + datetime.timedelta(days=-prev_day_n)
        # Range is open interval -> skip today's date
        return [getdate(x) for x in range(n, 0, -1)]
    
    @staticmethod
    def _get_exercise_time(mfp_day):
        ex_time = 0
        for ex_type in mfp_day.exercises:
            for ex_entry in ex_type:
                ex_info = ex_entry.nutrition_information
                ex_time += ex_info['minutes']
        return ex_time

    def _get_mfp_day(self, mfp, day):
        logger.info("Reading MyFitnessPal day {} from API. This is a slow operation.".format(day))
        try:
            w = mfp.get_measurements('Weight', day)[day]
        except KeyError:
            w = None

        day_log = mfp.get_date(day)
        cals = day_log.totals['calories']
        ex = self._get_exercise_time(day_log)
        return MFP_Stats(weight=w, calories_consumed=cals, exercise_minutes=ex)

    def _get_stats(self, ignore_cache_day_count, days):
        cache = shelve.open(self.local_cache_fname)
        stats = OrderedDict()
        mfp = None

        for day in self._get_mfp_prev_dates(days):
            day_key = 'mfp{}'.format(str(day))
            if (datetime.date.today() - day).days > self.ignore_cache_day_count \
                        and cache.get(day_key) is not None:
                stats[day] = cache[day_key]
            else:
                if mfp is None:
                    mfp = myfitnesspal.Client(self.usr, self.pwd)
                stats[day] = self._get_mfp_day(mfp, day)
                cache[day_key] = stats[day] 

        cache.close()
        return stats

