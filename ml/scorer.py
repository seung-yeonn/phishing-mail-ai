# 카테고리별 키워드 사전
KEYWORDS = {
    "urgency": {  # 긴급성 표현 (+15점)
        "score": 15,
        "keywords": [
            "즉시", "지금 바로", "오늘까지", "만료", "긴급",
            "빨리", "서둘러", "마감", "기한", "당장",
            "지금 확인", "즉각", "신속히", "바로 지금"
        ]
    },
    "personal_info": {  # 개인정보 요구 (+20점)
        "score": 20,
        "keywords": [
            "비밀번호", "주민등록번호", "계좌번호", "인증번호",
            "카드번호", "주민번호", "신용카드", "보안카드",
            "OTP", "공인인증서", "계좌 정보", "개인정보", "개인정보 입력", "본인인증"
        ]
    },
    "threat": {  # 위협 및 유도 (+10점)
        "score": 10,
        "keywords": [
            "정지됩니다", "차단됩니다", "확인하지 않으면",
            "삭제됩니다", "제한됩니다", "불이익", "법적 조치",
            "계정이 잠깁니다", "서비스 중단", "이용 정지", "인증하세요"
        ]
    },
    "impersonation": {  # 기관 사칭 (+15점)
        "score": 15,
        "keywords": [
            "국세청", "금융감독원", "경찰청", "검찰",
            "카카오 고객센터", "네이버 보안팀", "금융위원회"
        ]
    },
    "reward": {  # 보상/당첨 유도 (+10점)
        "score": 10,
        "keywords": [
            "당첨", "무료", "축하합니다", "선물",
            "환급", "캐시백"
        ]
    }
}

def match_keywords(text: str) -> dict:
    """키워드 매칭 후 카테고리별 탐지 결과 반환"""
    results = {}

    for category, data in KEYWORDS.items():
        found = [kw for kw in data["keywords"] if kw in text]
        if found:
            results[category] = {
                "found": found,
                "score": data["score"]
            }

    return results

def calculate_score(text: str, url_score: int = 0) -> dict:
    """최종 점수 계산 및 등급 분류"""
    matched = match_keywords(text)
    
    # 점수 합산
    # 첫 키워드 기본 점수 + 같은 카테고리 반복시 추가 키워드당 10점씩으로 계산

    total_score = sum(
    v["score"] + (len(v["found"]) - 1) * 10
    for v in matched.values()
    )
    total_score += url_score



    # 탐지된 키워드 리스트 합치기 (출력을 위해)
    threats = []
    for v in matched.values():
        threats.extend(v["found"])

    return {
        "score": total_score,
        "threats": threats,
        "matched_categories": list(matched.keys())
    }


# 테스트
if __name__ == "__main__":
    sample = "즉시 본인인증 하세요. 비밀번호를 입력하지 않으면 계정이 잠깁니다."
    result = calculate_score(sample)
    print(result)