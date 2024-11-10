import socket, argparse
from utils import *  # contains helper functions like `get_content_type`

# Prepare a GET HTTP request message
def prepare_get_message(file_path: str, 
                        server_address: str, 
                        connection_type: str="keep-alive", 
                        server_port: int=8000) -> str:
    return f"GET /{file_path} HTTP/1.1\r\nHost:{server_address}:{server_port}\r\nConnection:{connection_type}\r\n\r\n"

# Prepare a POST HTTP request message with headers for content type and length
def prepare_post_message(file_path: str, 
                         server_address: str, 
                         data_len: int, 
                         connection_type: str="keep-alive", 
                         content_type: str="text/plain",
                         server_port: int=8000) -> str:
    return f"POST /{file_path} HTTP/1.1\r\nHost:{server_address}:{server_port}\r\nConnection:{connection_type}\r\nContent-Type:{content_type}\r\nContent-Length:{data_len}\r\n\r\n"

# Parse a command line input into operation, file path, hostname, and port number
def parse_command(command):
    parts = command.split()
    operation = parts[0]
    file_path = parts[1]
    host_name = parts[2]
    port_number = int(parts[3]) if len(parts) > 3 else 8000
    return operation, file_path, host_name, port_number

# Main client function for sending HTTP requests
def client(server_ip="127.0.0.1", port_no=8000):

    try:
        # Create a socket object using IPv4 and TCP
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to the server using the specified IP and port
        client.connect((server_ip, port_no))
        print(f"Connected to server at {server_ip}:{port_no}")

        # Prompt for input file path containing commands
        # commands = input("Enter the commands file path:")
        commands = "input.txt"
        

        # Read commands from the specified file
        with open(commands, "r") as file:
            commands = file.readlines()
        
        # Process each command in the file
        for command in commands:
            # Parse command for operation type, file path, host name, and port number
            operation, file_path, host_name, port_number = parse_command(command.strip())

            # Determine the content type and set file path for request
            file_type = get_content_type(file_path)
            file_path = os.getcwd() + "/client/" + os.path.basename(file_path)

            if operation not in ["client_get", "client_post"]:
                print(f"Invalid operation: {operation}\n\n")
                continue    

            if operation == "client_post" and not os.path.exists(file_path):
                print(f"File not found: {file_path}\n\n")
                continue
            
            server_ip = host_name
            port_no = port_number

            msg = ""
            # If the operation is a GET request
            if operation == "client_get":
                msg = prepare_get_message(file_path, host_name, port_number)
                client.sendall(msg.encode("utf-8"))  # Send GET request to server

            # If the operation is a POST request
            elif operation == "client_post":
                data = ""
                with open(file_path, "rb") as file:
                    data = file.read()  # Read file data to post
                # Prepare the POST request headers and append file data
                msg = prepare_post_message( file_path=file_path, 
                                            server_address=host_name,
                                            data_len=len(data), 
                                            server_port=port_number,
                                            content_type=get_content_type(file_path),
                                            ).encode("utf-8")
                msg += data  # Append data to message
                client.sendall(msg)  # Send POST request to server

            # Initialize buffer for receiving server response
            request = b""
            while True:
                chunk = client.recv(4096)  # Read data in 4KB chunks
                if b"HTTP" not in chunk:
                    continue
                request += chunk  # Accumulate chunks in request
                if b"\r\n\r\n" in request:  # End of headers detected
                    break
            
            # Find end of headers in the response
            headers_end_b = request.find(b"\r\n\r\n")

            # Decode headers and separate content from headers
            msg = request[:headers_end_b+4].decode('utf-8')
            data = request[headers_end_b+4:]

            print(msg)
            if "404 Not Found" in msg:
                continue

            request_lines = msg.split("\r\n")
            content_length = 0

            # Extract Content-Length if present
            if "Content-Length" in msg:
                for line in request_lines:
                    if line.lower().startswith("content-length:"):
                        content_length = int(line[15:].strip())
                        break
                bytes_remaining = content_length - len(data)
                # Retrieve remaining bytes until content length is satisfied
                while bytes_remaining > 0:
                    chunk = client.recv(4096)
                    data += chunk
                    bytes_remaining -= len(chunk)

                arg = 'w'  # Default write mode
                if "image" in file_type:
                    content = data
                    arg = 'wb'  # Write binary if image
                else:
                    content = data.decode("utf-8")  # Decode text content

                # Save content to file in the client directory
                path = os.getcwd() + "/client/" + os.path.basename(file_path)
                with open(path, arg) as f:
                    f.write(content)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the client socket connection to the server
        client.close()
        print("Connection to server closed")

if __name__ == "__main__":
    # Set up command-line arguments for server IP and port
    parser = argparse.ArgumentParser(prog="python my_server", description="Server to listen on a specified port.")
    parser.add_argument(
        "server_ip", 
        type=str,  
        default="127.0.0.1", 
        help="The ip address to listen on."
    )
    parser.add_argument(
        "port_number", 
        type=int, 
        nargs="?",
        default=8000, 
        help="The port number to listen on (must be an integer between 1 and 65535)."
    )
    
    args = parser.parse_args()

    # Run the client function with provided arguments
    client(args.server_ip, args.port_number)
