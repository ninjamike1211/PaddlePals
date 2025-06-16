from http.server import HTTPServer, BaseHTTPRequestHandler

class DatabaseServer(BaseHTTPRequestHandler):

    def do_GET(self):
        print(self.path)
        self.send_response_only(200)
    #    if self.path == '/':
    #        self.path = '/test.html'
    #    try:
    #        file_to_open = open(self.path[1:]).read()
    #        self.send_response(200)
    #    except:
    #        file_to_open = "File not found"
    #        self.send_response(404)
    #    self.end_headers()
    #    self.wfile.write(bytes(file_to_open, 'utf-8'))


httpd = HTTPServer(('localhost',8080),DatabaseServer)
httpd.serve_forever()