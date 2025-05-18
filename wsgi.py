from flask import Flask, render_template, redirect, url_for, request
from scripts.matrixcom import MatrixConnection, NotConnected

host="192.168.178.5"
port=8252


def get_matrixcom_effects(conn: MatrixConnection) -> list[str]:
    """ Returns a list of effects supported by the LED matrix. """
    effects = conn.send_command(['apps'])
    return [e[3:] for e in effects.split('\n')]


def get_app_settings(conn: MatrixConnection, app: str) -> dict[str, bool | float | int | str]:
    """ Returns a dictionary of properties and their value for `app`. """
    all_settings = conn.send_command(['list'])
    curr_app = None
    settings = {}
    for line in map(str.strip, all_settings.split('\n')):
        if line.startswith('-'):
            if curr_app == app:
                setting, value = line[1:].split(': ')
                settings[setting] = value
        else:
            curr_app = line
    
    for k, v in settings.items():
        if ',' in v:
            # This is a color. It has four floats for RGBW.
            settings[k] = list(map(float, v.split(',')))
        try:
            v_int = int(v)
            settings[k] = v_int
        except ValueError:
            try:
                v_float = float(v)
                settings[k] = v_float
            except ValueError:
                # Keep it as a string property.
                pass
    return settings


def set_app_setting(conn: MatrixConnection, setting: str, value):
    """ Sets the setting to the provided value. """
    cmd = ['set', setting, str(value)]
    print(f"Sending command {cmd}")
    conn.send_command(cmd)


def create_app():
    app = Flask(__name__)

    # This is where we connect to the LED matrix. We keep this connection persistent.
    conn = MatrixConnection(host, port)
    effects = None
    active_effect = None

    @app.route("/")
    def home():
        nonlocal effects
        get_app_settings(conn, "colorwave")
        try:
            # Try to use cached effects to serve the page faster.
            if effects is None:
                effects = get_matrixcom_effects(conn)
            brightness = get_app_settings(conn, "matrix")["brightness"]
            return render_template(
                'index.html',
                no_connection=False,
                active_effect=active_effect,
                effects=effects,
                brightness=brightness
            )
        except NotConnected:
            effects = None
            return render_template(
                'index.html',
                no_connection=True
            )

    @app.route("/toggle/<effect>")
    def toggle_effect(effect):
        nonlocal active_effect, effects
        try:
            if effect == active_effect:
                conn.send_command(['stop', effect])
                active_effect = None
            else:
                conn.send_command(['start', effect])
                active_effect = effect
        except NotConnected:
            effects = None
            active_effect = None
        return redirect(url_for('home'))

    @app.route("/settings/<effect>", methods=["GET", "POST"])
    def effect_settings(effect):
        nonlocal effects
        if request.method == "POST":
            for key, value in request.form.items():
                # Try to parse numbers, else treat as string
                try:
                    if "," in value:
                        # RGBW float list
                        parsed = list(map(float, value.split(',')))
                        value = ','.join(map(str, parsed))
                    elif "." in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    value = value.strip()
                
                setting = f"matrix.{effect}.{key}"
                try:
                    set_app_setting(conn, setting, value)
                except NotConnected:
                    effects = None
                    return redirect(url_for('home'))

            return redirect(url_for("effect_settings", effect=effect))

        try:
            settings = get_app_settings(conn, effect)
            return render_template("settings.html", effect=effect, settings=settings)
        except NotConnected:
            effects = None
            return redirect(url_for('home'))

    @app.route("/set_brightness", methods=["POST"])
    def set_brightness():
        nonlocal effects
        brightness = request.form.get("brightness")
        value = float(brightness)
        if value < 0.0:
            value = 0.0
        elif value > 255.0:
            value = 255.0
        
        try:
            set_app_setting(conn, "matrix.brightness", value)
        except NotConnected:
            effects = None
            return redirect(url_for('home'))
        return '', 204  # No content

    return app