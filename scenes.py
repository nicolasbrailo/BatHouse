import json

class SceneHandler(object):
    def __init__(self, flask_app, world):
        self.world = world
        self.scenes = [x for x in dir(self) if not x.startswith('_')]

        @flask_app.route('/scenes/list')
        def flask_endpoint_get_scenes():
            return json.dumps(self.scenes)

        @flask_app.route('/scene_set/<name>')
        def flask_endpoint_set_scene(name):
            m = getattr(self, name, None)
            if m is None:
                return "No scene {}".format(action, thing_name), 405

            m()
            return "OK"

    def living_room_evening(self):
        self.world.get_thing_by_name('DeskLamp').set_brightness(60)
        self.world.get_thing_by_name('DeskLamp').set_rgb('ED7F0C')
        self.world.get_thing_by_name('Floorlamp').set_brightness(100)
        self.world.get_thing_by_name('Livingroom Lamp').set_brightness(100)

    def dinner(self):
        self.world.get_thing_by_name('DeskLamp').set_brightness(30)
        self.world.get_thing_by_name('Floorlamp').set_brightness(100)
        self.world.get_thing_by_name('Livingroom Lamp').light_off()
        self.world.get_thing_by_name('Kitchen Counter - Right').set_brightness(50)
        self.world.get_thing_by_name('Kitchen Counter - Left').set_brightness(80)
        self.world.get_thing_by_name('Baticueva TV').stop()

    def sleepy(self):
        self.world.get_thing_by_name('DeskLamp').set_brightness(20)
        self.world.get_thing_by_name('Floorlamp').set_brightness(20)
        self.world.get_thing_by_name('Livingroom Lamp').light_off()
        self.world.get_thing_by_name('Kitchen Counter - Right').set_brightness(40)
        self.world.get_thing_by_name('Kitchen Counter - Left').light_off()
        self.world.get_thing_by_name('Baticueva TV').stop()
        try:
            self.world.get_thing_by_name('Spotify').stop()
        except:
            pass

    def world_off(self):
        self.world.get_thing_by_name('DeskLamp').light_off()
        self.world.get_thing_by_name('Floorlamp').light_off()
        self.world.get_thing_by_name('Livingroom Lamp').light_off()
        self.world.get_thing_by_name('Kitchen Counter - Right').light_off()
        self.world.get_thing_by_name('Kitchen Counter - Left').light_off()
        self.world.get_thing_by_name('Baticueva TV').stop()
        try:
            self.world.get_thing_by_name('Spotify').stop()
        except:
            pass

    def test(self):
        self.world.get_thing_by_name('DeskLamp').set_rgb('F00000')

    def test2(self):
        self.world.get_thing_by_name('DeskLamp').light_toggle()


