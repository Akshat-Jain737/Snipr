import time
import uuid

from fastapi import Request, HTTPException
import redis.asyncio as aioredis
rdis = aioredis.from_url(url='redis://localhost:6379', decode_responses=True)

async def rate_limit(request:Request):
    ip=request.client.host
    window_limit=10
    key=f'rate_limt:{ip}'
    window_size=60
    curr_time=time.time()
    window=curr_time-window_size
    req_id=str(uuid.uuid4())
    pipe=rdis.pipeline()
    async with rdis.pipeline() as pipe:
        pipe.zremrangebyscore(key, 0, window)
        pipe.zadd(key, {req_id: curr_time})
        pipe.zcard(key)
        pipe.expire(key, window_size)
        result = pipe.execute()
    total_Request_in_window=result[2]
    if total_Request_in_window>window_limit:
        raise HTTPException(status_code=429, detail="to many requests")
