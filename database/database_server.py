from http.server import HTTPServer, BaseHTTPRequestHandler
from database_api import restAPI

class DatabaseServer(BaseHTTPRequestHandler):

    def pickle_handle_request(self):
        print(f'GET {self.path}')

        try:
            response = pickleAPI.handle_request(self.command, self.path)
            print(response)

        except Exception as error:
            print(f'ERROR: {error}')
            response = f'Error: {error}'

        finally:
            self.send_response(200)
            self.end_headers()

            self.wfile.write(bytes(str(response), 'utf-8'))

    def do_GET(self):
        return self.pickle_handle_request()

    def do_PUT(self):
        return self.pickle_handle_request()

    def do_POST(self):
        return self.pickle_handle_request()

    def do_DELETE(self):
        return self.pickle_handle_request()

pickleAPI = restAPI()
httpd = HTTPServer(('localhost',8080),DatabaseServer)
httpd.serve_forever()