import ipaddress
import socket
from urllib.parse import urlparse
from flask import Flask, request
import requests

app = Flask(__name__)

def is_safe_url(target_url: str) -> bool:
    try:
        parsed = urlparse(target_url)

        # 1. Enforce allowed schemes
        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # 2. Resolve hostname to all associated IPs
        # (SOCK_STREAM ensures resolution to standard TCP addresses)
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        
        for entry in addr_info:
            ip_str = entry[4][0]
            ip = ipaddress.ip_address(ip_str)

            # Block private, loopback, link-local, multicast, and reserved ranges
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
            ):
                return False

        return True
    except Exception:
        # Deny on any resolution error or malformed input
        return False


@app.route("/")
def index():
    return "Secured Fetch Endpoint. Validates schemes, DNS resolution, and IP spaces."

@app.route("/fetch")
def fetch():
    target_url = request.args.get("url")
    if not target_url:
        return "Missing 'url' parameter", 400

    # Validate the target prior to sending the request
    if not is_safe_url(target_url):
        return "Request blocked: Target resolves to an internal or restricted network address.", 403

    try:
        # allow_redirects=False prevents bypassing the IP check via an open external redirect
        response = requests.get(target_url, timeout=5, allow_redirects=False)
        return response.text
    except Exception as e:
        return f"Fetch error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)