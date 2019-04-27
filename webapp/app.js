
// http://dygraphs.com/options.html
function dygraph_helper_horizontalLine(ctx, graph, y_val, color) {
  var xl = graph.toDomCoords(0,y_val);
  ctx.strokeStyle= color;
  ctx.beginPath();
  ctx.moveTo(xl[0],xl[1]);
  ctx.lineTo(9e22,xl[1]);
  ctx.closePath();
  ctx.stroke();      
}

class DumbHouseApp {
    constructor() {
        this.things_app = new ThingsApp("/ZMF/", "/ZMF/webapp/", [Lamp, MediaPlayer, MqttDeviceInfo]);
        this.is_ready = $.Deferred();
        this.baticueva_extras_tmpl_ready = $.Deferred();

        var self = this;
        $(document).ready(function(){
            $.when(self.things_app.is_ready).then(function() {
                $.when(self.baticueva_extras_tmpl_ready).then(function() {
                    self.media_players = self.things_app.get_things_of_type(MediaPlayer);
                    self.monkeypatch();
                    self.is_ready.resolve(); 
                });
            });
        });

        // Get Baticueva extras
        var self = this;
        $.ajax({
            url: "Baticueva_TV_extras.html",
            cache: true,
            type: 'get',
            dataType: 'html',
            success: function(tmpl) {
                if (!Handlebars || !Handlebars.registerHelper) {
                    console.error("Handlebars plugin not found");
                }

                self.render_baticueva_extras = Handlebars.compile(tmpl);
                self.baticueva_extras_tmpl_ready.resolve();
            }
        });
    }

    get_player(name) {
        for (var p of this.media_players) {
            if (p.name == name) return p; 
        }
    }

    monkeypatch() {
        var self = this;
        var patched_self = this.get_player('Baticueva TV');
        var patched_func = this.get_player('Baticueva TV').updateUI;
        this.get_player('Baticueva TV').updateUI = function() {
            self.before_baticueva_tv_shown();
            patched_func.apply(patched_self);
            self.on_baticueva_tv_shown();
        }
    }

    before_baticueva_tv_shown() {
        this.baticueva_extras_open = $('#Baticueva_TV_extras_div').is(':visible');
    }

    on_baticueva_tv_shown() {
        $('#media_player_Baticueva_TV_ctrl').append(this.render_baticueva_extras());
        if (this.baticueva_extras_open) $('#Baticueva_TV_extras_div').show();
    }

    invoke_action(url, cb) {
        $.ajax({
            url: url,
            cache: false,
            type: 'get',
            dataType: 'json',
            success: function(action_res) {
                if (cb) {
                    cb(action_res);
                } else {
                    console.log(url, " => ", action_res);
                }
            }
        });

        return false;
    }

    invoke_media_player_action(player_name, url) {
        var self = this;
        return this.invoke_action(url, function(res) {
                console.log(player_name, ".", url, " => ", action_res);
                // Try to trigger a UI update in a second
                // TODO: This doesn't actually work: updateUI only recreates the UI, doesn't fetch new state
                // A call to updateStatus would be smarter
                setTimeout(function(){ self.get_player(player_name).updateUI(); }, 2000);
        });
    }

    show_list_of_media_players(element_selector) {
        for (var thing of this.media_players) {
            $(element_selector).append(thing.create_ui());
        }

        this.on_baticueva_tv_shown();
    }

    show_list_of(thing_type, element_selector) {
        for (var thing of this.things_app.get_things_of_type(thing_type)) {
            $(element_selector).append(thing.create_ui());
        }
    }

    show_scenes(template_element_selector) {
        this.scenes_tmpl_ready = $.Deferred();
        var self = this;

        $.ajax({
            url: "scenes_view.html",
            cache: true,
            type: 'get',
            dataType: 'html',
            success: function(tmpl) {
                if (!Handlebars || !Handlebars.registerHelper) {
                    console.error("Handlebars plugin not found");
                }

                self.render_scenes = Handlebars.compile(tmpl);
                self.scenes_tmpl_ready.resolve();
            }
        });

        $.ajax({
            url: '/scenes/list',
            cache: false,
            type: 'get',
            dataType: 'json',
            success: function(scenes) {
                $.when(self.scenes_tmpl_ready.is_ready).then(function() {
                    $(template_element_selector).replaceWith(self.render_scenes(scenes));
                });
            }
        });
    }

    toggle_Local_Sensors_Plot(dygraph_element_id) {
        $('#' + dygraph_element_id ).toggle();
        if ($('#' + dygraph_element_id ).is(':visible')) {
            this.plot_local_sensors(dygraph_element_id);
        }
    }

    plot_local_sensors(dygraph_element_id) {
        var opts = {
            labels: [ 'Date', 'Temperature', 'CO2'],
            ylabel: 'CO2 PPM',
            y2label: 'Temperature (C)',
            highlightCircleSize: 2,
            strokeWidth: 1,
            highlightSeriesOpts: {
                strokeWidth: 3,
                strokeBorderWidth: 1,
                highlightCircleSize: 5
            },
            series: {
                'Temperature': {'axis': 'y2'/*, 'plotter': smoothPlotter*/},
                'CO2': {'axis': 'y', 'plotter': smoothPlotter}
            },
            axes: { x: {
                valueFormatter: function(d) { return new Date(d*1000); },
                axisLabelFormatter: function(d, gran, opts) {
                    var t = new Date(d*1000);
                    return t.getHours() + ":" + t.getMinutes() + " " + t.getDay() + "/" + t.getMonth();
                }
            }},
        };

        new Dygraph(
            document.getElementById(dygraph_element_id),
            "co2_history.csv?random=" + new Date().getTime(),
            opts);
    }

