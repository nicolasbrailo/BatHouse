/* This is actually templated, but not a thing... */
class SceneList extends TemplatedThing {
    static matches_interface(actions) {return false;}
    constructor(scenes) {
        super("scene_list.html", "", name, [], status); 
        this.scenes = scenes;
    }
    update_status(stat) {}
    request_action(action_url) { console.error("No action possible for this object"); }
}

