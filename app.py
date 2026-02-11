import streamlit as st
import plotly.graph_objects as go
from logic import GBIEngine

# --------------------------------------------------
# 1. Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="Noah's Goal-Based Investing Engine",
    page_icon="💰",
    layout="wide"
)

engine = GBIEngine()

# --------------------------------------------------
# 2. Utility
# --------------------------------------------------
def format_krw(num):
    if num is None:
        return "-"
    return f"{num:,.0f} 원"

def format_manwon(num):
    if num is None:
        return "-"
    return f"{num/10000:,.0f} 만 원"

# --------------------------------------------------
# 3. Sidebar - Inputs
# --------------------------------------------------
with st.sidebar:
    st.header("📌 Goal Setting")

    target_amt = st.number_input(
        "목표 금액 (현재가치 기준, 원)",
        min_value=0,
        value=50_000_000,
        step=1_000_000
    )

    years = st.slider(
        "투자 기간 (년)",
        0.5, 30.0, 3.0, 0.5
    )

    st.header("💰 Current Status")

    curr_savings = st.number_input(
        "현재 보유 자산 (원)",
        min_value=0,
        value=10_000_000,
        step=1_000_000
    )

    monthly_dep = st.number_input(
        "월 저축액 (원)",
        min_value=0,
        value=1_000_000,
        step=100_000
    )

    is_begin = st.checkbox("월초 납입 (기초)", value=True)

    st.header("📈 Market Assumptions")

    ret_rate = st.slider(
        "연 기대 수익률 (%)",
        -10.0, 20.0, 4.0, 0.1
    ) / 100

    inf_rate = st.slider(
        "연 물가상승률 (%)",
        -2.0, 10.0, 2.0, 0.1
    ) / 100

    st.divider()
    st.caption("사전과제")

# --------------------------------------------------
# 4. Run Simulation
# --------------------------------------------------
st.title("💰 Goal-Based Investing Feasibility Engine")

sim_res = engine.run_simulation(
    target_amt,
    curr_savings,
    monthly_dep,
    ret_rate,
    years,
    inf_rate,
    is_begin
)

if "error" in sim_res:
    st.error(f"❌ 입력 오류: {sim_res['error']}")
    st.stop()

# 시계열은 validation 통과 후에만 생성
ts_data = engine.generate_timeseries(
    curr_savings,
    monthly_dep,
    ret_rate,
    years,
    inf_rate,
    is_begin
)

# --------------------------------------------------
# 5. Metrics Section
# --------------------------------------------------
m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "목표 달성률",
    f"{sim_res['attainment_rate']}%",
)

m2.metric(
    "실질 예상 가치 (현재가치)",
    format_manwon(sim_res["expected_fv_real"])
)

m3.metric(
    "명목 예상 잔고 (미래 통장금액)",
    format_manwon(sim_res["nominal_fv"])
)

m4.metric(
    "Gap (실질 기준)",
    format_manwon(sim_res["gap_real"])
)

st.divider()

# --------------------------------------------------
# 6. Chart + Solution
# --------------------------------------------------
col_chart, col_sol = st.columns([3, 2])

# ---------------- Chart ----------------
with col_chart:
    st.subheader("📈 자산 성장 경로")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=ts_data["months"],
            y=ts_data["nominal"],
            name="명목 자산",
            line=dict(width=2)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=ts_data["months"],
            y=ts_data["real"],
            name="실질 자산 (현재가치 기준)",
            line=dict(width=3)
        )
    )

    fig.add_hline(
        y=target_amt,
        line_dash="dash",
        annotation_text="목표 금액 (현재가치 기준)"
    )

    fig.update_layout(
        hovermode="x unified",
        xaxis_title="경과 월수",
        yaxis_title="금액 (원)",
        margin=dict(l=0, r=0, t=20, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------- Solution ----------------
with col_sol:
    st.subheader("💡 Interpretation")

    if sim_res["is_feasible"]:
        st.success("현재 가정 하에서 목표 달성이 가능합니다.")
    else:
        st.warning("현재 가정 하에서는 목표 달성이 어렵습니다.")

        req_pmt = sim_res["required_monthly_deposit"]
        add_needed = sim_res["additional_savings_needed"]

        if req_pmt is not None:
            st.markdown("### 📌 Required Adjustment")
            st.write(f"필요 월 저축액: **{format_manwon(req_pmt)}**")
            st.write(f"추가 저축 필요액: **{format_manwon(add_needed)}**")
        else:
            st.error(
                "현재 수익률이 0% 이하이므로 저축액 역산을 제공하지 않습니다. "
                "투자 수익률 가정을 재검토하십시오."
            )

st.divider()

# --------------------------------------------------
# 7. Documentation
# --------------------------------------------------
with st.expander("📄 프로젝트 기획서 및 로직 설명"):
    try:
        with open("DOCUMENTATION.md", "r", encoding="utf-8") as f:
            st.markdown(f.read())
    except FileNotFoundError:
        st.info("DOCUMENTATION.md 파일이 존재하지 않습니다.")
