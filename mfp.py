import myfitnesspal
import datetime
from collections import namedtuple
import shelve

MFP_Stats = namedtuple('MFP_Stats', 'calories_consumed weight exercise_minutes')

import logging
logger = logging.getLogger('BatHome')

class MFP_Crawler(object):
    def __init__(self, local_cache_fname, prev_days, usr, pwd):
        self.local_cache_fname = local_cache_fname
        self.prev_days = prev_days
        self.stats = self._get_stats(usr, pwd)

    @staticmethod
    def _get_mfp_prev_dates(n):
        def getdate(prev_day_n):
            return datetime.date.today() + datetime.timedelta(days=-prev_day_n)
        # Range 1 -> skip today's date
        return [getdate(x) for x in range(1, n)]
    
    @staticmethod
    def _get_exercise_time(mfp_day):
        ex_time = 0
        for ex_type in mfp_day.exercises:
            for ex_entry in ex_type:
                ex_info = ex_entry.nutrition_information
                ex_time += ex_info['minutes']
        return ex_time

    def _get_mfp_day(self, mfp, day):
        logger.info("Reading MyFitnessPal day {}. This is a slow operation.".format(day))
        try:
            w = mfp.get_measurements('Weight', day)[day]
        except KeyError:
            w = None

        day_log = mfp.get_date(day)
        cals = day_log.totals['calories']
        ex = self._get_exercise_time(day_log)
        return MFP_Stats(weight=w, calories_consumed=cals, exercise_minutes=ex)

    def _get_stats(self, usr, pwd):
        cache = shelve.open(self.local_cache_fname)
        stats = {}
        mfp = None

        for day in self._get_mfp_prev_dates(self.prev_days):
            try:
                stats[day] = cache['mfp{}'.format(str(day))]
            except KeyError:
                if mfp is None:
                    mfp = myfitnesspal.Client(usr, pwd)
                stats[day] = self._get_mfp_day(mfp, day)
                cache['mfp{}'.format(str(day))] = stats[day] 

        cache.close()
        return stats

