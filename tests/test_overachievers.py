import unittest
from unittest.mock import patch, MagicMock
from http.server import HTTPServer
from io import BytesIO
from octofit_tracker.backend.overachievers import (
    configure_https,
    is_rate_limited,
    check_database_connection,
    validate_environment_variables,
    health_check,
    metrics,
    HealthCheckHandler,
    MetricsHandler,
    start_time,
    load_config_from_file,
    load_environment_config,
    graceful_shutdown,
    log_startup,
    celery_app,
    example_task,
    send_email_task,
    check_redis_connection,
)
import json

class MockRequest:
    """Mock HTTP request for testing."""
    def __init__(self, path):
        self.path = path
        self.client_address = ("127.0.0.1", 12345)
        self.rfile = BytesIO()
        self.wfile = BytesIO()

    def send_response(self, code):
        self.response_code = code

    def send_header(self, key, value):
        pass

    def end_headers(self):
        pass

class TestOverachievers(unittest.TestCase):
    @patch("os.path.exists", return_value=True)
    @patch("ssl.create_default_context")
    def test_configure_https(self, mock_ssl_context, mock_path_exists):
        """Test HTTPS configuration with valid certificate and key files."""
        cert_file = "/path/to/certificate.crt"
        key_file = "/path/to/private.key"
        context = configure_https(cert_file, key_file)
        mock_ssl_context.assert_called_once()
        self.assertIsNotNone(context)

    def test_is_rate_limited(self):
        """Test rate limiting functionality."""
        client_ip = "127.0.0.1"
        self.assertFalse(is_rate_limited(client_ip))
        for _ in range(5):
            is_rate_limited(client_ip)
        self.assertTrue(is_rate_limited(client_ip))

    def test_check_database_connection(self):
        """Test database connection check."""
        with patch("octofit_tracker.backend.overachievers.logger") as mock_logger:
            result = check_database_connection()
            self.assertIn(result["status"], ["connected", "disconnected", "error"])
            mock_logger.error.assert_not_called()

    def test_validate_environment_variables(self):
        """Test validation of required environment variables."""
        with patch("os.getenv", side_effect=lambda var: "value" if var in ["CERT_FILE", "KEY_FILE"] else None):
            try:
                validate_environment_variables(["CERT_FILE", "KEY_FILE"])
            except EnvironmentError:
                self.fail("validate_environment_variables raised EnvironmentError unexpectedly!")

        with patch("os.getenv", side_effect=lambda var: None):
            with self.assertRaises(EnvironmentError):
                validate_environment_variables(["CERT_FILE", "KEY_FILE"])

    def test_health_check(self):
        """Test health check functionality."""
        initial_health_checks = metrics["health_checks"]
        health_check()
        self.assertEqual(metrics["health_checks"], initial_health_checks + 1)

class TestHTTPHandlers(unittest.TestCase):
    def test_health_check_handler_root(self):
        """Test the root endpoint."""
        request = MockRequest("/")
        handler = HealthCheckHandler(request, None, None)
        handler.do_GET()
        self.assertEqual(request.response_code, 200)

    def test_health_check_handler_health(self):
        """Test the /health endpoint."""
        request = MockRequest("/health")
        handler = HealthCheckHandler(request, None, None)
        handler.do_GET()
        self.assertEqual(request.response_code, 200)

    def test_health_check_handler_status(self):
        """Test the /status endpoint."""
        request = MockRequest("/status")
        handler = HealthCheckHandler(request, None, None)
        handler.do_GET()
        self.assertEqual(request.response_code, 200)

    def test_metrics_handler(self):
        """Test the /metrics endpoint."""
        request = MockRequest("/metrics")
        handler = MetricsHandler(request, None, None)
        handler.do_GET()
        self.assertEqual(request.response_code, 200)

class TestEdgeCases(unittest.TestCase):
    def test_health_check_handler_invalid_path(self):
        """Test an invalid path."""
        request = MockRequest("/invalid")
        handler = HealthCheckHandler(request, None, None)
        handler.do_GET()
        self.assertEqual(request.response_code, 404)

    def test_validate_environment_variables_missing(self):
        """Test validation of missing environment variables."""
        with patch("os.getenv", side_effect=lambda var: None):
            with self.assertRaises(EnvironmentError):
                validate_environment_variables(["MISSING_VAR"])

class TestRateLimiting(unittest.TestCase):
    def test_rate_limiting_single_client(self):
        """Test rate limiting for a single client."""
        client_ip = "127.0.0.1"
        for _ in range(5):
            self.assertFalse(is_rate_limited(client_ip))
        self.assertTrue(is_rate_limited(client_ip))

    def test_rate_limiting_multiple_clients(self):
        """Test rate limiting for multiple clients."""
        client_ip_1 = "127.0.0.1"
        client_ip_2 = "192.168.1.1"
        for _ in range(5):
            self.assertFalse(is_rate_limited(client_ip_1))
            self.assertFalse(is_rate_limited(client_ip_2))
        self.assertTrue(is_rate_limited(client_ip_1))
        self.assertTrue(is_rate_limited(client_ip_2))

