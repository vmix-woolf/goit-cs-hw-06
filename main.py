import datetime
import socket
import json
import threading
import socketserver
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse


host = 'localhost'
port = 27017
username ='viacheslav',
password ='ghj123YUI',
auth_db = 'admin'

def get_db():
    try:
        mongo_client = MongoClient(
            host,
            port,
            username=username,
            password=password,
            authSource=auth_db
        )

        print("Connection to MongoDB is successful!")
        return mongo_client["message_db"]
    except ConnectionFailure as e:
        print(f"Error connecting to MongoDB: {e}")
        exit(1)

# client = MongoClient("mongodb://localhost:27017/")
db = get_db()
collection = db['messages']


class MyHandler(BaseHTTPRequestHandler):
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
                "date": datetime.datetime.now().isoformat(),
                "username": parsed_data.get("username", [""])[0],
                "message": parsed_data.get("message", [""])[0],
            }

            # Отправка данных на socket-сервер (TCP)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(("localhost", 5001))
                sock.sendall(json.dumps(message_data).encode())

            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
        else:
            self.send_error(404, "Not Found")


# Create an HTTP server
def run_http_server():
    handler = MyHandler
    with socketserver.TCPServer(("", 3000), handler) as httpd:
        print("HTTP server is running on port 3000")
        httpd.serve_forever()

# Step 2: Create a Socket server for data processing
def run_socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 5001))
    sock.listen(1)

    while True:
        client_socket, client_address = sock.accept()
        data = client_socket.recv(1024).decode()
        if data:
            # Parsing data and saving to MongoDB
            try:
                message_data = json.loads(data)
                message_data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                collection.insert_one(message_data)
                print(f"Message saved: {message_data}")
            except Exception as e:
                print(f"Data processing error: {e}")
        client_socket.close()

# Function for sending data to the Socket server
def send_to_socket_server(user_name, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 5001))
    message_data = json.dumps({"username": user_name, "message": message})
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