class MFP {
    constructor(daily_target_cals) {
        this.daily_target_cals = daily_target_cals;

        this.diary_available = $.Deferred();
        var self = this;
        $.ajax({
            url: "/mfp/stats",
            cache: false,
            type: 'get',
            dataType: 'json',
            success: function(diary) {
                self.diary = diary;
                self.aggregated_stats = self._aggregate_mfp_diary(diary);

                var days = [];
                for (var d in diary) days.push(d);
                self.diary_days = days.sort();

                self.diary_available.resolve();
            },
        });

    }

    _aggregate_mfp_diary(diary) {
        var stats = {
                daily_target_cals: this.daily_target_cals,
                period_day_count: 0,
                period_exercise_days: 0,
                period_exercise_time: 0,
                period_total_cals: 0,
        }

        $.each(diary, function(day, log) {
            stats.period_day_count += 1;
            stats.period_total_cals += log.calories;
            if (log.exercise_minutes > 0) {
                stats.period_exercise_days += 1;
                stats.period_exercise_time += log.exercise_minutes;
            }
        });

        stats.daily_average_cals = Math.ceil(stats.period_total_cals / stats.period_day_count);
        stats.period_target_cals = stats.daily_target_cals * stats.period_day_count;
        stats.period_target_cals_pct = Math.ceil(100 * stats.period_total_cals / stats.period_target_cals);

        stats.recommendation = "";
        if (stats.period_target_cals_pct > 105) stats.recommendation = "eat less";
        if (stats.period_target_cals_pct <  80) stats.recommendation = "eat more";

        return stats;
    }

    create_ui(element_selector) {
        var self = this;
        $.when(self.diary_available).then(function() {
            var renderer = Handlebars.templates["mfp_eatmeter.html"];

            var exercise_days = [];
            for (var day of self.diary_days) {
                var log = self.diary[day];
                exercise_days.push({day: day.substr(5),
                                    minutes: log.exercise_minutes,
                                    activity: (log.exercise_minutes!=0)})
            }

            var ctx = {
                stats: self.aggregated_stats,
                exercise_days: exercise_days,
                // Adjusted so that the target is around the center
                ui_period_cals_pct: self.aggregated_stats.period_target_cals_pct - 50,
            };
            $(element_selector).html(renderer(ctx));
        });
    }

    plot_diary(dygraph_element_id) {
        var self = this;
        $.when(self.diary_available).then(function() {
            DumHouse_plot_mfp_diary(dygraph_element_id, self.diary_days,
                                        self.daily_target_cals, self.diary);
        });
    }
}

