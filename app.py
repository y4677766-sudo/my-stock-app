import streamlit as st
import FinanceDataReader as fdr
import pandas as pd

# --- 새로 추가된 기능: 숫자를 한글 금액으로 변환하는 함수 ---
def number_to_korean(num):
    if num == 0:
        return "0 원"
    
    units = ["", "만", "억", "조"]
    result = []
    unit_index = 0
    
    while num > 0:
        remainder = num % 10000
        if remainder > 0:
            # 1,000단위 콤마 추가하여 가독성 향상
            result.append(f"{remainder:,}{units[unit_index]}")
        num //= 10000
        unit_index += 1
        
    return " ".join(reversed(result)) + " 원"
# -----------------------------------------------------------------

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="한국 주식 종목 추천 AI", layout="wide")
st.title("🤖 한국 주식 AI 추천기")
st.markdown("네이버 금융/KRX 금융 데이터를 바탕으로 투자 가능성이 있는 금액에 적합하도록 추천합니다.")

# 2. 투자 가능 금액 설정 UI (화면을 가로로 나누어 배치)
col1, col2 = st.columns([7, 3]) # 입력칸과 한글 표시칸의 비율을 7:3으로 나눔

with col1:
    budget = st.number_input("💰 투자 가능한 금액을 입력하세요 (원)", min_value=1000, value=1000000, step=10000)

with col2:
    # 빈 공간을 살짝 띄워서 높이를 맞춤
    st.write("") 
    st.write("")
    # 한글 변환 결과를 크고 굵은 파란색 글씨로 출력
    korean_budget = number_to_korean(budget)
    st.markdown(f"<h3 style='color: #1E88E5; margin-top: 5px;'>{korean_budget}</h3>", unsafe_allow_html=True)


# 3. 추천 실행 로직 (기존 로직 100% 유지)
if st.button("추천 실행"):
    with st.spinner("실시간 한국 주식 전체 종목 데이터를 수집하고 분석하는 중입니다..."):
        try:
            # KRX(KOSPI, KOSDAQ, KONEX) 전체 종목 실시간 현재가 불러오기
            df = fdr.StockListing('KRX')
            
            # KOSPI, KOSDAQ 시장만 필터링
            df = df[df['Market'].isin(['KOSPI', 'KOSDAQ'])]
            
            # 투자 금액 기준 필터링 (현재가가 0보다 크고 예산보다 작거나 같은 종목)
            df_filtered = df[(df['Close'] > 0) & (df['Close'] <= budget)].copy()
            
            if df_filtered.empty:
                st.warning("해당 금액으로 매수할 수 있는 KOSPI/KOSDAQ 종목이 없습니다.")
            else:
                # 4. AI 퀀트 추천 스코어링 계산
                df_filtered = df_filtered[df_filtered['Volume'] > 0]
                
                max_volume = df_filtered['Volume'].max()
                df_filtered['Vol_Score'] = (df_filtered['Volume'] / max_volume) * 100
                
                df_filtered['AI_Score'] = (df_filtered['Vol_Score'] * 0.4) + (df_filtered['ChagesRatio'] * 0.6)
                
                top_stocks = df_filtered.sort_values(by='AI_Score', ascending=False).head(10)
                
                # 5. 결과 데이터 포맷팅 (소수점 둘째 자리 ROUND 처리 유지)
                result_df = pd.DataFrame({
                    '종목코드': top_stocks['Code'],
                    '종목명': top_stocks['Name'],
                    '시장': top_stocks['Market'],
                    '현재가(원)': top_stocks['Close'],
                    '등락률(%)': top_stocks['ChagesRatio'].apply(lambda x: round(x, 2)),
                    '당일거래량': top_stocks['Volume'],
                    'AI추천점수': top_stocks['AI_Score'].apply(lambda x: round(x, 2)),
                    '최대매수가능수량(주)': (budget // top_stocks['Close']).astype(int)
                })
                
                result_df.index = range(1, len(result_df) + 1)
                
                # 6. 결과 출력
                st.success(f"로직 검증 완료! 투자 가능 금액({korean_budget})에 맞춰 선별된 실시간 상위 10개 추천 종목입니다.")
                st.dataframe(result_df, use_container_width=True)
                
                st.info("💡 **추천 기준**: 현재가 기준 예산 범위 내 종목 중, 실시간 거래량(유동성)과 당일 등락률(모멘텀)을 스코어링하여 활발하게 움직이는 종목 위주로 선별했습니다.")
                
        except Exception as e:
            st.error(f"데이터 서버 통신 중 오류가 발생했습니다: {e}")