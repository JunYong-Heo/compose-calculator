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

# 세션 상태 초기화 (중요)
if 'oxide_recipes' not in st.session_state: st.session_state.oxide_recipes = []
if 'nitrate_recipes' not in st.session_state: st.session_state.nitrate_recipes = []

# --- 배너(Tab) 나누기 ---
tab1, tab2 = st.tabs(["🔥 Oxide SSR Method", "💧 Nitrate Sol-Gel Method"])

# ==========================================
# [TAB 1] Oxide 합성
# ==========================================
with tab1:
    st.header("Oxide 계열 시약 합성")
    with st.expander("➕ Oxide 레시피 추가하기", expanded=True):
        col_n, col_m = st.columns([2, 1])
        with col_n: ox_name_in = st.text_input("샘플 이름", key="ox_name_input")
        with col_m: ox_mass_in = st.number_input("목표 질량 (g)", value=3.0, step=0.1, key="ox_mass_input")
        
        ox_options = list(PRECURSORS_DB.keys())
        selected_ox = st.multiselect("원소 선택", options=ox_options, key="ox_select")
        
        if selected_ox:
            st.write("조성 계수 입력:")
            ox_idx_cols = st.columns(len(selected_ox))
            ox_inputs = {}
            for i, el in enumerate(selected_ox):
                ox_inputs[el] = ox_idx_cols[i].number_input(f"{el} Index", value=1.0, format="%.4f", key=f"ox_val_{el}")
            
            if st.button("🚀 Oxide 레시피 추가"):
                # 계산 로직
                total_fw = sum(coeff * (PRECURSORS_DB[el]["mw"]/PRECURSORS_DB[el]["n"]) for el, coeff in ox_inputs.items())
                temp_data = []
                for el, coeff in ox_inputs.items():
                    db = PRECURSORS_DB[el]
                    eff_mw = db["mw"]/db["n"]
                    weight = (coeff * eff_mw / total_fw) * ox_mass_in
                    temp_data.append({"Element": el, "Precursor": db["name"], "MW": db["mw"], "Index": coeff, "Weight": weight})
                
                # 자동 이름 생성
                final_name = ox_name_in if ox_name_in else "".join([f"{e}{c:g}" for e, c in ox_inputs.items()])
                st.session_state.oxide_recipes.append({"name": final_name, "data": pd.DataFrame(temp_data), "total": ox_mass_in})
                st.rerun()

    # Oxide 저장 목록 표시
    if st.session_state.oxide_recipes:
        st.subheader(f"📋 Oxide 관리 목록 ({len(st.session_state.oxide_recipes)})")
        for i, r in enumerate(st.session_state.oxide_recipes):
            with st.container():
                c_title, c_del = st.columns([5, 1])
                c_title.markdown(f"**{i+1}. {r['name']}** ({r['total']}g)")
                if c_del.button("삭제", key=f"del_ox_{i}"):
                    st.session_state.oxide_recipes.pop(i)
                    st.rerun()
                st.dataframe(r['data'][["Element", "Precursor", "Index", "Weight"]], use_container_width=True)

