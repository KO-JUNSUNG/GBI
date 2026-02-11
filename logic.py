class GBIEngine:
    def __init__(self):
        self.DEFAULT_TAX_RATE = 0.154

    # -----------------------------
    # 1. Validation Layer
    # -----------------------------
    def validate_inputs(self,
                        target_amount,
                        current_savings,
                        monthly_deposit,
                        years,
                        inflation_rate,
                        annual_return_rate):

        if target_amount <= 0:
            return "목표 금액은 0보다 커야 합니다."
        if current_savings < 0 or monthly_deposit < 0:
            return "현재 자산 및 저축액은 음수일 수 없습니다."
        if years <= 0:
            return "기간은 0보다 커야 합니다."
        if not (-0.5 <= inflation_rate <= 0.5):
            return "물가상승률 범위 오류 (-50% ~ 50%)"
        if annual_return_rate <= -1:
            return "수익률은 -100% 이하일 수 없습니다."
        if annual_return_rate > 5:
            return "비정상적으로 높은 수익률입니다."

        return None

    # -----------------------------
    # 2. 세후 연 수익률 계산
    # -----------------------------
    def calculate_after_tax_return(self, annual_return_rate):
        if annual_return_rate <= 0:
            return annual_return_rate
        return annual_return_rate * (1 - self.DEFAULT_TAX_RATE)

    # -----------------------------
    # 3. 월 이자율 변환
    # -----------------------------
    def annual_to_monthly_rate(self, annual_rate):
        return (1 + annual_rate) ** (1/12) - 1

    # -----------------------------
    # 4. 미래가치 계산
    # -----------------------------
    def calculate_future_value(self,
                               current_savings,
                               monthly_deposit,
                               monthly_rate,
                               months,
                               is_begin_period):

        fv_pv = current_savings * (1 + monthly_rate) ** months

        if monthly_rate != 0:
            annuity_factor = ((1 + monthly_rate) ** months - 1) / monthly_rate
            if is_begin_period:
                annuity_factor *= (1 + monthly_rate)
        else:
            annuity_factor = months

        fv_pmt = monthly_deposit * annuity_factor

        return fv_pv + fv_pmt, fv_pv, annuity_factor

    # -----------------------------
    # 5. Required PMT 역산
    # -----------------------------
    def calculate_required_pmt(self,
                               target_amount,
                               total_inflation_factor,
                               fv_pv,
                               annuity_factor,
                               monthly_deposit,
                               annual_after_tax_rate):

        # 음수 수익률 구간에서는 제공하지 않음
        if annual_after_tax_rate <= 0:
            return None, None

        target_nominal = target_amount * total_inflation_factor
        shortfall = target_nominal - fv_pv

        if shortfall <= 0:
            return 0, 0

        required_pmt = shortfall / annuity_factor
        additional_needed = max(required_pmt - monthly_deposit, 0)

        return required_pmt, additional_needed

    # -----------------------------
    # 6. 시뮬레이션 오케스트레이터
    # -----------------------------
    def run_simulation(self,
                       target_amount,
                       current_savings,
                       monthly_deposit,
                       annual_return_rate,
                       years,
                       inflation_rate=0.02,
                       is_begin_period=False):

        error = self.validate_inputs(
            target_amount,
            current_savings,
            monthly_deposit,
            years,
            inflation_rate,
            annual_return_rate
        )
        if error:
            return {"error": error, "is_feasible": False}

        years = float(years)
        months = int(years * 12)

        after_tax_rate = self.calculate_after_tax_return(annual_return_rate)
        monthly_rate = self.annual_to_monthly_rate(after_tax_rate)

        total_fv_nominal, fv_pv, annuity_factor = self.calculate_future_value(
            current_savings,
            monthly_deposit,
            monthly_rate,
            months,
            is_begin_period
        )

        inflation_factor = (1 + inflation_rate) ** years
        expected_fv_real = total_fv_nominal / inflation_factor

        gap = target_amount - expected_fv_real
        is_feasible = gap <= 0
        attainment_rate = (expected_fv_real / target_amount) * 100

        required_pmt, additional_needed = (None, None)
        if not is_feasible:
            required_pmt, additional_needed = self.calculate_required_pmt(
                target_amount,
                inflation_factor,
                fv_pv,
                annuity_factor,
                monthly_deposit,
                after_tax_rate
            )

        return {
            "nominal_fv": round(total_fv_nominal, 0),
            "expected_fv_real": round(expected_fv_real, 0),
            "gap_real": round(gap, 0),
            "attainment_rate": round(attainment_rate, 1),
            "is_feasible": is_feasible,
            "required_monthly_deposit":
                round(required_pmt, 0) if required_pmt is not None else None,
            "additional_savings_needed":
                round(additional_needed, 0) if additional_needed is not None else None
        }
