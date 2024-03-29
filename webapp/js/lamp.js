
class Lamp extends TemplatedThing {
    static has_on_off(actions) { return actions.includes('light_on') && actions.includes('light_off'); }
    static has_brightness(actions) { return actions.includes('set_brightness'); }
    static has_color(actions) { return actions.includes('set_rgb'); }
    static has_color_temp(actions) { return actions.includes('set_color_temp'); }

    /**
     * Check if a list of actions look like an interface for a lamp
     */
    static matches_interface(actions) {
        return Lamp.has_on_off(actions) || Lamp.has_brightness(actions);
    }

    constructor(things_server_url, name, supported_actions, status) {
        super("lamp.html", things_server_url, name, supported_actions, status);

        this.supports_onoff = Lamp.has_on_off(supported_actions);
        this.supports_brightness = Lamp.has_brightness(supported_actions);
        this.has_color = Lamp.has_color(supported_actions);
        this.has_color_temp = Lamp.has_color_temp(supported_actions);
        this.has_extra_cfg = this.has_color || this.has_color_temp;
        this.start_periodic_status_updates();

        // Register object UI callbacks
        var self = this;

        $(document).on('click', '#lamp_open_panel_ctrl'+this.html_id,
            function(){ $('#lamp_detailed_panel_ctrl'+self.html_id).toggle(); });

        $(document).on('click', '#lamp_is_on_checkbox'+this.html_id,
            function(){ self.update_on_state_from_ui(); });

        $(document).on('click', '#lamp_set_brightness_slider'+this.html_id,
            function(){ self.update_brigthness_from_ui(); });
        $(document).on('touchend', '#lamp_set_brightness_slider'+this.html_id,
            function(){ self.update_brigthness_from_ui(); });


        $(document).on('click', '#lamp_set_rgb'+this.html_id,
            function(){ self.pause_periodic_status_updates(); });
        $(document).on('blur', '#lamp_set_rgb'+this.html_id,
            function(){ self.start_periodic_status_updates(); });
        $(document).on('change', '#lamp_set_rgb'+this.html_id,
            function(){ self.update_color_from_ui(); self.start_periodic_status_updates(); });

        $(document).on('input', '#lamp_color_shifter_'+this.html_id,
            function(){ self.toggle_shift(); });

        $(document).on('click', '#lamp_set_color_temp_slider'+this.html_id,
            function(){ self.update_color_temp_from_ui(); });
        $(document).on('touchend', '#lamp_set_color_temp_slider'+this.html_id,
            function(){ self.update_color_temp_from_ui(); });
    }

    updateUI() {
        var show_panel = $('#lamp_detailed_panel_ctrl'+this.html_id).is(':visible');
        $('#lamp_view'+this.html_id).replaceWith(this.create_ui());
        if (show_panel) $('#lamp_detailed_panel_ctrl'+this.html_id).show();
    }

    update_status(stat) {
        this.is_on = stat.is_on;
        this.brightness = stat.brightness;
        this.rgb_color = stat.rgb;
        this.color_temp = stat.color_temp;
        this.updateUI();
    }

    update_on_state_from_ui() {
        var should_be_on = $('#lamp_is_on_checkbox'+this.html_id).is(':checked');
        this.is_on = should_be_on;
        this.updateUI();
        this.request_action((should_be_on? '/light_on' : '/light_off'));
    }

    update_brigthness_from_ui() {
        var brightness_pct = $('#lamp_set_brightness_slider'+this.html_id).val();
        this.brightness = brightness_pct;
        this.is_on = (brightness_pct > 0);
        this.updateUI();
        this.request_action('/set_brightness/' + brightness_pct);
    }

    set_rgb_color(color) {
        this.rgb_color = color;
        this.request_action('/set_rgb/' + color);
    }

    update_color_temp_from_ui() {
        var color_temp = $('#lamp_set_color_temp_slider'+this.html_id).val();
        this.color_temp = color_temp;
        this.updateUI();
        this.request_action('/set_color_temp/' + color_temp);
    }

    update_color_from_ui() {
        var color = $('#lamp_set_rgb'+this.html_id).val().substring(1);
        this.rgb_color = color;
        this.updateUI();
        this.request_action('/set_rgb/' + color);
    }

    toggle_shift() {
        this.request_action('/light_color_shift_toggle');
    }

    throttled_update_color_from_ui() {
        if (this.timeout_active) return;

        var throttle_time = 250;
        var self = this;
        this.timeout_active = setTimeout(function(){
                clearTimeout(self.timeout_active);
                self.timeout_active = null; 
            }, throttle_time);

        var color = $('#lamp_set_rgb'+this.html_id).val().substring(1);
        this.request_action('/set_rgb/' + color);
    }
}

