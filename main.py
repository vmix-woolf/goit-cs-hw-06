import socketserver
import socket
import json
from datetime import datetime
import http.server
import threading
import multiprocessing
import urllib.parse
from pymongo import MongoClient
import traceback

# Settings
HTTP_PORT = 3000
SOCKET_PORT = 5001
MONGO_HOST = "mongo"
MONGO_PORT = 27017
DB_NAME = "message_db"
COLLECTION_NAME = "messages"
MONGO_USER = "viacheslav"
MONGO_PASSWORD = "gHBf993$^^5"

# Connection to MongoDB with authorization
client = MongoClient(f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/")
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


def get_db():
    try:
        # mongo_client = MongoClient(MONGO_URI)
        print("Connection to MongoDB is successful!")
        return client["message_db"]
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        exit(1)


class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path).path

        match parsed_path:
            case "/":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                with open("index.html", "rb") as file:
                    self.wfile.write(file.read())

            case "/message.html":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                with open("message.html", "rb") as file:
                    self.wfile.write(file.read())

            case "/style.css":
                self.send_response(200)
                self.send_header("Content-type", "text/css")
                self.end_headers()
                with open("style.css", "rb") as file:
                    self.wfile.write(file.read())

            case "/logo.png":
                self.send_response(200)
                self.send_header("Content-type", "image/png")
                self.end_headers()
                with open("logo.png", "rb") as file:
                    self.wfile.write(file.read())

            case _:
                self.send_error(404, "Not Found")
                with open("error.html", "rb") as file:
                    self.wfile.write(file.read())

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            parsed_data = urllib.parse.parse_qs(post_data.decode())

            message_data = {
                "date": datetime.now().isoformat(),
                "username": parsed_data.get("username", [""])[0],
                "message": parsed_data.get("message", [""])[0],
            }

            # Sending data to a socket server (TCP)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect(("host.docker.internal", 5001))
                    sock.sendall(json.dumps(message_data).encode())
            except Exception as e:
                traceback.print_exc()
                self.send_error(500, f"Message sending error: {e}")
                return

            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
        else:
            self.send_error(404, "Not Found")


# Create an HTTP server
def run_http_server():
    handler = MyHandler
    with socketserver.TCPServer(("", HTTP_PORT), handler) as httpd:
        print(f"HTTP server is running on port {HTTP_PORT}")
        httpd.serve_forever()


# Create a Socket server for data processing
def run_socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", SOCKET_PORT))
    print(f"Starting a socket server on a port {SOCKET_PORT}")
    while True:
        data, _ = sock.recvfrom(1024)
        message_data = json.loads(data.decode())
        collection.insert_one(message_data)


def send_to_socket_server(username, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('mongo', 5001))
    message_data = json.dumps({"username": username, "message": message})
    sock.sendall(message_data.encode())
    sock.close()


if __name__ == '__main__':
    # Running servers in separate threads
    http_thread = threading.Thread(target=run_http_server)
    socket_thread = threading.Thread(target=run_socket_server)

    http_thread.start()
    socket_thread.start()

    http_thread.join()
    socket_thread.join()
