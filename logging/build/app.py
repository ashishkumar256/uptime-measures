from flask import Flask, request, abort
import time
import os
from werkzeug.serving import WSGIRequestHandler
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

@app.route("/")
def home():
    mode = request.args.get("mode", "")
    if mode == "":
        return "Hello world"

    elif mode == "delay":
        time.sleep(10)
        return "Delayed response"

    elif mode == "crash":
        raise Exception("Crashing now!")

    elif mode == "zero_div":
        result = 1 / 0
        return f"This should not execute: {result}"

    else:
        abort(500, description="An internal error was forced due to a mismatch with the specified mode. Available modes: \"\", \"delay\", \"crash\", \"zero_div\"")

@app.route("/health")
def health_check():
    return "OK", 200

# Custom request handler to suppress logs for kube-probe health checks
class QuietHealthProbeHandler(WSGIRequestHandler):
    def log_request(self, code='-', size='-'):
        user_agent = self.headers.get('User-Agent', '')
        path = self.path
        if path == "/health" and user_agent.startswith("kube-probe"):
            return  # Suppress logging
        super().log_request(code, size)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, request_handler=QuietHealthProbeHandler)
