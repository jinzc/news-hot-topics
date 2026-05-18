#!/usr/bin/env python3
"""
各平台资讯热榜爬虫
- 微博、抖音、B站: 直接抓取（保持现有方式）
- 知乎、百度、IT之家: RSS订阅抓取
"""

import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import os


def get_beijing_time():
    """获取北京时间"""
    return datetime.now(timezone(timedelta(hours=8)))


def make_request(url, headers=None, timeout=15):
    """通用请求方法"""
    if headers is None:
        headers = {}
    headers.setdefault("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    headers.setdefault("Accept", "application/json, application/xml, text/xml, */*")

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        print(f"  请求失败: {e}")
        return None


def parse_rss(xml_data, platform_name, max_items=30):
    """解析RSS/XML数据为统一格式"""
    items = []
    try:
        root = ET.fromstring(xml_data)

        # RSS 2.0 格式
        channel = root.find("channel")
        if channel is not None:
            for item in channel.findall("item")[:max_items]:
                title = item.find("title")
                link = item.find("link")

                title_text = title.text if title is not None else ""
                link_text = link.text if link is not None else ""

                if title_text:
                    items.append({
                        "rank": len(items) + 1,
                        "title": title_text,
                        "url": link_text,
                        "hot": 0,
                        "tag": "",
                    })
            return items

        # Atom 格式
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        if entries:
            for entry in entries[:max_items]:
                title = entry.find("atom:title", ns)
                link = entry.find("atom:link", ns)

                title_text = title.text if title is not None else ""
                link_text = link.get("href", "") if link is not None else ""

                if title_text:
                    items.append({
                        "rank": len(items) + 1,
                        "title": title_text,
                        "url": link_text,
                        "hot": 0,
                        "tag": "",
                    })
            return items

        # 其他格式尝试
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
        print(f"  RSS解析失败: {e}")
        return []


def fetch_weibo():
    """微博热搜 - 直接抓取（保持现有方式）"""
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


def fetch_zhihu():
    """知乎热榜 - RSS订阅"""
    print("  抓取知乎(RSS)...")

    # RSSHub 知乎热榜
    rss_urls = [
        "https://rsshub.app/zhihu/hot",
        "https://rsshub.rssforever.com/zhihu/hot",
        "https://rss.shab.fun/zhihu/hot",
    ]

    for url in rss_urls:
        try:
            print(f"    尝试: {url}")
            data = make_request(url, timeout=20)
            if not data:
                continue

            items = parse_rss(data, "知乎")
            if items:
                print(f"    ✅ 成功获取 {len(items)} 条")
                return {"name": "知乎热榜", "items": items, "updated": get_beijing_time().isoformat()}
        except Exception as e:
            print(f"    失败: {e}")
            continue

    return {"name": "知乎热榜", "items": [], "updated": get_beijing_time().isoformat(), "error": "所有RSS源均失败"}


def fetch_baidu():
    """百度热搜 - RSS订阅"""
    print("  抓取百度(RSS)...")

    # 百度RSS源
    rss_urls = [
        "https://rsshub.app/baidu/topwords/1",  # 实时热点
        "https://rsshub.rssforever.com/baidu/topwords/1",
    ]

    for url in rss_urls:
        try:
            print(f"    尝试: {url}")
            data = make_request(url, timeout=20)
            if not data:
                continue

            items = parse_rss(data, "百度")
            if items:
                print(f"    ✅ 成功获取 {len(items)} 条")
                return {"name": "百度热搜", "items": items, "updated": get_beijing_time().isoformat()}
        except Exception as e:
            print(f"    失败: {e}")
            continue

    return {"name": "百度热搜", "items": [], "updated": get_beijing_time().isoformat(), "error": "所有RSS源均失败"}


def fetch_douyin():
    """抖音热点 - 直接抓取（保持现有方式）"""
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


def fetch_bilibili():
    """B站热门 - 直接抓取（保持现有方式）"""
    print("  抓取B站...")
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
        print(f"  B站失败: {e}")
        return {"name": "B站热门", "items": [], "updated": get_beijing_time().isoformat(), "error": str(e)}


def fetch_ithome():
    """IT之家 - RSS订阅"""
    print("  抓取IT之家(RSS)...")

    # IT之家官方RSS
    rss_urls = [
        "https://www.ithome.com/rss/",
        "https://rsshub.app/ithome/ranking/24h",  # 24小时热榜
    ]

    for url in rss_urls:
        try:
            print(f"    尝试: {url}")
            data = make_request(url, timeout=20)
            if not data:
                continue

            items = parse_rss(data, "IT之家")
            if items:
                print(f"    ✅ 成功获取 {len(items)} 条")
                return {"name": "IT之家", "items": items, "updated": get_beijing_time().isoformat()}
        except Exception as e:
            print(f"    失败: {e}")
            continue

    return {"name": "IT之家", "items": [], "updated": get_beijing_time().isoformat(), "error": "所有RSS源均失败"}


def main():
    """主函数：抓取所有平台数据"""
    print(f"开始抓取数据... {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}")
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
