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

# --- [공통 함수] 엑셀 생성 (첫 번째 코드 스타일 유지) ---
def generate_excel(recipes, p_db, mode="Oxide"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Batch_Recipe')
        
        # 서식 설정
        head_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
        title_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#2E75B6'})
        mw_fmt = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.00'})
        four_digit_fmt = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.0000'})

        # 1. 시료 정보
        worksheet.write(0, 0, "1&2. Precursor Info", title_fmt)
        headers = ["Precursor", "MW", "Eff_MW"]
        for c, h in enumerate(headers): worksheet.write(1, c, h, head_fmt)
        
        precursor_info = {}
        weight_rows = []
        index_rows = []

        for r_item in recipes:
            w_row = {"Sample Name": r_item['name'], "Total(g)": r_item['total']}
            i_row = {"Sample Name": r_item['name']}
            for _, row in r_item['data'].iterrows():
                precursor_info[row['Precursor']] = {"MW": row['MW'], "Eff_MW": row['MW']/p_db.get(row['Element'], {"n":1})["n"]}
                w_row[row['Precursor']] = row['Weight']
                i_row[row['Element']] = row['Index']
            
            # Nitrate 전용 컬럼 추가
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

        # 4. Indices
        idx_start_row = len(df_w) + 4
        worksheet.write(idx_start_row, start_col, "4. Composition Indices", title_fmt)
        df_i = pd.DataFrame(index_rows)
        for c, col in enumerate(df_i.columns):
            worksheet.write(idx_start_row + 1, start_col + c, col, head_fmt)
            for r, val in enumerate(df_i[col], start=idx_start_row + 2):
                fmt = four_digit_fmt if c > 0 else mw_fmt
                worksheet.write(r, start_col + c, val if pd.notna(val) else "-", fmt)

        worksheet.set_column(0, 0, 20); worksheet.set_column(4, 25, 15)
    return output.getvalue()

# ==========================================
# [TAB 1] Oxide 합성
# ==========================================
with tab1:
    with st.expander("➕ Oxide 레시피 추가", expanded=True):
        c1, c2 = st.columns([2, 1])
        name = c1.text_input("샘플 이름", key="ox_n")
        mass = c2.number_input("목표 질량 (g)", value=3.0, step=0.1, key="ox_m")
        els = st.multiselect("원소 선택", options=list(PRECURSORS_DB.keys()), key="ox_s")
        if els:
            cols = st.columns(len(els))
            inds = {el: cols[i].number_input(f"{el} Index", value=1.0, format="%.4f", key=f"ox_v_{el}") for i, el in enumerate(els)}
            if st.button("🚀 Oxide 추가"):
                fw = sum(inds[e]*(PRECURSORS_DB[e]["mw"]/PRECURSORS_DB[e]["n"]) for e in els)
                data = [{"Element": e, "Precursor": PRECURSORS_DB[e]["name"], "MW": PRECURSORS_DB[e]["mw"], "Index": inds[e], "Weight": (inds[e]*(PRECURSORS_DB[e]["mw"]/PRECURSORS_DB[e]["n"])/fw)*mass} for e in els]
                st.session_state.oxide_recipes.append({"name": name if name else "Oxide_Sample", "data": pd.DataFrame(data), "total": mass})
                st.rerun()

    for i, r in enumerate(st.session_state.oxide_recipes):
        st.subheader(f"{i+1}. {r['name']}")
        st.table(r['data'][["Element", "Precursor", "MW", "Index", "Weight"]])
        if st.button(f"삭제", key=f"ox_del_{i}"): st.session_state.oxide_recipes.pop(i); st.rerun()

    if st.session_state.oxide_recipes:
        st.download_button("📥 Oxide 엑셀 다운로드", generate_excel(st.session_state.oxide_recipes, PRECURSORS_DB, "Oxide"), "Oxide_Recipes.xlsx", use_container_width=True)

# ==========================================
# [TAB 2] Nitrate 합성
# ==========================================
with tab2:
    with st.expander("➕ Nitrate 레시피 추가", expanded=True):
        c1, c2 = st.columns([2, 1])
        name = c1.text_input("샘플 이름", key="ni_n")
        mass = c2.number_input("목표 생성물 질량 (g)", value=5.0, step=0.1, key="ni_m")
        els = st.multiselect("원소 선택", options=list(NITRATE_DB.keys()), key="ni_s")
        if els:
            cols = st.columns(len(els))
            inds = {el: cols[i].number_input(f"{el} Index", value=1.0, format="%.4f", key=f"ni_v_{el}") for i, el in enumerate(els)}
            if st.button("🚀 Nitrate 추가"):
                fw = sum(inds[e]*(NITRATE_DB[e]["mw"]/NITRATE_DB[e]["n"]) for e in els)
                total_moles = (mass / fw) * sum(inds.values())
                
                edta_w = total_moles * 292.24 * 1.0
                ca_w = total_moles * 210.14 * 2.0
                # 암모니아 계산: EDTA(3H+) + CA(3H+) 중화 가정, 28% NH4OH (15M) 기준
                nh4oh_vol = ((total_moles * 1.0 * 3) + (total_moles * 2.0 * 3)) / 15.0 * 1000.0
                
                data = [{"Element": e, "Precursor": NITRATE_DB[e]["name"], "MW": NITRATE_DB[e]["mw"], "Index": inds[e], "Weight": (inds[e]*(NITRATE_DB[e]["mw"]/NITRATE_DB[e]["n"])/fw)*mass} for e in els]
                st.session_state.nitrate_recipes.append({"name": name if name else "Nit_Sample", "data": pd.DataFrame(data), "total": mass, "edta": edta_w, "ca": ca_w, "nh4oh": nh4oh_vol})
                st.rerun()

    for i, r in enumerate(st.session_state.nitrate_recipes):
        st.subheader(f"{i+1}. {r['name']}")
        st.table(r['data'][["Element", "Precursor", "MW", "Index", "Weight"]])
        c1, c2, c3 = st.columns(3)
        c1.metric("EDTA (g)", f"{r['edta']:.4f}")
        c2.metric("Citric Acid (g)", f"{r['ca']:.4f}")
        c3.metric("Est. NH4OH (mL)", f"{r['nh4oh']:.2f}", help="28% 암모니아수 기준 pH 8 도달 예상 부피")
        if st.button(f"삭제", key=f"ni_del_{i}"): st.session_state.nitrate_recipes.pop(i); st.rerun()

    if st.session_state.nitrate_recipes:
        st.download_button("📥 Nitrate 엑셀 다운로드", generate_excel(st.session_state.nitrate_recipes, NITRATE_DB, "Nitrate"), "Nitrate_Recipes.xlsx", use_container_width=True)
