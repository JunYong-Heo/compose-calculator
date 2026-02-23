import streamlit as st
import pandas as pd

# 1. 시료 데이터베이스 (알파벳 순 정렬)
PRECURSORS_DB = {
    "Ba": {"name": "BaCO3", "mw": 197.34, "n": 1},
    "Co": {"name": "Co3O4", "mw": 240.8,  "n": 3},
    "Hf": {"name": "HfO2",  "mw": 210.49, "n": 1},
    "Mo": {"name": "MoO2",  "mw": 127.94, "n": 1},
    "Nb": {"name": "Nb2O5", "mw": 265.81, "n": 2},
    "Sc": {"name": "Sc2O3", "mw": 137.91, "n": 2},
    "Ta": {"name": "Ta2O5", "mw": 441.89, "n": 2},
    "Ti": {"name": "TiO2",  "mw": 79.9,   "n": 1},
    "W":  {"name": "WO3",   "mw": 231.84, "n": 1},
    "Y":  {"name": "Y2O3",  "mw": 225.81, "n": 2},
    "Zr": {"name": "ZrO2",  "mw": 123.22, "n": 1}
}

st.set_page_config(page_title="AECSL Stoichiometry", layout="wide")
st.title("🔬 PCFC/PCEC Stoichiometry & Correction")

# --- 설정 구역 (사이드바) ---
with st.sidebar:
    st.header("⚙️ 기본 설정")
    target_mass = st.number_input("목표 합성량 (Total g)", value=5.0, step=0.1)

# --- 1단계: 원소 선택 ---
st.write("### 1. 합성할 원소 선택")
selected_elements = st.multiselect(
    "사용할 원소를 선택하세요",
    options=list(PRECURSORS_DB.keys()),
    default=["Ba"]
)

# --- 2단계: 계수 입력 및 초기 계산 ---
if selected_elements:
    st.write("### 2. 조성 계수(Index) 입력")
    inputs = {}
    cols = st.columns(len(selected_elements) if len(selected_elements) < 5 else 4)
    
    for i, el in enumerate(selected_elements):
        with cols[i % len(cols)]:
            dv = 1.0 if el == "Ba" else 0.0
            inputs[el] = st.number_input(f"{el} Index", value=dv, format="%.4f", key=f"idx_{el}")

    # 초기 레시피 계산 로직
    total_fw = 0
    base_data = []
    for el in selected_elements:
        coeff = inputs[el]
        if coeff > 0:
            db = PRECURSORS_DB[el]
            eff_mw = db["mw"] / db["n"]
            total_fw += coeff * eff_mw
            base_data.append({
                "Element": el,
                "Precursor": db["name"],
                "Eff_MW": eff_mw,
                "Index": coeff
            })

    if total_fw > 0:
        # 초기 목표 무게 산출
        for item in base_data:
            item["Target_Weight"] = (item["Index"] * item["Eff_MW"] / total_fw) * target_mass
        
        df_init = pd.DataFrame(base_data)
        
        st.divider()
        st.subheader(f"📋 초기 레시피 (Target: {target_mass}g)")
        st.table(df_init[["Element", "Precursor", "Index", "Target_Weight"]].rename(columns={"Target_Weight": "Weight (g)"}))

        # --- 3단계: 오차 수정 (Over-weighing) ---
        st.divider()
        st.subheader("⚠️ 3. 칭량 오차 수정 (Scale-up)")
        st.info("시료를 더 넣었다면 아래에 입력하세요. 나머지 시료의 추가 칭량값을 계산합니다.")

        fix_c1, fix_c2 = st.columns(2)
        with fix_c1:
            error_p = st.selectbox("실수한 시료 선택", df_init['Precursor'].tolist())
        with fix_c2:
            # 선택된 시료의 원래 목표값
            orig_w = df_init.loc[df_init['Precursor'] == error_p, 'Target_Weight'].values[0]
            # 실제 들어간 무게 입력 (기본값은 목표값으로)
            actual_w = st.number_input("실제로 넣은 무게 (g)", value=float(orig_w), format="%.5f", key="fix_val")

        # 수정 로직: 더 많이 넣었을 경우에만 작동
        if actual_w > orig_w:
            ratio = actual_w / orig_w
            st.warning(f"🚨 {error_p}가 {actual_w - orig_w:.5f}g 더 들어갔습니다. 전체 스케일을 {ratio:.4f}배 키웁니다.")
            
            adj_list = []
            for _, row in df_init.iterrows():
                new_total = row['Target_Weight'] * ratio
                add_more = new_total - row['Target_Weight']
                
                # 본인 시료는 이미 들어갔으므로 추가량은 0
                is_error_item = (row['Precursor'] == error_p)
                
                adj_list.append({
                    "Precursor": row['Precursor'],
                    "Original (g)": row['Target_Weight'],
                    "New Total (g)": round(new_total, 5),
                    "추가로 더 넣을 양 (Add More)": 0.0 if is_error_item else round(add_more, 5)
                })
            
            st.write("#### ✅ [수정된 레시피] 나머지 시료를 아래만큼 더 넣으세요")
            st.dataframe(pd.DataFrame(adj_list).style.format(precision=5).highlight_max(subset=["추가로 더 넣을 양 (Add More)"], color="#223344"), use_container_width=True)
            st.success(f"💡 최종 총 질량은 **{target_mass * ratio:.4f}g**이 됩니다.")
        else:
            st.write("정상 칭량 중입니다. 목표치보다 많이 넣으면 수정 가이드가 나타납니다.")

    else:
        st.warning("계수(Index)를 입력하면 계산이 시작됩니다.")
else:
    st.info("위의 박스에서 합성할 원소들을 선택해 주세요.")