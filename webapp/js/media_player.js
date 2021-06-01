if (!Handlebars || !Handlebars.registerHelper) {
    console.error("Handlebars plugin not found: templates may fail to render");
} else {
    Handlebars.registerHelper('media_player_formatSeconds', function(seconds, options) {
        // Map seconds to HH:MM:SS
        return (new Date(seconds * 1000).toISOString()).substr(11, 8);
    });

    Handlebars.registerHelper('selectIfEq', function(a, b) {
        if (a==b) return "selected";
        return "";
    });
}


class MediaPlayer extends TemplatedThing {
    /**
     * Check if a list of actions look like an interface for a MediaPlayer
     */
    static matches_interface(actions) {
        var minimal_interface = ["playpause", "stop", "toggle_mute", "set_volume_pct"];
        for (var mthd of minimal_interface) {
            if (!actions.includes(mthd)) return false;
        }

        return true;
    }

    constructor(things_server_url, name, supported_actions, status) {
        super("media_player.html", things_server_url, name, supported_actions, status);

        this.has_extended_control = true;

        // Register object UI callbacks
        var self = this;
        // Div ID: '#media_player_'+this.html_id+'_ctrl'
        $(document).on('click',    '#media_player_'+this.html_id+'_play',     function(){ self.on_play(); });
        $(document).on('click',    '#media_player_'+this.html_id+'_stop',     function(){ self.on_stop(); });
        $(document).on('click',    '#media_player_'+this.html_id+'_mute',     function(){ self.on_mute(); }); 
        $(document).on('click',    '#media_player_'+this.html_id+'_prev',     function(){ self.on_prev(); });
        $(document).on('click',    '#media_player_'+this.html_id+'_next',     function(){ self.on_next(); });
        $(document).on('click',    '#media_player_'+this.html_id+'_volume',   function(){ self.on_volume(); });
        $(document).on('touchend', '#media_player_'+this.html_id+'_volume',   function(){ self.on_volume(); });
        $(document).on('click',    '#media_player_'+this.html_id+'_playtime', function(){ self.on_playtime(); });
        $(document).on('touchend', '#media_player_'+this.html_id+'_playtime', function(){ self.on_playtime(); });
        $(document).on('change',   '#media_player_'+this.html_id+'_device', function(){ self.on_device_change(); });

        $(document).on('click', '#media_player_'+this.html_id+'_extended_control_open',
            function(){ $('#media_player_'+self.html_id+'_extended_control').toggle(); });

        this.start_periodic_status_updates();
    }

    update_status(new_status) {
        this.status = new_status;
        this.has_media = !(!new_status.media);
        this.player_icon = (new_status.media && new_status.media.icon)?
                                new_status.media.icon :
                                null;
        this.updateUI();
    }

    updateUI() {
        var show_panel = $('#media_player_'+this.html_id+'_extended_control').is(':visible');
        $('#media_player_'+this.html_id+'_ctrl').replaceWith(this.create_ui());
        if (show_panel) $('#media_player_'+this.html_id+'_extended_control').show();

        if (this.status.active_device) {
            $('#media_player_'+this.html_id+'_device').val(this.status.active_device);
        }
    }

    on_play()          { this.request_action('/playpause'); }
    on_stop()          { this.request_action('/stop'); }
    on_mute()          { this.request_action('/toggle_mute'); } 
    on_prev()          { this.request_action('/play_prev_in_queue'); }
    on_next()          { this.request_action('/play_next_in_queue'); }
    on_volume()        { this.request_action('/set_volume_pct/' + $('#media_player_'+this.html_id+'_volume').val()); }
    on_playtime()      { this.request_action('/set_playtime/' + $('#media_player_'+this.html_id+'_playtime').val()); }
    on_device_change() { this.request_action('/play_in_device/' + $('#media_player_'+this.html_id+'_device').val()); }
}

