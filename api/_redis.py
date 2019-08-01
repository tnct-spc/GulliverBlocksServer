from settings import REDIS_URL
import redis


redis_connection = redis.from_url(REDIS_URL)