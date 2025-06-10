import requests
from bs4 import BeautifulSoup
import re
import logging

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def crawl_yonsei():
    BASE_URL = "https://wsw.yonsei.ac.kr"
    MAIN_URL = f"{BASE_URL}/wsw/notice/scholarship-board.do"

    soup = BeautifulSoup(requests.get(MAIN_URL, headers=HEADERS).text, "html.parser")
    results = []

    for a in soup.select(".board-table tbody tr"):
        title_tag = a.select_one("td.td-subject a")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        href = title_tag.get("href")
        full_link = BASE_URL + href

        results.append({
            "source": "연세대 미래캠",
            "title": title,
            "link": full_link,
            "deadline": "미정"
        })

    return results


def crawl_kosaf():
    BASE_URL = "https://www.kosaf.go.kr"
    MAIN_URL = f"{BASE_URL}/ko/scholar.do?pg=scholarship_main&hmNavi=JH,00,00,00"
    results = []

    try:
        res = requests.get(MAIN_URL, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.select("dl[class^=box] dd ul li a"):
            try:
                title = a.get_text(strip=True)
                href = a.get("href")
                full_link = BASE_URL + href

                detail_res = requests.get(full_link, headers=HEADERS, timeout=10)
                detail_res.raise_for_status()
                detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                text = detail_soup.get_text(separator="\n")
                deadline = "직접 확인"

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
                logging.warning(f"[KOSAF 세부페이지 오류] {full_link} → {e}")
                continue

    except Exception as e:
        logging.warning(f"[KOSAF 메인페이지 요청 실패] {e}")
        return []

    return results


def crawl_scholarships():
    return crawl_yonsei() + crawl_kosaf()
