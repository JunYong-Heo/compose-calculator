import streamlit as st
import pandas as pd
import io

# 1. 시약 데이터베이스 설정
PRECURSORS_DB = {
    "Ba": {"name": "BaCO3", "mw": 197.34, "n": 1}, "Sr": {"name": "SrCO3", "mw": 147.63, "n": 1},
    "Sc": {"name": "Sc2O3", "mw": 137.91, "n": 2}, "Ta": {"name": "Ta2O5", "mw": 441.893, "n": 2},
    "Co": {"name": "Co3O4", "mw": 240.8,  "n": 3}, "Ni": {"name": "NiO",   "mw": 74.71,  "n": 1},
    "Hf": {"name": "HfO2",  "mw": 210.49, "n": 1}, "Mo": {"name": "MoO2",  "mw": 127.94, "n": 1},
    "Nb": {"name": "Nb2O5", "mw": 265.81, "n": 2}, "Ti": {"name": "TiO2",  "mw": 79.9,   "n": 1},
    "W":  {"name": "WO3",   "mw": 231.84, "n": 1}, "Y":  {"name": "Y2O3",  "mw": 225.81, "n": 2},
    "Zr": {"name": "ZrO2",  "mw": 123.22, "n": 1}
}

NITRATE_DB = {
    "La": {"name": "La(NO3)3·6H2O", "mw": 433.01, "n": 1}, "Sr": {"name": "Sr(NO3)2", "mw": 211.63, "n": 1},
    "Co": {"name": "Co(NO3)2·6H2O", "mw": 291.04, "n": 1}, "Fe": {"name": "Fe(NO3)3·9H2O", "mw": 404.00, "n": 1},
    "K":  {"name": "KNO3", "mw": 101.11, "n": 1}, "Ba": {"name": "Ba(NO3)2", "mw": 261.35, "n": 1},
    "Sc": {"name": "Sc(NO3)3·5H2O", "mw": 321.05, "n": 1}, "Ta": {"name": "Ta(OC2H5)5", "mw": 406.25, "n": 1},
    "Ag": {"name": "AgNO3", "mw": 169.87, "n": 1}, "Ca": {"name": "Ca(NO3)2", "mw": 236.15, "n": 1},
    "Li": {"name": "LiNO3", "mw": 68.95, "n": 1}, "Na": {"name": "NaNO3", "mw": 84.99, "n": 1},
    "Cs": {"name": "CsNO3", "mw": 194.91, "n": 1}, "F": {"name": "BaF2", "mw": 175.32, "n": 2}
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
        workbook, worksheet = writer.book, writer.book.add_worksheet('Batch_Recipe')
        h_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
        a_fmt = workbook.add_format({'bold': True, 'bg_color': '#FCE4D6', 'border': 1, 'align': 'center'})
        t_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#2E75B6'})
        m_fmt = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.00'})
        f_fmt = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.0000'})
        n_fmt = workbook.add_format({'bold': True, 'font_color': 'red'})

        worksheet.write(0, 0, "1&2. Precursor Info", t_fmt)
        for c, h in enumerate(["Precursor", "MW", "Eff_MW"]): worksheet.write(1, c, h, h_fmt)
        info_data = {}
        for r_item in recipes:
            for _, row in r_item['data'].iterrows():
                p_info = p_db.get(row['Raw_Element'], p_db.get(row['Element']))
                info_data[row['Precursor']] = {"mw": row['MW'], "eff": row['MW']/p_info['n']}
        for r, (p_name, v) in enumerate(info_data.items(), start=2):
            worksheet.write(r, 0, p_name, m_fmt); worksheet.write(r, 1, v['mw'], m_fmt); worksheet.write(r, 2, v['eff'], m_fmt)

        sc = 4
        worksheet.write(0, sc, f"3. {mode} Metal Precursors (g)", t_fmt)
        ws, adds, idxs = [], [], []
        for r_item in recipes:
            w_row = {"Sample Name": r_item['name'], "Total(g)": r_item['total']}
            i_row = {"Sample Name": r_item['name']}
            for _, row in r_item['data'].iterrows():
                w_row[row['Precursor']] = row['Weight']
                i_row[row['Element']] = row['Index']
            ws.append(w_row); idxs.append(i_row)
            if mode == "Nitrate":
                adds.append({"Sample": r_item['name'], "EDTA(g)": r_item['edta'], "CA(g)": r_item['ca'], "NH4OH(mL)": r_item['nh4oh'], "pH": 8.0})

        df_w = pd.DataFrame(ws)
        for c, col in enumerate(df_w.columns):
            worksheet.write(1, sc+c, col, h_fmt)
            for r, val in enumerate(df_w[col], start=2):
                fmt = f_fmt if c > 0 else m_fmt
                worksheet.write(r, sc+c, val if pd.notna(val) else "-", fmt)

        cr = len(df_w) + 4
        if mode == "Nitrate":
            worksheet.write(cr, sc, "3-2. Additives & Notes", t_fmt)
            df_a = pd.DataFrame(adds)
            for c, col in enumerate(df_a.columns):
                worksheet.write(cr+1, sc+c, col, a_fmt)
                for r, val in enumerate(df_a[col], start=cr+2):
                    worksheet.write(r, sc+c, val, f_fmt if c > 0 else m_fmt)
            cr += len(df_a) + 2
            worksheet.write(cr, sc, "※ NH4OH는 pH 미터를 사용하여 천천히 투입하십시오.", n_fmt)
            cr += 2

        worksheet.write(cr, sc, "4. Composition Indices", t_fmt)
        df_i = pd.DataFrame(idxs)
        for c, col in enumerate(df_i.columns):
            worksheet.write(cr+1, sc+c, col, h_fmt)
            for r, val in enumerate(df_i[col], start=cr+2):
                fmt = f_fmt if c > 0 else m_fmt
                worksheet.write(r, sc+c, val if pd.notna(val) else "-", fmt)

        worksheet.set_column(0, 0, 25); worksheet.set_column(4, 50, 18)
    return output.getvalue()

tab1, tab2 = st.tabs(["🔥 Oxide SSR Method", "💧 Nitrate Sol-Gel Method"])

with tab1:
    with st.expander("➕ Oxide 레시피 추가", expanded=True):
        c1, c2 = st.columns([2, 1])
        name_in, mass = c1.text_input("샘플 명", key="on"), c2.number_input("목표 질량(g)", value=3.0, key="om")
        sel = st.multiselect("원소", sorted(list(PRECURSORS_DB.keys())), key="os")
        if sel:
            cols = st.columns(len(sel))
            inds = {e: cols[i].number_input(f"{e}", value=1.0, format="%.4f", key=f"ov{e}") for i, e in enumerate(sel)}
            if sum(inds.values()) % 1 != 0: st.warning(f"⚠️ 조성 합계: {sum(inds.values()):g}")
            if st.button("추가", key="ob"):
                fw = sum(inds[e]*(PRECURSORS_DB[e]['mw']/PRECURSORS_DB[e]['n']) for e in sel)
                data = [{"Element": e, "Raw_Element": e, "Precursor": PRECURSORS_DB[e]['name'], "MW": PRECURSORS_DB[e]['mw'], "Index": inds[e], "Weight": (inds[e]*(PRECURSORS_DB[e]['mw']/PRECURSORS_DB[e]['n'])/fw)*mass} for e in sel]
                st.session_state.oxide_recipes.append({"name": name_in if name_in.strip() else generate_formula(inds), "data": pd.DataFrame(data), "total": mass})
                st.rerun()
    for i, r in enumerate(st.session_state.oxide_recipes):
        st.subheader(f"{i+1}. {r['name']}"); st.table(r['data'][["Element", "Precursor", "MW", "Index", "Weight"]])
        if st.button("삭제", key=f"od{i}"): st.session_state.oxide_recipes.pop(i); st.rerun()
    if st.session_state.oxide_recipes: st.download_button("📥 엑셀 다운로드", generate_excel_final(st.session_state.oxide_recipes, PRECURSORS_DB), "Oxide_Recipes.xlsx")

with tab2:
    with st.expander("➕ Nitrate 레시피 추가", expanded=True):
        c1, c2 = st.columns([2, 1])
        name_in, mass = c1.text_input("샘플 명", key="nn"), c2.number_input("목표 Oxide 환산 질량(g)", value=5.0, key="nm")
        sel = st.multiselect("원소", sorted(list(NITRATE_DB.keys())), key="ns")
        if sel:
            cols = st.columns(len(sel))
            inds = {e: cols[i].number_input(f"{e}", value=1.0 if i==0 else 0.5, format="%.4f", key=f"nv{e}") for i, e in enumerate(sel)}
            if sum(inds.values()) % 1 != 0: st.warning(f"⚠️ 조성 합계: {sum(inds.values()):g}")
            
            if st.button("추가", key="nb"):
                f_idx = inds.get("F", 0.0)
                ba_from_f = f_idx / 2.0
                ba_target = inds.get("Ba", 0.0)
                ba_extra = ba_target - ba_from_f
                
                if ba_extra < -0.0001:
                    st.error(f"❌ BaF2 유래 Ba({ba_from_f:g})가 목표({ba_target:g})를 초과합니다.")
                else:
                    fw = sum(inds[e]*(NITRATE_DB[e]['mw']/NITRATE_DB[e]['n']) for e in sel if e not in ["Ba", "F"])
                    fw += (ba_from_f * 175.32/2) + (max(0, ba_extra) * 261.35)
                    molar_scale = mass / fw
                    data = []
                    for e in sel:
                        if e == "F":
                            data.append({"Element": "F", "Raw_Element": "F", "Precursor": "BaF2", "MW": 175.32, "Index": inds[e], "Weight": (inds[e]*87.66/fw)*mass})
                        elif e == "Ba":
                            if ba_extra > 0:
                                data.append({"Element": "Ba (Extra)", "Raw_Element": "Ba", "Precursor": "Ba(NO3)2", "MW": 261.35, "Index": ba_extra, "Weight": (ba_extra*261.35/fw)*mass})
                        else:
                            db = NITRATE_DB[e]
                            data.append({"Element": e, "Raw_Element": e, "Precursor": db['name'], "MW": db['mw'], "Index": inds[e], "Weight": (inds[e]*(db['mw']/db['n'])/fw)*mass})
                    
                    tm = molar_scale * sum(inds.values())
                    st.session_state.nitrate_recipes.append({
                        "name": name_in if name_in.strip() else generate_formula(inds), "data": pd.DataFrame(data), "total": mass,
                        "edta": tm * 292.24, "ca": tm * 210.14 * 2.0, "nh4oh": (tm * 9 / 15.0) * 1000.0
                    })
                    st.rerun()
    for i, r in enumerate(st.session_state.nitrate_recipes):
        st.subheader(f"{i+1}. {r['name']}"); st.table(r['data'][["Element", "Precursor", "MW", "Index", "Weight"]])
        c1, c2, c3 = st.columns(3)
        c1.metric("EDTA (g)", f"{r['edta']:.4f}"); c2.metric("Citric Acid (g)", f"{r['ca']:.4f}"); c3.metric("NH4OH (mL)", f"{r['nh4oh']:.2f}")
        st.info("💡 **안내:** 암모니아는 pH 미터를 사용하여 pH 8.0이 될 때까지 소량씩 투입하십시오.")
        if st.button("삭제", key=f"nd{i}"): st.session_state.nitrate_recipes.pop(i); st.rerun()
    if st.session_state.nitrate_recipes: st.download_button("📥 엑셀 다운로드", generate_excel_final(st.session_state.nitrate_recipes, NITRATE_DB, "Nitrate"), "Nitrate_Recipes.xlsx")