    /*******************************************************/
    /* WEATHER INTEGRATION */
    /*******************************************************/
    toggle_Weather_Plots(rain_forecast_element, temp_forecast_element, hours){
        $('#' + rain_forecast_element).toggle();
        $('#' + temp_forecast_element).toggle();
        if ($('#' + temp_forecast_element).is(':visible')) {
            this.plot_temp_forecast(temp_forecast_element, hours);
            this.plot_rain(rain_forecast_element);
        }
    }

    plot_temp_forecast(dygraph_element_id, hours) {
        $.ajax({
            url: "https://api.meteoplaza.com/v2/meteo/completelocation/5237.494?lang=en",
            cache: false,
            type: 'get',
            dataType: 'json',
            success: function(forecast) {
                    var csv = "Date,Temp (C)\n";
                    for(var h of forecast.Hourly.slice(0, hours)) {
                        csv += h.ValidDt + "," + h.TTTT + "\n";
                    }

                    new Dygraph(document.getElementById(dygraph_element_id), csv,
                        {fillGraph: true});
                }
        });
    }

    plot_rain(dygraph_element_id) {
        $.ajax({
            url: "https://cdn-secure.buienalarm.nl/api/3.4/forecast.php?lat=52.37064&lon=4.94223&region=nl&unit=mm/u",
            cache: false,
            type: 'get',
            dataType: 'json',
            success: function(forecast) {
                var csv = "Date,Rain(mm/h)\n";
                var t = forecast.start;
                for (var rain of forecast.precip) {
                    csv += t + "," + rain + "\n";
                    t += forecast.delta;
                }

                var dygraph_opts ={
                    series: {'Rain(mm/h)': {'plotter': smoothPlotter}},
                    axes: {
                        y: {valueRange: [0, 5],},
                        x: {
                            valueFormatter: function(d) { return new Date(d*1000); },
                            axisLabelFormatter: function(d, gran, opts) {
                                var t = new Date(d*1000);
                                return t.getHours() + ":" + t.getMinutes();
                            }
                        },
                    },
                    underlayCallback: function(ctx, area, graph) {
                        dygraph_helper_horizontalLine(ctx, graph, 0.25, 'green');
                        dygraph_helper_horizontalLine(ctx, graph, 1, 'yellow');
                        dygraph_helper_horizontalLine(ctx, graph, 2.5, 'red');
                    }
                }; 

                new Dygraph(document.getElementById(dygraph_element_id),
                        csv, dygraph_opts);
            }
        });
    }


    /*******************************************************/
    /* MFP INTEGRATION */
    /*******************************************************/
    get_mfp_stats(daily_target_cals, callback) {
        var self = this;
        $.ajax({
            url: "/mfp/stats",
            cache: false,
            type: 'get',
            dataType: 'json',
            success: function(diary) {
                var stats = self.aggregate_mfp_diary(daily_target_cals, diary);

                var recommend = ""
                if (stats.period_target_cals_pct > 105) recommend = "<li><b>eat less</b></li>";
                if (stats.period_target_cals_pct <  80) recommend = "<li><b>eat more</b></li>";

                var mfp_summary = {
                        title: "MFP "+stats.period_day_count+" day stats",
                        text: "<ul>" +
                            "<li>avg " + stats.daily_average_cals + " cal/day " +
                            "("+ stats.period_target_cals_pct +"%)</li>" +
                            "<li>trained "+stats.period_exercise_days+" days out of "+stats.period_day_count+
                            " ("+stats.period_exercise_time+"min)</li>" +
                            recommend +
                            "</ul>",
                };

                var days = [];
                for (var d in diary) days.push(d);
                days = days.sort();

                callback(days, diary, stats, mfp_summary);
            },
        });
    }

    aggregate_mfp_diary(daily_target_cals, diary) {
        var stats = {
                daily_target_cals: daily_target_cals,
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

        stats.daily_average_cals = stats.period_total_cals / stats.period_day_count;
        stats.period_target_cals = stats.daily_target_cals * stats.period_day_count;
        stats.period_target_cals_pct = Math.ceil(100 * stats.period_total_cals / stats.period_target_cals);
        return stats;
    }

    plot_mfp_diary(dygraph_element_id, days, daily_target_cals, diary) {
        var csv = "Date,Calories,Weight\n";
        var weight_min = 999;
        var weight_max = 0;
        for (var day of days) {
            var log = diary[day];
            csv += day + "," + log.calories + "," + (log.weight? log.weight : '') + "\n";

            if (log.weight && log.weight < weight_min) weight_min = log.weight; 
            if (log.weight && log.weight > weight_max) weight_max = log.weight; 
        }

        new Dygraph(
          document.getElementById(dygraph_element_id), csv,
          {
              ylabel: 'Calories',
              y2label: 'Weight',
              series: {
                  'Calories': {axis: 'y'},
                  'Weight': {axis: 'y2'},
              },
              axes: {
                // Carefully picked ranges to make the graph look pretty
                y : { valueRange: [daily_target_cals*0.4, daily_target_cals*1.5], },
                y2: { valueRange: [weight_min * 0.98, weight_max * 1.12], },
              },
              strokeWidth: 3,
              pointSize : 5,
              drawPoints: true,
              highlightCircleSize: 5,
              highlightSeriesOpts: {strokeWidth: 5, highlightCircleSize: 10},
              underlayCallback: function(ctx, area, graph) {
                  dygraph_helper_horizontalLine(ctx, graph, daily_target_cals*0.8, 'yellow');
                  dygraph_helper_horizontalLine(ctx, graph, daily_target_cals, 'green');
                  dygraph_helper_horizontalLine(ctx, graph, daily_target_cals*1.1, 'red');
              },
          }
        );
    }
}

