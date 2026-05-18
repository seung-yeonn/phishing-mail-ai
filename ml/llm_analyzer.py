import os
from openai import OpenAI
import json
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), timeout=10.0)

def analyze_text_with_llm(text: str) -> dict:

    
    # 입력값 검증 (analyzer에서 진행중이지만 한 번 더)
    if not text or not text.strip():
        return {"score": 0, "reasons": [], "highlight_sentences": []}
    
    fallback_result = {
        "score": 0,
        "reasons": [], 
        "highlight_sentences": []
    }

    system_prompt = """
    너는 기업 및 개인 이메일을 타겟으로 하는 스피어 피싱 및 사회공학적 공격을 탐지하는 최고의 사이버 보안 AI 전문가야.
    제공된 이메일 본문을 정밀 분석하여 피싱 위험도를 평가하고, 반드시 아래에 지정된 JSON 형식으로만 응답해줘.

    [분석 기준 및 점수 가이드]
    1. 긴급성/압박 (최대 30점): '즉시', '지금 바로', '오늘까지', '계정 만료' 등 사용자를 심리적으로 압박하는지 여부
    2. 개인정보/인증 요구 (최대 40점): '비밀번호 변경', '인증번호 입력', '계좌 확인' 등을 유도하는지 여부
    3. 위협/불이익 언급 (최대 30점): '확인하지 않으면 계정이 정지됩니다', '차단됩니다' 등 불이익을 주며 행동을 강제하는지 여부

    [주의 사항]
    - 이메일 내용이 완벽히 정상적인 비즈니스 레터나 뉴스레터라면 점수는 0점이며, reasons와 highlight_sentences는 빈 리스트여야 해.
    - 다른 설명이나 마크다운(```json 등)은 절대 붙이지 말고 오직 순수 JSON 데이터만 반환해.

    [출력 JSON 포맷 정의]
    {
        "score": 점수합산 (0 ~ 100 사이의 정수),
        "reasons": ["위험하다고 판단한 구체적인 근거 문장 1", "근거 문장 2"],
        "highlight_sentences": ["사용자가 주의 깊게 봐야 할 본문 속 위험한 핵심 문장 (최대 2~3개)"]
    }
    """

    try:
        # 응답 형식을 JSON 객체로 고정하는 response_format 세팅 적용
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"다음 이메일 본문을 분석해줘:\n\n{text}"}
            ],
            response_format={"type": "json_object"}, # 무조건 JSON으로만 대답하게 강제
            temperature=0.1 # 일관된 결과를 위해 창의성을 낮춤
        )
        
        # 결과 파싱
        result_content = response.choices[0].message.content
        try:
            return json.loads(result_content)
        except json.JSONDecodeError:
            return fallback_result

    except Exception as e:
        # API 오류, 네트워크 문제, 키 누락 등이 발생하면 프로그램이 터지지 않고
        # 룰 기반 엔진으로만 돌아가도록 안전하게 Fallback 결과를 리턴
        print(f"[Warning] OpenAI API 호출 중 에러 발생: {e}")
        return fallback_result
