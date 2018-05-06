import redis

class RedisQueue(object):
    """Simple Queue with Redis Backend"""
    def __init__(self, name, namespace='queue', **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self._db= redis.Redis(**redis_kwargs)
        self.key = '%s:%s' %(namespace, name)

    def qsize(self):
        return self._db.llen(self.key)

    def append(self, item):
        self._db.rpush(self.key, item)

    def pop(self, block=True, timeout=None):
        return self._db.lpop(self.key)