/* This is actually templated, but not a thing... */
class Baticueva_TV_extras extends TemplatedThing {
    static matches_interface(actions) {return false;}
    constructor() {
        super("Baticueva_TV_extras.html", "", name, [], status); 
    }
    update_status(stat) {}
    request_action(action_url) { console.error("No action possible for this object"); }
}

