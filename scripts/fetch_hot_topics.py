#!/usr/bin/env python3
"""
各平台资讯热榜爬虫
支持：微博热搜、知乎热榜、百度热搜、抖音热点、B站热门、IT之家热榜
使用多个备用数据源提高成功率
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
import os
import ssl

# 忽略 SSL 证书验证（某些平台需要）
ssl._create_default_https_context = ssl._create_unverified_context


def get_beijing_time():
    """获取北京时间"""
    return datetime.now(timezone(timedelta(hours=8)))


def make_request(url, headers=None, timeout=20):
    """通用请求方法"""
    if headers is None:
        headers = {}
    headers.setdefault("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    headers.setdefault("Accept", "application/json, text/html, */*")
    headers.setdefault("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        print(f"  请求失败: {e}")
        return None


def fetch_weibo():
    """微博热搜"""
    print("  正在抓取微博...")
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {
        "Referer": "https://weibo.com/",
        "Accept": "application/json",
    }
    try:
        data = make_request(url, headers)
        if not data:
            return {"name": "微博热搜", "items": [], "updated": get_beijing_time().isoformat(), "error": "请求失败"}

        result = json.loads(data.decode("utf-8"))
        items = []
        for item in result.get("data", {}).get("realtime", [])[:30]:
            word = item.get("word", "")
            if not word:
                continue
            items.append({
                "rank": item.get("rank", len(items) + 1),
                "title": word,
                "url": f"https://s.weibo.com/weibo?q={urllib.parse.quote(word)}",
                "hot": item.get("raw_hot", 0),
                "tag": item.get("category", ""),
            })
        return {"name": "微博热搜", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"  微博抓取失败: {e}")
        return {"name": "微博热搜", "items": [], "updated": get_beijing_time().isoformat(), "error": str(e)}


def fetch_zhihu():
    """知乎热榜 - 使用备用API"""
    print("  正在抓取知乎...")

    # 备用API 1: 直接接口
    urls = [
        "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50",
        "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=30",
    ]

    for url in urls:
        try:
            headers = {
                "Referer": "https://www.zhihu.com/",
                "Accept": "application/json",
            }
            data = make_request(url, headers, timeout=15)
            if not data:
                continue

            result = json.loads(data.decode("utf-8"))
            items = []
            for item in result.get("data", [])[:30]:
                detail = item.get("target", {})
                title = detail.get("title", "")
                if not title:
                    continue
                url_str = detail.get("url", "")
                if "api.zhihu.com" in url_str:
                    url_str = url_str.replace("api.zhihu.com", "zhihu.com")
                items.append({
                    "rank": len(items) + 1,
                    "title": title,
                    "url": url_str or f"https://zhihu.com",
                    "hot": detail.get("metrics", {}).get("score", 0),
                    "tag": item.get("card_label", {}).get("text", ""),
                })
            if items:
                return {"name": "知乎热榜", "items": items, "updated": get_beijing_time().isoformat()}
        except Exception as e:
            print(f"  知乎API尝试失败: {e}")
            continue

    return {"name": "知乎热榜", "items": [], "updated": get_beijing_time().isoformat(), "error": "所有API均失败"}


def fetch_baidu():
    """百度热搜 - 使用备用API"""
    print("  正在抓取百度...")

    # 备用API: 使用百度开放接口
    urls = [
        "https://top.baidu.com/board?tab=realtime",
        "https://top.baidu.com/api/board?platform=wise&tab=realtime",
    ]

    for url in urls:
        try:
            headers = {
                "Accept": "text/html,application/json",
            }
            data = make_request(url, headers, timeout=15)
            if not data:
                continue

            html = data.decode("utf-8")

            # 尝试匹配 cardData
            match = re.search(r'cardData\s*=\s*(\[.*?\]);', html, re.DOTALL)
            if match:
                result = json.loads(match.group(1))
                items = []
                for item in result[:30]:
                    title = item.get("word", "")
                    if not title:
                        continue
                    items.append({
                        "rank": item.get("index", len(items) + 1),
                        "title": title,
                        "url": item.get("url", f"https://www.baidu.com/s?wd={urllib.parse.quote(title)}"),
                        "hot": item.get("hotScore", 0),
                        "tag": item.get("category", ""),
                    })
                if items:
                    return {"name": "百度热搜", "items": items, "updated": get_beijing_time().isoformat()}

            # 尝试匹配 JSON API 格式
            try:
                result = json.loads(html)
                if "data" in result:
                    items = []
                    for item in result.get("data", {}).get("cards", [])[:30]:
                        title = item.get("word", "")
                        if not title:
                            continue
                        items.append({
                            "rank": len(items) + 1,
                            "title": title,
                            "url": item.get("url", ""),
                            "hot": item.get("hotScore", 0),
                            "tag": item.get("category", ""),
                        })
                    if items:
                        return {"name": "百度热搜", "items": items, "updated": get_beijing_time().isoformat()}
            except:
                pass

        except Exception as e:
            print(f"  百度API尝试失败: {e}")
            continue

    return {"name": "百度热搜", "items": [], "updated": get_beijing_time().isoformat(), "error": "所有API均失败"}


def fetch_douyin():
    """抖音热点"""
    print("  正在抓取抖音...")
    url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
    headers = {
        "Referer": "https://www.douyin.com/",
        "Accept": "application/json",
    }
    try:
        data = make_request(url, headers)
        if not data:
            return {"name": "抖音热点", "items": [], "updated": get_beijing_time().isoformat(), "error": "请求失败"}

        result = json.loads(data.decode("utf-8"))
        items = []
        for item in result.get("data", {}).get("word_list", [])[:30]:
            word = item.get("word", "")
            if not word:
                continue
            items.append({
                "rank": item.get("rank", len(items) + 1),
                "title": word,
                "url": f"https://www.douyin.com/search/{urllib.parse.quote(word)}",
                "hot": item.get("hot_value", 0),
                "tag": "",
            })
        return {"name": "抖音热点", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"  抖音抓取失败: {e}")
        return {"name": "抖音热点", "items": [], "updated": get_beijing_time().isoformat(), "error": str(e)}


def fetch_bilibili():
    """B站热门"""
    print("  正在抓取B站...")
    url = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all"
    headers = {
        "Referer": "https://www.bilibili.com/",
        "Accept": "application/json",
    }
    try:
        data = make_request(url, headers)
        if not data:
            return {"name": "B站热门", "items": [], "updated": get_beijing_time().isoformat(), "error": "请求失败"}

        result = json.loads(data.decode("utf-8"))
        items = []
        for item in result.get("data", {}).get("list", [])[:30]:
            title = item.get("title", "")
            if not title:
                continue
            bvid = item.get("bvid", "")
            url_str = item.get("short_link", f"https://www.bilibili.com/video/{bvid}")
            items.append({
                "rank": len(items) + 1,
                "title": title,
                "url": url_str,
                "hot": item.get("stat", {}).get("view", 0),
                "tag": item.get("tname", ""),
            })
        return {"name": "B站热门", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"  B站抓取失败: {e}")
        return {"name": "B站热门", "items": [], "updated": get_beijing_time().isoformat(), "error": str(e)}


def fetch_ithome():
    """IT之家热榜 - 使用备用API"""
    print("  正在抓取IT之家...")

    urls = [
        "https://api.ithome.com/api/news/getnewslist?r=0",
        "https://api.ithome.com/json/newslist/news?r=0",
    ]

    for url in urls:
        try:
            headers = {
                "Referer": "https://www.ithome.com/",
                "Accept": "application/json",
            }
            data = make_request(url, headers, timeout=15)
            if not data:
                continue

            result = json.loads(data.decode("utf-8"))
            items = []

            # API 1 格式
            if "data" in result and "list" in result.get("data", {}):
                for item in result["data"]["list"][:30]:
                    title = item.get("Title", "")
                    if not title:
                        continue
                    items.append({
                        "rank": len(items) + 1,
                        "title": title,
                        "url": item.get("Url", ""),
                        "hot": item.get("CommentCount", 0),
                        "tag": item.get("CategoryName", ""),
                    })
            # API 2 格式
            elif isinstance(result, list):
                for item in result[:30]:
                    title = item.get("title", "")
                    if not title:
                        continue
                    items.append({
                        "rank": len(items) + 1,
                        "title": title,
                        "url": item.get("url", ""),
                        "hot": item.get("commentCount", 0),
                        "tag": item.get("category", ""),
                    })

            if items:
                return {"name": "IT之家", "items": items, "updated": get_beijing_time().isoformat()}

        except Exception as e:
            print(f"  IT之家API尝试失败: {e}")
            continue

    return {"name": "IT之家", "items": [], "updated": get_beijing_time().isoformat(), "error": "所有API均失败"}


def main():
    """主函数：抓取所有平台数据"""
    print(f"\n开始抓取数据... {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

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

    print("=" * 50)
    print(f"数据已保存到: {output_path}")
    print(f"共 {len(sources)} 个平台")
    for s in sources:
        status = "✅" if s.get("items") else "❌"
        error_info = f" ({s.get('error', '')})" if s.get("error") else ""
        print(f"  {status} {s['name']}: {len(s.get('items', []))} 条{error_info}")


if __name__ == "__main__":
    main()
