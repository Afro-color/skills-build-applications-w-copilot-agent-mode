import unittest
from redis import Redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class TestRedisConnection(unittest.TestCase):
    def test_redis_connection(self):
        try:
            redis_client = Redis.from_url(REDIS_URL)
            self.assertTrue(redis_client.ping(), "Redis connection failed")
        except Exception as e:
            self.fail(f"Redis connection test raised an exception: {e}")

if __name__ == "__main__":
    unittest.main()
