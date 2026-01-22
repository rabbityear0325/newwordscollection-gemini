import time
import json
import random
import os
import pandas as pd
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError
from datetime import datetime

# ================= 配置: 极度保守模式 =================
OUTPUT_FILE = "trending_data.json"
HL = 'en-US'
TZ = 360  # US CST

# 策略配置
BATCH_SIZE = 20      # 每次只抓 20 个种子词 (每次运行极其轻量)
MIN_DELAY = 15       # 最小等待时间 (秒)
MAX_DELAY = 40       # 最大等待时间 (秒) -- 极其缓慢，像真人在看网页一样

# ================= 完整的 279+ 个种子词库 =================
# 这里填入完整的种子列表，脚本每次会随机挑几个来更新
ALL_SEEDS = [
    # --- Year/General ---
    "2026", "2025", "Best", "Top", "list", "example", "template", "sample", "guide", 
    "format", "How to", "tutorial", "trends", "news", "review", "vs", "alternatives",
    
    # --- AI & Tech (Core) ---
    "ai", "openai", "chatgpt", "gemini", "claude", "llama", "mistral", "hugging face",
    "assistant", "agent", "advisor", "copilot", "chatbot", "llm", "diffusion", "transformer",
    "generator", "creator", "maker", "builder", "designer", "developer", "coder",
    "android", "ios", "windows", "linux", "macos", "python", "javascript", "react", "nextjs",
    "compiler", "interpreter", "algorithm", "framework", "library", "api", "sdk",
    
    # --- Tools & Utilities ---
    "upscale", "unblur", "editor", "enhancer", "optimizer", "converter", "compressor",
    "scraper", "crawler", "parser", "extractor", "summarizer", "transcriber", "translator",
    "paraphraser", "rewriter", "writer", "checker", "detector", "humanizer", "scanner",
    "tester", "evaluator", "analyzer", "calculator", "simulator", "emulator",
    "manager", "tracker", "scheduler", "planner", "calendar", "organizer", "syncer",
    "recorder", "player", "viewer", "reader", "browser", "notifier", "alert",
    
    # --- Assets & Resources ---
    "resources", "dashboard", "directory", "portal", "hub", "finder", "search",
    "layout", "starter", "boilerplate", "ui kit", "component", "plugin", "extension",
    "theme", "icon", "logo", "font", "illustration", "vector", "mockup",
    
    # --- Creative & Media ---
    "image", "photo", "picture", "face", "portrait", "avatar", "profile",
    "video", "movie", "film", "short", "clip", "reel",
    "audio", "voice", "sound", "music", "song", "beat", "podcast",
    "text", "code", "script", "prompt", "caption", "subtitle",
    "style", "filter", "effect", "preset", "lut", "palette",
    "chart", "graph", "diagram", "infographic", "map",
    "anime", "cartoon", "manga", "comic", "tattoo", "sketch", "drawing",
    "coloring page", "wallpaper", "background", "texture", "pattern",
    "meme", "emoji", "sticker", "gif",
    
    # --- Platforms & Gaming ---
    "Steam", "Roblox", "Scratch", "Itch.io", "Discord", "Twitch", "TikTok", 
    "Instagram", "YouTube", "Twitter", "Reddit", "Pinterest", "LinkedIn",
    "Github", "Gitlab", "Bitbucket", "Stack Overflow", "Kaggle",
    "Epic Games", "Nintendo", "PlayStation", "Xbox", "Unity", "Unreal Engine",
    "Godot", "Blender", "Figma", "Canva", "Adobe", "Microsoft", "Google", "Apple",
    
    # --- Finance & Crypto ---
    "crypto", "bitcoin", "ethereum", "solana", "nft", "blockchain", "web3", "defi",
    "wallet", "exchange", "broker", "trading", "investment", "stock", "market",
    "insurance", "loan", "mortgage", "credit", "card", "bank", "tax", "wealth",
    "finance", "money", "gold", "silver", "forex", "refinance", "attorney", "lawyer",
    
    # --- Lifestyle & Other ---
    "job", "career", "remote", "freelance", "salary", "interview", "resume",
    "travel", "flight", "hotel", "booking", "trip", "visa",
    "health", "fitness", "diet", "workout", "yoga", "meditation",
    "food", "recipe", "restaurant", "delivery",
    "shopping", "deal", "coupon", "discount", "sale", "price",
    "gift", "present", "toy", "game", "book", "course", "lesson"
]

