#!/usr/bin/env python3
"""
各平台资讯热榜爬虫
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
import os


def get_beijing_time():
    """获取北京时间"""
    return datetime.now(timezone(timedelta(hours=8)))


def fetch_weibo():
    """微博热搜"""
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://weibo.com/",
        "Accept": "application/json",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = []
        for item in data.get("data", {}).get("realtime", [])[:30]:
            word = item.get("word", "")
            if not word:
                continue
            items.append({
                "rank": item.get("rank", 0),
                "title": word,
                "url": f"https://s.weibo.com/weibo?q={urllib.parse.quote(word)}",
                "hot": item.get("raw_hot", 0),
                "tag": item.get("category", ""),
            })
        return {"name": "微博热搜", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"微博抓取失败: {e}")
        return {"name": "微博热搜", "items": [], "updated": get_beijing_time().isoformat(), "error": str(e)}


def fetch_zhihu():
    """知乎热榜"""
    url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.zhihu.com/",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = []
        for item in data.get("data", [])[:30]:
            detail = item.get("target", {})
            url_str = detail.get("url", "")
            if "api.zhihu.com" in url_str:
                url_str = url_str.replace("api.zhihu.com", "zhihu.com")
            items.append({
                "rank": len(items) + 1,
                "title": detail.get("title", ""),
                "url": url_str,
                "hot": detail.get("metrics", {}).get("score", 0),
                "tag": item.get("card_label", {}).get("text", ""),
            })
        return {"name": "知乎热榜", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"知乎抓取失败: {e}")
        return {"name": "知乎热榜", "items": [], "updated": get_beijing_time().isoformat(), "error": str(e)}


def fetch_baidu():
    """百度热搜"""
    url = "https://top.baidu.com/board?tab=realtime"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")

        import re
        match = re.search(r'cardData\s*=\s*(\[.*?\]);', html, re.DOTALL)
        if not match:
            return {"name": "百度热搜", "items": [], "updated": get_beijing_time().isoformat(), "error": "未找到数据"}

        data = json.loads(match.group(1))
        items = []
        for item in data[:30]:
            items.append({
                "rank": item.get("index", 0),
                "title": item.get("word", ""),
                "url": item.get("url", ""),
                "hot": item.get("hotScore", 0),
                "tag": item.get("category", ""),
            })
        return {"name": "百度热搜", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"百度抓取失败: {e}")
        return {"name": "百度热搜", "items": [], "updated": get_beijing_time().isoformat(), "error": str(e)}


def fetch_douyin():
    """抖音热点"""
    url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.douyin.com/",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = []
        for item in data.get("data", {}).get("word_list", [])[:30]:
            word = item.get("word", "")
            items.append({
                "rank": item.get("rank", 0),
                "title": word,
                "url": f"https://www.douyin.com/search/{urllib.parse.quote(word)}",
                "hot": item.get("hot_value", 0),
                "tag": "",
            })
        return {"name": "抖音热点", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"抖音抓取失败: {e}")
        return {"name": "抖音热点", "items": [], "updated": get_beijing_time().isoformat(), "error": str(e)}


def fetch_bilibili():
    """B站热门"""
    url = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com/",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = []
        for item in data.get("data", {}).get("list", [])[:30]:
            bvid = item.get("bvid", "")
            url_str = item.get("short_link", f"https://www.bilibili.com/video/{bvid}")
            items.append({
                "rank": len(items) + 1,
                "title": item.get("title", ""),
                "url": url_str,
                "hot": item.get("stat", {}).get("view", 0),
                "tag": item.get("tname", ""),
            })
        return {"name": "B站热门", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"B站抓取失败: {e}")
        return {"name": "B站热门", "items": [], "updated": get_beijing_time().isoformat(), "error": str(e)}


def fetch_ithome():
    """IT之家热榜"""
    url = "https://api.ithome.com/api/news/getnewslist?r=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.ithome.com/",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = []
        for item in data.get("data", {}).get("list", [])[:30]:
            items.append({
                "rank": len(items) + 1,
                "title": item.get("Title", ""),
                "url": item.get("Url", ""),
                "hot": item.get("CommentCount", 0),
                "tag": item.get("CategoryName", ""),
            })
        return {"name": "IT之家", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"IT之家抓取失败: {e}")
        return {"name": "IT之家", "items": [], "updated": get_beijing_time().isoformat(), "error": str(e)}


def main():
    """主函数：抓取所有平台数据"""
    print(f"开始抓取数据... {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}")

    sources = [
        fetch_weibo(),
        fetch_zhihu(),
        fetch_baidu(),
        fetch_douyin(),
        fetch_bilibili(),
        fetch_ithome(),
    ]

    result = {
        "update_time": get_beijing_time().strftime("%Y-%m-%d %H:%M:%S"),
        "sources": sources,
    }

    # 使用绝对路径保存到项目根目录的 data 文件夹
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    os.makedirs(DATA_DIR, exist_ok=True)

    output_path = os.path.join(DATA_DIR, "hot_topics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"数据已保存，共 {len(sources)} 个平台")
    for s in sources:
        status = "✅" if s.get("items") else "❌"
        print(f"  {status} {s['name']}: {len(s.get('items', []))} 条")


if __name__ == "__main__":
    main()
