from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Thing

import time

from spotipy import Spotify
from spotipy.client import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

# Use the same logger as ZMF things
import logging
logger = logging.getLogger('zigbee2mqtt2flask.thing')

class _ThingSpotifyDummy(Thing):
    """ Dummy Spotify thing used when no auth token is valid """

    def __init__(self, api_base_url):
        super().__init__("Spotify")
        self.api_base_url = api_base_url

    def supported_actions(self):
        s = super().supported_actions()
        s.extend(['playpause', 'stop', 'play_next_in_queue', 'play_prev_in_queue',
                'toggle_mute', 'volume_up', 'volume_down', 'set_volume_pct',
                'play_in_device', 'auth_token_refresh', 'set_new_auth_code'])
        return s

    def playpause(self):
        pass

    def stop(self):
        pass

    def play_next_in_queue(self):
        pass

    def play_prev_in_queue(self):
        pass

    def set_playtime(self, t):
        pass

    def volume_up(self):
        pass

    def volume_down(self):
        pass

    def set_volume_pct(self, pct):
        pass

    def toggle_mute(self):
        pass

    def play_in_device(self, dev_name):
        pass

    def json_status(self):
        err_solve = "<a href='/{}/thing/{}/auth_token_refresh' target='blank'>Refresh authentication data</a>"
        return {
                'error': 'Not authenticated',
                'error_html_details': err_solve.format(self.api_base_url, self.get_id()),
                'name': self.get_id(),
                'uri': None,
                'active_device': None,
                'available_devices': None,
                'app': None,
                'volume_pct': 0,
                'volume_muted': True,
                'player_state': None,
                'media': None,
                }


class _ThingSpotifyImpl(_ThingSpotifyDummy):
    def __init__(self, api_base_url, tok):
        super().__init__(api_base_url)
        self._sp = Spotify(auth=tok)
        self.unmuted_vol_pct = 0
        self.volume_up_pct_delta = 10;

        self.status_cache_seconds = 10
        self.last_status = None
        self.last_status_t = 0

    def playpause(self):
        if self._is_active():
            self._sp.pause_playback()
        else:
            self._sp.start_playback()

    def stop(self):
        self._sp.pause_playback()

    def play_next_in_queue(self):
        self._sp.next_track()
    
    def play_prev_in_queue(self):
        # First 'prev' just moves playtime back to 0
        self._sp.previous_track()
        self._sp.previous_track()

    def set_playtime(self, t):
        if not self._is_active():
            return

        self._sp.seek_track(int(t) * 1000)

    def volume_up(self):
        if not self._is_active():
            return

        vol = self._get_volume_pct() + self.volume_up_pct_delta
        if vol > 100:
            vol = 100
        self.set_volume_pct(vol)

    def volume_down(self):
        if not self._is_active():
            return

        vol = self._get_volume_pct() - self.volume_up_pct_delta
        if vol < 0:
            vol = 0
        self.set_volume_pct(vol)

    def set_volume_pct(self, pct):
        if not self._is_active():
            return
        self._sp.volume(int(pct))

    def toggle_mute(self):
        if not self._is_active():
            return
        vol = self._get_volume_pct()
        if vol == 0:
            self.set_volume_pct(self.unmuted_vol_pct)
        else:
            self.unmuted_vol_pct = vol
            self.set_volume_pct(0)

    def play_in_device(self, dev_name):
        devs = self._sp.devices()['devices']
        for dev in devs:
            if dev['name'] == dev_name:
                self._sp.transfer_playback(dev['id'])
                return

        raise KeyError("Spotify knows no device called {}".format(dev_name))

    def _get_volume_pct(self):
        l = [x for x in self._sp.devices()['devices'] if x['is_active'] == True]
        if len(l) == 0:
            return 0 
        return l[0]['volume_percent']

    def _is_active(self):
        track = self._sp.current_user_playing_track()
        return (track is not None) and track['is_playing']

    def json_status(self):
        if self.last_status is not None:
            if time.time() - self.last_status_t < self.status_cache_seconds:
                logger.debug("Return Spotify status from cache")
                return self.last_status
        
        self.last_status_t = time.time()

        devices = self._sp.devices()['devices']

        active_dev = None
        if len(devices) > 0:
            act_devs = [x for x in devices if x['is_active'] == True]
            if len(act_devs) > 0:
                active_dev = act_devs[0]

        vol = active_dev['volume_percent'] if active_dev is not None else 0

        track = self._sp.current_user_playing_track()
        is_active = (track is not None) and track['is_playing']

        self.last_status = {
                'name': self.get_id(),
                'uri': None,
                'active_device': active_dev['name'] if active_dev is not None else None,
                'available_devices': [x['name'] for x in devices],
                'app': None,
                'volume_pct': vol,
                'volume_muted': (vol == 0),
                'player_state': 'Playing' if is_active else 'Idle',
                'media': None,
                }
        
        if track is None:
            return self.last_status

        # Get all cover images sorted by image size
        imgs = [(img['height'] * img['width'], img['url'])
                    for img in track['item']['album']['images']]
        imgs.sort()

        # Pick an image that's at least 300*300 (or the biggest, if all are smaller)
        selected_img = None
        for img in imgs:
            area, selected_img = img
            if area >= 90000:
                break

        self.last_status['media'] = {
                    'icon': selected_img,
                    'title': track['item']['name'],
                    'duration': track['item']['duration_ms'] / 1000,
                    'current_time': track['progress_ms'] / 1000,
                    'spotify_metadata': {
                        'artist': ', '.join([x['name'] for x in track['item']['album']['artists']]),
                        'album_link': track['item']['album']['external_urls']['spotify'],
                        'album_name': track['item']['album']['name'],
                        'track_count': track['item']['album']['total_tracks'],
                        'current_track': track['item']['track_number'],
                    }
                }

        return self.last_status


