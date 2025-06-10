from flask import Flask, render_template, request
from crawler import crawl_scholarships
from datetime import datetime

app = Flask(__name__)

def filter_by_income(scholarships, income):
    if int(income) < 10:
        return scholarships

    excluded_titles = [
        "국가근로장학금",
        "지역인재장학금",
        "다자녀 국가장학금",
        "국가장학금 Ⅰ유형",
        "국가장학금 Ⅱ유형"
    ]

    filtered = []
    for post in scholarships:
        if not any(excluded in post['title'] for excluded in excluded_titles):
            filtered.append(post)
    return filtered

def filter_by_gpa(scholarships, gpa):
    filtered = []
    gpa = float(gpa)

    for post in scholarships:
        title = post['title']

        if gpa < 2.0 and "국가근로장학금" in title:
            continue
        if gpa < 3.0 and "지역인재장학금" in title:
            continue
        if gpa < 3.5 and "어학우수장학금" in title:
            continue
        if gpa < 3.7 and "대통령과학장학금" in title:
            continue
        if gpa < 3.4 and ("인문100년장학금" in title or "예술체육비전장학금" in title):
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
