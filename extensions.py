import os
import redis
# [架构思考] 为什么要用 ConnectionPool (连接池)？
# 普通连接：每次操作 Redis 都要进行 TCP 三次握手(建立) -> 发数据 -> 四次挥手(断开)。这非常慢！
# 连接池：  先把连接建好放在池子里，要用的时候捞一个，用完放回去。复用连接，性能提升 10 倍以上。

redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))


# 2. 初始化连接池
# decode_responses=True 很重要！
# 如果不加，Redis 返回的是 bytes 类型 (b'hello')，加了直接返回 string ('hello')，省得你自己 decode。

pool = redis.ConnectionPool(
    host=redis_host,
    port=redis_port,
    db=0,
    decode_responses=True
)

redis_client = redis.Redis(connection_pool=pool)

#