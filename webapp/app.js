
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

    invoke_media_player_action(player_name, url) {
        var self = this;
        $.ajax({
            url: url,
            cache: false,
            type: 'get',
            dataType: 'html',
            success: function(action_res) {
                console.log(player_name, ".", url, " => ", action_res);
                // Try to trigger a UI update in a second
                // TODO: This doesn't actually work: updateUI only recreates the UI, doesn't fetch new state
                // A call to updateStatus would be smarter
                setTimeout(function(){ self.get_player(player_name).updateUI(); }, 2000);
            }
        });

        return false;
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
}

