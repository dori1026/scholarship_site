from datetime import datetime

def filter_by_deadline(posts, user_pref_show_closed):
    """
    사용자가 '마감된 장학금 보기'를 껐을 때,
    마감일이 지난 것과 '정보 없음'도 제외
    """
    if user_pref_show_closed == 'Y':
        return posts

    today = datetime.today().date()
    filtered = []

    for post in posts:
        deadline_str = post.get("deadline", "").strip()

        if deadline_str in ["정보 없음", "없음", ""]:
            continue  # ❌ 마감일이 정보 없음이면 제외

        try:
            deadline = datetime.strptime(deadline_str, "%Y.%m.%d").date()
            if deadline >= today:
                filtered.append(post)  # ✅ 오늘 이후면 포함
        except ValueError:
            continue  # ❌ 날짜 형식 이상한 경우 제외

    return filtered
