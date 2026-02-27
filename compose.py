import streamlit as st
import pandas as pd
import io

# [데이터베이스 설정 - 기존 유지]
PRECURSORS_DB = {
    "Ba": {"name": "BaCO3", "mw": 197.34, "n": 1}, "Co": {"name": "Co3O4", "mw": 240.8,  "n": 3},
    "Hf": {"name": "HfO2",  "mw": 210.49, "n": 1}, "Mo": {"name": "MoO2",  "mw": 127.94, "n": 1},
    "Nb": {"name": "Nb2O5", "mw": 265.81, "n": 2}, "Sc": {"name": "Sc2O3", "mw": 137.91, "n": 2},
    "Ta": {"name": "Ta2O5", "mw": 441.89, "n": 2}, "Ti": {"name": "TiO2",  "mw": 79.9,   "n": 1},
    "W":  {"name": "WO3",   "mw": 231.84, "n": 1}, "Y":  {"name": "Y2O3",  "mw": 225.81, "n": 2},
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

if 'oxide_recipes' not in st.session_state: st.session_state.oxide_recipes = []
if 'nitrate_recipes' not in st.session_state: st.session_state.nitrate_recipes = []

def generate_formula(inputs):
    formula = ""
    for el, val in inputs.items():
        if val > 0:
            idx_str = "" if val == 1.0 else f"{val:g}"
            formula += f"{el}{idx_str}"
    return formula

def generate_excel_final(recipes, p_db, mode="Oxide"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Batch_Recipe')
        
        head_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
        add_head_fmt = workbook.add_format({'bold': True, 'bg_color': '#FCE4D6', 'border': 1, 'align': 'center'})
        title_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#2E75B6'})
        mw_fmt = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.00'})
        four_digit_fmt = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.0000'})
        note_fmt = workbook.add_format({'bold': True, 'font_color': 'red'})

        # 1&2. Precursor Info
        worksheet.write(0, 0, "1&2. Precursor Info", title_fmt)
        for c, h in enumerate(["Precursor", "MW", "Eff_MW"]): worksheet.write(1, c, h, head_fmt)
        info_data = {}
        for r_item in recipes:
            for _, row in r_item['data'].iterrows():
                info_data[row['Precursor']] = {"mw": row['MW'], "eff": row['MW']/p_db[row['Element']]['n']}
        for r, (p_name, v) in enumerate(info_data.items(), start=2):
            worksheet.write(r, 0, p_name, mw_fmt); worksheet.write(r, 1, v['mw'], mw_fmt); worksheet.write(r, 2, v['eff'], mw_fmt)

        # 3. Weights
        start_col = 4
        worksheet.write(0, start_col, f"3. {mode} Metal Precursors (g)", title_fmt)
        weights, adds, idxs = [], [], []
        for r_item in recipes:
            w_row = {"Sample Name": r_item['name'], "Total(g)": r_item['total']}
            i_row = {"Sample Name": r_item['name']}
            for _, row in r_item['data'].iterrows():
                w_row[row['Precursor']] = row['Weight']
                i_row[row['Element']] = row['Index']
            weights.append(w_row); idxs.append(i_row)
            if mode == "Nitrate":
                adds.append({"Sample": r_item['name'], "EDTA(g)": r_item['edta'], "CA(g)": r_item['ca'], "NH4OH(mL)": r_item['nh4oh'], "pH": 8.0})

        df_w = pd.DataFrame(weights)
        for c, col in enumerate(df_w.columns):
            worksheet.write(1, start_col + c, col, head_fmt)
            for r, val in enumerate(df_w[col], start=2):
                fmt = four_digit_fmt if c > 0 else mw_fmt
                worksheet.write(r, start_col + c, val if pd.notna(val) else "-", fmt)

        curr_row = len(df_w) + 4
        if mode == "Nitrate":
            worksheet.write(curr_row, start_col, "3-2. Additives & Notes", title_fmt)
            df_a = pd.DataFrame(adds)
            for c, col in enumerate(df_a.columns):
                worksheet.write(curr_row+1, start_col+c, col, add_head_fmt)
                for r, val in enumerate(df_a[col], start=curr_row+2):
                    worksheet.write(r, start_col+c, val, four_digit_fmt if c > 0 else mw_fmt)
            curr_row += len(df_a) + 2
            worksheet.write(curr_row, start_col, "※ NH4OH 주의사항: 이론적 수치이므로 pH 미터를 사용하여 서서히 투입하십시오.", note_fmt)
            curr_row += 2

        worksheet.write(curr_row, start_col, "4. Composition Indices", title_fmt)
        df_i = pd.DataFrame(idxs)
        for c, col in enumerate(df_i.columns):
            worksheet.write(curr_row+1, start_col+c, col, head_fmt)
            for r, val in enumerate(df_i[col], start=curr_row+2):
                fmt = four_digit_fmt if c > 0 else mw_fmt
                worksheet.write(r, start_col+c, val if pd.notna(val) else "-", fmt)

        worksheet.set_column(0, 0, 25); worksheet.set_column(4, 25, 18)
    return output.getvalue()

tab1, tab2 = st.tabs(["🔥 Oxide SSR Method", "💧 Nitrate Sol-Gel Method"])

# --- Tab 1 Oxide ---
with tab1:
    with st.expander("➕ Oxide 레시피 추가", expanded=True):
        c1, c2 = st.columns([2, 1])
        name_in = c1.text_input("샘플 명", key="on")
        mass = c2.number_input("목표 질량(g)", value=3.0, key="om")
        sel = st.multiselect("원소", list(PRECURSORS_DB.keys()), key="os")
        if sel:
            cols = st.columns(len(sel))
            inds = {e: cols[i].number_input(f"{e}", value=1.0, format="%.4f", key=f"ov{e}") for i, e in enumerate(sel)}
            total_idx = sum(inds.values())
            if total_idx % 1 != 0: st.warning(f"⚠️ 조성 합계가 정수가 아닙니다: {total_idx:g}")
            if st.button("추가", key="ob"):
                final_name = name_in if name_in.strip() else generate_formula(inds)
                fw = sum(inds[e]*(PRECURSORS_DB[e]['mw']/PRECURSORS_DB[e]['n']) for e in sel)
                data = [{"Element": e, "Precursor": PRECURSORS_DB[e]['name'], "MW": PRECURSORS_DB[e]['mw'], "Index": inds[e], "Weight": (inds[e]*(PRECURSORS_DB[e]['mw']/PRECURSORS_DB[e]['n'])/fw)*mass} for e in sel]
                st.session_state.oxide_recipes.append({"name": final_name, "data": pd.DataFrame(data), "total": mass})
                st.rerun()
    for i, r in enumerate(st.session_state.oxide_recipes):
        st.subheader(f"{i+1}. {r['name']}"); st.table(r['data'][["Element", "Precursor", "MW", "Index", "Weight"]])
        if st.button("삭제", key=f"od{i}"): st.session_state.oxide_recipes.pop(i); st.rerun()
    if st.session_state.oxide_recipes: st.download_button("📥 Oxide 엑셀 다운로드", generate_excel_final(st.session_state.oxide_recipes, PRECURSORS_DB), "Oxide_Recipes.xlsx")

# --- Tab 2 Nitrate ---
with tab2:
    with st.expander("➕ Nitrate 레시피 추가", expanded=True):
        c1, c2 = st.columns([2, 1])
        name_in = c1.text_input("샘플 명", key="nn")
        mass = c2.number_input("목표 oxide 질량(g)", value=5.0, key="nm")
        sel = st.multiselect("원소", list(NITRATE_DB.keys()), key="ns")
        if sel:
            cols = st.columns(len(sel))
            inds = {e: cols[i].number_input(f"{e}", value=1.0 if i==0 else 0.5, format="%.4f", key=f"nv{e}") for i, e in enumerate(sel)}
            total_idx = sum(inds.values())
            if total_idx % 1 != 0: st.warning(f"⚠️ 조성 합계가 정수가 아닙니다: {total_idx:g}")
            if st.button("추가", key="nb"):
                final_name = name_in if name_in.strip() else generate_formula(inds)
                fw = sum(inds[e]*(NITRATE_DB[e]['mw']/NITRATE_DB[e]['n']) for e in sel)
                total_moles = (mass / fw) * sum(inds.values())
                edta, ca = total_moles * 292.24, total_moles * 210.14 * 2.0
                nh4 = ((total_moles * 3) + (total_moles * 2 * 3)) / 15.0 * 1000.0
                data = [{"Element": e, "Precursor": NITRATE_DB[e]['name'], "MW": NITRATE_DB[e]['mw'], "Index": inds[e], "Weight": (inds[e]*(NITRATE_DB[e]['mw']/NITRATE_DB[e]['n'])/fw)*mass} for e in sel]
                st.session_state.nitrate_recipes.append({"name": final_name, "data": pd.DataFrame(data), "total": mass, "edta": edta, "ca": ca, "nh4oh": nh4})
                st.rerun()
    for i, r in enumerate(st.session_state.nitrate_recipes):
        st.subheader(f"{i+1}. {r['name']}")
        st.table(r['data'][["Element", "Precursor", "MW", "Index", "Weight"]])
        c1, c2, c3 = st.columns(3)
        c1.metric("EDTA (g)", f"{r['edta']:.4f}")
        c2.metric("Citric Acid (g)", f"{r['ca']:.4f}")
        c3.metric("NH4OH (mL)", f"{r['nh4oh']:.2f}")
        st.info("💡 **암모니아 투입 가이드:** 위 부피는 28~30% 암모니아수 기준의 이론치입니다. 반드시 **pH 미터**를 사용하여 pH 8.0이 될 때까지 소량씩 천천히 첨가하십시오.")
        if st.button("삭제", key=f"nd{i}"): st.session_state.nitrate_recipes.pop(i); st.rerun()
    if st.session_state.nitrate_recipes: st.download_button("📥 Nitrate 엑셀 다운로드", generate_excel_final(st.session_state.nitrate_recipes, NITRATE_DB, "Nitrate"), "Nitrate_Recipes.xlsx")
