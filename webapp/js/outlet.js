
class Outlet extends TemplatedThing {
    static matches_interface(actions) {
       return actions.includes('outlet_on') && actions.includes('outlet_off');
    }

    constructor(things_server_url, name, supported_actions, status) {
        super("outlet.html", things_server_url, name, supported_actions, status);

        var self = this;
        $(document).on('click', '#outlet_is_on_checkbox'+this.html_id,
            function(){ self.update_on_state_from_ui(); });
    }

    updateUI() {
        $('#outlet_view'+this.html_id).replaceWith(this.create_ui());
    }

    update_status(stat) {
        this.outlet_powered = stat.outlet_powered;
        this.updateUI();
    }

    update_on_state_from_ui() {
        var should_be_on = $('#outlet_is_on_checkbox'+this.html_id).is(':checked');
        this.outlet_powered = should_be_on;
        this.updateUI();
        this.request_action((should_be_on? '/outlet_on' : '/outlet_off'));
    }
}

