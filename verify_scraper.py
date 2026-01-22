import time
import pandas as pd
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError

# 1. 配置
# 我们先用几个简单的词来测试，不想因为请求太多被 Google 封锁
TEST_SEEDS = ["ai", "python", "crypto", "marketing"]
HL = 'en-US' # 语言
TZ = 360 # 时区 (360 = US CST)

def fetch_rising_keywords():
    print(f"[*] 初始化 Google Trends 连接...")
    # retries=2, backoff_factor=0.1 增加重试机制，防止网络抖动
    pytrends = TrendReq(hl=HL, tz=TZ, timeout=(10,25), retries=2, backoff_factor=0.1)

    results = {}

    for keyword in TEST_SEEDS:
        print(f"\n[>] 正在抓取: '{keyword}' ...")
        
        try:
            # 构建请求 payload
            pytrends.build_payload([keyword], cat=0, timeframe='now 7-d', geo='', gprop='')
            
            # 获取相关查询
            related_queries = pytrends.related_queries()
            
            # 提取 'rising' (飙升) 数据
            data = related_queries.get(keyword)
            
            if data and data['rising'] is not None:
                rising_df = data['rising']
                
                # 只要 'value' (增长率) 大于 0 的词
                # Google Trends 的 'breakout' 通常会被标记为极大值，或者我们需要处理一下
                print(f"    √ 成功获取! 发现 {len(rising_df)} 个飙升词")
                
                # 打印前 5 个来看看
                top_5 = rising_df.head(5)
                for index, row in top_5.iterrows():
                    query = row['query']
                    value = row['value']
                    print(f"      - {query} (+{value}%)")
                
                results[keyword] = rising_df.to_dict('records')
            else:
                print(f"    ! 没有找到关于 '{keyword}' 的飙升词。")

            # 休眠，防止触发 429 Error
            time.sleep(2)

        except ResponseError as e:
            print(f"    x Google 拒绝了请求 (API Error): {e}")
            print("    建议：尝试更换 IP 或增加等待时间。")
        except Exception as e:
            print(f"    x 发生未知错误: {e}")

    return results

if __name__ == "__main__":
    print("--- 开始测试 Google Trends 抓取 ---")
    data = fetch_rising_keywords()
    print("\n--- 测试结束 ---")
    if data:
        print("测试成功！我们成功从 Google 拿到了数据。")
    else:
        print("测试未获取到有效数据，请检查网络或代理设置。")
