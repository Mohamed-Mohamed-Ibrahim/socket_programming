import os

MIME_TYPES = {
    ".html": "text/html",
    ".txt": "text/plain",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".css": "text/css",
    ".js": "application/javascript",
    # Add more MIME types as needed
}

BUFFER_SIZE = 4096

def get_file_type(file_path):
    _, file_extension = os.path.splitext(file_path)
    return file_extension.lower()

def get_content_type(path):
    # Return the MIME type based on file extension, default to 'application/octet-stream' for unknown types
    return MIME_TYPES.get(get_file_type(path), "application/octet-stream")

def recvall(sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        return buf
