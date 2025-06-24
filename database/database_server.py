from http.server import HTTPServer, BaseHTTPRequestHandler
import json

from database_api import restAPI

class DatabaseServer(BaseHTTPRequestHandler):

    def pickle_handle_request(self):

        print(f'{self.command} {self.path}')

        try:
            body_length = int(self.headers['Content-Length'])
            body = self.rfile.read(body_length)
            print(body)

            params = json.loads(body.decode('utf-8'))
            print(params)

            response, code = pickleAPI.handle_request(self.path, params)
            print(response, code)

            if code == 200:
                self.send_response(code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(bytes(json.dumps(response), 'utf-8'))
            else:
                self.send_error(code, str(response))

        except Exception as error:
            self.send_error(400, f'Error: {error}')

    def do_GET(self):
        return self.pickle_handle_request()

    def do_PUT(self):
        return self.pickle_handle_request()

    def do_POST(self):
        return self.pickle_handle_request()

    def do_DELETE(self):
        return self.pickle_handle_request()

pickleAPI = restAPI()

httpd = HTTPServer(('',80),DatabaseServer)

print('PicklePals server started, now listening for incoming requests')

httpd.serve_forever()