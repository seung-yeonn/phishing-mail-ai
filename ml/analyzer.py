from dotenv import load_dotenv
import os

load_dotenv()


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from url_analyzer import analyze_urls
from llm_analyzer import analyze_text_with_llm
from scorer import calculate_score

app = FastAPI(title="AI 피싱 메일 탐지 API")

class MailAnalyzeRequest(BaseModel):
    text: str

@app.post("/analyze")
async def analyze_email(request: MailAnalyzeRequest):
    body_text = request.text
    
    if not body_text.strip():
        raise HTTPException(status_code=400, detail="이메일 본문이 비어있습니다.")

    # ────────────────────────────────────────────────────────
    # 1단계: 룰베이스 및 URL 분석 엔진
    # ────────────────────────────────────────────────────────
    u_res = analyze_urls(body_text)
    k_res = calculate_score(body_text)

    rule_total = u_res["total_url_score"] + k_res["score"]
    rule_final = min(rule_total, 60)

    rule_evidence = []
    for u in u_res["urls"]:
        rule_evidence.extend(u.get("reasons", []))
    rule_evidence = list(set(rule_evidence + k_res["threats"])) # 중복 제거
    
    # ────────────────────────────────────────────────────────
    # Early Exit : 본문이 너무 깨끗하고 URL도 없거나 완전 안전하면 GPT 호출 패스
    # ────────────────────────────────────────────────────────
    
    if rule_final >= 50:
        return {
            "score": rule_final,
            "grade": "위험",
            "threats": k_res["threats"],
            "urls": [u["url"] for u in u_res["urls"] if u["score"] > 0],
            "method": "fast-track" # 룰베이스만으로 잡음!
        }
    
    suspicious_keywords = ["즉시", "비밀번호", "인증", "정지", "차단", "만료"]
    is_keyword_safe = not any(kw in body_text for kw in suspicious_keywords)
    
    if u_res["total_url_score"] == 0 and is_keyword_safe:
        return {
            "score": 0,
            "grade": "안전",
            "threats": [],
            "urls": [],
            "highlight_sentences": []
        }

    # ────────────────────────────────────────────────────────
    # 2단계: GPT-4o-mini 문맥 분석 엔진 가동
    # ────────────────────────────────────────────────────────
    gpt_res = analyze_text_with_llm(body_text)

    
    # GPT 점수를 40점 만점으로 가중치 스케일링
    gpt_score = gpt_res.get("score", 0)
    llm_weighted_score = min(gpt_score * 0.4, 40)

    # ────────────────────────────────────────────────────────
    # 3단계: 결과 통합 및 최종 점수/등급 산출
    # ────────────────────────────────────────────────────────
    final_score = int(rule_final + llm_weighted_score)
    total_threats = list(set(gpt_res.get("reasons", []) + rule_evidence))
    
    # 등급 분류
    if final_score >= 70:
        grade = "위험"
    elif final_score >= 40:
        grade = "주의"
    else:
        grade = "안전"

    # 프론트엔드가 요구한 최종 JSON 구조로 조립
    return {
        "score": final_score,
        "grade": grade,
        "threats": total_threats,
        "urls": [u["url"] for u in u_res["urls"] if u.get("score", 0) > 0],
        "highlight_sentences": gpt_res.get("highlight_sentences", [])
    }