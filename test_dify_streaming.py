 #!/usr/bin/env python3
import asyncio
import time
import httpx
from loguru import logger

DIFY_API_BASE = "http://localhost/v1"
DIFY_API_KEY = "app-your-dify-api-key-here"

async def test_streaming_response():
    """测试Dify流式响应速度"""
    
    test_messages = ["你好", "今天天气怎么样？", "请介绍一下你自己"]
    
    for i, message in enumerate(test_messages, 1):
        logger.info(f"测试流式响应 {i}/3: {message}")
        start_time = time.time()
        first_byte_time = None
        
        try:
            headers = {
                "Authorization": f"Bearer {DIFY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": {},
                "query": message,
                "response_mode": "streaming",
                "user": f"test_user_{i}"
            }
            
            timeout = httpx.Timeout(connect=1.0, read=10.0, write=1.0, pool=1.0)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    f"{DIFY_API_BASE}/chat-messages",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status_code != 200:
                        logger.error(f"❌ API调用失败: {response.status_code}")
                        continue
                    
                    answer = ""
                    async for line in response.aiter_lines():
                        if first_byte_time is None:
                            first_byte_time = time.time()
                            logger.success(f"⚡ 首字节时间: {first_byte_time - start_time:.2f}秒")
                        
                        if line.startswith("data: "):
                            try:
                                import json
                                data = json.loads(line[6:])
                                
                                if data.get("event") == "message":
                                    answer += data.get("answer", "")
                                elif data.get("event") == "message_end":
                                    break
                            except json.JSONDecodeError:
                                continue
                    
                    end_time = time.time()
                    total_time = end_time - start_time
                    logger.success(f"✅ 总响应时间: {total_time:.2f}秒")
                    logger.info(f"回复: {answer[:100]}...")
                    
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            logger.error(f"💥 请求异常: {e}, 耗时: {response_time:.2f}秒")
        
        await asyncio.sleep(1)

async def test_blocking_vs_streaming():
    """对比阻塞模式和流式模式的性能"""
    
    message = "你好"
    
    # 测试阻塞模式
    logger.info("🔄 测试阻塞模式...")
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
            "user": "test_blocking"
        }
        
        timeout = httpx.Timeout(connect=1.0, read=10.0, write=1.0, pool=1.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{DIFY_API_BASE}/chat-messages",
                headers=headers,
                json=payload
            )
            
            end_time = time.time()
            blocking_time = end_time - start_time
            
            if response.status_code == 200:
                logger.success(f"🔄 阻塞模式响应时间: {blocking_time:.2f}秒")
            else:
                logger.error(f"❌ 阻塞模式失败: {response.status_code}")
                
    except Exception as e:
        logger.error(f"💥 阻塞模式异常: {e}")
    
    await asyncio.sleep(1)
    
    # 测试流式模式
    logger.info("⚡ 测试流式模式...")
    start_time = time.time()
    first_byte_time = None
    
    try:
        payload["response_mode"] = "streaming"
        payload["user"] = "test_streaming"
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{DIFY_API_BASE}/chat-messages",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status_code != 200:
                    logger.error(f"❌ 流式模式失败: {response.status_code}")
                    return
                
                async for line in response.aiter_lines():
                    if first_byte_time is None:
                        first_byte_time = time.time()
                        first_byte_duration = first_byte_time - start_time
                        logger.success(f"⚡ 流式模式首字节时间: {first_byte_duration:.2f}秒")
                        break
                
                end_time = time.time()
                streaming_time = end_time - start_time
                logger.success(f"⚡ 流式模式总时间: {streaming_time:.2f}秒")
                
                if first_byte_time:
                    improvement = blocking_time - first_byte_duration
                    logger.info(f"📈 首字节时间改善: {improvement:.2f}秒 ({improvement/blocking_time*100:.1f}%)")
                
    except Exception as e:
        logger.error(f"💥 流式模式异常: {e}")

if __name__ == "__main__":
    logger.info("🚀 开始测试Dify流式响应...")
    asyncio.run(test_streaming_response())
    
    logger.info("\n" + "="*50)
    logger.info("🆚 对比测试：阻塞模式 vs 流式模式")
    asyncio.run(test_blocking_vs_streaming())
    
    logger.info("✨ 测试完成")