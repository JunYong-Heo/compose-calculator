import streamlit as st
import pandas as pd
import io

# 1. 데이터베이스 설정
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

NITRATE_DB = {
    "La": {"name": "La(NO3)3·6H2O", "mw": 433.01, "n": 1},
    "Sr": {"name": "Sr(NO3)2",      "mw": 211.63, "n": 1},
    "Co": {"name": "Co(NO3)2·6H2O", "mw": 291.04, "n": 1},
    "Fe": {"name": "Fe(NO3)3·9H2O", "mw": 404.00, "n": 1},
}

st.set_page_config(page_title="AECSL Smart Calc", layout="wide")
st.title("🔬 AECSL Advanced Batch Manager")

# 세션 상태 초기화
if 'oxide_recipes' not in st.session_state: st.session_state.oxide_recipes = []
if 'nitrate_recipes' not in st.session_state: st.session_state.nitrate_recipes = []

# --- 배너(Tab) 나누기 ---
tab1, tab2 = st.tabs(["🔥 Oxide SSR Method", "💧 Nitrate Sol-Gel Method"])

# ==========================================
# [TAB 1] Oxide 합성 (기존 로직)
# ==========================================
with tab1:
    st.header("Oxide 계열 시약 합성")
    with st.expander("➕ Oxide 레시피 추가하기", expanded=True):
        col_n, col_m = st.columns([2, 1])
        s_name = col_n.text_input("샘플 이름", key="ox_name")
        t_mass = col_m.number_input("목표 질량 (g)", value=3.0, step=0.1, key="ox_mass")
        
        selected_els = st.multiselect("원소 선택", options=list(PRECURSORS_DB.keys()), key="ox_el")
        if selected_els:
            current_inputs = {}
            idx_cols = st.columns(len(selected_els))
            for i, el in enumerate(selected_els):
                current_inputs[el] = idx_cols[i].number_input(f"{el} Index", value=1.0, format="%.4f", key=f"ox_idx_{el}")
            
            if st.button("🚀 Oxide 레시피 추가"):
                total_fw = sum(c * (PRECURSORS_DB[e]["mw"]/PRECURSORS_DB[e]["n"]) for e, c in current_inputs.items())
                temp_list = []
                for e, c in current_inputs.items():
                    db = PRECURSORS_DB[e]
                    eff_mw = db["mw"]/db["n"]
                    w = (c * eff_mw / total_fw) * t_mass
                    temp_list.append({"Element": e, "Precursor": db["name"], "MW": db["mw"], "Index": c, "Weight": w})
                st.session_state.oxide_recipes.append({"name": s_name, "data": pd.DataFrame(temp_list), "total": t_mass})
                st.rerun()

    # 리스트 출력 및 삭제 로직 (생략 - 기존과 동일)

# ==========================================
# [TAB 2] Nitrate 합성 (신규 로직)
# ==========================================
with tab2:
    st.header("Nitrate 계열 (EDTA-Citrate) 합성")
    with st.expander("➕ Nitrate 레시피 추가하기", expanded=True):
        col_n, col_m = st.columns([2, 1])
        s_name_nit = col_n.text_input("샘플 이름", key="nit_name")
        t_mass_nit = col_m.number_input("목표 생성물 질량 (g)", value=5.0, step=0.1, key="nit_mass")
        
        selected_els_nit = st.multiselect("원소 선택", options=list(NITRATE_DB.keys()), key="nit_el")
        if selected_els_nit:
            current_inputs_nit = {}
            idx_cols_nit = st.columns(len(selected_els_nit))
            for i, el in enumerate(selected_els_nit):
                current_inputs_nit[el] = idx_cols_nit[i].number_input(f"{el} Index", value=1.0, format="%.4f", key=f"nit_idx_{el}")
            
            if st.button("🚀 Nitrate 레시피 추가"):
                # 계산 로직
                total_fw = sum(c * (NITRATE_DB[e]["mw"]/NITRATE_DB[e]["n"]) for e, c in current_inputs_nit.items())
                total_metal_moles = t_mass_nit / total_fw # 전체 스케일 결정하는 몰수
                
                temp_list = []
                for e, c in current_inputs_nit.items():
                    db = NITRATE_DB[e]
                    eff_mw = db["mw"]/db["n"]
                    w = (c * eff_mw / total_fw) * t_mass_nit
                    temp_list.append({"Element": e, "Precursor": db["name"], "MW": db["mw"], "Index": c, "Weight": w})
                
                edta_w = (sum(current_inputs_nit.values()) * total_metal_moles) * 292.24 * 1.0
                ca_w = (sum(current_inputs_nit.values()) * total_metal_moles) * 210.14 * 2.0
                
                st.session_state.nitrate_recipes.append({
                    "name": s_name_nit, "data": pd.DataFrame(temp_list), 
                    "total": t_mass_nit, "edta": edta_w, "ca": ca_w
                })
                st.rerun()

    # 결과 디스플레이
    for i, r in enumerate(st.session_state.nitrate_recipes):
        st.subheader(f"{i+1}. {r['name']}")
        st.table(r['data'][["Element", "Precursor", "Weight"]])
        c1, c2, c3 = st.columns(3)
        c1.write(f"**EDTA:** {r['edta']:.4f} g")
        c2.write(f"**Citric Acid:** {r['ca']:.4f} g")
        c3.warning("pH 8.0 (Ammonia)")

# ==========================================
# 📊 공통 엑셀 다운로드 (엑셀 시트 정리)
# ==========================================
if st.session_state.oxide_recipes or st.session_state.nitrate_recipes:
    st.divider()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        num_fmt = workbook.add_format({'num_format': '0.0000', 'border': 1})
        head_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})

        # 1. Oxide 시트
        if st.session_state.oxide_recipes:
            ox_df = pd.concat([r['data'].assign(Sample=r['name']) for r in st.session_state.oxide_recipes])
            ox_df.to_excel(writer, sheet_name='Oxide_Batch', index=False)

        # 2. Nitrate 시트 (EDTA/CA 포함)
        if st.session_state.nitrate_recipes:
            nit_rows = []
            for r in st.session_state.nitrate_recipes:
                for _, row in r['data'].iterrows():
                    nit_rows.append({
                        "Sample": r['name'], "Element": row['Element'], "Precursor": row['Precursor'],
                        "Weight(g)": row['Weight'], "EDTA(g)": r['edta'], "CA(g)": r['ca'], "pH": 8.0
                    })
            pd.DataFrame(nit_rows).to_excel(writer, sheet_name='Nitrate_Batch', index=False)

    st.download_button("📥 통합 엑셀 보고서 다운로드", data=output.getvalue(), file_name="AECSL_All_Recipes.xlsx", use_container_width=True)
