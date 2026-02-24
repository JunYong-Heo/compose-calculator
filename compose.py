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

st.set_page_config(page_title="AECSL Smart Calc", layout="wide")
st.title("🔬 AECSL Advanced Batch Manager")

if 'recipes' not in st.session_state:
    st.session_state.recipes = []

# --- 1단계: 레시피 설계 및 추가 ---
with st.expander("➕ 새 레시피 추가하기", expanded=True):
    col_name, col_mass = st.columns([2, 1])
    with col_name:
        sample_name_input = st.text_input("샘플 이름 (비워두면 화학식 자동 생성)", value="")
    with col_mass:
        target_mass = st.number_input("목표 질량 (g)", value=3.0, step=0.1)

    selected_els = st.multiselect("원소 선택", options=list(PRECURSORS_DB.keys()), default=["Ba"])
    
    if selected_els:
        st.write("조성 계수 입력:")
        idx_cols = st.columns(min(len(selected_els), 5))
        current_inputs = {}
        for i, el in enumerate(selected_els):
            with idx_cols[i % 5]:
                dv = 1.0 if el == "Ba" else 0.0
                current_inputs[el] = st.number_input(f"{el} Index", value=dv, format="%.4f", key=f"new_{el}")
        
        total_idx = sum(current_inputs.values())
        is_integer = (total_idx % 1 == 0)
        
        if not is_integer:
            st.warning(f"⚠️ 현재 Index의 합이 {total_idx:.4f}입니다. 정수인지 확인하세요!")

        if st.button("🚀 목록에 레시피 추가"):
            if not sample_name_input.strip():
                formula_parts = []
                for el in selected_els:
                    val = current_inputs[el]
                    if val > 0:
                        idx_str = "" if val == 1.0 else f"{val:g}"
                        formula_parts.append(f"{el}{idx_str}")
                sample_name = "".join(formula_parts)
            else:
                sample_name = sample_name_input

            total_fw = 0
            temp_list = []
            for el, coeff in current_inputs.items():
                if coeff > 0:
                    db = PRECURSORS_DB[el]
                    eff_mw = db["mw"] / db["n"]
                    total_fw += coeff * eff_mw
                    temp_list.append({"Element": el, "Precursor": db["name"], "MW": db["mw"], "Eff_MW": eff_mw, "Index": coeff})
            
            if total_fw > 0:
                for item in temp_list:
                    item["Weight"] = (item["Index"] * item["Eff_MW"] / total_fw) * target_mass
                st.session_state.recipes.append({"name": sample_name, "target_mass": target_mass, "data": pd.DataFrame(temp_list), "is_int": is_integer})
                st.rerun()

