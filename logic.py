import decimal 

class GBIEngine:
    def __init__(self):
        self.DEFAULT_TAX_RATE = 0.154 

    def validate_inputs(self, target_amount, current_savings, monthly_deposit, years, inflation_rate, annual_return_rate):
        """
        보안 및 금융 논리 취약점 방어
        """
        if target_amount <= 0:
            return "목표 금액은 0보다 커야 합니다."
        if current_savings < 0 or monthly_deposit < 0:
            return "현재 자산 및 저축액은 음수일 수 없습니다."
        if years <= 0.083:  # 1개월 미만 방지 (0.083년 = 1개월)
            return "기간은 최소 1개월 이상이어야 합니다."
        
        # annual return rate, inflation_rate 검증 추가: 하이퍼인플레이션이나 비정상 입력 방어
        if not (0 <= inflation_rate <= 0.5): 
            return "물가상승률이 비정상적입니다 (0% ~ 50% 범위를 입력하세요)."
        if annual_return_rate <= -1:
            return "수익률은 -100% 이하일 수 없습니다."
        if annual_return_rate > 5:
            return "비정상적으로 높은 수익률입니다."
        return None

    def run_simulation(self, 
                       target_amount, 
                       current_savings, 
                       monthly_deposit, 
                       annual_return_rate, 
                       years, 
                       inflation_rate=0.02, 
                       is_begin_period=False):
        """
        :param target_amount: 목표 금액 (현재 가치 기준, KRW)
        :param current_savings: 현재 보유 자산 (KRW)
        :param monthly_deposit: 매월 신규 적립액 (KRW)
        :param annual_return_rate: 연간 명목 수익률 (단위: 0.05 = 5%)
        :param years: 투자 기간 (단위: 년)
        :param inflation_rate: 예상 연간 물가상승률 (단위: 0.02 = 2%)
        :param is_begin_period: 기초 납입 여부 (True: 월초, False: 월말)
        """
        # 1. Validation 레이어 (보안 및 논리 검증)
        error = self.validate_inputs(target_amount, current_savings, monthly_deposit, years, inflation_rate, annual_return_rate)
        if error:
            return {"error": error, "is_feasible": False}

        # 2. 데이터 타입 강제 (Type Safety)
        try:
            years = decimal.Decimal(years)
            months = int(years * 12)
        except (ValueError, TypeError):
            return {"error": "숫자 형식의 입력값이 필요합니다."}

        # 3. 세후 명목 연 수익률 계산
        if annual_return_rate < 0:
            nominal_after_tax_rate = annual_return_rate  # 손실 시 세금 없음
        else:
            nominal_after_tax_rate = annual_return_rate * (1 - self.DEFAULT_TAX_RATE)
        # 4. 월 이자율 변환(기하평균 적용)
        monthly_rate = (1 + nominal_after_tax_rate)**(1/12) - 1
        # 5. 명목 미래 가치 계산 (현재 자산 + 월 적립금)
        fv_pv_nominal = current_savings * (1 + monthly_rate)**months
        
        if monthly_rate != 0:
            annuity_factor = ((1 + monthly_rate)**months - 1) / monthly_rate
            if is_begin_period:
                annuity_factor *= (1 + monthly_rate)
            fv_pmt_nominal = monthly_deposit * annuity_factor
        else:
            fv_pmt_nominal = monthly_deposit * months
            
        total_fv_nominal = fv_pv_nominal + fv_pmt_nominal
        # 6. 실질 가치로 환산 (인플레이션 반영)
        total_inflation_factor = (1 + inflation_rate)**years
        expected_fv_real = total_fv_nominal / total_inflation_factor
        # 7. 결과 분석
        gap = target_amount - expected_fv_real
        attainment_rate = (expected_fv_real / target_amount) * 100 if target_amount > 0 else 100

        return {
            "nominal_fv": round(total_fv_nominal, 0),
            "expected_fv_real": round(expected_fv_real, 0),
            "gap_real": round(gap, 0),
            "attainment_rate": round(attainment_rate, 1),
            "is_feasible": gap <= 0
        }