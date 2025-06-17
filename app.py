from flask import Flask, render_template, request
from crawler import crawl_scholarships
from datetime import datetime

app = Flask(__name__)

def parse_grade(grade_raw):
    """
    학년 문자열에서 숫자만 추출해서 정수로 변환 (예: "3학년" → 3)
    """
    try:
        return int(''.join(filter(str.isdigit, grade_raw)))
    except:
        return None


def filter_by_income(scholarships, income):
    income = int(income)

    # 항상 제외할 장학금 키워드
    always_excluded = [
        "파란사다리 사업", 
        "인천인재평생교육진흥원", 
        "인천 청년 해외배낭연수", 
        "강원·세종건설·신디자인랩", 
        "가구원 동의", 
        "농촌출신대학생 학자금융자"
    ]

    if income < 10:
        base_excluded = [
            "국가근로장학금",
            "지역인재장학금",
            "다자녀 국가장학금",
            "국가장학금 Ⅰ유형",
            "국가장학금 Ⅱ유형"
        ]
    else:
        base_excluded = []

    filtered = []
    for post in scholarships:
        title = post['title']

        # 항상 제외할 항목
        if any(keyword in title for keyword in always_excluded):
            continue

        # 고소득자용 제외 필터
        if any(excluded in title for excluded in base_excluded):
            continue

        # 나머지 조건은 그대로
        if "광진복지재단 미래도약" in title and income > 5:
            continue
        if "주거안정장학금" in title and income != 1:
            continue
        if "우양재단 북평고 졸업 장학생" in title and income > 4:
            continue
        if "상반기 강화군 대학생" in title and income > 8:
            continue
        if "푸른등대 삼성기부장학금" in title and income > 3:
            continue
        if "우양재단 강릉여고졸업" in title and income > 4:
            continue
        if "우양재단 자매애" in title and income > 4:
            continue
        if "MG새마을금고 청년누리장학생" in title and income > 5:
            continue
        if "서울희망 대학 진로 장학금" in title and income > 4:
            continue
        if "강원인재원 주거비" in title and income > 5:
            continue
        if "포스코비전장학생" in title and income > 5:

        filtered.append(post)

    return filtered





def filter_by_grade(scholarships, grade_raw):
    grade = parse_grade(grade_raw)
    if grade is None:
        return scholarships  # 학년 파싱 실패하면 필터링 생략

    filtered = []
    for post in scholarships:
        title = post['title']

        # 2학년 이상
        if grade < 2 and any(keyword in title for keyword in [
            "양천장학회", "서울희망 대학 진로", "미래에셋 해외교환", "한경범장학회", "청파장학회"
        ]):
            continue

        # 3학년만
        if grade != 3 and "국가우수장학금(이공계)" in title:
            continue

        # 1학년만
        if grade != 1 and any(keyword in title for keyword in [
            "EBS 꿈장학생", "달서인재육성장학재단"
        ]):
            continue

        # 3학년 이하
        if grade > 3 and "푸른등대 삼성기부장학금" in title:
            continue

        # 1, 3학년만
        if grade not in (1, 3) and "인문100년장학금 장학생 선발" in title:
            continue

        # 3학년 이상
        if grade < 3 and any(keyword in title for keyword in [
            "중소기업 취업연계 장학사업", "삼원·지헌장학생"
        ]):
            continue

        # 4학년만
        if grade != 4 and "우양재단 자매애" in title:
            continue

        filtered.append(post)

    return filtered



def filter_by_gpa(scholarships, gpa):
    filtered = []
    gpa = float(gpa)

    for post in scholarships:
        title = post['title']

        if gpa < 2.0 and ("국가근로장학금" in title or "다문화가정장학금 신청안내" in title or "고졸 후학습자 장학사업(희망사다리Ⅱ유형)" in title or "중소기업 취업연계 장학사업" in title or "(재)연세동문장학회 제24기" in title or " 삼다수 장학생" in title):
            continue
        if gpa < 3.0 and ("지역인재장학금" in title or "상반기 강화군 대학생 등록금" in title or "성남시 다자녀가구 대학생" in title or "포스코비전장학생" in title):
            continue
        if gpa < 3.5 and ("어학우수장학금" in title or "한경범장학회 장학금" in title or "청파장학회 장학금" in title):
            continue
        if gpa < 2.7 and "후기 양천장학회 장학생" in title:
            continue
        if gpa < 3.7 and "대통령과학장학금" in title:
            continue
        if gpa < 3.4 and ("인문100년장학금" in title or "예술체육비전장학금" in title or "인문100년장학금 장학생" in title):
            continue
        if gpa < 3.3 and "국가우수장학금(이공계)" in title:
            continue
        if gpa < 2.4 and ("형제장학금 신청 안내" in title or "외국인재학생장학금 신청" in title):
            continue
        if gpa < 2.87 and "미래에셋 해외교환" in title:
            continue

        filtered.append(post)

    return filtered

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/result', methods=['POST'])
def result():
    user_info = {
        'age': request.form['age'],
        'grade': request.form['grade'],
        'income': request.form['income_level'],
        'gpa': request.form['gpa'],
        'filter_closed': request.form['filter_closed']
    }

    age = int(user_info['age'])
    if age <= 18:
        return render_template('result.html', posts=[], user=user_info, message="18세 이하에게 적합한 장학금이 없습니다.", kosaf_failed=False)

    scholarships = crawl_scholarships()

    # KOSAF 실패 여부 체크
    kosaf_failed = not any(post['source'] == "국가장학금" for post in scholarships)

    # 마감일 필터링
    if user_info['filter_closed'] == 'N':
        today = datetime.today().date()
        filtered_scholarships = []
        for post in scholarships:
            deadline = post.get('deadline')
            try:
                if deadline != '없음':
                    deadline_date = datetime.strptime(deadline, "%Y.%m.%d").date()
                    if deadline_date >= today:
                        filtered_scholarships.append(post)
                else:
                    filtered_scholarships.append(post)
            except:
                filtered_scholarships.append(post)
    else:
        filtered_scholarships = scholarships

    # 소득분위 필터링
    filtered_scholarships = filter_by_income(filtered_scholarships, user_info['income'])

    # 학년 필터링
    filtered_scholarships = filter_by_grade(filtered_scholarships, user_info['grade'])

    # GPA 필터링
    filtered_scholarships = filter_by_gpa(filtered_scholarships, user_info['gpa'])

    # 특정 장학금 추가 필터 (우양재단 북평고)
    if int(user_info['income']) >= 5:
        filtered_scholarships = [post for post in filtered_scholarships if "우양재단 북평고" not in post['title']]

    return render_template(
        'result.html',
        posts=filtered_scholarships,
        user=user_info,
        message=None,
        kosaf_failed=kosaf_failed
    )

if __name__ == '__main__':
    app.run(debug=True)
