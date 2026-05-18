import re
import difflib
from urllib.parse import urlparse
import tldextract  

# 1. 안전한 공식 도메인 화이트리스트
WHITELIST_DOMAINS = [
    "naver.com",
    "kakao.com",
    "daum.net",
    "google.com",
    "apple.com",
    "microsoft.com",
    "kbstar.com",
    "shinhan.com"
]

# 2. 타이포스쿼팅 비교 대상 대기업 브랜드명 리스트
TARGET_BRANDS = ["naver", "kakao", "google", "daum", "apple", "microsoft", "kbstar", "shinhan"]

# 3. 알려진 URL 단축 서비스
SHORTENER_DOMAINS = [
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly",
    "short.io", "rebrand.ly", "cutt.ly", "is.gd", "buff.ly"
]

# 4. 구조적 사칭 패턴 (단순 키워드 결합형만 유지)
BRAND_PATTERNS = [
    r"(naver|kakao|google|daum|apple|microsoft|kbstar|shinhan)-",
    r"-(login|secure|verify|auth|update|account)"
]

def extract_urls(text: str) -> list:
    """본문에서 URL 전체 추출"""
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(pattern, text)

def normalize_word(word: str) -> str:
    """시각적으로 속이기 쉬운 숫자나 오타 유도 문자를 정규화"""
    maps = {'0': 'o', '1': 'l', '3': 'e', '5': 's'}
    for k, v in maps.items():
        word = word.replace(k, v)
    return word

def is_typosquatting(domain: str) -> bool:
    """tldextract를 이용해 주 도메인과 서브도메인을 완벽히 분리 후 사칭 검사"""
    ext = tldextract.extract(domain)
    
    subdomain = ext.subdomain.lower() 
    registered_domain = ext.domain.lower()  

    # ────────────────────────────────────────────────────────
    # 탐지 시나리오 1: 서브도메인 낚시 기법 방어
    # 주 도메인은 따로 있으면서, 서브도메인 영역에 대기업 브랜드 이름을 슬쩍 끼워 넣은 경우
    # 예: pay.naver.pajmve.com -> subdomain에 'naver'가 포함됨
    # ────────────────────────────────────────────────────────
    sub_words = re.split(r'[\.-]', subdomain)
    for sw in sub_words:
        if not sw: continue
        if normalize_word(sw) in TARGET_BRANDS:
            return True

    # ────────────────────────────────────────────────────────
    # 탐지 시나리오 2: 진짜 메인 도메인 자체의 철자 변형(오타) 방어
    # 예: g00gle.com -> registered_domain이 'g00gle'
    # ────────────────────────────────────────────────────────
    normalized_main = normalize_word(registered_domain)
    
    # 2-1) 정규화했더니 브랜드명이랑 똑같아진 경우 (g00gle -> google)
    if normalized_main in TARGET_BRANDS and registered_domain not in TARGET_BRANDS:
        return True
        
    # 2-2) 철자가 묘하게 닮은 경우 (nvaer, never)
    for brand in TARGET_BRANDS:
        similarity = difflib.SequenceMatcher(None, brand, normalized_main).ratio()
        if 0.75 <= similarity < 1.0:
            return True
            
    return False

def analyze_url(url: str) -> dict:
    """URL 하나에 대한 위험도 분석"""
    score = 0
    reasons = []
    
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
    except:
        return {"url": url, "score": 0, "reasons": ["부적절한 URL 형식"]}

    # [화이트리스트 체크]
    is_safe = any(domain == white or domain.endswith("." + white) for white in WHITELIST_DOMAINS)
    if is_safe:
        return {"url": url, "score": 0, "reasons": []}

    # 1. HTTP 걸러내기 
    if url.startswith("http://"):
        score += 10
        reasons.append("HTTP 비암호화 연결")

    # 2. IP 주소 사용 
    if re.search(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', domain):
        score += 40
        reasons.append("IP 주소를 직접 사용한 도메인")

    # 3. URL 단축 서비스
    if any(shortener in domain for shortener in SHORTENER_DOMAINS):
        score += 12
        reasons.append("신뢰할 수 없는 URL 단축 서비스")

    # 4. 유사/사칭 도메인 및 구조 분석
    # 4-1) 비주류 TLD 사용
    if not domain.endswith(('.com', '.net', '.org', '.kr')): 
         score += 10
    
    # 4-2) 구조적 사칭 패턴
    for pattern in BRAND_PATTERNS:
        if re.search(pattern, domain):
            score += 30
            reasons.append("유명 브랜드 사칭 의심 패턴")
            break

    # 4-3) 알고리즘 기반 타이포스쿼팅/서브도메인 낚시 검사 
    if is_typosquatting(domain):
        score += 30
        reasons.append("타이포스쿼팅(오타 유도) 및 서브도메인 사칭 의심")

    # 5. 서브도메인이 과도하게 많은 경우
    if domain.count('.') >= 3:
        score += 15
        reasons.append("다중 서브도메인 (낚시성 경로)")

    return {
        "url": url,
        "score": score,
        "reasons": list(set(reasons))
    }

def analyze_urls(text: str) -> dict:
    urls = extract_urls(text)
    if not urls:
        return {"urls": [], "total_url_score": 0}

    results = [analyze_url(url) for url in urls]
    total_url_score = sum(r["score"] for r in results)

    return {
        "urls": results,
        "total_url_score": total_url_score
    }

if __name__ == "__main__":
    import json
    
    test_cases = """
    
    """
    
    result = analyze_urls(test_cases)
    print(json.dumps(result, indent=2, ensure_ascii=False))