# ==========================================
# [TAB 2] Nitrate 합성
# ==========================================
with tab2:
    st.header("Nitrate 계열 (EDTA-Citrate) 합성")
    with st.expander("➕ Nitrate 레시피 추가하기", expanded=True):
        col_n, col_m = st.columns([2, 1])
        with col_n: nit_name_in = st.text_input("샘플 이름", key="nit_name_input")
        with col_m: nit_mass_in = st.number_input("목표 생성물 질량 (g)", value=5.0, step=0.1, key="nit_mass_input")
        
        nit_options = list(NITRATE_DB.keys())
        selected_nit = st.multiselect("원소 선택", options=nit_options, key="nit_select")
        
        if selected_nit:
            st.write("조성 계수 입력:")
            nit_idx_cols = st.columns(len(selected_nit))
            nit_inputs = {}
            for i, el in enumerate(selected_nit):
                nit_inputs[el] = nit_idx_cols[i].number_input(f"{el} Index", value=1.0, format="%.4f", key=f"nit_val_{el}")
            
            if st.button("🚀 Nitrate 레시피 추가"):
                # 1. 시약 투입 질량 계산
                total_fw = sum(coeff * (NITRATE_DB[el]["mw"]/NITRATE_DB[el]["n"]) for el, coeff in nit_inputs.items())
                # (중요) 금속 총 몰수 계산: (목표질량 / 전체FW) * 원자 Index 합
                total_molar_scale = nit_mass_in / total_fw
                sum_indices = sum(nit_inputs.values())
                total_metal_moles = total_molar_scale * sum_indices
                
                temp_data = []
                for el, coeff in nit_inputs.items():
                    db = NITRATE_DB[el]
                    eff_mw = db["mw"]/db["n"]
                    weight = (coeff * eff_mw / total_fw) * nit_mass_in
                    temp_data.append({"Element": el, "Precursor": db["name"], "MW": db["mw"], "Index": coeff, "Weight": weight})
                
                # 2. EDTA / CA 계산 (총 몰수 기준)
                edta_w = total_metal_moles * 292.24 * 1.0  # 1:1
                ca_w = total_metal_moles * 210.14 * 2.0    # 1:2
                
                final_name = nit_name_in if nit_name_in else "".join([f"{e}{c:g}" for e, c in nit_inputs.items()])
                st.session_state.nitrate_recipes.append({
                    "name": final_name, "data": pd.DataFrame(temp_data), 
                    "total": nit_mass_in, "edta": edta_w, "ca": ca_w
                })
                st.rerun()

    # Nitrate 저장 목록 표시
    if st.session_state.nitrate_recipes:
        st.subheader(f"📋 Nitrate 관리 목록 ({len(st.session_state.nitrate_recipes)})")
        for i, r in enumerate(st.session_state.nitrate_recipes):
            with st.container():
                c_title, c_del = st.columns([5, 1])
                c_title.markdown(f"**{i+1}. {r['name']}** ({r['total']}g)")
                if c_del.button("삭제", key=f"del_nit_{i}"):
                    st.session_state.nitrate_recipes.pop(i)
                    st.rerun()
                
                st.dataframe(r['data'][["Element", "Precursor", "Index", "Weight"]], use_container_width=True)
                
                res1, res2, res3 = st.columns(3)
                res1.success(f"🧪 **EDTA:** {r['edta']:.4f} g")
                res2.success(f"🍋 **Citric Acid:** {r['ca']:.4f} g")
                res3.warning("💧 **pH 조절:** pH 8.0 (NH4OH)")
                st.write("---")

# ==========================================
# 📊 통합 엑셀 다운로드 로직
# ==========================================
if st.session_state.oxide_recipes or st.session_state.nitrate_recipes:
    st.divider()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        if st.session_state.oxide_recipes:
            ox_combined = []
            for r in st.session_state.oxide_recipes:
                df = r['data'].copy()
                df['Sample_Name'] = r['name']
                ox_combined.append(df)
            pd.concat(ox_combined).to_excel(writer, sheet_name='Oxide_Recipe', index=False)
            
        if st.session_state.nitrate_recipes:
            nit_combined = []
            for r in st.session_state.nitrate_recipes:
                df = r['data'].copy()
                df['Sample_Name'] = r['name']
                df['EDTA_g'] = r['edta']
                df['CA_g'] = r['ca']
                df['Target_pH'] = 8.0
                nit_combined.append(df)
            pd.concat(nit_combined).to_excel(writer, sheet_name='Nitrate_Recipe', index=False)

    st.download_button("📥 최종 엑셀 보고서 다운로드", data=output.getvalue(), file_name="AECSL_Batch_Report.xlsx", use_container_width=True)
