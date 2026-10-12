from flask import Flask, request
import requests

app = Flask(__name__)

@app.route("/")
def index():
    return "Vulnerable Webhook/Fetch Endpoint. Use ?url=http://example.com to fetch."

@app.route("/fetch")
def fetch():
    target_url = request.args.get("url")
    if not target_url:
        return "Missing 'url' parameter", 400

    try:
        # VULNERABILITY:
        # 1. No validation on scheme (file://, gopher://, etc. if using raw sockets/curl)
        # 2. No check for loopback (127.0.0.1) or private IP spaces (10.0.0.0/8, 172.16.0.0/12, etc.)
        # 3. Follows redirects indiscriminately
        response = requests.get(target_url, timeout=5)
        return response.text
    except Exception as e:
        return f"Fetch error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)