#!/usr/bin/env python3
"""
各平台资讯热榜爬虫 - 终极版本
包含多种备选渠道：直接API、第三方聚合API、RSS
- 微博、抖音: 直接抓取（稳定）
- B站: 直接抓取 + 备选API
- 知乎、百度、IT之家: 多种备选渠道尝试
"""

import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import os


def get_beijing_time():
    return datetime.now(timezone(timedelta(hours=8)))


def make_request(url, headers=None, timeout=10):
    if headers is None:
        headers = {}
    headers.setdefault("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    headers.setdefault("Accept", "application/json, application/xml, text/html, */*")

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        print(f"    请求失败: {str(e)[:50]}")
        return None


def parse_rss(xml_data, max_items=30):
    """解析RSS/XML数据"""
    items = []
    try:
        root = ET.fromstring(xml_data)

        # RSS 2.0
        channel = root.find("channel")
        if channel is not None:
            for item in channel.findall("item")[:max_items]:
                title = item.find("title")
                link = item.find("link")
                if title is not None and title.text:
                    items.append({
                        "rank": len(items) + 1,
                        "title": title.text,
                        "url": link.text if link is not None else "",
                        "hot": 0,
                        "tag": "",
                    })
            return items

        # Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        if entries:
            for entry in entries[:max_items]:
                title = entry.find("atom:title", ns)
                link = entry.find("atom:link", ns)
                if title is not None and title.text:
                    items.append({
                        "rank": len(items) + 1,
                        "title": title.text,
                        "url": link.get("href", "") if link is not None else "",
                        "hot": 0,
                        "tag": "",
                    })
            return items

        # 通用item
        for item in root.iter("item"):
            if len(items) >= max_items:
                break
            title = item.find("title")
            link = item.find("link")
            if title is not None and title.text:
                items.append({
                    "rank": len(items) + 1,
                    "title": title.text,
                    "url": link.text if link is not None else "",
                    "hot": 0,
                    "tag": "",
                })
        return items
    except Exception as e:
        print(f"    RSS解析失败: {e}")
        return []


# ==================== 微博 ====================
def fetch_weibo():
    """微博热搜 - 直接抓取（稳定）"""
    print("  抓取微博...")
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
        print(f"  微博失败: {e}")
        return {"name": "微博热搜", "items": [], "updated": get_beijing_time().isoformat(), "error": str(e)}


# ==================== 知乎 ====================
def fetch_zhihu():
    """知乎热榜 - 多种渠道尝试"""
    print("  抓取知乎...")

    # 渠道1: 直接API（有时能成功）
    print("    尝试渠道1: 直接API")
    try:
        headers = {
            "Referer": "https://www.zhihu.com/",
            "Accept": "application/json",
        }
        data = make_request("https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50", headers)
        if data:
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
                    "url": url_str or "https://zhihu.com",
                    "hot": detail.get("metrics", {}).get("score", 0),
                    "tag": item.get("card_label", {}).get("text", ""),
                })
            if items:
                print(f"    ✅ 直接API成功: {len(items)}条")
                return {"name": "知乎热榜", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"    ❌ 直接API失败: {e}")

    # 渠道2: RSSHub
    print("    尝试渠道2: RSSHub")
    rss_urls = [
        "https://rsshub.app/zhihu/hot",
        "https://rsshub.rssforever.com/zhihu/hot",
    ]
    for url in rss_urls:
        try:
            data = make_request(url, timeout=15)
            if data:
                items = parse_rss(data)
                if items:
                    print(f"    ✅ RSSHub成功: {len(items)}条")
                    return {"name": "知乎热榜", "items": items, "updated": get_beijing_time().isoformat()}
        except Exception as e:
            print(f"    ❌ RSSHub失败: {e}")

    # 渠道3: 第三方聚合API
    print("    尝试渠道3: 第三方聚合API")
    api_urls = [
        "https://api.98dou.cn/api/hotlist?type=zhihu",
    ]
    for url in api_urls:
        try:
            data = make_request(url, timeout=10)
            if data:
                result = json.loads(data.decode("utf-8"))
                if result.get("code") == 200 and result.get("data"):
                    items = []
                    for item in result["data"][:30]:
                        items.append({
                            "rank": len(items) + 1,
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "hot": item.get("hot", 0),
                            "tag": "",
                        })
                    if items:
                        print(f"    ✅ 第三方API成功: {len(items)}条")
                        return {"name": "知乎热榜", "items": items, "updated": get_beijing_time().isoformat()}
        except Exception as e:
            print(f"    ❌ 第三方API失败: {e}")

    print("    所有渠道均失败")
    return {"name": "知乎热榜", "items": [], "updated": get_beijing_time().isoformat(), "error": "所有渠道均失败"}


# ==================== 百度 ====================
def fetch_baidu():
    """百度热搜 - 多种渠道尝试"""
    print("  抓取百度...")

    # 渠道1: 百度官方API（有时能成功）
    print("    尝试渠道1: 官方API")
    try:
        headers = {
            "Referer": "https://top.baidu.com/",
            "Accept": "application/json",
        }
        data = make_request("https://top.baidu.com/api/board?platform=wise&tab=realtime", headers)
        if data:
            result = json.loads(data.decode("utf-8"))
            items = []
            cards = result.get("data", {}).get("cards", [])
            for card in cards:
                for item in card.get("content", [])[:30]:
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
                print(f"    ✅ 官方API成功: {len(items)}条")
                return {"name": "百度热搜", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"    ❌ 官方API失败: {e}")

    # 渠道2: 第三方聚合API
    print("    尝试渠道2: 第三方聚合API")
    api_urls = [
        "https://api.1314.cool/getbaiduhot/",
        "https://api.aa1.cn/api/baidu-rs/",
        "https://api.98dou.cn/api/hotlist?type=baidu",
    ]
    for url in api_urls:
        try:
            data = make_request(url, timeout=10)
            if data:
                result = json.loads(data.decode("utf-8"))
                items = []

                # 处理不同API格式
                if isinstance(result, list):
                    for item in result[:30]:
                        items.append({
                            "rank": len(items) + 1,
                            "title": item.get("word", item.get("title", "")),
                            "url": item.get("url", ""),
                            "hot": item.get("hot", 0),
                            "tag": "",
                        })
                elif isinstance(result, dict):
                    data_list = result.get("data", result.get("list", []))
                    for item in data_list[:30]:
                        items.append({
                            "rank": len(items) + 1,
                            "title": item.get("word", item.get("title", "")),
                            "url": item.get("url", ""),
                            "hot": item.get("hot", 0),
                            "tag": "",
                        })

                if items:
                    print(f"    ✅ 第三方API成功: {len(items)}条")
                    return {"name": "百度热搜", "items": items, "updated": get_beijing_time().isoformat()}
        except Exception as e:
            print(f"    ❌ 第三方API失败: {url[:30]}... {e}")

    print("    所有渠道均失败")
    return {"name": "百度热搜", "items": [], "updated": get_beijing_time().isoformat(), "error": "所有渠道均失败"}


# ==================== 抖音 ====================
def fetch_douyin():
    """抖音热点 - 直接抓取（稳定）"""
    print("  抓取抖音...")
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
        print(f"  抖音失败: {e}")
        return {"name": "抖音热点", "items": [], "updated": get_beijing_time().isoformat(), "error": str(e)}


# ==================== B站 ====================
def fetch_bilibili():
    """B站热门 - 多种渠道尝试"""
    print("  抓取B站...")

    # 渠道1: 官方API（有时能成功）
    print("    尝试渠道1: 官方API")
    try:
        headers = {
            "Referer": "https://www.bilibili.com/",
            "Accept": "application/json",
        }
        data = make_request("https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all", headers)
        if data:
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
            if items:
                print(f"    ✅ 官方API成功: {len(items)}条")
                return {"name": "B站热门", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"    ❌ 官方API失败: {e}")

    # 渠道2: 第三方聚合API
    print("    尝试渠道2: 第三方聚合API")
    api_urls = [
        "https://api.98dou.cn/api/hotlist?type=bilibili",
    ]
    for url in api_urls:
        try:
            data = make_request(url, timeout=10)
            if data:
                result = json.loads(data.decode("utf-8"))
                if result.get("code") == 200 and result.get("data"):
                    items = []
                    for item in result["data"][:30]:
                        items.append({
                            "rank": len(items) + 1,
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "hot": item.get("hot", 0),
                            "tag": "",
                        })
                    if items:
                        print(f"    ✅ 第三方API成功: {len(items)}条")
                        return {"name": "B站热门", "items": items, "updated": get_beijing_time().isoformat()}
        except Exception as e:
            print(f"    ❌ 第三方API失败: {e}")

    print("    所有渠道均失败")
    return {"name": "B站热门", "items": [], "updated": get_beijing_time().isoformat(), "error": "所有渠道均失败"}


# ==================== IT之家 ====================
def fetch_ithome():
    """IT之家 - 多种渠道尝试"""
    print("  抓取IT之家...")

    # 渠道1: 官方API（有时能成功）
    print("    尝试渠道1: 官方API")
    try:
        headers = {
            "Referer": "https://www.ithome.com/",
            "Accept": "application/json",
        }
        data = make_request("https://api.ithome.com/api/news/getnewslist?r=0", headers)
        if data:
            result = json.loads(data.decode("utf-8"))
            items = []
            for item in result.get("data", {}).get("list", [])[:30]:
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
            if items:
                print(f"    ✅ 官方API成功: {len(items)}条")
                return {"name": "IT之家", "items": items, "updated": get_beijing_time().isoformat()}
    except Exception as e:
        print(f"    ❌ 官方API失败: {e}")

    # 渠道2: RSS
    print("    尝试渠道2: RSS")
    rss_urls = [
        "https://www.ithome.com/rss/",
    ]
    for url in rss_urls:
        try:
            data = make_request(url, timeout=15)
            if data:
                items = parse_rss(data)
                if items:
                    print(f"    ✅ RSS成功: {len(items)}条")
                    return {"name": "IT之家", "items": items, "updated": get_beijing_time().isoformat()}
        except Exception as e:
            print(f"    ❌ RSS失败: {e}")

    # 渠道3: 第三方聚合API
    print("    尝试渠道3: 第三方聚合API")
    api_urls = [
        "https://api.98dou.cn/api/hotlist?type=ithome",
    ]
    for url in api_urls:
        try:
            data = make_request(url, timeout=10)
            if data:
                result = json.loads(data.decode("utf-8"))
                if result.get("code") == 200 and result.get("data"):
                    items = []
                    for item in result["data"][:30]:
                        items.append({
                            "rank": len(items) + 1,
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "hot": item.get("hot", 0),
                            "tag": "",
                        })
                    if items:
                        print(f"    ✅ 第三方API成功: {len(items)}条")
                        return {"name": "IT之家", "items": items, "updated": get_beijing_time().isoformat()}
        except Exception as e:
            print(f"    ❌ 第三方API失败: {e}")

    print("    所有渠道均失败")
    return {"name": "IT之家", "items": [], "updated": get_beijing_time().isoformat(), "error": "所有渠道均失败"}


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"开始抓取: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

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

    # 保存
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    os.makedirs(DATA_DIR, exist_ok=True)

    output_path = os.path.join(DATA_DIR, "hot_topics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"已保存: {output_path}")
    for s in sources:
        status = "✅" if s.get("items") else "❌"
        print(f"  {status} {s['name']}: {len(s.get('items', []))} 条")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
