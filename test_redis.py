"""Test Redis connection."""

from src.config import config
from src.redis_cache import RedisCacheClient

def test_redis():
    """Test Redis connection and configuration."""
    print("=== Redis Configuration ===")
    print(f"Host: {config.redis.host}")
    print(f"Port: {config.redis.port}")
    print(f"SSL: {config.redis.ssl}")
    print(f"Password set: {'Yes' if config.redis.password else 'No'}")
    print()

    if not config.redis.host or not config.redis.password:
        print("❌ Redis is not configured!")
        print("Please set REDIS_HOST and REDIS_ACCESS_KEY in your .env file")
        return

    print("=== Testing Redis Connection ===")
    client = RedisCacheClient()
    redis_client = client._get_redis_client()

    if redis_client is None:
        print("❌ Failed to connect to Redis")
        print("Check your credentials and network connectivity")
        return

    try:
        # Test ping
        result = redis_client.ping()
        print(f"✅ Redis ping successful: {result}")

        # Test set/get
        test_key = "test_key"
        test_value = "test_value"
        redis_client.setex(test_key, 60, test_value)
        retrieved = redis_client.get(test_key)
        
        if retrieved == test_value:
            print(f"✅ Redis set/get test successful")
        else:
            print(f"❌ Redis set/get test failed: expected '{test_value}', got '{retrieved}'")

        # Cleanup
        redis_client.delete(test_key)
        print("✅ Redis is working correctly!")

    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_redis()

