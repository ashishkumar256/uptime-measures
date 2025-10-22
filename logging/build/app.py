from flask import Flask, request, abort
import os, sys, json, time, ctypes, argparse
from werkzeug.serving import WSGIRequestHandler
from prometheus_flask_exporter import PrometheusMetrics

import requests, redis, psycopg2, mysql.connector, boto3
from elasticsearch import Elasticsearch

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Global readiness flag
startup_checks_passed = False

# --- Health Check Functions ---

def check_postgres(config):
    print(f"Checking PostgreSQL: {config['name']}...")
    try:
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            dbname=config["dbname"],
            connect_timeout=5
        )
        conn.close()
        print("  -> PostgreSQL check **SUCCESS**.")
        return True
    except Exception as e:
        print(f"  -> PostgreSQL check **FAILURE**: {e}")
        return False

def check_mysql(config):
    print(f"Checking MySQL: {config['name']}...")
    try:
        conn = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            connection_timeout=5
        )
        conn.close()
        print("  -> MySQL check **SUCCESS**.")
        return True
    except Exception as e:
        print(f"  -> MySQL check **FAILURE**: {e}")
        return False

def check_redis(config):
    print(f"Checking Redis: {config['name']}...")
    try:
        r_check = redis.Redis(host=config['host'], port=config['port'], socket_timeout=5)
        r_check.ping()
        print("  -> Redis check **SUCCESS**.")
        return True
    except Exception as e:
        print(f"  -> Redis check **FAILURE**: {e}")
        return False

def check_elasticsearch(config):
    print(f"Checking Elasticsearch: {config['name']}...")
    try:
        es = Elasticsearch([config['url']], timeout=5)
        if es.ping():
            print("  -> Elasticsearch check **SUCCESS**.")
            return True
        else:
            print("  -> Elasticsearch check **FAILURE**: ping returned False.")
            return False
    except Exception as e:
        print(f"  -> Elasticsearch check **FAILURE**: {e}")
        return False

def check_s3(config):
    print(f"Checking S3: {config['name']}...")
    try:
        s3 = boto3.client('s3', region_name=config['region'])
        s3.head_bucket(Bucket=config['bucket_name'])
        print("  -> S3 check **SUCCESS**.")
        return True
    except Exception as e:
        print(f"  -> S3 check **FAILURE**: {e}")
        return False

def check_http_get(config):
    print(f"Checking HTTP GET: {config['name']}...")
    try:
        response = requests.get(config['url'], timeout=config['timeout'])
        if response.status_code == 200:
            print("  -> HTTP GET check **SUCCESS**.")
            return True
        else:
            print(f"  -> HTTP GET check **FAILURE**: Status code {response.status_code}")
            return False
    except Exception as e:
        print(f"  -> HTTP GET check **FAILURE**: {e}")
        return False

# --- Check Dispatcher ---
CHECK_FUNCTIONS = {
    "postgres": check_postgres,
    "mysql": check_mysql,
    "redis": check_redis,
    "elasticsearch": check_elasticsearch,
    "s3": check_s3,
    "http_get": check_http_get,
}

CRITICAL_CATEGORIES = ["database_checks", "caching_checks"]

def perform_startup_checks():
    global startup_checks_passed

    config_json = os.getenv("HEALTH_CHECK_CONFIG")
    if not config_json:
        print("⚠️ HEALTH_CHECK_CONFIG environment variable not found. Skipping startup checks.")
        startup_checks_passed = False
        return

    try:
        config = json.loads(config_json)
    except json.JSONDecodeError:
        print("❌ Failed to parse HEALTH_CHECK_CONFIG JSON. Exiting.")
        startup_checks_passed = False
        return

    all_critical_checks_passed = True
    print("\n--- Starting Pre-Server Health Checks ---")

    for category, checks in config.items():
        if isinstance(checks, list):
            is_critical = category in CRITICAL_CATEGORIES
            for check_config in checks:
                check_type = check_config.get("type")
                check_func = CHECK_FUNCTIONS.get(check_type)

                if check_func:
                    if not check_func(check_config):
                        print(f"Check FAILED: Type={check_type}, Name={check_config.get('name')}")
                        if is_critical:
                            all_critical_checks_passed = False
                            print("  -> This is a **CRITICAL** dependency. Startup will fail.")
                        else:
                            print("  -> This is a non-critical dependency. Startup will continue.")
                else:
                    print(f"Warning: Unknown check type '{check_type}' for {check_config.get('name')}. Skipping.")

    print("--- Finished Pre-Server Health Checks ---\n")
    startup_checks_passed = all_critical_checks_passed

# --- Flask Routes ---

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

@app.route("/readiness-health")
def health_check():
    if startup_checks_passed:
        return "OK", 200
    else:
        return "Startup checks failed", 503

@app.route("/liveness-health")
def health_check():
    return "OK", 200
    
@app.route("/restart")
def restart():
    print("⚠️ Forcing segmentation fault to restart process...")
    ctypes.string_at(0)
    return "This will never execute", 200

class QuietHealthProbeHandler(WSGIRequestHandler):
    def log_request(self, code='-', size='-'):
        user_agent = self.headers.get('User-Agent', '')
        path = self.path
        if path == "/health" and user_agent.startswith("kube-probe"):
            return
        super().log_request(code, size)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask Probe App")
    parser.add_argument("--startup-delay", type=int, default=0, help="Seconds to wait before running startup checks")
    args = parser.parse_args()

    if args.startup_delay > 0:
        print(f"⏳ Waiting {args.startup_delay} seconds before running startup checks...")
        time.sleep(args.startup_delay)

    perform_startup_checks()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, request_handler=QuietHealthProbeHandler)