from apscheduler.schedulers.background import BackgroundScheduler


class ThingSpotify(Thing):
    @staticmethod
    def _get_spotify_scopes():
        return 'app-remote-control user-read-playback-state user-modify-playback-state user-read-currently-playing'

    @staticmethod
    def _get_auth_obj(cfg):
        return SpotifyOAuth(cfg['client_id'], 
                            cfg['client_secret'],
                            cfg['redirect_uri'],
                            scope=ThingSpotify._get_spotify_scopes(),
                            cache_path=cfg['spotipy_cache'])

    @staticmethod
    def _get_cached_token(cfg):
        """ Call to try and receive a cached auth token. Will return
        None if there is no valid token. If so, goto refresh_url to get a new token
        from Spotify (user will need to do that manually: it requires user approval).
        If the token is valid, it should refresh it so it continues being valid for
        a while more. """
        tok = ThingSpotify._get_auth_obj(cfg).get_cached_token()
        if tok:
            logger.debug("Got Spotify token from cache")
            return tok['access_token']
        else:
            logger.debug("Can't get Spotify token from cache")
            return None

    @staticmethod
    def _force_tok_refresh(cfg):
        tok = ThingSpotify._get_auth_obj(cfg).get_cached_token()
        if not tok:
            logger.debug("Force Spotify token refresh failed: no cached token")
            return None

        new_tok = ThingSpotify._get_auth_obj(cfg).refresh_access_token(tok['refresh_token'])
        logger.debug("Force Spotify token refresh succeeded: new token is {}".format(str(new_tok)))
        return new_tok['access_token']

    @staticmethod
    def _update_token_from_url_code(cfg, code):
        """ If get_cached_token failed, call get_token_from_redir_url with the result of the url
        redirect that comes from calling the new authorize url """
        tok = ThingSpotify._get_auth_obj(cfg).get_access_token(code)
        if tok:
            logger.debug("Updated access token from code")
            return tok['access_token']

        # Check if there's a cached token we can use
        return ThingSpotify._get_cached_token(cfg)


    def __init__(self, cfg, api_base_url):
        super().__init__("Spotify")
        self.cfg = cfg
        self.api_base_url = api_base_url
        self.secs_between_tok_revalidate = 60 * 45

        tok = ThingSpotify._get_cached_token(cfg)
        if tok is None:
            self.impl = _ThingSpotifyDummy(api_base_url)
            logger.warning("Spotify token needs a refresh! User will need to manually update token.")
        else:
            self.impl = _ThingSpotifyImpl(api_base_url, tok)

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(func=self._cached_tok_refresh,
                               trigger="interval", seconds=self.secs_between_tok_revalidate)
        self.scheduler.start()

    def _cached_tok_refresh(self):
        # This should refresh the token for another hour or so...
        logger.debug("Forcing Spotify token refresh")
        tok = ThingSpotify._force_tok_refresh(self.cfg)
        self.impl = _ThingSpotifyImpl(self.api_base_url, tok)

    def shutdown(self):
        self.scheduler.shutdown()

    def supported_actions(self):
        return self.impl.supported_actions()

    def auth_token_refresh(self):
        """ A bit hackish, but works: returns an HTML view to let a user manually
        update the auth token for spotify """
        html = """
            <h1>Spotify Auth Update</h1>
            <ol>
                <li>Goto <a href="{}" target="blank">this page</a>.
                    If asked, accept the permission request from Spotify.</li>
                <li>If approved, you'll be redirected to another page. Copy the URL of this new page.</li>
                <li>
                    Paste the URL here: <input type="text" id="redir_url" onChange="validateCode()"/>
                    <div id="invalid_code" style="display: inline">
                        That looks like an invalid code! Please try again.
                    </div>
                </li>
                <li id="valid_code">
                    That looks like a valid code! <a href="#" id="set_new_code_link">Update Spotify token.</a>
                </li>
            </ol>

            <script>
                document.getElementById("valid_code").style.visibility = "hidden";
                document.getElementById("invalid_code").style.visibility = "hidden";

                function validateCode() {{
                    var url = document.getElementById("redir_url").value;
                    var sep = "?code=";
                    var code = url.substr(url.indexOf(sep) + sep.length)
                    console.log("Code = ", code);

                    if (code.length > 10) {{
                        document.getElementById("invalid_code").style.visibility = "hidden";
                        document.getElementById("valid_code").style.visibility = "visible";
                        document.getElementById("set_new_code_link").href = "set_new_auth_code/" + code;
                    }} else {{
                        document.getElementById("invalid_code").style.visibility = "visible";
                        document.getElementById("valid_code").style.visibility = "hidden";
                    }}
                }}
            </script>
        """
        return html.format(ThingSpotify._get_auth_obj(self.cfg).get_authorize_url())

    def set_new_auth_code(self, code):
        try:
            tok = ThingSpotify._update_token_from_url_code(self.cfg, code)
            if tok is None:
                logger.debug("User setting invalid new Spotify access token {}".format(code))
                return "Sorry, token doesn't seem valid"
            else:
                self.impl = _ThingSpotifyImpl(self.api_base_url, tok)
                logger.debug("User set new Spotify access token {}, Spotify client should work again".format(code))
                return "Updated!"
        except Exception as ex:
            logger.error("Error while updating Spotify token", exc_info=True)
            return str(ex)

    def _catch_spotify_deauth(base_func):
        """ Detect if Spotify has an expired token. Set impl to a dummy object
        if auth expired """
        def wrap(self, *a, **kw):
            try:
                return base_func(self, *a, **kw)
            except SpotifyException as ex:
                if ex.http_status == 401:
                    logger.debug("Spotify access token expired, impl is now dummy Spotify thing")
                    self.impl = _ThingSpotifyDummy(self.api_base_url)

                    logger.debug("Trying to renew token...")
                    tok = ThingSpotify._get_cached_token(self.cfg)
                    if tok is None:
                        logger.debug("Refresh token failed, user will need to renew manually")
                    else:
                        logger.debug("Refresh token OK: {}".format(tok))
                        self.impl = _ThingSpotifyImpl(self.api_base_url, tok)

                    return base_func(self, *a, **kw)
                else:
                    raise ex
        return wrap

    @_catch_spotify_deauth
    def playpause(self):
        return self.impl.playpause()

    @_catch_spotify_deauth
    def stop(self):
        return self.impl.stop()

    @_catch_spotify_deauth
    def play_next_in_queue(self):
        return self.impl.play_next_in_queue()

    @_catch_spotify_deauth
    def play_prev_in_queue(self):
        return self.impl.play_prev_in_queue()

    @_catch_spotify_deauth
    def set_playtime(self, t):
        return self.impl.set_playtime(t)

    @_catch_spotify_deauth
    def volume_up(self):
        return self.impl.volume_up()

    @_catch_spotify_deauth
    def volume_down(self):
        return self.impl.volume_down()

    @_catch_spotify_deauth
    def set_volume_pct(self, pct):
        return self.impl.set_volume_pct(pct)

    @_catch_spotify_deauth
    def toggle_mute(self):
        return self.impl.toggle_mute()

    @_catch_spotify_deauth
    def play_in_device(self, dev_name):
        return self.impl.play_in_device(dev_name)

    @_catch_spotify_deauth
    def json_status(self):
        return self.impl.json_status()

