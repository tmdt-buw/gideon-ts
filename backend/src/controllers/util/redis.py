import redis

from src.config.settings import get_settings

redis_instance = redis.Redis(host=get_settings().redis_url, port=get_settings().redis_port)
