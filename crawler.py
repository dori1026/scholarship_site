# crawler.py
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
import time

HEADERS = {"User-Agent": "Mozilla/5.0"}
TARGET_YEAR = datetime.today().year

def extract_deadline_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    patterns = [
        r"(\d{4}[./-]\s*\d{1,2}[./-]\s*\d{1,2})",              # 2025.06.15 or 2025-6-15
        r"~\s*(\d{1,2})[./-](\d{1,2})",                        # ~6.15
        r"\d{1,2}[./-]\d{1,2}\s*(까지|마감)"                   # 6.15 마감
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if len(match.groups()) == 2:
                    month, day = map(int, match.groups())
                    return f"{TARGET_YEAR}.{month:02}.{day:02}"
                elif len(match.groups()) == 1:
                    date_str = match.group(1).replace(' ', '').replace('/', '.').replace('-', '.')
                    return date_str
            except:
                continue

    return "없음"

def crawl_yonsei():
    BASE_URL = "https://wsw.yonsei.ac.kr/wsw/notice/scholarship-board.do"
    offset = 0
    article_limit = 10
    seen_posts = set()
    results = []

    while True:
        page_url = f"{BASE_URL}?mode=list&articleLimit={article_limit}&article.offset={offset}"
        soup = BeautifulSoup(requests.get(page_url, headers=HEADERS).text, "html.parser")
        rows = soup.select("table.board-table tbody tr")

        if not rows:
            break

        new_post_found = False

        for row in rows:
            tds = row.select("td")
            if len(tds) < 5:
                continue

            is_notice = tds[0].get_text(strip=True) == "공지"
            date_text = tds[-1].get_text(strip=True)

            if is_notice and offset != 0:
                continue

            try:
                post_year = int("20" + date_text.split(".")[0])
            except:
                continue

            if post_year != TARGET_YEAR:
                continue

            title_tag = row.select_one("a.c-board-title")
            if not title_tag:
                continue

            title = re.sub(r'\s+', ' ', title_tag.get_text()).strip()
            relative_link = title_tag.get("href")
            full_link = BASE_URL.split("?")[0] + relative_link

            key = f"{title}|{full_link}"
            if key in seen_posts:
                continue
            seen_posts.add(key)

            match = re.search(r"~\s*(\d{1,2})[/.](\d{1,2})", title)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                deadline = f"{TARGET_YEAR}.{month:02}.{day:02}"

                results.append({
                    "source": "연세대학교",
                    "title": title,
                    "link": full_link,
                    "deadline": deadline
                })

                if not is_notice:
                    new_post_found = True

            # `else: pass`로 처리하면 "없음"일 경우 아무 작업도 하지 않음

        if not new_post_found:
            break

        offset += article_limit

    return results


def crawl_kosaf():
    BASE_URL = "https://www.kosaf.go.kr"
    MAIN_URL = f"{BASE_URL}/ko/scholar.do?pg=scholarship_main&hmNavi=JH,00,00,00"
    results = []

    try:
        # 메인 페이지 요청
        res = requests.get(MAIN_URL, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.select("dl[class^=box] dd ul li a"):
            try:
                title = a.get_text(strip=True)
                href = a.get("href")
                full_link = BASE_URL + href

                # 상세 페이지 요청
                detail_res = requests.get(full_link, headers=HEADERS, timeout=10)
                detail_res.raise_for_status()
                detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                text = detail_soup.get_text(separator="\n")
                deadline = "직접 확인"

                # 마감일 추출
                match = re.search(r"~\s*['‘]?\d{2,4}[./년\s]*\d{1,2}[./월\s]*\d{1,2}", text)
                if match:
                    raw = match.group().replace("~", "").replace("‘", "").replace("'", "").strip()
                    nums = re.findall(r"\d+", raw)
                    if len(nums) == 3:
                        year = int(nums[0])
                        if year < 100:
                            year += 2000
                        month = int(nums[1])
                        day = int(nums[2])
                        deadline = f"{year}.{month:02}.{day:02}"

                results.append({
                    "source": "국가장학금",
                    "title": title,
                    "link": full_link,
                    "deadline": deadline
                })

            except Exception as e:
                print(f"[KOSAF 세부페이지 오류] {full_link} → {e}")
                continue

    except Exception as e:
        print(f"[KOSAF 메인페이지 요청 실패] {e}")
        return []  # 실패했으면 빈 리스트 반환

    return results


def crawl_scholarships():
    return crawl_yonsei() + crawl_kosaf()
