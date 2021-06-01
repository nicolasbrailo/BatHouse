
class TemplatedThing {
    constructor(template_name, things_server_url, name, supported_actions, status) {
        if (!this.update_status) {
            console.error("Subclass must define update_status()");
        }

        // If auto-updates are requested, the default update frequency has a random
        // component to avoid a thundering herd every N seconds
        var default_ui_update_freq_s = 5 + Math.round(Math.random() * 10, 0);
        this.default_ui_update_freq_ms = default_ui_update_freq_s * 1000;

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

    static warn_if_visibility_not_supported(visChangeAction) {
      if (this.visibility_checked !== undefined) return;
      this.visibility_checked = true;
      if (visChangeAction === undefined) {
        console.log("Visibility changes not supported: UI elements won't auto-refresh");
      }
    }

    install_visibility_callback() {
      if (this.vis_cb_installed !== undefined) return;
      this.vis_cb_installed = true;

      var hidden, visChangeAction;
      if (typeof document.hidden !== "undefined") { // Opera 12.10 and Firefox 18 and later support
          hidden = "hidden";
          visChangeAction = "visibilitychange";
      } else if (typeof document.msHidden !== "undefined") {
          hidden = "msHidden";
          visChangeAction = "msvisibilitychange";
      } else if (typeof document.webkitHidden !== "undefined") {
          hidden = "webkitHidden";
          visChangeAction = "webkitvisibilitychange";
      }

      TemplatedThing.warn_if_visibility_not_supported(visChangeAction);
      if (visChangeAction !== undefined) {
        document.addEventListener(visChangeAction, () => {
          const app_hidden = document[hidden];
          app_hidden? this.app_became_hidden() : this.app_became_visible();
        });
      }
    }

    app_became_hidden() {
      this.skip_periodic_updates = true;
    }

    app_became_visible() {
      this.skip_periodic_updates = false;
      this.request_action('/json_status');
    }

    start_periodic_status_updates(ui_update_freq_ms) {
        this.install_visibility_callback();

        if (ui_update_freq_ms == undefined) {
          ui_update_freq_ms = this.default_ui_update_freq_ms
        }

        this.ui_update_freq_ms = ui_update_freq_ms;
        var self = this;
        this.status_updater_task = setTimeout(function(){
            clearTimeout(self.status_updater_task);
            if (!self.skip_periodic_updates) {
              self.request_action('/json_status');
            }
            self.start_periodic_status_updates(ui_update_freq_ms);
        }, ui_update_freq_ms);
    }

}

