class GBIEngine:
    def __init__(self):
        self.DEFAULT_TAX_RATE = 0.154 

    def validate_inputs(self, target_amount, current_savings, monthly_deposit, years):
        """
        보안 취약점 방어: 비정상적 입력값 필터링 (Input Sanitization)
        """
        if target_amount <= 0:
            return "목표 금액은 0보다 커야 합니다."
        if current_savings < 0 or monthly_deposit < 0:
            return "현재 자산 및 저축액은 음수일 수 없습니다."
        if years <= 0.083: # 최소 1개월
            return "기간은 최소 1개월(0.083년) 이상이어야 합니다."
        if years > 100: # 현실적인 범위 제한 (DoS성 대규모 계산 방지)
            return "기간은 100년을 초과할 수 없습니다."
        return None

    def run_simulation(self, 
                       target_amount, 
                       current_savings, 
                       monthly_deposit, 
                       annual_return_rate, 
                       years, 
                       inflation_rate=0.02, 
                       is_begin_period=False):
        
        # 1. Validation 레이어 (보안 및 논리 검증)
        error = self.validate_inputs(target_amount, current_savings, monthly_deposit, years)
        if error:
            return {"error": error, "is_feasible": False}

        # 2. 데이터 타입 강제 (Type Safety)
        try:
            years = float(years)
            months = int(years * 12)
        except (ValueError, TypeError):
            return {"error": "숫자 형식의 입력값이 필요합니다."}

        # --- [기존 시뮬레이션 로직 시작] ---
        nominal_after_tax_rate = annual_return_rate * (1 - self.DEFAULT_TAX_RATE)
        monthly_rate = (1 + nominal_after_tax_rate)**(1/12) - 1
        
        fv_pv_nominal = current_savings * (1 + monthly_rate)**months
        
        if monthly_rate != 0:
            annuity_factor = ((1 + monthly_rate)**months - 1) / monthly_rate
            if is_begin_period:
                annuity_factor *= (1 + monthly_rate)
            fv_pmt_nominal = monthly_deposit * annuity_factor
        else:
            fv_pmt_nominal = monthly_deposit * months
            
        total_fv_nominal = fv_pv_nominal + fv_pmt_nominal
        total_inflation_factor = (1 + inflation_rate)**years
        expected_fv_real = total_fv_nominal / total_inflation_factor
        
        gap = target_amount - expected_fv_real
        attainment_rate = (expected_fv_real / target_amount) * 100 if target_amount > 0 else 100
        # --- [기존 시뮬레이션 로직 끝] ---

        return {
            "nominal_fv": round(total_fv_nominal, 0),
            "expected_fv_real": round(expected_fv_real, 0),
            "gap_real": round(gap, 0),
            "attainment_rate": round(attainment_rate, 1),
            "is_feasible": gap <= 0
        }