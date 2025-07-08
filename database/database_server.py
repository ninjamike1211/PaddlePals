from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys

from database_api import restAPI

class DatabaseServer(BaseHTTPRequestHandler):

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

            response = pickleAPI.handle_request(self.path, params, apiKey)
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
    auth = not (len(sys.argv) >= 2 and sys.argv[1] == 'noAuth')
    pickleAPI = restAPI(useAuth=auth)

    try:
        httpd = HTTPServer(('',80),DatabaseServer)
    except PermissionError:
        httpd = HTTPServer(('',8080), DatabaseServer)

    print(f'PicklePals server started on port {httpd.server_port} with authentication {'enabled' if auth else 'disabled'}.')

    httpd.serve_forever()