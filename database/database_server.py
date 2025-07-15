from http.server import HTTPServer, BaseHTTPRequestHandler
from functools import partial
import threading
import json
import sys

from database.database_api import restAPI

class PickleServer():
    def __init__(self, api:restAPI, port:int):
        self.api = api

        http_handler = partial(self.PickleHandler, api)
        self.server = HTTPServer(('',port),http_handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start_server(self):
        self.server_thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.api.close()

    def __enter__(self):
        self.start_server()

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()


    class PickleHandler(BaseHTTPRequestHandler):

        def __init__(self, api, *args, **kwargs):
            self.api = api
            super().__init__(*args, **kwargs)

        def do_POST(self):
            print(f'{self.command} {self.path}')

            try:
                print(f"Message Headers:\n{self.headers}")

                body_length = int(self.headers['Content-Length'])
                body = self.rfile.read(body_length)
                print(body)

                params = json.loads(body.decode('utf-8'))
                print(params)

                auth_message = self.headers.get('Authorization')
                apiKey = None

                if auth_message:
                    auth_message_split = auth_message.split(' ')
                    if auth_message_split[0] == 'Bearer':
                        apiKey = auth_message_split[1]

                response = self.api.handle_request(self.path, params, apiKey)
                print(response)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(bytes(json.dumps(response), 'utf-8'))

            except restAPI.APIError as error:
                self.send_error(error.code, f'API Error: {error}')

            except Exception as error:
                self.send_error(400, f'Non-API Error: {error}')


if __name__ == "__main__":
    auth = not 'noAuth' in sys.argv
    clear = 'clearDB' in sys.argv
    pickleAPI = restAPI(useAuth=auth, clearDB=clear)

    try:
        server = PickleServer(pickleAPI, 80)
    except PermissionError:
        server = PickleServer(pickleAPI, 8080)

    server.start_server()

    try:
        while True:
            pass

    except KeyboardInterrupt:
        print("Keyboard Interrupt, shutting down server!")

    finally:
        server.close()