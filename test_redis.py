# test_redis.py
import redis.asyncio as aioredis
import asyncio

async def test_redis():
    print("Testing Redis connection...")
    
    try:
        r = await aioredis.from_url("redis://localhost:6379/0", decode_responses=True)
        
        await r.ping()
        print("Redis connected successfully!")
        
        await r.set("test_key", "Hello Redis!")
        value = await r.get("test_key")
        print(f"Read value: {value}")
        
        await r.sadd("test_set", "item1")
        await r.sadd("test_set", "item2")
        members = await r.smembers("test_set")
        print(f"Set members: {members}")
        
        await r.delete("test_key")
        await r.delete("test_set")
        await r.close()
        
        print("\nAll Redis tests passed! Ready to scrape!")
        return True
        
    except Exception as e:
        print(f"Redis connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if Docker is running: docker ps")
        print("2. Check Redis container: docker logs redis-stack")
        print("3. Restart Redis: docker restart redis-stack")
        return False

if __name__ == "__main__":
    asyncio.run(test_redis())