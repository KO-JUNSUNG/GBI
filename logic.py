def calculate_gbi(target_amount, current_savings, monthly_deposit, annual_interest_rate, years):
    """
    GBI 타당성 검증 핵심 로직 (Refactored)
    - AI Code Review 반영: 엣지 케이스 방어 및 음수 금리 로직 개선
    """
    # 1. 입력값 검증 (Validation)
    if target_amount <= 0:
        return {"error": "목표 금액은 0보다 커야 합니다."}
    if years <= 0:
        return {"error": "기간은 1개월 이상이어야 합니다."}

    months = int(years * 12)  # 정수형 강제 변환
    monthly_rate = (annual_interest_rate / 100) / 12
    
    # 2. 미래 가치(FV) 계산
    # Case A: 이자율이 0인 경우 (ZeroDivision 방지)
    if monthly_rate == 0:
         fv = current_savings + (monthly_deposit * months)
    
    # Case B: 이자율이 존재할 때 (양수/음수 모두 복리 공식 적용)
    # FV = PV*(1+r)^n + PMT * (((1+r)^n - 1) / r)
    else:
        fv = (current_savings * (1 + monthly_rate)**months) + \
             (monthly_deposit * ((1 + monthly_rate)**months - 1) / monthly_rate)
        
    gap = target_amount - fv
    attainment_rate = (fv / target_amount) * 100
    
    # 3. 결과 반환
    return {
        "expected_fv": round(fv, 2),
        "gap": round(gap, 2),
        "attainment_rate": round(attainment_rate, 1),
        "is_achievable": fv >= target_amount
    }