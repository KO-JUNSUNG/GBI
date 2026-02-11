def calculate_gbi(target_amount, current_savings, monthly_deposit, annual_interest_rate, years):
    """
    GBI 타당성 검증 핵심 로직
    """
    months = years * 12
    monthly_rate = (annual_interest_rate / 100) / 12
    
    # 1. 미래 가치(FV) 계산 (월 복리 가정)
    # FV = PV*(1+r)^n + PMT * (((1+r)^n - 1) / r)
    if monthly_rate > 0:
        fv = (current_savings * (1 + monthly_rate)**months) + \
             (monthly_deposit * ((1 + monthly_rate)**months - 1) / monthly_rate)
    else:
        fv = current_savings + (monthly_deposit * months)
        
    gap = target_amount - fv
    attainment_rate = (fv / target_amount) * 100
    
    return {
        "expected_fv": round(fv, 2),
        "gap": round(gap, 2),
        "attainment_rate": round(attainment_rate, 1)
    }