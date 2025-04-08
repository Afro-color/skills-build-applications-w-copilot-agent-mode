import os
import shutil
import ssl
import logging
import time
import signal
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread, Lock
from datetime import datetime
from collections import defaultdict
from time import time

# Configure structured logging dynamically based on environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json").lower()

if LOG_FORMAT == "json":
    import json_log_formatter
    formatter = json_log_formatter.JSONFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(LOG_LEVEL)
else:
    logging.basicConfig(level=LOG_LEVEL)
    logger = logging.getLogger(__name__)

# Metrics collection with thread safety
metrics = {"health_checks": 0, "https_failures": 0}
metrics_lock = Lock()

# Uptime tracking
start_time = datetime.now()

# Rate limiting configuration
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 5))  # Max requests per second
rate_limit_data = defaultdict(lambda: {"last_request": 0, "request_count": 0})

def is_rate_limited(client_ip):
    """Check if a client IP is rate-limited."""
    current_time = time()
    client_data = rate_limit_data[client_ip]
    if current_time - client_data["last_request"] > 1:
        client_data["last_request"] = current_time
        client_data["request_count"] = 1
        return False
    else:
        client_data["request_count"] += 1
        if client_data["request_count"] > RATE_LIMIT:
            return True
        return False

def ensure_correct_folder(expected_folder):
    """Ensure the script is running from the correct folder."""
    current_folder = os.path.basename(os.path.dirname(__file__))
    if current_folder != expected_folder:
        raise RuntimeError(f"Expected to be in the '{expected_folder}' folder, but found '{current_folder}'.")

def ensure_correct_module_name(expected_module_name):
    """Ensure the module name is correct."""
    if __name__ != expected_module_name:
        raise ImportError(f"Module incorrectly named. Expected module name: '{expected_module_name}', but got '{__name__}'.")

def clear_pycache():
    """Clear the __pycache__ directory if it exists."""
    pycache_path = os.path.join(os.path.dirname(__file__), '__pycache__')
    if os.path.exists(pycache_path):
        try:
            shutil.rmtree(pycache_path)
            logger.info("__pycache__ cleared.")
        except PermissionError:
            logger.error(f"Permission denied: Unable to clear {pycache_path}.")
        except Exception as e:
            logger.error(f"An error occurred while clearing __pycache__: {e}")
    else:
        logger.info("__pycache__ directory does not exist.")

def initialize_package():
    """Initialize the package with a basic message."""
    logger.info("OctoFit Tracker - Overachievers package initialized.")

