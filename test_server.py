import http.server
import socketserver

PORT = 3000
Handler = http.server.SimpleHTTPRequestHandler

print(f"Starting server on port {PORT}...")
print(f"Access at http://localhost:{PORT} or http://127.0.0.1:{PORT}")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server running on port {PORT}")
    httpd.serve_forever()