class TestErrorResponses(unittest.TestCase):
    def test_health_check_handler_error(self):
        """Test error response for health check."""
        with patch("octofit_tracker.backend.overachievers.check_database_connection", side_effect=Exception("Database error")):
            request = MockRequest("/health")
            handler = HealthCheckHandler(request, None, None)
            handler.do_GET()
            self.assertEqual(request.response_code, 500)

class TestConfiguration(unittest.TestCase):
    def test_load_config_from_file_valid(self):
        """Test loading a valid configuration file."""
        valid_config = {"CERT_FILE": "/path/to/certificate.crt", "KEY_FILE": "/path/to/private.key"}
        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(valid_config))):
            with patch("os.path.exists", return_value=True):
                config = load_config_from_file("/path/to/config.json")
                self.assertEqual(config, valid_config)

    def test_load_config_from_file_missing(self):
        """Test loading a missing configuration file."""
        with patch("os.path.exists", return_value=False):
            with self.assertRaises(FileNotFoundError):
                load_config_from_file("/path/to/missing_config.json")

    def test_load_environment_config_valid(self):
        """Test loading a valid environment-specific configuration."""
        with patch("os.getenv", side_effect=lambda var: "development" if var == "ENVIRONMENT" else None):
            config = load_environment_config()
            self.assertEqual(config["health_check_port"], 8080)
            self.assertEqual(config["log_level"], "DEBUG")

    def test_load_environment_config_invalid(self):
        """Test loading an invalid environment-specific configuration."""
        with patch("os.getenv", side_effect=lambda var: "invalid" if var == "ENVIRONMENT" else None):
            with self.assertRaises(ValueError):
                load_environment_config()

class TestGracefulShutdown(unittest.TestCase):
    def test_graceful_shutdown(self):
        """Test graceful shutdown behavior."""
        with patch("octofit_tracker.backend.overachievers.logger") as mock_logger:
            with patch("threading.Thread.join") as mock_join:
                with patch("http.server.HTTPServer.server_close") as mock_server_close:
                    graceful_shutdown()
                    mock_logger.info.assert_any_call("Performing graceful shutdown...")
                    mock_server_close.assert_called()
                    mock_join.assert_called()

class TestLoggingBehavior(unittest.TestCase):
    def test_log_startup(self):
        """Test logging during application startup."""
        with patch("octofit_tracker.backend.overachievers.logger") as mock_logger:
            log_startup()
            mock_logger.info.assert_any_call("Starting OctoFit Tracker - Overachievers API...")
            mock_logger.info.assert_any_call("Environment: development")
            mock_logger.info.assert_any_call("Health Check Port: 8080")
            mock_logger.info.assert_any_call("Metrics Port: 9090")

class TestCeleryIntegration(unittest.TestCase):
    def test_celery_task_execution(self):
        """Test that a Celery task executes successfully."""
        result = example_task.apply().get()
        self.assertEqual(result, "Task completed successfully!")

    def test_celery_configuration(self):
        """Test that Celery is configured with the correct broker and backend."""
        self.assertEqual(celery_app.conf.broker_url, "redis://localhost:6379/0")
        self.assertEqual(celery_app.conf.result_backend, "redis://localhost:6379/0")

class TestDatabaseConnection(unittest.TestCase):
    def test_check_database_connection_success(self):
        """Test successful database connection."""
        with patch("octofit_tracker.backend.overachievers.logger") as mock_logger:
            result = check_database_connection()
            self.assertEqual(result["status"], "connected")
            mock_logger.error.assert_not_called()

    def test_check_database_connection_failure(self):
        """Test failed database connection."""
        with patch("octofit_tracker.backend.overachievers.logger") as mock_logger:
            with patch("octofit_tracker.backend.overachievers.check_database_connection", side_effect=Exception("Connection error")):
                result = check_database_connection()
                self.assertEqual(result["status"], "error")
                self.assertIn("error", result)
                mock_logger.error.assert_called_with("Database connection check failed: Connection error")

class TestEmailTask(unittest.TestCase):
    @patch("octofit_tracker.backend.overachievers.smtplib.SMTP")
    def test_send_email_task_success(self, mock_smtp):
        """Test successful email sending."""
        result = send_email_task("test@example.com", "Test Subject", "Test Message")
        self.assertEqual(result, "Email sent to test@example.com")
        mock_smtp.assert_called_once()

    @patch("octofit_tracker.backend.overachievers.smtplib.SMTP", side_effect=Exception("SMTP error"))
    def test_send_email_task_failure(self, mock_smtp):
        """Test failed email sending."""
        with self.assertRaises(Exception):
            send_email_task("test@example.com", "Test Subject", "Test Message")

class TestRedisConnection(unittest.TestCase):
    def test_check_redis_connection_success(self):
        """Test successful Redis connection."""
        with patch("octofit_tracker.backend.overachievers.Redis.from_url") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            result = check_redis_connection()
            self.assertEqual(result["status"], "connected")

    def test_check_redis_connection_failure(self):
        """Test failed Redis connection."""
        with patch("octofit_tracker.backend.overachievers.Redis.from_url", side_effect=Exception("Connection error")):
            result = check_redis_connection()
            self.assertEqual(result["status"], "error")
            self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()
