
class MqttDeviceInfo extends TemplatedThing {
    /**
     * Check if a list of actions look like an interface for an MqttDevice
     */
    static matches_interface(actions) {
        return actions.includes("mqtt_status");
    }

    constructor(things_server_url, name, supported_actions, status) {
        super("mqtt_device_info.html", "", name, [], status);
    }

    update_status(stat) {
        this.link_quality = stat.link_quality;
        this.battery_level = stat.battery_level;
    }
}

