#!/usr/bin/env python3

import socket


class NotConnected(Exception):
    pass


class CommandError(Exception):
    pass


class MatrixConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
    

    def _connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)  #Wait upto 0.5 seconds for a server response
        try:
            sock.connect((self.host, self.port))
            print("[backend] Connected to {}:{}".format(self.host, self.port))
        except socket.gaierror:
            pass
        except (TimeoutError, OSError):
            print("[backend] Failed to connect to {}:{}".format(self.host, self.port))
            raise NotConnected
        return sock


    def send_command(self, command):
        sock = self._connect()
        sock.sendall(str.encode('%'.join(command) + ';'))
        return self._receive_response(sock)


    def _receive_response(self, sock):
        message = ""
        command_response = ""
        while True:
            try:
                data = sock.recv(2048)
            except socket.timeout:
                return False

            if data == 0:
                return False

            data = data.decode()

            tokens = data.split(';')
            for token in tokens[:-1]:
                message += token
                if message == "ack":
                    print(f"[backend] Received {tokens}")
                    if command_response.startswith("[Error]"):
                        raise CommandError
                    return command_response
                else:
                    command_response = message.rstrip()
                message = ''

            message += tokens[-1]  #If it was ended by the delimeter it will be empty