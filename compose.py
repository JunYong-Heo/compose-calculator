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

st.set_page_config(page_title="AECSL Advanced Calc", layout="wide")
st.title("🔬 AECSL Advanced Batch Manager")

if 'oxide_recipes' not in st.session_state: st.session_state.oxide_recipes = []
if 'nitrate_recipes' not in st.session_state: st.session_state.nitrate_recipes = []

tab1, tab2 = st.tabs(["🔥 Oxide SSR Method", "💧 Nitrate Sol-Gel Method"])

# --- [공통 함수] 첫 번째 코드 스타일의 엑셀 생성 ---
def generate_excel(recipes, p_db, mode="Oxide"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Batch_Recipe')
        
        head_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
        title_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#2E75B6'})
        mw_fmt = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.00'})
        four_digit_fmt = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.0000'})

        # 1. 시료 정보 (MW 포함)
        worksheet.write(0, 0, "1&2. Precursor Info", title_fmt)
        for c, h in enumerate(["Precursor", "MW", "Eff_MW"]): worksheet.write(1, c, h, head_fmt)
        
        precursor_info = {}
        weight_rows = []
        index_rows = []

        for r_item in recipes:
            w_row = {"Sample Name": r_item['name'], "Total(g)": r_item['total']}
            i_row = {"Sample Name": r_item['name']}
            for _, row in r_item['data'].iterrows():
                # DB에서 시료 정보를 가져옴 (Oxide/Nitrate 구분)
                p_info = p_db.get(row['Element'])
                precursor_info[row['Precursor']] = {"MW": row['MW'], "Eff_MW": row['MW']/p_info['n']}
                w_row[row['Precursor']] = row['Weight']
                i_row[row['Element']] = row['Index']
            
            if mode == "Nitrate":
                w_row["EDTA(g)"] = r_item['edta']
                w_row["CA(g)"] = r_item['ca']
                w_row["NH4OH(mL)"] = r_item['nh4oh']
            weight_rows.append(w_row)
            index_rows.append(i_row)

        for r, (p_name, vals) in enumerate(precursor_info.items(), start=2):
            worksheet.write(r, 0, p_name, mw_fmt)
            worksheet.write(r, 1, vals["MW"], mw_fmt)
            worksheet.write(r, 2, vals["Eff_MW"], mw_fmt)

        # 3. Weighing Recipes
        start_col = 4
        worksheet.write(0, start_col, f"3. {mode} Weighing Recipes (g)", title_fmt)
        df_w = pd.DataFrame(weight_rows)
        for c, col in enumerate(df_w.columns):
            worksheet.write(1, start_col + c, col, head_fmt)
            for r, val in enumerate(df_w[col], start=2):
                fmt = four_digit_fmt if c > 0 else mw_fmt
                worksheet.write(r, start_col + c, val if pd.notna(val) else "-", fmt)

        # 4. Composition Indices
        idx_start_row = len(df_w) + 4
        worksheet.write(idx_start_row, start_col, "4. Composition Indices", title_fmt)
        df_i = pd.DataFrame(index_rows)
        for c, col in enumerate(df_i.columns):
            worksheet.write(idx_start_row + 1, start_col + c, col, head_fmt)
            for r, val in enumerate(df_i[col], start=idx_start_row + 2):
                fmt = four_digit_fmt if c > 0 else mw_fmt
                worksheet.write(r, start_col + c, val if pd.notna(val) else "-", fmt)

        worksheet.set_column(0, 0, 22); worksheet.set_column(4, 25, 18)
    return output.getvalue()

# ==========================================
# [TAB 1] Oxide SSR Method
# ==========================================
with tab1:
    with st.expander("➕ Oxide 레시피 추가", expanded=True):
        c1, c2 = st.columns([2, 1])
        ox_name = c1.text_input("샘플 이름", key="ox_n")
        ox_mass = c2.number_input("목표 질량 (g)", value=3.0, step=0.1, key="ox_m")
        selected_ox = st.multiselect("원소 선택", options=list(PRECURSORS_DB.keys()), key="ox_s")
        
        if selected_ox:
            st.write("조성 계수 입력:")
            cols = st.columns(len(selected_ox))
            ox_inds = {}
            for i, el in enumerate(selected_ox):
                ox_inds[el] = cols[i].number_input(f"{el} Index", value=1.0, format="%.4f", key=f"ox_v_{el}")
            
            if st.button("🚀 Oxide 추가"):
                fw = sum(ox_inds[e]*(PRECURSORS_DB[e]["mw"]/PRECURSORS_DB[e]["n"]) for e in selected_ox)
                data = []
                for e in selected_ox:
                    db = PRECURSORS_DB[e]
                    w = (ox_inds[e]*(db["mw"]/db["n"])/fw)*ox_mass
                    data.append({"Element": e, "Precursor": db["name"], "MW": db["mw"], "Index": ox_inds[e], "Weight": w})
                st.session_state.oxide_recipes.append({"name": ox_name if ox_name else "Oxide_Sample", "data": pd.DataFrame(data), "total": ox_mass})
                st.rerun()

    for i, r in enumerate(st.session_state.oxide_recipes):
        st.subheader(f"{i+1}. {r['name']}")
        st.table(r['data'][["Element", "Precursor", "MW", "Index", "Weight"]])
        if st.button(f"삭제", key=f"ox_del_{i}"): st.session_state.oxide_recipes.pop(i); st.rerun()

    if st.session_state.oxide_recipes:
        st.download_button("📥 Oxide 엑셀 다운로드", generate_excel(st.session_state.oxide_recipes, PRECURSORS_DB, "Oxide"), "Oxide_Recipes.xlsx")

# ==========================================
# [TAB 2] Nitrate Sol-Gel Method
# ==========================================
with tab2:
    with st.expander("➕ Nitrate 레시피 추가", expanded=True):
        c1, c2 = st.columns([2, 1])
        ni_name = c1.text_input("샘플 이름", key="ni_n")
        ni_mass = c2.number_input("목표 생성물 질량 (g)", value=5.0, step=0.1, key="ni_m")
        selected_ni = st.multiselect("원소 선택", options=list(NITRATE_DB.keys()), key="ni_s")
        
        if selected_ni:
            st.write("조성 계수 입력:")
            # 컬럼 생성을 안정적으로 처리
            ni_cols = st.columns(len(selected_ni))
            ni_inds = {}
            for i, el in enumerate(selected_ni):
                # 4개 이상 선택 시에도 입력칸이 유지되도록 함
                ni_inds[el] = ni_cols[i].number_input(f"{el} Index", value=1.0 if i==0 else 0.5, format="%.4f", key=f"ni_v_{el}")
            
            if st.button("🚀 Nitrate 추가"):
                # 1. 시약 필요량 계산
                fw = sum(ni_inds[e]*(NITRATE_DB[e]["mw"]/NITRATE_DB[e]["n"]) for e in selected_ni)
                # 금속 총 몰수 = (목표질량 / 1몰당 질량) * 금속 계수의 합
                molar_scale = ni_mass / fw
                total_metal_moles = molar_scale * sum(ni_inds.values())
                
                # 2. EDTA / CA / NH4OH 계산
                edta_w = total_metal_moles * 292.24 * 1.0
                ca_w = total_metal_moles * 210.14 * 2.0
                # 중화 공식: (EDTA 3H+ + CA 3H+) / 15M Ammonia
                nh4oh_v = ((total_metal_moles * 3) + (total_metal_moles * 2 * 3)) / 15.0 * 1000.0
                
                data = []
                for e in selected_ni:
                    db = NITRATE_DB[e]
                    w = (ni_inds[e]*(db["mw"]/db["n"])/fw)*ni_mass
                    data.append({"Element": e, "Precursor": db["name"], "MW": db["mw"], "Index": ni_inds[e], "Weight": w})
                
                st.session_state.nitrate_recipes.append({
                    "name": ni_name if ni_name else "Nitrate_Sample", 
                    "data": pd.DataFrame(data), "total": ni_mass, 
                    "edta": edta_w, "ca": ca_w, "nh4oh": nh4oh_v
                })
                st.rerun()

    # Nitrate 결과 출력
    for i, r in enumerate(st.session_state.nitrate_recipes):
        st.subheader(f"{i+1}. {r['name']}")
        st.table(r['data'][["Element", "Precursor", "MW", "Index", "Weight"]])
        res_c1, res_c2, res_c3 = st.columns(3)
        res_c1.metric("EDTA (g)", f"{r['edta']:.4f}")
        res_c2.metric("Citric Acid (g)", f"{r['ca']:.4f}")
        res_c3.metric("NH4OH (mL)", f"{r['nh4oh']:.2f}", help="pH 8 도달 예상 부피")
        if st.button(f"삭제", key=f"ni_del_{i}"): st.session_state.nitrate_recipes.pop(i); st.rerun()

    if st.session_state.nitrate_recipes:
        st.download_button("📥 Nitrate 엑셀 다운로드", generate_excel(st.session_state.nitrate_recipes, NITRATE_DB, "Nitrate"), "Nitrate_Recipes.xlsx")
