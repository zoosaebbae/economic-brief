"""
매일 아침 GitHub Actions가 이 스크립트를 실행해서 news.json을 갱신합니다.
- 외부 유료 API를 전혀 쓰지 않습니다 (RSS + 한국경제 랭킹페이지만 사용, 무료/키 불필요)
- 표준 라이브러리만 사용하므로 별도 설치가 필요 없습니다

카테고리(네이버뉴스 경제 섹션 참고): 금융 / 증권 / 부동산 / 글로벌경제 / 생활경제

기사 2개 선정 기준 (진짜 조회수 데이터는 무료로 구할 수 없어서 이렇게 근사합니다)
  1순위: 한국경제 실제 랭킹(조회순 상위 30) + 다른 언론사도 같이 다룬 주제 (교집합)
  2순위: 랭킹 여부와 무관하게, 2곳 이상 언론사가 동시에 다룬 주제
  3순위: 그래도 부족하면 최신순으로 나머지 채움
"""
import urllib.request
import xml.etree.ElementTree as ET
import re
import json
import datetime
import html
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

DIRECT_FEEDS = [
    ("https://www.hankyung.com/feed/realestate",     "한국경제", "realestate"),
    ("https://www.hankyung.com/feed/international",  "한국경제", "global"),
    ("https://mofe.go.kr/com/detailRssTagService.do?bbsId=MOSFBBS_000000000028", "기획재정부", "policy"),
    ("https://www.moel.go.kr/rss/policy.do", "고용노동부", "employment"),
]

CLASSIFY_FEEDS = [
    ("https://www.hankyung.com/feed/finance", "한국경제", "finance"),  # 분류 안 되면 기본값 finance
    ("https://www.yna.co.kr/rss/economy.xml", "연합뉴스", None),
    ("https://www.mk.co.kr/rss/30100041/",    "매일경제", None),
]

RANKING_URL = "https://www.hankyung.com/ranking"
RANKING_LIMIT = 30

KEYWORD_RULES = [
    ("realestate",  ["부동산", "아파트", "전세", "월세", "분양", "종부세", "양도세", "재건축", "재개발", "청약"]),
    ("employment",  ["취업", "실업", "채용", "구직", "구인", "일자리", "최저임금", "임금인상", "임금협상", "임금교섭", "임금체불", "고용률", "실업률"]),
    ("life",        ["장바구니", "외식", "전기요금", "가스요금", "생활비", "프랜차이즈", "대형마트", "배달", "연말정산", "구독료", "택배"]),
    ("securities",  ["코스피", "코스닥", "증시", "주가", "상장", "공모주", "ETF", "채권", "펀드",
                      "종목", "매수", "매도", "자사주", "특징주", "실적", "배당", "시총", "목표주가", "리포트", "장마감", "증권가"]),
    ("finance",     ["은행", "대출", "보험", "카드", "예금", "적금", "금리", "물가", "환율", "핀테크", "금융위", "저축은행"]),
    ("global",      ["연준", "미국", "중국", "유럽", "무역", "관세", "달러", "글로벌", "세계", "일본", "수출"]),
]

STOPWORDS = {"오늘", "기자", "단독", "속보", "영상", "포토", "인터뷰", "현장", "특파원", "종합", "업데이트", "논란"}

# 경제와 무관하거나 연예/가십성으로 흐르는 기사는 카테고리 매칭이 되더라도 제외
EXCLUDE_KEYWORDS = [
    "유튜브", "유튜버", "인플루언서", "구독자", "연예인", "배우", "가수", "아이돌",
    "스타", "셀럽", "예능", "드라마", "결혼", "이혼", "열애", "임신", "출산",
]

def is_excluded(text):
    lower = text.lower()
    return any(kw.lower() in lower for kw in EXCLUDE_KEYWORDS)

def classify(text):
    lower = text.lower()
    for category, keywords in KEYWORD_RULES:
        for kw in keywords:
            if kw.lower() in lower:
                return category
    return None

def finance_subtag(text):
    """금융 카테고리 안에서 카드에 표시할 세부 태그(금리/물가/환율/금융)를 정한다."""
    lower = text.lower()
    if "금리" in lower:
        return "금리"
    if "물가" in lower:
        return "물가"
    if "환율" in lower:
        return "환율"
    return "금융"

def clean(text):
    if not text:
        return ""
    text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def fetch_items(url, source):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    raw_items = [el for el in root.iter() if el.tag.split('}')[-1] == 'item']

    def get_child_text(el, name):
        for child in el:
            if child.tag.split('}')[-1] == name:
                return child.text
        return None

    results = []
    for item in raw_items:
        title = clean(get_child_text(item, "title"))
        link = (get_child_text(item, "link") or "").strip()
        desc = clean(get_child_text(item, "description"))
        if not desc or desc == title:
            desc = title
        if len(desc) > 110:
            desc = desc[:108].rstrip() + "…"
        if not title or not link:
            continue
        raw_date = get_child_text(item, "pubDate") or get_child_text(item, "date")
        pubdate = None
        if raw_date:
            try:
                pubdate = parsedate_to_datetime(raw_date)
            except Exception:
                pubdate = None
        results.append({
            "headline": title,
            "summary": desc,
            "source": source,
            "url": link,
            "_date": pubdate,
        })
    print(f"  → {source} ({url}): {len(results)}개 항목 파싱됨")
    return results

