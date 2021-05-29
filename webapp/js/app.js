var MY_POS_LAT = 52.37064;
var MY_POS_LON = 4.94223;

class DumbHouseApp {
    constructor() {
        // Cache this for scope
        var self = this;
        this.api_base_url = "/ZMF/";
        // Promise to be resolved when all objects have been initialized
        this.is_ready = $.Deferred();

        this.things = [];
        this.things_ready = $.Deferred();
        $.ajax({
          type: 'GET',
          dataType: 'json',
          url: this.api_base_url + "world/status",
          success: function(things){
            self.things = things;
            self.things_ready.resolve();
          },
        });

        $(document).ready(function(){
            $.when(self.things_ready).then(function() {
                self.media_players = self.get_things_of_type(MediaPlayer);
                self.monkeypatch();
                self.is_ready.resolve();
            });
        });
    };

    get_things_of_type(thing_class) {
        if (!thing_class) return this.things;

        var matching_things = [];
        for (var thing_name in this.things) {
            var thing = this.things[thing_name];
            var is_a_duck = thing_class.matches_interface(thing.supported_actions); 
            if (is_a_duck) {
                var mapped_thing = new thing_class(this.api_base_url, thing_name,
                                             this.things[thing_name].supported_actions,
                                             this.things[thing_name].status)
                matching_things.push(mapped_thing);
            }
        }

        return matching_things;
    }

    get_thing_by_name(name) {
        for (var thing_name in this.things) {
            if (thing_name == name) return this.things[thing_name];
        }
        return null;
    }

    get_player(name) {
        for (var p of this.media_players) {
            if (p.name == name) return p; 
        }
    }

    monkeypatch() {
        var self = this;
        var patched_self = this.get_player('Baticueva TV');
        if (patched_self === undefined) return;
        var patched_func = this.get_player('Baticueva TV').updateUI;
        self.get_player('Baticueva TV').updateUI = function() {
            self.before_baticueva_tv_shown();
            patched_func.apply(patched_self);
            self.on_baticueva_tv_shown();
        }
    }

    before_baticueva_tv_shown() {
        this.baticueva_extras_open = $('#Baticueva_TV_extras_div').is(':visible');
    }

    on_baticueva_tv_shown() {
        $('#media_player_Baticueva_TV_ctrl').append((new Baticueva_TV_extras()).create_ui());
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
        for (var thing of this.get_things_of_type(thing_type)) {
            $(element_selector).append(thing.create_ui());
        }
    }

    show_scenes(template_element_selector) {
        var self = this;
        $.ajax({
            url: '/scenes/list',
            cache: false,
            type: 'get',
            dataType: 'json',
            success: function(scenes) {
                $(template_element_selector).replaceWith(
                        (new SceneList(scenes)).create_ui());
            }
        });
    }

    show_scene_shortcuts(elm_select) {
        var renderer = Handlebars.templates["scene_shortcuts.html"];
        var tmpl = renderer();
        $(elm_select).html(tmpl);
    }

    show_mfp_diary(daily_target_cals, mfp_eatmeter_elm, mfp_dygraph_elm) {
        var mfp = new MFP(daily_target_cals);
        mfp.create_ui(mfp_eatmeter_elm);
        mfp.plot_diary(mfp_dygraph_elm);
    }

    toggle_Local_Sensors_Plot(dygraph_element_id) {
        $('#' + dygraph_element_id ).toggle();
        if ($('#' + dygraph_element_id ).is(':visible')) {
            DumbHouse_plot_local_sensors(dygraph_element_id);
        }
    }

    toggle_Weather_Plots(rain_forecast_element, temp_forecast_element, hours){
        $('#' + rain_forecast_element).toggle();
        $('#' + temp_forecast_element).toggle();
        if ($('#' + temp_forecast_element).is(':visible')) {
            DumbHouse_plot_temp_forecast(temp_forecast_element, hours);
            DumbHouse_plot_rain(MY_POS_LAT, MY_POS_LON, rain_forecast_element);
        }
    }
}


