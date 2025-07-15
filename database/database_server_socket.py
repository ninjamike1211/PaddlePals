import socket
import selectors
import threading
import json
import email
import sys

from database_api import restAPI

class PickleServer:

    def __init__(self, api:restAPI, port:int):
        self.api = api

        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('0.0.0.0', port))
        self.socket.setblocking(False)
        self.socket.listen(5)

        self.selector = selectors.DefaultSelector()
        self.selector.register(self.socket, selectors.EVENT_READ)

        self.socket_thread = threading.Thread(target=self.socket_server, daemon=True)


    def start_server(self):
        self.socket_thread.start()


    def _decode_message(self, message:str):
        lines = message.splitlines()

        command = lines[0]
        payload = lines[-1]
    
    def socket_server(self):
        try:
            while True:
                event = self.selector.select(timeout=1)

                if event:
                    client_socket, client_address = self.socket.accept()

                    with client_socket:
                        print(f"Connection from {client_address}")

                        raw_data = client_socket.recv(2048)
                        if raw_data:
                            request = email.message_from_bytes(raw_data)
                            print(f'Data received: "{raw_data.decode()}"')
                            print(f'Data received: "{dict(request.items())}"')

                        client_socket.sendall("HTTP/1.1 200 OK".encode('utf-8'))
                    
        
        except OSError:
            print('Shutting down server thread')
            sys.exit()


    def close(self):
        self.socket.close()
        self.api.close()


    def __enter__(self):
        self.start_server()

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()


if __name__ == "__main__":
    pickleAPI = restAPI('database/pickle.db', False, False)
    server = PickleServer(pickleAPI, 80)
    server.start_server()

    try:
        while True:
            pass

    except KeyboardInterrupt:
        print("Keyboard Interrupt, shutting down server!")

    finally:
        server.close()