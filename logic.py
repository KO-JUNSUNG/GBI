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
        # deflation(음수 물가상승률)도 일부 허용하도록 수정
        if not (-0.5 <= inflation_rate <= 0.5): 
            return "물가상승률이 비정상적입니다 (-50% ~ 50% 범위를 입력하세요)."
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
        # `float` 자료형 사용 시 부동소수점 오차로 인해 금전적 정합성이 깨질 위험이 있음
        # 향후 years, inflation_rate 등 float 타입을 decimal.Decimal 등으로 변경 고려
        try:
            years = float(years) 
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
        # 거치식(PV)의 명목 미래 가치
        fv_pv_nominal = current_savings * (1 + monthly_rate)**months
        # 적립식(PMT)의 명목 미래 가치
        if monthly_rate != 0:
            annuity_factor = ((1 + monthly_rate)**months - 1) / monthly_rate
            if is_begin_period:
                annuity_factor *= (1 + monthly_rate)
            fv_pmt_nominal = monthly_deposit * annuity_factor
        else:
            annuity_factor = months # 이자율 0%인 경우 단순 합산
            fv_pmt_nominal = monthly_deposit * months
            
        total_fv_nominal = fv_pv_nominal + fv_pmt_nominal
        # 6. 실질 가치로 환산 (인플레이션 반영)
        total_inflation_factor = (1 + inflation_rate)**years
        expected_fv_real = total_fv_nominal / total_inflation_factor
        # 7. 결과 분석
        gap = target_amount - expected_fv_real
        attainment_rate = (expected_fv_real / target_amount) * 100 if target_amount > 0 else 100
        is_feasible = gap <= 0
        # 8. Required PMT 계산
        required_monthly_deposit = 0
        additional_savings_needed = 0

        if not is_feasible:
            # 수학적으로는 음수 수익률에서도 PMT 역산이 가능하지만,
            # 손실 자산에 추가 납입을 유도하는 것은 합리적 재무 의사결정이 아니라고 판단
            # 따라서 음수 수익률 구간에서는 역산 결과를 제공하지 않음
            if nominal_after_tax_rate <= 0:
                required_monthly_deposit = None
                additional_savings_needed = None
            else:
                # 목표 금액의 명목 가치 환산 (인플레이션 감안)
                # "3년 뒤의 1억(현재가치)"을 모으려면 "3년 뒤 통장에 1억*물가상승분"이 있어야 함
                target_nominal = target_amount * total_inflation_factor
                
                # 현재 보유 자산(PV)으로 커버 가능한 명목 금액 차감
                shortfall_nominal = target_nominal - fv_pv_nominal
                
                # 부족분(Shortfall)을 메우기 위한 PMT 역산
                if shortfall_nominal > 0:
                    # PMT = FV / Annuity_Factor
                    # (앞서 구한 annuity_factor 재사용)
                    if annuity_factor != 0:
                        required_monthly_deposit = shortfall_nominal / annuity_factor
                    else:
                        required_monthly_deposit = shortfall_nominal  # 0개월인 경우
                
                # 추가 필요 금액 (Required - Current)
                additional_savings_needed = required_monthly_deposit - monthly_deposit
                
                # (음수 방어: PV만으로 이미 달성 가능한 경우)
                if additional_savings_needed < 0:
                    additional_savings_needed = 0
                    required_monthly_deposit = 0

        return {
            "nominal_fv": round(total_fv_nominal, 0),
            "expected_fv_real": round(expected_fv_real, 0),
            "gap_real": round(gap, 0),
            "attainment_rate": round(attainment_rate, 1),
            "is_feasible": is_feasible,
            # [추가됨] 역산 결과
            "required_monthly_deposit": round(required_monthly_deposit, 0) if required_monthly_deposit is not None else None,
            "additional_savings_needed": round(additional_savings_needed, 0) if additional_savings_needed is not None else None
        }