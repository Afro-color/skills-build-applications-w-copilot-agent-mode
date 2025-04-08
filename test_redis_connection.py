from redis import Redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def check_redis_connection():
    try:
        redis_client = Redis.from_url(REDIS_URL)
        redis_client.ping()
        print("Redis connection successful!")
    except Exception as e:
        print(f"Redis connection failed: {e}")

if __name__ == "__main__":
    check_redis_connection()
