from flask import Flask, request, jsonify, abort

import time
import os
import redis

from werkzeug.serving import WSGIRequestHandler
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Redis connection from environment variables
import os
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Set short timeout to simulate failure
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_timeout=1)

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

@app.route('/score/<username>')
def get_score(username):
    score = r.get(username)
    if score is None:
        return jsonify({"message": f"No score found for {username}"}), 404

    score = int(score)
    if score >= 90:
        remark = "Excellent performance!"
    elif score >= 75:
        remark = "Good job!"
    elif score >= 50:
        remark = "Needs improvement."
    else:
        remark = "Poor performance. Let's work on it!"

    return jsonify({
        "username": username,
        "score": score,
        "remark": remark
    })

@app.route('/score/<username>', methods=['POST'])
def set_score(username):
    data = request.get_json()
    score = data.get("score")
    if score is None or not isinstance(score, int):
        return jsonify({"error": "Please provide a valid integer score"}), 400

    r.set(username, score)
    return jsonify({"message": f"Score for {username} set to {score}"}), 200

@app.route('/redis-timeout')
def simulate_timeout():
    try:
        # This Lua script sleeps for 2 seconds, exceeding the 1-second timeout
        r.eval("redis.call('ping'); redis.call('client', 'pause', 2000)", 0)
        return "Redis responded", 200
    except redis.exceptions.TimeoutError:
        return "Redis timeout occurred", 504
    except Exception as e:
        return f"Unexpected error: {str(e)}", 500

@app.route('/redis-block')
def simulate_block():
    try:
        r.blpop("nonexistent-key", timeout=5)  # Will block for 5 seconds
        return "Redis responded", 200
    except redis.exceptions.TimeoutError:
        return "Redis timeout occurred", 504

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, request_handler=QuietHealthProbeHandler)
