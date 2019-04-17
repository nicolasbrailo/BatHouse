from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Button

class MyIkeaButton(Button):
    def __init__(self, mqtt_id, pretty_name, btn1, btn2):
        super().__init__(mqtt_id, pretty_name)
        self.btn1 = btn1
        self.btn2 = btn2

    def handle_action(self, action, msg):
        if action == 'arrow_right_click':
            self.btn1.brightness_up()
        if action == 'arrow_left_click':
            self.btn1.brightness_down()
        if action == 'brightness_up_click':
            self.btn2.brightness_up()
        if action == 'brightness_down_click':
            self.btn2.brightness_down()
        if action == 'toggle':
            if self.btn1.is_on or self.btn2.is_on:
                self.btn1.light_off()
                self.btn2.light_off()
            else:
                self.btn2.set_brightness(20)

class HueButton(Button):
    def __init__(self, mqtt_id, pretty_name):
        super().__init__(mqtt_id, pretty_name)

    def handle_action(self, action, msg):
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
    
