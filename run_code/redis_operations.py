import redis
from typing import List, Optional, Dict
import settings

class RedisOperations:
    def __init__(self, host: str = settings.REDIS_HOST, port: int = settings.REDIS_PORT, db: int = 0):
        self.client = redis.Redis(host=host, port=port, db=db)

    def set_value(self, key: str, value: str, ex: int=None) -> bool:
        try:
            self.client.set(key, value, ex=ex)
            return True
        except Exception as e:
            print(f"Error setting value: {e}")
            return False

    def get_value(self, key: str) -> Optional[str]:
        try:
            value = self.client.get(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            print(f"Error getting value: {e}")
            return None

    def delete_key(self, key: str) -> bool:
        try:
            result = self.client.delete(key)
            return result > 0
        except Exception as e:
            print(f"Error deleting key: {e}")
            return False

    def push_to_list(self, list_name: str, value: str) -> bool:
        try:
            self.client.rpush(list_name, value)
            return True
        except Exception as e:
            print(f"Error pushing to list: {e}")
            return False

    def pop_from_list(self, list_name: str) -> Optional[str]:
        try:
            value = self.client.lpop(list_name)
            return value.decode('utf-8') if value else None
        except Exception as e:
            print(f"Error popping from list: {e}")
            return None

    def get_all_from_list(self, list_name: str) -> List[str]:
        try:
            values = self.client.lrange(list_name, 0, -1)
            return [value.decode('utf-8') for value in values]
        except Exception as e:
            print(f"Error getting all from list: {e}")
            return []

    def set_hash_field(self, hash_name: str, field: str, value: str) -> bool:
        try:
            self.client.hset(hash_name, field, value)
            return True
        except Exception as e:
            print(f"Error setting hash field: {e}")
            return False

    def get_hash_field(self, hash_name: str, field: str) -> Optional[str]:
        try:
            value = self.client.hget(hash_name, field)
            return value.decode('utf-8') if value else None
        except Exception as e:
            print(f"Error getting hash field: {e}")
            return None

    def get_all_from_hash(self, hash_name: str) -> Dict[str, str]:
        try:
            fields = self.client.hgetall(hash_name)
            return {k.decode('utf-8'): v.decode('utf-8') for k, v in fields.items()}
        except Exception as e:
            print(f"Error getting all from hash: {e}")
            return {}


redis_operations = RedisOperations()


if __name__ == "__main__":
    redis_ops = RedisOperations()

    # Set and get a value
    redis_ops.set_value('my_key', 'my_value')
    print(redis_ops.get_value('my_key'))

    # Push and pop from a list
    redis_ops.push_to_list('my_list', 'item1')
    redis_ops.push_to_list('my_list', 'item2')
    print(redis_ops.pop_from_list('my_list'))

    # Set and get from a hash
    redis_ops.set_hash_field('my_hash', 'field1', 'value1')
    print(redis_ops.get_hash_field('my_hash', 'field1'))

    # Get all from a hash
    print(redis_ops.get_all_from_hash('my_hash'))
