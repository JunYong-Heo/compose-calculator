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
st.title("🔬 AECSL Batch Recipe Manager")

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
    
    # 엑셀 생성을 위한 데이터 수집함
    mw_dict = {}
    eff_mw_dict = {}
    weight_rows = []

    for idx, recipe in enumerate(st.session_state.recipes):
        with st.container():
            col_title, col_del = st.columns([5, 1])
            col_title.markdown(f"#### {idx+1}. {recipe['name']}")
            if col_del.button("삭제", key=f"del_{idx}"):
                st.session_state.recipes.pop(idx)
                st.rerun()

            df = recipe['data'].copy()
            with st.expander(f"🔍 {recipe['name']} 상세 및 수정"):
                st.table(df[["Element", "Precursor", "Index", "Weight"]])
                
                err_p = st.selectbox("실수한 시료 선택", df['Precursor'].tolist(), key=f"err_sel_{idx}")
                orig_w = df.loc[df['Precursor'] == err_p, 'Weight'].values[0]
                actual_w = st.number_input(f"실제 무게 (g)", value=float(orig_w), format="%.5f", key=f"act_w_{idx}")
                
                final_total = recipe['target_mass']
                if actual_w > orig_w:
                    ratio = actual_w / orig_w
                    final_total = recipe['target_mass'] * ratio
                    df['Weight'] = df['Weight'] * ratio

                # 데이터 수집 (엑셀용)
                w_row = {"Sample Name": recipe['name'], "Total Mass(g)": round(final_total, 4)}
                for _, r in df.iterrows():
                    mw_dict[r['Precursor']] = r['MW']
                    eff_mw_dict[r['Precursor']] = r['Eff_MW']
                    w_row[r['Precursor']] = round(r['Weight'], 5)
                weight_rows.append(w_row)

    # --- 3단계: 구조화된 엑셀 다운로드 ---
    if weight_rows:
        st.divider()
        
        # 엑셀 파일 생성
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            sheet_name = 'Batch_Recipe'
            
            # 스타일 설정
            head_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
            title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#2E75B6'})
            cell_fmt = workbook.add_format({'border': 1, 'align': 'center'})

            # 데이터프레임 변환
            df_mw = pd.DataFrame([mw_dict]).rename(index={0: 'Molecular Weight (g/mol)'})
            df_eff = pd.DataFrame([eff_mw_dict]).rename(index={0: 'Effective MW (g/mol)'})
            df_weights = pd.DataFrame(weight_rows)

            # 1. 분자량 표 (MW)
            worksheet = workbook.add_worksheet(sheet_name)
            writer.sheets[sheet_name] = worksheet
            
            worksheet.write(0, 0, "1. Precursor Information (Pure MW)", title_fmt)
            df_mw.to_excel(writer, sheet_name=sheet_name, startrow=1)
            
            # 2. 환산 분자량 표 (Eff_MW)
            worksheet.write(4, 0, "2. Effective Molecular Weight (MW / n)", title_fmt)
            df_eff.to_excel(writer, sheet_name=sheet_name, startrow=5)
            
            # 3. 샘플별 칭량 레시피 표 (Weights)
            worksheet.write(9, 0, "3. Sample Weighing Recipes (g)", title_fmt)
            df_weights.to_excel(writer, sheet_name=sheet_name, startrow=10, index=False)
            
            # 열 너비 조정
            worksheet.set_column(0, 20, 18)

        st.download_button(
            label="📥 구조화된 통합 엑셀 다운로드",
            data=output.getvalue(),
            file_name="AECSL_Batch_Recipe_Structured.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
else:
    st.info("실험할 샘플들을 먼저 추가해 주세요.")
