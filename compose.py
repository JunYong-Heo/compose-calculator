import streamlit as st
import pandas as pd
import io

# 1. 시약 데이터베이스 설정 (기본값)
PRECURSORS_DB = {
    "Ba": {"name": "BaCO3", "mw": 197.34, "n": 1}, "Sr": {"name": "SrCO3", "mw": 147.63, "n": 1},
    "Sc": {"name": "Sc2O3", "mw": 137.91, "n": 2}, "Ta": {"name": "Ta2O5", "mw": 441.893, "n": 2},
    "Co": {"name": "Co3O4", "mw": 240.8,  "n": 3}, "Ni": {"name": "NiO",   "mw": 74.71,  "n": 1},
    "Pr": {"name": "Pr6O11", "mw": 1021.44, "n": 6}, "Hf": {"name": "HfO2",  "mw": 210.49, "n": 1}, 
    "Mo": {"name": "MoO2",  "mw": 127.94, "n": 1}, "Nb": {"name": "Nb2O5", "mw": 265.81, "n": 2}, 
    "Ti": {"name": "TiO2",  "mw": 79.9,   "n": 1}, "W":  {"name": "WO3",   "mw": 231.84, "n": 1}, 
    "Y":  {"name": "Y2O3",  "mw": 225.81, "n": 2}, "Zr": {"name": "ZrO2",  "mw": 123.22, "n": 1}
}

NITRATE_DB = {
    "La": {"name": "La(NO3)3·6H2O", "mw": 433.01, "n": 1}, "Sr": {"name": "Sr(NO3)2", "mw": 211.63, "n": 1},
    "Co": {"name": "Co(NO3)2·6H2O", "mw": 291.04, "n": 1}, "Fe": {"name": "Fe(NO3)3·9H2O", "mw": 404.00, "n": 1},
    "Pr": {"name": "Pr(NO3)3·6H2O", "mw": 435.01, "n": 1}, "Nd": {"name": "Nd(NO3)3·6H2O", "mw": 438.35, "n": 1},
    "Mo": {"name": "(NH4)6Mo7O24·4H2O", "mw": 1235.86, "n": 7}, "K":  {"name": "KNO3", "mw": 101.11, "n": 1}, 
    "Ba": {"name": "Ba(NO3)2", "mw": 261.35, "n": 1}, "Sc": {"name": "Sc(NO3)3·5H2O", "mw": 321.05, "n": 1}, 
    "Ta": {"name": "Ta(OC2H5)5", "mw": 406.25, "n": 1}, "Ag": {"name": "AgNO3", "mw": 169.87, "n": 1}, 
    "Ca": {"name": "Ca(NO3)2", "mw": 236.15, "n": 1}, "Li": {"name": "LiNO3", "mw": 68.95,  "n": 1}, 
    "Na": {"name": "NaNO3", "mw": 84.99,  "n": 1}, "Cs": {"name": "CsNO3", "mw": 194.91, "n": 1}, 
    "F": {"name": "BaF2", "mw": 175.32, "n": 2}
}

st.set_page_config(page_title="AECSL Smart Calc", layout="wide")
st.title("🔬 AECSL Advanced Batch Manager")

if 'oxide_recipes' not in st.session_state: st.session_state.oxide_recipes = []
if 'nitrate_recipes' not in st.session_state: st.session_state.nitrate_recipes = []

# --- 유틸리티 함수 ---
def generate_formula(inputs):
    formula = ""
    for el, val in sorted(inputs.items()):
        if val > 0:
            idx_str = "" if val == 1.0 else f"{val:g}"
            formula += f"{el}{idx_str}"
    return formula

