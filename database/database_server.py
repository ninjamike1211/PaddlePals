from http.server import HTTPServer, BaseHTTPRequestHandler
import json

from database_api import restAPI

class DatabaseServer(BaseHTTPRequestHandler):

    def do_POST(self):
        print(f'{self.command} {self.path}')

        try:
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

            response, code = pickleAPI.handle_request(self.path, params, apiKey)
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


pickleAPI = restAPI()

try:
    httpd = HTTPServer(('',80),DatabaseServer)
except PermissionError:
    httpd = HTTPServer(('',8080), DatabaseServer)

print('PicklePals server started, now listening for incoming requests')

httpd.serve_forever()