
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

/**************************************/
/* WEATHER */
/**************************************/

function DumbHouse_plot_rain(dygraph_element_id) {
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

function DumbHouse_plot_temp_forecast(dygraph_element_id, hours) {
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


/**************************************/
/* Local sensors */
/**************************************/
function DumbHouse_plot_local_sensors(dygraph_element_id) {
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


/**************************************/
/* MFP */
/**************************************/
function DumHouse_plot_mfp_diary(dygraph_element_id, days, daily_target_cals, diary) {
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



