"""
매일 아침 GitHub Actions가 이 스크립트를 실행해서 news.json을 갱신합니다.
- 외부 유료 API를 전혀 쓰지 않습니다 (한국경제 RSS만 사용, 무료/키 불필요)
- 표준 라이브러리만 사용하므로 별도 설치가 필요 없습니다
"""
import urllib.request
import xml.etree.ElementTree as ET
import re
import json
import datetime
from zoneinfo import ZoneInfo

# 카테고리별 RSS 피드 (한국경제 공식 RSS, 무료)
FEEDS = {
    "stocks":     ("https://www.hankyung.com/feed/finance",      "한국경제"),
    "global":     ("https://www.hankyung.com/feed/international","한국경제"),
    "industry":   ("https://www.hankyung.com/feed/it",           "한국경제"),
    "realestate": ("https://www.hankyung.com/feed/realestate",   "한국경제"),
}

def clean(text):
    if not text:
        return ""
    text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def fetch_feed(url, source, limit=2):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    items = []
    for item in root.findall(".//item")[:limit]:
        title = clean(item.findtext("title"))
        link = (item.findtext("link") or "").strip()
        desc = clean(item.findtext("description"))
        if not desc or desc == title:
            desc = title
        if len(desc) > 110:
            desc = desc[:108].rstrip() + "…"
        if title and link:
            items.append({
                "headline": title,
                "summary": desc,
                "source": source,
                "url": link,
            })
    return items

def main():
    result = {}
    for key, (url, source) in FEEDS.items():
        try:
            items = fetch_feed(url, source)
        except Exception as e:
            print(f"[경고] {key} 피드를 가져오지 못했습니다: {e}")
            items = []
        result[key] = items

    kst_now = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
    result["updated_at"] = kst_now.strftime("%Y년 %m월 %d일 %H:%M 기준")

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("news.json 갱신 완료:", result["updated_at"])

if __name__ == "__main__":
    main()
