import time
import json
import random
import pandas as pd
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError
from datetime import datetime

# ================= 配置 =================
OUTPUT_FILE = "trending_data.json"
HL = 'en-US'
TZ = 360  # US CST

# 这里是完整的种子词列表 (模拟原网站的279个)
# 为了演示，我先放入我们分类出来的几十个核心词。
# 实际运行时，你可以把279个词都填进去。
SEEDS = [
    # AI & Generator
    "ai", "assistant", "generator", "creator", "maker", "builder", "agent", 
    "chatbot", "llm", "diffusion", "copilot",
    # Tools
    "upscale", "unblur", "editor", "enhancer", "converter", "scraper", "crawler",
    "detector", "checker", "analyzer", "summarizer", "writer",
    # Platforms
    "roblox", "steam", "discord", "twitch", "tiktok", "instagram", "youtube",
    # Tech
    "python", "javascript", "react", "nextjs", "css", "linux", "docker",
    # Web3 / Finance
    "crypto", "bitcoin", "ethereum", "nft", "trading", "investment", "stock",
    # General / Yearly
    "2026", "trends", "news", "best", "top", "guide", "tutorial"
]

# 在本地测试时，只取前 5 个，避免等待太久
# 部署到 GitHub Actions 时，可以去掉这个切片
ACTIVE_SEEDS = SEEDS[:] # 使用全部 (需注意频率限制)

def scrape():
    print(f"[*] 启动抓取任务 - {datetime.now()}")
    print(f"[*] 目标种子词数: {len(ACTIVE_SEEDS)}")
    
    # 尝试加载现有数据，实现增量更新（防止一次挂掉全部重来）
    try:
        with open(OUTPUT_FILE, 'r') as f:
            existing_data = json.load(f).get('data', {})
            print(f"[*] 已加载现有数据: {len(existing_data)} 个分类")
    except FileNotFoundError:
        existing_data = {}
        print("[*] 未发现现有数据，将创建新文件")

    pytrends = TrendReq(hl=HL, tz=TZ,  timeout=(10,25), retries=2, backoff_factor=0.2)
    
    success_count = 0
    fail_count = 0
    
    for i, keyword in enumerate(ACTIVE_SEEDS):
        print(f"\n[{i+1}/{len(ACTIVE_SEEDS)}] 正在处理: {keyword}")
        
        try:
            pytrends.build_payload([keyword], cat=0, timeframe='now 7-d', geo='', gprop='')
            related = pytrends.related_queries()
            data_payload = related.get(keyword)
            
            if data_payload and data_payload['rising'] is not None:
                df = data_payload['rising']
                
                # 转换 Breakout 为可视化数值或字符串
                # 这里的逻辑是直接保存原始值，前端处理显示
                records = df.to_dict('records')
                
                # 存入大字典
                existing_data[keyword] = records
                success_count += 1
                print(f"    √ 获取到 {len(records)} 个飙升词")
            else:
                print(f"    - 无飙升数据")
                existing_data[keyword] = [] # 记录为空，避免重复请求? 也可以不记录

            # 关键：随机休眠 2-6 秒，模拟人类
            # 如果是 GitHub Actions，可以把这个时间设得更长，比如 60 秒，反正跑在云端不急
            sleep_time = random.uniform(2, 5)
            print(f"    ...休息 {sleep_time:.1f} 秒...")
            time.sleep(sleep_time)

        except ResponseError as e:
            print(f"    x Google 429 Error (Too Many Requests). 暂停 60秒...")
            fail_count += 1
            time.sleep(60) # 遇到限制就睡 1 分钟
        except Exception as e:
            print(f"    x 错误: {e}")
            fail_count += 1

    # 保存结果
    output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": existing_data
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
        
    print(f"\n[*] 任务结束. 成功: {success_count}, 失败: {fail_count}")
    print(f"[*] 数据已保存至 {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape()
