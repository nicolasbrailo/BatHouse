
class DumbHouseApp {
    constructor() {
        this.things_app = new ThingsApp("/ZMF/", "/ZMF/webapp/", [Lamp, MediaPlayer, MqttDeviceInfo]);
        this.is_ready = $.Deferred();
        this.scenes_tmpl_ready = $.Deferred();
        this.baticueva_extras_tmpl_ready = $.Deferred();

        var self = this;
        $(document).ready(function(){
            $.when(self.things_app.is_ready).then(function() {
                $.when(self.baticueva_extras_tmpl_ready).then(function() {
                    self.media_players = self.things_app.get_things_of_type(MediaPlayer);
                    self.monkeypatch();

                    $.when(self.scenes_tmpl_ready.is_ready).then(function() {
                        self.is_ready.resolve(); 
                    });
                });
            });
        });

        // Get scenes template
        var self = this;
        $.ajax({
            url: "scenes_view.html",
            cache: false,
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

        // Get Baticueva extras
        var self = this;
        $.ajax({
            url: "Baticueva_TV_extras.html",
            cache: false,
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
            patched_func.apply(patched_self);
            self.on_baticueva_tv_shown();
        }
    }

    on_baticueva_tv_shown() {
        $('#media_player_Baticueva_TV_ctrl').append(this.render_baticueva_extras());
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
        var self = this;
        $.ajax({
            url: '/scenes/list',
            cache: false,
            type: 'get',
            dataType: 'json',
            success: function(scenes) {
                $('#scene_list').replaceWith(self.render_scenes(scenes));
            }
        });
    }
}

