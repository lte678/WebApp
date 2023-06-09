#!/usr/bin/env python3

import socket


class NotConnected(Exception):
    pass


def connect_to_matrix(host, port):
    print("[matrixcom] Connecting to {}:{}".format(host, port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)  #Wait upto 0.5 seconds for a server response
    try:
        sock.connect((host, port))
    except socket.gaierror:
        pass
    except TimeoutError:
        raise NotConnected
    
    return sock


def _receive_response(clientSocket):
    message = ""
    command_response = ""
    while True:
        try:
            data = clientSocket.recv(2048)
        except socket.timeout:
            return False

        if data == 0:
            return False

        data = data.decode()

        tokens = data.split(';')
        for token in tokens[:-1]:
            message += token
            if message == "ack":
                return command_response
            else:
                command_response = message.rstrip()
            message = ''

        message += tokens[-1]  #If it was ended by the delimeter it will be empty


def send_command(sock, command):
    if not sock:
        raise NotConnected

    sock.sendall(str.encode('%'.join(command) + ';'))
    return _receive_response(sock)
