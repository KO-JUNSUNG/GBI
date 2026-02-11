import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from logic import GBIEngine

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="Noah's GBI Engine", page_icon="💰", layout="wide")

# 시각적 가독성을 위한 커스텀 CSS
st.markdown("""
    <style>
    .stMetric { border: 1px solid #e6e9ef; padding: 10px; border-radius: 10px; background-color: #f8f9fb; }
    </style>
    """, unsafe_allow_html=True)

# 엔진 초기화
engine = GBIEngine()

# --- 2. 사이드바: 정밀한 입력 제어 ---
with st.sidebar:
    st.header("📊 입력 파라미터")
    
    with st.expander("🎯 목표 및 기간", expanded=True):
        target_amt = st.number_input("목표 금액 (현재가치 기준, 원)", value=50000000, step=1000000)
        years = st.slider("목표 기간 (년)", 0.5, 30.0, 3.0, 0.5)
    
    with st.expander("💵 자산 및 저축", expanded=True):
        curr_savings = st.number_input("현재 보유 자산 (원)", value=10000000, step=1000000)
        monthly_dep = st.number_input("월 저축 가능액 (원)", value=1000000, step=50000)
        is_begin = st.checkbox("월초 납입 (기초)", value=True)

    with st.expander("📈 시장 가정", expanded=True):
        ret_rate = st.slider("연 기대 수익률 (%)", -10.0, 20.0, 4.0, 0.1) / 100
        inf_rate = st.slider("연 물가상승률 (%)", -2.0, 10.0, 2.0, 0.1) / 100

    st.divider()
    st.caption("2026 노아에이티에스 신입사원 채용 사전과제")

# --- 3. 메인 대시보드 및 로직 실행 ---
st.title("💰 Noah's GBI(Goal-Based Investing) Engine")

# 엔진 실행 (핵심 계산 및 시계열 생성)
sim_res = engine.run_simulation(target_amt, curr_savings, monthly_dep, ret_rate, years, inf_rate, is_begin)
ts_data = engine.generate_timeseries(curr_savings, monthly_dep, ret_rate, years, inf_rate, is_begin)

if "error" in sim_res:
    st.error(f"❌ 설정 오류: {sim_res['error']}")
else:
    # (1) 핵심 지표 Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("목표 달성률", f"{sim_res['attainment_rate']}%", 
              delta="성공" if sim_res['is_feasible'] else "미달", 
              delta_color="normal" if sim_res['is_feasible'] else "inverse")
    m2.metric("실질 예상 가치", f"{sim_res['expected_fv_real']/10000:,.0f}만 원")
    m3.metric("명목 도달 금액", f"{sim_res['nominal_fv']/10000:,.0f}만 원")
    m4.metric("최종 Gap (실질)", f"{sim_res['gap_real']/10000:,.0f}만 원", delta_color="inverse")

    st.divider()

    # (2) 시계열 차트 및 솔루션 섹션
    col_chart, col_sol = st.columns([3, 2])

    with col_chart:
        st.subheader("📈 자산 성장 시뮬레이션")
        
        # Plotly를 이용한 전문적인 시계열 시각화
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ts_data['months'], y=ts_data['nominal'], name="명목 자산 (통장 잔고)", line=dict(color='#BDC3C7')))
        fig.add_trace(go.Scatter(x=ts_data['months'], y=ts_data['real'], name="실질 자산 (구매력 기준)", line=dict(color='#3498DB', width=3)))
        fig.add_hline(y=target_amt, line_dash="dash", line_color="#E74C3C", annotation_text="목표 실질 금액")
        
        fig.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title="경과 월수",
            yaxis_title="금액 (원)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_sol:
        st.subheader("💡 Solution & Insights")
        if sim_res['is_feasible']:
            st.success("🎉 현재 플랜은 재무적으로 매우 건전합니다!")
            st.balloons()
        else:
            req_pmt = sim_res['required_monthly_deposit']
            add_needed = sim_res['additional_savings_needed']
            
            if req_pmt:
                st.warning("⚠️ 목표 달성을 위해 저축액 증액이 필요합니다.")
                st.write(f"**필요 월 저축액:** {req_pmt/10000:,.0f}만 원")
                st.info(f"현재보다 매월 **{add_needed/10000:,.0f}만 원**을 추가로 저축하면 목표 달성이 가능합니다.")
            else:
                st.error("현재 수익률이 물가상승률보다 낮아 자산 가치가 하락 중입니다. 투자 수익률 개선이 최우선입니다.")

    # (3) 기획서 연동 탭
    with st.expander("📄 기획서 및 개발 문서 확인"):
        try:
            with open("DOCUMENTATION.md", "r", encoding="utf-8") as f:
                st.markdown(f.read())
        except FileNotFoundError:
            st.warning("문서 파일을 찾을 수 없습니다.")