def load_existing_data():
    """读取已有的 JSON 文件，如果不存在则返回空结构"""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                content = json.load(f)
                # 兼容不同格式，确保返回字典
                return content.get('data', content) 
        except Exception as e:
            print(f"[!] 读取现有文件出错: {e}, 将创建新数据。")
    return {}

def scrape_stealth_mode():
    print(f"[*] 启动隐秘抓取模式 (Stealth Mode) - {datetime.now()}")
    
    # 1. 加载旧数据
    current_data = load_existing_data()
    print(f"[*] 现有知识库包含 {len(current_data)} 个分类")
    
    # 2. 随机选择本轮任务
    # 从所有种子中随机选 BATCH_SIZE 个
    # 优先选那些还没抓过的，或者很久没更新的（这里简化为纯随机，长期看是均匀的）
    target_seeds = random.sample(ALL_SEEDS, min(BATCH_SIZE, len(ALL_SEEDS)))
    
    print(f"[*] 本次目标: {len(target_seeds)} 个随机词 -> {target_seeds}")
    
    # 初始化 pytrends (增加重试参数)
    pytrends = TrendReq(
        hl=HL, 
        tz=TZ, 
        timeout=(10,25), 
        retries=3, 
        backoff_factor=1.0 # 失败后等待更久
    )
    
    success_count = 0
    fail_count = 0
    
    # 3. 开始慢速抓取
    for i, keyword in enumerate(target_seeds):
        percent = (i + 1) / len(target_seeds) * 100
        print(f"\n[{i+1}/{len(target_seeds)}] ({percent:.0f}%) 处理: {keyword}")
        
        try:
            # 构建请求
            pytrends.build_payload([keyword], cat=0, timeframe='now 7-d', geo='', gprop='')
            
            # 获取数据
            related = pytrends.related_queries()
            data_payload = related.get(keyword)
            
            if data_payload and data_payload['rising'] is not None:
                df = data_payload['rising']
                records = df.to_dict('records')
                
                # 更新到总数据库中 (覆盖旧的)
                current_data[keyword] = records
                success_count += 1
                print(f"    √ 成功! 发现 {len(records)} 个新词")
            else:
                print(f"    - 无飙升数据 (可能是冷门词)")
                # 即使没有数据，也记录一下，避免它是空的
                current_data[keyword] = [] 

            # ===== 核心：超长随机休眠 =====
            # 只有在不是最后一个词的时候才休眠
            if i < len(target_seeds) - 1:
                sleep_time = random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"    ...隐身休眠 {sleep_time:.1f} 秒...")
                time.sleep(sleep_time)

        except ResponseError as e:
            print(f"    x 触发 Google 警报 (429): {e}")
            fail_count += 1
            # 遇到封锁，直接进入长睡眠，甚至可以考虑直接退出脚本，明天再试
            print("    ! 检测到封锁，强制休眠 120 秒...")
            time.sleep(120)
            
        except Exception as e:
            print(f"    x 未知错误: {e}")
            fail_count += 1
            time.sleep(10)

    # 4. 保存结果 (合并更新)
    print(f"\n[*] 正在保存数据...")
    
    final_output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_seeds_tracked": len(ALL_SEEDS),
        "active_data_count": len(current_data),
        "data": current_data
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
        
    print(f"[*] 任务完成. 成功更新: {success_count}, 失败: {fail_count}")
    print(f"[*] 此时数据库共包含 {len(current_data)} 个分类的数据")

if __name__ == "__main__":
    scrape_stealth_mode()
