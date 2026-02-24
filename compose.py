import streamlit as st
import pandas as pd
import io

# 1. 시료 데이터베이스
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

st.set_page_config(page_title="AECSL Multi-Calc", layout="wide")
st.title("🔬 AECSL Multi-Batch Stoichiometry")

if 'recipes' not in st.session_state:
    st.session_state.recipes = []

# --- 1단계: 레시피 설계 및 추가 ---
with st.expander("➕ 새 레시피 추가하기", expanded=True):
    col_name, col_mass = st.columns([2, 1])
    with col_name:
        sample_name = st.text_input("샘플 이름", value=f"Sample_{len(st.session_state.recipes)+1}")
    with col_mass:
        target_mass = st.number_input("목표 질량 (g)", value=5.0, step=0.1)

    selected_els = st.multiselect("원소 선택", options=list(PRECURSORS_DB.keys()), default=["Ba"])
    
    if selected_els:
        st.write("조성 계수 입력:")
        idx_cols = st.columns(min(len(selected_els), 5))
        current_inputs = {}
        for i, el in enumerate(selected_els):
            with idx_cols[i % 5]:
                dv = 1.0 if el == "Ba" else 0.0
                current_inputs[el] = st.number_input(f"{el} Index", value=dv, format="%.4f", key=f"new_{el}")
        
        if st.button("🚀 목록에 레시피 추가"):
            total_fw = 0
            temp_list = []
            for el, coeff in current_inputs.items():
                if coeff > 0:
                    db = PRECURSORS_DB[el]
                    eff_mw = db["mw"] / db["n"]
                    total_fw += coeff * eff_mw
                    temp_list.append({
                        "Element": el, 
                        "Precursor": db["name"], 
                        "MW": db["mw"],
                        "Eff_MW": eff_mw, 
                        "Index": coeff
                    })
            
            if total_fw > 0:
                for item in temp_list:
                    item["Weight"] = (item["Index"] * item["Eff_MW"] / total_fw) * target_mass
                
                st.session_state.recipes.append({
                    "name": sample_name,
                    "target_mass": target_mass,
                    "data": pd.DataFrame(temp_list)
                })
                st.rerun()

# --- 2단계: 저장된 목록 및 개별 수정 ---
if st.session_state.recipes:
    st.divider()
    st.subheader(f"📋 관리 중인 레시피 ({len(st.session_state.recipes)}개)")
    
    export_rows = []

    for idx, recipe in enumerate(st.session_state.recipes):
        with st.container():
            col_title, col_del = st.columns([5, 1])
            col_title.markdown(f"#### {idx+1}. {recipe['name']}")
            if col_del.button("삭제", key=f"del_{idx}"):
                st.session_state.recipes.pop(idx)
                st.rerun()

            df = recipe['data'].copy()
            with st.expander(f"🔍 {recipe['name']} 상세"):
                st.table(df[["Element", "Precursor", "Index", "Weight"]])
                
                err_p = st.selectbox("실수한 시료 선택", df['Precursor'].tolist(), key=f"err_sel_{idx}")
                orig_w = df.loc[df['Precursor'] == err_p, 'Weight'].values[0]
                actual_w = st.number_input(f"실제 무게 (g)", value=float(orig_w), format="%.5f", key=f"act_w_{idx}")
                
                final_total_mass = recipe['target_mass']
                if actual_w > orig_w:
                    ratio = actual_w / orig_w
                    final_total_mass = recipe['target_mass'] * ratio
                    df['Weight'] = df['Weight'] * ratio # 수정된 무게로 업데이트
                
                # 엑셀 출력을 위한 데이터 정리 (샘플별 한 행으로 변환)
                row_data = {"Sample_Name": recipe['name'], "Total_Mass(g)": round(final_total_mass, 4)}
                for _, r in df.iterrows():
                    prefix = f"{r['Element']}({r['Precursor']})"
                    row_data[f"{prefix}_MW"] = r['MW']
                    row_data[f"{prefix}_Eff_MW"] = r['Eff_MW']
                    row_data[f"{prefix}_Index"] = r['Index']
                    row_data[f"{prefix}_Weight(g)"] = round(r['Weight'], 5)
                
                export_rows.append(row_data)

    # --- 3단계: 개선된 가로형 엑셀 다운로드 ---
    if export_rows:
        st.divider()
        final_df = pd.DataFrame(export_rows)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False, sheet_name='Batch_Summary')
            
            workbook = writer.book
            worksheet = writer.sheets['Batch_Summary']
            
            # 셀 서식
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
            num_format = workbook.add_format({'align': 'center', 'border': 1})
            
            for col_num, value in enumerate(final_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15, num_format)

        st.download_button(
            label="📥 통합 레시피 엑셀 다운로드 (가로형)",
            data=output.getvalue(),
            file_name="AECSL_Batch_Analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
else:
    st.info("레시피를 추가해 주세요.")