def fetch_ranking_urls(limit=RANKING_LIMIT):
    """한국경제 랭킹뉴스 페이지에서 실제 조회순 상위 기사 URL을 순서대로 추출."""
    req = urllib.request.Request(RANKING_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    found = re.findall(r'href="(https://www\.hankyung\.com/article/[0-9A-Za-z]+)"', html)
    ordered = []
    for u in found:
        if u not in ordered:
            ordered.append(u)
        if len(ordered) >= limit:
            break
    return ordered

def tokenize(text):
    tokens = re.split(r"[\s,·'\"\[\]\(\):…\-/]+", text)
    return {t for t in tokens if len(t) >= 2 and t not in STOPWORDS}

def mark_cross_source(items):
    """다른 언론사 기사와 headline/summary에 겹치는 키워드가 있으면 같은 주제로 보고 표시."""
    token_sets = [tokenize(it["headline"] + " " + it["summary"]) for it in items]
    for i, item in enumerate(items):
        item["_cross_source"] = False
        for j, other in enumerate(items):
            if i == j or item["source"] == other["source"]:
                continue
            if token_sets[i] & token_sets[j]:
                item["_cross_source"] = True
                break

def select_top2(items, ranking_rank_map):
    for it in items:
        it["_rank"] = ranking_rank_map.get(it["url"])
        it["_in_ranking"] = it["_rank"] is not None
    mark_cross_source(items)

    tier1_ids, tier2_ids = set(), set()
    tier1 = [it for it in items if it["_in_ranking"] and it["_cross_source"]]
    tier1_ids = {id(it) for it in tier1}
    tier2 = [it for it in items if id(it) not in tier1_ids and it["_cross_source"]]
    tier2_ids = {id(it) for it in tier2}
    tier3 = [it for it in items if id(it) not in tier1_ids and id(it) not in tier2_ids]

    tier1.sort(key=lambda x: x["_rank"])
    epoch = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    tier2.sort(key=lambda x: x["_date"] or epoch, reverse=True)
    tier3.sort(key=lambda x: x["_date"] or epoch, reverse=True)

    ordered = tier1 + tier2 + tier3
    print(f"    (교집합 {len(tier1)}개 / 복수언론 {len(tier2)}개 / 나머지 {len(tier3)}개 중 상위 2개 채택)")

    selected = ordered[:2]
    for it in selected:
        for k in ("_date", "_rank", "_in_ranking", "_cross_source"):
            it.pop(k, None)
    return selected

def main():
    buckets = {
        "finance": [], "securities": [], "realestate": [], "global": [],
        "life": [], "employment": [], "policy": [],
    }

    for url, source, category in DIRECT_FEEDS:
        try:
            items = fetch_items(url, source)
        except Exception as e:
            print(f"[경고] {source}({category}) 피드를 가져오지 못했습니다: {e}")
            items = []
        items = [it for it in items if not is_excluded(it["headline"] + " " + it["summary"])]
        buckets[category].extend(items)

    for url, source, default_category in CLASSIFY_FEEDS:
        try:
            items = fetch_items(url, source)
        except Exception as e:
            print(f"[경고] {source} 피드를 가져오지 못했습니다: {e}")
            items = []
        matched = 0
        defaulted = 0
        excluded_count = 0
        for it in items:
            text = it["headline"] + " " + it["summary"]
            if is_excluded(text):
                excluded_count += 1
                continue
            category = classify(text)
            if not category and default_category:
                category = default_category
                defaulted += 1
            if category:
                buckets[category].append(it)
                matched += 1
        print(f"  → {source}: {len(items)}개 중 {matched}개 카테고리 분류 성공 (기본값 적용 {defaulted}개, 가십/무관 제외 {excluded_count}개)")

    try:
        ranking_urls = fetch_ranking_urls()
        ranking_rank_map = {u: i + 1 for i, u in enumerate(ranking_urls)}
        print(f"  → 한국경제 랭킹뉴스: {len(ranking_rank_map)}개 URL 확보")
    except Exception as e:
        print(f"[경고] 랭킹뉴스 페이지를 가져오지 못했습니다: {e}")
        ranking_rank_map = {}

    result = {}
    for category, items in buckets.items():
        print(f"  [{category}] 후보 {len(items)}개")
        selected = select_top2(items, ranking_rank_map)
        if category == "finance":
            for it in selected:
                it["tag"] = finance_subtag(it["headline"] + " " + it["summary"])
        result[category] = selected

    kst_now = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
    result["updated_at"] = kst_now.strftime("%Y년 %m월 %d일 %H:%M 기준")

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("news.json 갱신 완료:", result["updated_at"])

if __name__ == "__main__":
    main()
