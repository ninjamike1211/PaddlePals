from http.server import HTTPServer, BaseHTTPRequestHandler
from functools import partial
import threading
import json
import sys
import time

from .database_api import restAPI

class PickleServer():
    def __init__(self, api:restAPI, port:int):
        self.port = port
        self.api = api
        http_handler = partial(self.PickleHandler, self.api)
        self.server = HTTPServer(('',self.port),http_handler)

        self.server_thread = threading.Thread(target=self.run, daemon=True)
        self.api.close()

    def run(self):
        self.api.openCon()
        self.server.serve_forever()

        self.api.close()

    def start_server(self):
        self.server_thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()

    def __enter__(self):
        self.start_server()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()

    def __del__(self):
        self.close()


    class PickleHandler(BaseHTTPRequestHandler):

        def __init__(self, api:restAPI, *args, **kwargs):
            self.api = api
            super().__init__(*args, **kwargs)

        def do_POST(self):
            print(f'{self.command} {self.path}')

            try:
                print(f"\nMessage Headers:\n----------------\n{self.headers}")

                body_length = int(self.headers['Content-Length'])
                body = self.rfile.read(body_length)
                print(f'Message Body:\n-------------\n{body}')

                params = json.loads(body.decode('utf-8'))
                print(f'\nMessage JSON:\n-------------\n{params}')

                auth_message = self.headers.get('Authorization')
                apiKey = None

                if auth_message:
                    auth_message_split = auth_message.split(' ')
                    if auth_message_split[0] == 'Bearer':
                        apiKey = auth_message_split[1]

                response = self.api.handle_request(self.path, params, apiKey)
                print(f'\nResponse JSON:\n--------------\n{response}\n')

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(bytes(json.dumps(response), 'utf-8'))

            except restAPI.APIError as error:
                self.send_error(error.code, f'API Error: {error}')

            except json.decoder.JSONDecodeError as error:
                self.send_error(400, f'Error, improperly formatted JSON: {error}')

            except ValueError as error:
                self.send_error(400, f'Type Error: {error}')

            except Exception as error:
                self.send_error(500, f'Server Error: {error}')


if __name__ == "__main__":
    auth = not 'noAuth' in sys.argv
    clear = 'clearDB' in sys.argv
    altPort = 'altPort' in sys.argv

    pickleAPI = restAPI(dbFile='database/pickle.db', useAuth=auth, clearDB=clear)
    server = PickleServer(pickleAPI, 8080 if altPort else 80)
    with server:
        print(f'PicklePals server started on port {server.port} with authentication {"enabled" if auth else "disabled"}')

        try:
            while True:
                time.sleep(0.5)

        except KeyboardInterrupt:
            print("Keyboard Interrupt, shutting down server!")