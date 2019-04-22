
class DumbHouseApp {
    constructor() {
        this.things_app = new ThingsApp("/ZMF/", "/ZMF/webapp/", [Lamp, MediaPlayer, MqttDeviceInfo]);
        this.is_ready = $.Deferred();
        this.scenes_tmpl_ready = $.Deferred();

        var self = this;
        $(document).ready(function(){
            $.when(self.things_app.is_ready).then(function() {
                $.when(self.scenes_tmpl_ready.is_ready).then(function() {
                    self.is_ready.resolve(); 
                });
            });
        });

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