# --- 2단계: 저장된 목록 및 수정 ---
if st.session_state.recipes:
    st.divider()
    st.subheader(f"📋 관리 중인 레시피 ({len(st.session_state.recipes)}개)")
    
    precursor_info = {}
    weight_rows = []
    index_rows = []

    for idx, recipe in enumerate(st.session_state.recipes):
        with st.container():
            col_title, col_del = st.columns([5, 1])
            if not recipe["is_int"]:
                col_title.warning(f"⚠️ {idx+1}. {recipe['name']} (Index 합 확인 필요)")
            else:
                col_title.markdown(f"#### {idx+1}. {recipe['name']}")
            
            if col_del.button("삭제", key=f"del_{idx}"):
                st.session_state.recipes.pop(idx)
                st.rerun()

            df = recipe['data'].copy()
            with st.expander(f"🔍 상세 정보 및 수정"):
                st.table(df[["Element", "Precursor", "MW", "Index", "Weight"]])
                
                st.write("---")
                st.write("**칭량 실수 시 아래를 입력하세요:**")
                err_p = st.selectbox("실수한 시료 선택", df['Precursor'].tolist(), key=f"err_sel_{idx}")
                orig_w = df.loc[df['Precursor'] == err_p, 'Weight'].values[0]
                actual_w = st.number_input(f"실제로 넣은 {err_p} 무게 (g)", value=float(orig_w), format="%.5f", key=f"act_w_{idx}")
                
                final_total = recipe['target_mass']
                
                # 수정 로직 및 화면 출력 보강
                if actual_w > orig_w:
                    ratio = actual_w / orig_w
                    final_total = recipe['target_mass'] * ratio
                    
                    st.warning(f"🚨 오차 감지: 모든 성분을 {ratio:.4f}배 증량합니다. (최종 목표: {final_total:.4f}g)")
                    
                    # 수정된 무게 계산
                    df_adj = df.copy()
                    df_adj['New Total(g)'] = df_adj['Weight'] * ratio
                    df_adj['Add More(g)'] = df_adj.apply(lambda x: 0.0 if x['Precursor'] == err_p else x['New Total(g)'] - x['Weight'], axis=1)
                    
                    st.write("**[수정 레시피: 추가로 더 넣어야 할 양]**")
                    st.dataframe(df_adj[["Precursor", "Weight", "New Total(g)", "Add More(g)"]].style.format(precision=4), use_container_width=True)
                    
                    # 엑셀 저장을 위해 df 업데이트
                    df['Weight'] = df_adj['New Total(g)']
                
                # 엑셀용 데이터 수집
                w_row = {"Sample Name": recipe['name'], "Total(g)": round(final_total, 4)}
                idx_row = {"Sample Name": recipe['name']}
                for _, r in df.iterrows():
                    precursor_info[r['Precursor']] = {"MW": round(r['MW'], 2), "Eff_MW": round(r['Eff_MW'], 2)}
                    w_row[r['Precursor']] = round(r['Weight'], 4)
                    idx_row[r['Precursor']] = round(r['Index'], 4)
                weight_rows.append(w_row)
                index_rows.append(idx_row)

    # --- 3단계: 엑셀 다운로드 (기존과 동일) ---
    if weight_rows:
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Batch_Recipe')
            head_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
            cell_fmt = workbook.add_format({'border': 1, 'align': 'center'})
            title_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#2E75B6'})

            # 1&2. 시료 정보
            worksheet.write(0, 0, "1&2. Precursor Info", title_fmt)
            for c, h in enumerate(["Precursor", "MW", "Eff_MW"]): worksheet.write(1, c, h, head_fmt)
            for r, (p_name, vals) in enumerate(precursor_info.items(), start=2):
                worksheet.write(r, 0, p_name, cell_fmt); worksheet.write(r, 1, vals["MW"], cell_fmt); worksheet.write(r, 2, vals["Eff_MW"], cell_fmt)

            # 3. Weighing (오른쪽)
            start_col = 4
            worksheet.write(0, start_col, "3. Weighing Recipes (g)", title_fmt)
            df_weights = pd.DataFrame(weight_rows)
            for c, col_name in enumerate(df_weights.columns):
                worksheet.write(1, start_col + c, col_name, head_fmt)
                for r, val in enumerate(df_weights[col_name], start=2): worksheet.write(r, start_col + c, val if pd.notna(val) else "-", cell_fmt)

            # 4. Indices (아래쪽)
            idx_start_row = len(df_weights) + 4
            worksheet.write(idx_start_row, start_col, "4. Composition Indices", title_fmt)
            df_indices = pd.DataFrame(index_rows)
            for c, col_name in enumerate(df_indices.columns):
                worksheet.write(idx_start_row + 1, start_col + c, col_name, head_fmt)
                for r, val in enumerate(df_indices[col_name], start=idx_start_row + 2): worksheet.write(r, start_col + c, val if pd.notna(val) else "-", cell_fmt)

            worksheet.set_column(0, 25, 15)

        st.download_button(label="📥 최종 보고서 엑셀 다운로드", data=output.getvalue(), file_name="AECSL_Auto_Recipe.xlsx", use_container_width=True)
