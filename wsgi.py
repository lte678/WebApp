from flask import Flask, render_template, redirect, g
import scripts.matrixcom as matrixcom


host="192.168.0.5"
port=8252

sock = None
effects_index = 0
effects = []


def prepare_socket():
    global sock
    if sock is None:
        sock = matrixcom.connect_to_matrix("192.168.0.5", 8252)


def get_matrixcom_effects():
    global effects
    # Can raise a NotConnected exception
    prepare_socket()
    effects = matrixcom.send_command(sock, ['apps'])
    return [e[3:] for e in effects.split('\n')]


def create_app():
    global effects, effects_index
    app = Flask(__name__)

    effects_index = 0
    effects = get_matrixcom_effects()

    @app.route("/")
    def home():
        return render_template('index.html', effect_name=effects[effects_index])


    @app.route("/next")
    def next():
        global sock, effects, effects_index
        effects_index += 1
        if effects_index >= len(effects):
            effects_index = 0
        new_effect = effects[effects_index]
        try:
            prepare_socket()
            matrixcom.send_command(sock, ['start', new_effect])
        except matrixcom.NotConnected:
            return redirect("/disconnected")
        return redirect("/")


    @app.route("/previous")
    def previous():
        global sock, effects, effects_index
        effects_index -= 1
        if effects_index < 0:
            effects_index = len(effects) - 1
        new_effect = effects[effects_index]
        try:
            prepare_socket()
            matrixcom.send_command(sock, ['start', new_effect])
        except matrixcom.NotConnected:
            return redirect("/disconnected")
        return redirect("/")


    @app.route("/stop")
    def stop():
        global sock
        try:
            prepare_socket()
            matrixcom.send_command(sock, ['stop'])
        except matrixcom.NotConnected:
            return redirect("/disconnected")
        return redirect("/")


    @app.route("/disconnected")
    def disconnected():
        try:
            prepare_socket()
            return redirect("/")
        except matrixcom.NotConnected:
            pass
        return render_template('disconnected.html')

    return app