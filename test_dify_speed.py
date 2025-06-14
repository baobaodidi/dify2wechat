 #!/usr/bin/env python3
import asyncio
import time
import httpx
from loguru import logger

DIFY_API_BASE = "http://localhost/v1"
DIFY_API_KEY = "app-your-dify-api-key-here"

async def test_dify_speed():
    test_messages = ["你好", "今天天气怎么样？", "请介绍一下你自己"]
    
    for i, message in enumerate(test_messages, 1):
        logger.info(f"测试 {i}/3: {message}")
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {DIFY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": {},
                "query": message,
                "response_mode": "blocking",
                "user": f"test_user_{i}"
            }
            
            timeout = httpx.Timeout(connect=1.0, read=10.0, write=1.0, pool=1.0)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{DIFY_API_BASE}/chat-messages",
                    headers=headers,
                    json=payload
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get("answer", "")
                    logger.success(f"✅ 响应时间: {response_time:.2f}秒")
                    logger.info(f"回复: {answer[:100]}...")
                else:
                    logger.error(f"❌ API调用失败: {response.status_code}")
                    
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            logger.error(f"💥 请求异常: {e}, 耗时: {response_time:.2f}秒")
        
        await asyncio.sleep(1)

if __name__ == "__main__":
    logger.info("🚀 开始测试Dify API响应速度...")
    asyncio.run(test_dify_speed())
    logger.info("✨ 测试完成")