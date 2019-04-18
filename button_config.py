from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Button

class MyIkeaButton(Button):
    def __init__(self, mqtt_id, pretty_name, world):
        super().__init__(mqtt_id, pretty_name)
        self.world = world
        self.l1 = world.get_thing_by_name('Kitchen Counter - Left')
        self.l2 = world.get_thing_by_name('Kitchen Counter - Right')

    def handle_action(self, action, msg):
        if action == 'brightness_up_click':
            self.l1.set_brightness(100)
            self.l2.set_brightness(100)
            return True
        if action == 'arrow_right_click':
            self.l1.set_brightness(75)
            self.l2.set_brightness(75)
            return True
        if action == 'brightness_down_click':
            self.l1.set_brightness(50)
            self.l2.set_brightness(50)
            return True
        if action == 'arrow_left_click':
            self.l1.set_brightness(25)
            self.l2.set_brightness(25)
            return True
        if action == 'toggle':
            if self.l1.is_on or self.l2.is_on:
                self.l1.light_off()
                self.l2.light_off()
            else:
                self.l2.set_brightness(20)
            return True

        print("Unknown action: Ikea button - ", action)
        

class HueButton(Button):
    def __init__(self, mqtt_id, pretty_name, world, scenes):
        super().__init__(mqtt_id, pretty_name)
        self.world = world
        self.scenes = scenes

    def handle_action(self, action, msg):
        if action == 'up-hold':
            # Start media vol up
            print("VOL UP")
            return True

        if action == 'up-hold-release':
            # Stop media vol up
            print("VOL UP STOP")
            return True

        if action == 'up-press':
            print("UP")
            return True

        if action == 'down-press':
            print("DOWN")
            return True

        if action == 'off-hold':
            print("OFF")
            return True

        if action == 'off-press':
            print("OFF2")
            return True

        if action == 'on-press':
            print("ON")
            return True

        print("No handler for action {} message {}".format(action, msg))
        return False
    