def generate_excel_final(recipes, mode="Oxide"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook, worksheet = writer.book, writer.book.add_worksheet('Batch_Recipe')
        h_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
        a_fmt = workbook.add_format({'bold': True, 'bg_color': '#FCE4D6', 'border': 1, 'align': 'center'})
        t_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#2E75B6'})
        m_fmt = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.00'})
        f_fmt = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.0000'})
        n_fmt = workbook.add_format({'bold': True, 'font_color': 'red'})

        # Precursor Info
        worksheet.write(0, 0, "1&2. Precursor Info", t_fmt)
        for c, h in enumerate(["Precursor", "MW", "n"]): worksheet.write(1, c, h, h_fmt)
        info_dict = {}
        for r in recipes:
            for _, row in r['data'].iterrows():
                info_dict[row['Precursor']] = {"mw": row['MW'], "n": row['n']}
        for r, (name, v) in enumerate(info_dict.items(), start=2):
            worksheet.write(r, 0, name, m_fmt); worksheet.write(r, 1, v['mw'], m_fmt); worksheet.write(r, 2, v['n'], m_fmt)

        sc = 4
        worksheet.write(0, sc, f"3. {mode} Metal Precursors (g)", t_fmt)
        ws, adds, idxs = [], [], []
        for r in recipes:
            w_row = {"Sample Name": r['name'], "Total(g)": r['total']}
            i_row = {"Sample Name": r['name']}
            for _, row in r['data'].iterrows():
                w_row[row['Precursor']] = row['Weight']
                i_row[row['Element']] = row['Index']
            ws.append(w_row); idxs.append(i_row)
            if mode == "Nitrate":
                adds.append({"Sample": r['name'], "EDTA(g)": r['edta'], "CA(g)": r['ca'], "NH4OH(mL)": r['nh4oh'], "pH": 8.0})

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

# --- Tab 1 Oxide ---
with tab1:
    with st.expander("➕ Oxide 레시피 추가", expanded=True):
        c1, c2 = st.columns([2, 1])
        name_in, mass = c1.text_input("샘플 명", key="on"), c2.number_input("목표 질량(g)", value=3.0, key="om")
        sel = st.multiselect("원소 선택", sorted(list(PRECURSORS_DB.keys())), key="os")
        
        if sel:
            st.markdown("#### 📏 시약별 분자량(MW) 확인 및 수정")
            mw_cols = st.columns(len(sel))
            current_mw = {}
            for i, e in enumerate(sel):
                current_mw[e] = mw_cols[i].number_input(f"{e} MW", value=float(PRECURSORS_DB[e]['mw']), format="%.3f", key=f"ox_mw_{e}")
            
            st.markdown("#### 🔢 조성 계수(Index) 입력")
            idx_cols = st.columns(len(sel))
            inds = {e: idx_cols[i].number_input(f"{e} Index", value=1.0, format="%.4f", key=f"ov{e}") for i, e in enumerate(sel)}
            
            if sum(inds.values()) % 1 != 0: st.warning(f"⚠️ 조성 합계: {sum(inds.values()):g}")
            
            if st.button("추가", key="ob"):
                fw = sum(inds[e]*(current_mw[e]/PRECURSORS_DB[e]['n']) for e in sel)
                data = []
                for e in sel:
                    db = PRECURSORS_DB[e]
                    w = (inds[e]*(current_mw[e]/db['n'])/fw)*mass
                    data.append({"Element": e, "Raw_Element": e, "Precursor": db['name'], "MW": current_mw[e], "n": db['n'], "Index": inds[e], "Weight": w})
                st.session_state.oxide_recipes.append({"name": name_in if name_in.strip() else generate_formula(inds), "data": pd.DataFrame(data), "total": mass})
                st.rerun()

    for i, r in enumerate(st.session_state.oxide_recipes):
        st.subheader(f"{i+1}. {r['name']}"); st.table(r['data'][["Element", "Precursor", "MW", "Index", "Weight"]])
        if st.button("삭제", key=f"od{i}"): st.session_state.oxide_recipes.pop(i); st.rerun()
    if st.session_state.oxide_recipes: st.download_button("📥 Oxide 엑셀 다운로드", generate_excel_final(st.session_state.oxide_recipes, "Oxide"), "Oxide_Recipes.xlsx")

# --- Tab 2 Nitrate ---
with tab2:
    with st.expander("➕ Nitrate 레시피 추가", expanded=True):
        c1, c2 = st.columns([2, 1])
        name_in, mass = c1.text_input("샘플 명", key="nn"), c2.number_input("목표 Oxide 환산 질량(g)", value=5.0, key="nm")
        sel = st.multiselect("원소 선택", sorted(list(NITRATE_DB.keys())), key="ns")
        
        if sel:
            st.markdown("#### 📏 시약별 분자량(MW) 확인 및 수정")
            mw_cols = st.columns(len(sel))
            current_mw_ni = {}
            for i, e in enumerate(sel):
                current_mw_ni[e] = mw_cols[i].number_input(f"{e} MW", value=float(NITRATE_DB[e]['mw']), format="%.3f", key=f"ni_mw_{e}")

            st.markdown("#### 🔢 조성 계수(Index) 입력")
            idx_cols = st.columns(len(sel))
            inds = {e: idx_cols[i].number_input(f"{e} Index", value=1.0 if i==0 else 0.5, format="%.4f", key=f"nv{e}") for i, e in enumerate(sel)}
            
            if sum(inds.values()) % 1 != 0: st.warning(f"⚠️ 조성 합계: {sum(inds.values()):g}")
            
            if st.button("추가", key="nb"):
                f_idx = inds.get("F", 0.0)
                ba_from_f = f_idx / 2.0
                ba_target = inds.get("Ba", 0.0)
                ba_extra = ba_target - ba_from_f
                
                if ba_extra < -0.0001:
                    st.error(f"❌ BaF2 유래 Ba({ba_from_f:g})가 목표({ba_target:g})를 초과합니다.")
                else:
                    # 유효 FW 계산 (수정된 MW 반영)
                    fw = sum(inds[e]*(current_mw_ni[e]/NITRATE_DB[e]['n']) for e in sel if e not in ["Ba", "F"])
                    # BaF2는 F기준 n=2, Ba(NO3)2는 Ba기준 n=1
                    fw += (ba_from_f * current_mw_ni.get("F", 175.32)/2) + (max(0, ba_extra) * current_mw_ni.get("Ba", 261.35))
                    
                    molar_scale = mass / fw
                    data = []
                    for e in sel:
                        mw_val = current_mw_ni[e]
                        if e == "F":
                            data.append({"Element": "F", "Raw_Element": "F", "Precursor": "BaF2", "MW": mw_val, "n": 2, "Index": inds[e], "Weight": (inds[e]*(mw_val/2)/fw)*mass})
                        elif e == "Ba":
                            if ba_extra > 0:
                                data.append({"Element": "Ba (Extra)", "Raw_Element": "Ba", "Precursor": "Ba(NO3)2", "MW": mw_val, "n": 1, "Index": ba_extra, "Weight": (ba_extra*mw_val/fw)*mass})
                        else:
                            db = NITRATE_DB[e]
                            data.append({"Element": e, "Raw_Element": e, "Precursor": db['name'], "MW": mw_val, "n": db['n'], "Index": inds[e], "Weight": (inds[e]*(mw_val/db['n'])/fw)*mass})
                    
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
        st.info("💡 **안내:** 암모니아는 이론치입니다. pH 미터로 pH 8.0을 확인하며 천천히 투입하십시오.")
        if st.button("삭제", key=f"nd{i}"): st.session_state.nitrate_recipes.pop(i); st.rerun()
    if st.session_state.nitrate_recipes: st.download_button("📥 Nitrate 엑셀 다운로드", generate_excel_final(st.session_state.nitrate_recipes, "Nitrate"), "Nitrate_Recipes.xlsx")