def configure_https(cert_file, key_file, retries=3, delay=2):
    """Configure HTTPS using the provided certificate and key files with retries."""
    for attempt in range(retries):
        try:
            if not os.path.exists(cert_file) or not os.path.exists(key_file):
                raise FileNotFoundError("Certificate or key file not found. Ensure HTTPS files are correctly configured.")
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)
            logger.info("HTTPS configured successfully.")
            return ssl_context
        except Exception as e:
            with metrics_lock:
                metrics["https_failures"] += 1
            logger.warning(f"Attempt {attempt + 1} to configure HTTPS failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logger.error("All attempts to configure HTTPS have failed.")
                raise

def validate_environment_variables(required_vars):
    """Validate that all required environment variables are set."""
    for var in required_vars:
        if not os.getenv(var):
            raise EnvironmentError(f"Required environment variable '{var}' is not set.")
    logger.info("All required environment variables are set.")

def graceful_shutdown(signum=None, frame=None):
    """Perform cleanup tasks during application shutdown."""
    logger.info("Performing graceful shutdown...")
    for server in servers:
        logger.info(f"Shutting down server: {server.server_address}")
        server.server_close()
    for thread in threads:
        if thread.is_alive():
            logger.info(f"Stopping thread: {thread.name}")
            thread.join(timeout=5)
    logger.info("All threads and servers stopped. Shutdown complete.")
    exit(0)

def health_check():
    """Perform a basic health check."""
    with metrics_lock:
        metrics["health_checks"] += 1
    logger.info("Health check passed. Application is running correctly.")

def load_config_from_file(config_path):
    """Load configuration from a JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file '{config_path}' not found.")
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    logger.info(f"Configuration loaded from {config_path}.")
    return config

def load_environment_config():
    """Load environment-specific configuration."""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    logger.info(f"Loading configuration for environment: {environment}")

    config = {
        "development": {
            "health_check_port": 8080,
            "log_level": "DEBUG",
            "metrics_port": 9090,
        },
        "staging": {
            "health_check_port": 8081,
            "log_level": "INFO",
            "metrics_port": 9091,
        },
        "production": {
            "health_check_port": 80,
            "log_level": "WARNING",
            "metrics_port": 9092,
        },
    }.get(environment, {})

    if not config:
        raise ValueError(f"Unknown environment: {environment}")

    return config

def check_database_connection():
    """Check database connectivity."""
    # Simulate a database connection check (replace with actual logic)
    try:
        connected = True  # Simulated database connection status
        if connected:
            return {"status": "connected"}
        else:
            return {"status": "disconnected"}
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return {"status": "error", "error": str(e)}

class RateLimitedHandler(BaseHTTPRequestHandler):
    """Base HTTP handler with rate limiting and request logging."""
    def log_request(self, code="-", size="-"):
        """Log the HTTP request."""
        logger.info(f"Request from {self.client_address[0]}: {self.command} {self.path} {code}")

    def handle_rate_limit(self):
        client_ip = self.client_address[0]
        if is_rate_limited(client_ip):
            self.log_request(429)
            self.send_response(429)  # Too Many Requests
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Too many requests"}).encode())
            return True
        return False

class HealthCheckHandler(RateLimitedHandler):
    """HTTP handler for health check endpoint."""
    def do_GET(self):
        if self.handle_rate_limit():
            return
        if self.path == "/health":
            uptime = (datetime.now() - start_time).total_seconds()
            db_status = check_database_connection()
            response = {
                "status": "healthy" if db_status["status"] == "connected" else "unhealthy",
                "uptime_seconds": uptime,
                "metrics": metrics,
                "database": db_status
            }
            self.log_request(200 if db_status["status"] == "connected" else 500)
            self.send_response(200 if db_status["status"] == "connected" else 500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.log_request(404)
            self.send_response(404)
            self.end_headers()

class MetricsHandler(RateLimitedHandler):
    """HTTP handler for Prometheus-compatible metrics endpoint."""
    def do_GET(self):
        if self.handle_rate_limit():
            return
        if self.path == "/metrics":
            with metrics_lock:
                metrics_data = [
                    f"health_checks_total {metrics['health_checks']}",
                    f"https_failures_total {metrics['https_failures']}",
                    f"uptime_seconds {(datetime.now() - start_time).total_seconds()}",
                ]
            response = "\n".join(metrics_data)
            self.log_request(200)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            self.wfile.write(response.encode())
        else:
            self.log_request(404)
            self.send_response(404)
            self.end_headers()

# Global variables to manage threads and servers
threads = []
servers = []

def start_health_check_server(port=None):
    """Start a simple HTTP server for health checks."""
    port = port or int(os.getenv("HEALTH_CHECK_PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    servers.append(server)
    logger.info(f"Health check server running on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Health check server shutting down...")
        server.server_close()

def start_metrics_server(port=None):
    """Start a simple HTTP server for Prometheus-compatible metrics."""
    port = port or int(os.getenv("METRICS_PORT", 9090))
    server = HTTPServer(("0.0.0.0", port), MetricsHandler)
    servers.append(server)
    logger.info(f"Metrics server running on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Metrics server shutting down...")
        server.server_close()

def validate_config(config, required_keys):
    """Validate the loaded configuration."""
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Missing required configuration keys: {', '.join(missing_keys)}")
    logger.info("Configuration validation passed.")

# === Main Initialization Logic ===
try:
    # Load environment-specific configuration
    env_config = load_environment_config()
    os.environ["LOG_LEVEL"] = env_config.get("log_level", "INFO")
    health_check_port = env_config.get("health_check_port", 8080)
    metrics_port = env_config.get("metrics_port", 9090)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, graceful_shutdown)
    signal.signal(signal.SIGINT, graceful_shutdown)

    ensure_correct_folder("overachievers")
    ensure_correct_module_name("overachievers")
    clear_pycache()
    initialize_package()

    # Start health check server in a separate thread with dynamic port
    health_check_thread = Thread(target=start_health_check_server, args=(health_check_port,), daemon=True, name="HealthCheckThread")
    health_check_thread.start()
    threads.append(health_check_thread)

    # Start metrics server in a separate thread with dynamic port
    metrics_thread = Thread(target=start_metrics_server, args=(metrics_port,), daemon=True, name="MetricsThread")
    metrics_thread.start()
    threads.append(metrics_thread)

    # Load configuration from file or environment variables
    CONFIG_PATH = os.getenv("CONFIG_PATH", "/path/to/config.json")
    try:
        config = load_config_from_file(CONFIG_PATH)
        validate_config(config, ["CERT_FILE", "KEY_FILE"])
        CERT_FILE = config.get("CERT_FILE", "/path/to/certificate.crt")
        KEY_FILE = config.get("KEY_FILE", "/path/to/private.key")
    except Exception as e:
        logger.warning(f"Failed to load configuration file: {e}. Falling back to environment variables.")
        CERT_FILE = os.getenv("CERT_FILE", "/path/to/certificate.crt")
        KEY_FILE = os.getenv("KEY_FILE", "/path/to/private.key")

    # Validate required environment variables
    REQUIRED_ENV_VARS = ["CERT_FILE", "KEY_FILE"]
    validate_environment_variables(REQUIRED_ENV_VARS)

    # HTTPS Configuration
    try:
        ssl_context = configure_https(CERT_FILE, KEY_FILE)
    except Exception as e:
        logger.warning(f"Failed to configure HTTPS: {e}. Running without HTTPS.")

    # Perform a health check
    health_check()

except Exception as e:
    logger.error(f"Application failed to start: {e}")
    graceful_shutdown()
    raise