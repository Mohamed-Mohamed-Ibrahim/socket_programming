import socket, threading, argparse
from utils import *  # includes helper functions like `get_content_type`
from concurrent.futures import ThreadPoolExecutor

# Maximum number of threads in the thread pool
MAX_WORKERS = 10

# Dynamically calculate timeout based on server load
def calculate_timeout(available_workers):
    base_timeout = 20  # Maximum timeout in seconds
    min_timeout = 5    # Minimum timeout in seconds
    # Calculate load factor and adjust timeout based on server load
    load_factor = (MAX_WORKERS - available_workers) / MAX_WORKERS
    timeout = max(min_timeout, base_timeout * (1 - load_factor))
    return timeout

# Prepare a 200 OK HTTP response for a successful GET request
def prepare_get_response_found(data_len: int, content_type: str = "text/plain", connection_type: str = "keep-alive") -> str:
    return f"HTTP/1.1 200 OK\r\nConnection: {connection_type}\r\nContent-Type: {content_type}\r\nContent-Length: {data_len}\r\n\r\n"

# Prepare a 404 Not Found HTTP response when requested resource is missing
def prepare_get_response_not_found() -> str:
    return f"\r\n\r\nHTTP/1.1 404 Not Found\r\n\r\n"

# Prepare a 200 OK HTTP response for a successful POST request
def prepare_post_response() -> str:
    return f"HTTP/1.1 200 OK\r\n\r\n"

# Handle client requests in a separate thread
def handle_client(client_socket, addr):
    try:
        while True:
            # Initialize request buffer
            request = b""
            # Receive request data from the client until end of headers
            while True:
                chunk = client_socket.recv(4096)
                request += chunk
                if b"\r\n\r\n" in request:
                    break

            # Separate headers and data in the request
            headers_end_b = request.find(b"\r\n\r\n")
            msg = request[:headers_end_b+4].decode('utf-8')
            data = request[headers_end_b+4:]

            # Parse headers and retrieve Content-Length if it's a POST request
            request_lines = msg.split("\r\n")
            content_length = 0
            if request_lines[0].startswith("POST"):
                for line in request_lines:
                    if line.lower().startswith("content-length:"):
                        content_length = int(line[15:].strip())
                        continue
                # Continue receiving data until entire content is read
                bytes_remaining = content_length - len(data)
                while bytes_remaining > 0:
                    chunk = client_socket.recv(4096)
                    data += chunk
                    bytes_remaining -= len(chunk)

            # Parse request line and retrieve the HTTP method, path, and version
            command, path, version = request_lines[0].split(" ")

            msg = ""
            # Set the path for the requested resource in the server directory
            path = os.getcwd() + "/server/" + os.path.basename(path)
            file_type = get_content_type(path)

            # Handle GET request
            if command == "GET":
                if not os.path.exists(path):
                    # Prepare and send a 404 Not Found response
                    msg = prepare_get_response_not_found()
                    client_socket.sendall(msg.encode("utf-8"))
                    continue
                # Open and read the requested file
                with open(path, "rb") as file:
                    data = file.read()
                # Prepare and send a successful response with file data
                msg = prepare_get_response_found(   data_len=len(data), 
                                                    content_type=get_content_type(path),
                                                    connection_type="keep-alive"
                                                    ).encode("utf-8")
                msg += data
                client_socket.sendall(msg)

            # Handle POST request
            elif command == "POST":
                # Write data to file (binary or text based on file type)
                arg = 'wb' if "image" in file_type else 'w'
                content = data if "image" in file_type else data.decode("utf-8")
                with open(path, arg) as f:
                    f.write(content)
                
                # Prepare and send a successful response
                msg = prepare_post_response().encode("utf-8")
                client_socket.sendall(msg)

    except Exception as e:
        print(f"Error when handling client: {e}")
        # Send a 404 Not Found response in case of error
        msg = prepare_get_response_not_found()
        client_socket.send(msg.encode("utf-8"))
    finally:
        # Close the connection to the client
        client_socket.shutdown(socket.SHUT_RDWR)
        client_socket.close()
        print(f"Connection to client ({addr[0]}:{addr[1]}) closed")

# Main server function to accept and handle client connections
def run_server(server_ip="127.0.0.1", port=8000):
    try:
        # Create a socket and set options
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to IP address and port
        server.bind((server_ip, port))
        # Start listening for incoming connections
        server.listen()
        print(f"Listening on {server_ip}:{port}")

        # Use ThreadPoolExecutor to manage threads
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            while True:
                # Accept a new client connection
                client_socket, addr = server.accept()
                # Calculate timeout based on available worker threads
                available_workers = executor._max_workers - executor._work_queue.qsize()
                timeout = calculate_timeout(available_workers)
                client_socket.settimeout(timeout)
                print(f"Accepted connection from {addr[0]}:{addr[1]}")
                # Start a new thread to handle the client
                thread = threading.Thread(target=handle_client, args=(client_socket, addr,))
                thread.start()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the server socket on exit
        server.close()

if __name__ == "__main__":
    # Set up command-line arguments for server IP and port
    parser = argparse.ArgumentParser(prog="python my_server", description="Server to listen on a specified port.")
    parser.add_argument(
        "server_ip",
        type=str,
        help="The IP address to listen on."
    )
    parser.add_argument(
        "port_number",
        type=int,
        help="The port number to listen on (must be an integer between 1 and 65535)."
    )

    args = parser.parse_args()
    # Run the server with specified IP and port
    run_server(args.server_ip, args.port_number)
