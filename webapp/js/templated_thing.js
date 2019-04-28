
class TemplatedThing {
    constructor(template_name, things_server_url, name, supported_actions, status) {
        if (!this.update_status) {
            console.error("Subclass must define update_status()");
        }

        this.template_name = template_name;
        this.action_base_url = things_server_url + 'thing/' + name;
        this.name = name;
        // HTML ids can't contain whitespaces
        this.html_id = name.split(' ').join('_');
        this.supported_actions = supported_actions;
        this.update_status(status);

        console.log("Created thing ", this);
    }

    request_action(action_url) {
        var self = this;
        $.ajax({
          type: 'GET',
          dataType: 'json',
          url: self.action_base_url + action_url,
          success: function(thing_status){
            self.update_status(thing_status);
          },
        });
    }

    create_ui() {
        var renderer = Handlebars.templates[this.template_name];
        var ctx = this;
        return renderer(ctx);
    }
}

