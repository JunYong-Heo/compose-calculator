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

st.set_page_config(page_title="AECSL Calc & Export", layout="wide")
st.title("🔬 PCFC/PCEC Stoichiometry & Export")

with st.sidebar:
    st.header("⚙️ 기본 설정")
    target_mass = st.number_input("목표 합성량 (Total g)", value=5.0, step=0.1)

st.write("### 1. 합성할 원소 선택")
selected_elements = st.multiselect(
    "사용할 원소를 선택하세요",
    options=list(PRECURSORS_DB.keys()),
    default=["Ba"]
)

if selected_elements:
    st.write("### 2. 조성 계수(Index) 입력")
    inputs = {}
    cols = st.columns(min(len(selected_elements), 4))
    
    for i, el in enumerate(selected_elements):
        with cols[i % 4]:
            dv = 1.0 if el == "Ba" else 0.0
            inputs[el] = st.number_input(f"{el} Index", value=dv, format="%.4f", key=f"idx_{el}")

    total_fw = 0
    base_data = []
    for el in selected_elements:
        coeff = inputs[el]
        if coeff > 0:
            db = PRECURSORS_DB[el]
            eff_mw = db["mw"] / db["n"]
            total_fw += coeff * eff_mw
            base_data.append({"Element": el, "Precursor": db["name"], "Eff_MW": eff_mw, "Index": coeff})

    if total_fw > 0:
        for item in base_data:
            item["Weight (g)"] = (item["Index"] * item["Eff_MW"] / total_fw) * target_mass
        
        df_init = pd.DataFrame(base_data)
        st.divider()
        st.subheader(f"📊 초기 레시피 (Target: {target_mass}g)")
        st.table(df_init[["Element", "Precursor", "Index", "Weight (g)"]])

        # --- 엑셀 파일 생성 ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_init[["Element", "Precursor", "Index", "Weight (g)"]].to_excel(writer, index=False, sheet_name='Recipe')
            workbook = writer.book
            worksheet = writer.sheets['Recipe']
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
            for col_num, value in enumerate(df_init[["Element", "Precursor", "Index", "Weight (g)"]].columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        st.download_button(
            label="📥 엑셀 파일로 다운로드",
            data=output.getvalue(),
            file_name=f"AECSL_Recipe_{target_mass}g.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # --- 3단계: 오차 수정 ---
        st.divider()
        st.subheader("⚠️ 3. 칭량 오차 수정 (Scale-up)")
        error_p = st.selectbox("실수한 시료 선택", df_init['Precursor'].tolist())
        orig_w = df_init.loc[df_init['Precursor'] == error_p, 'Weight (g)'].values[0]
        actual_w = st.number_input("실제로 넣은 무게 (g)", value=float(orig_w), format="%.5f", key="fix_val")

        if actual_w > orig_w:
            ratio = actual_w / orig_w
            st.warning(f"🚨 {ratio:.4f}배 증량 모드")
            
            adj_list = []
            for _, row in df_init.iterrows():
                new_total = row['Weight (g)'] * ratio
                is_culprit = (row['Precursor'] == error_p)
                adj_list.append({
                    "Precursor": row['Precursor'],
                    "Original (g)": row['Weight (g)'],
                    "New Total (g)": round(new_total, 5),
                    "Add More (추가량)": 0.0 if is_culprit else round(new_total - row['Weight (g)'], 5)
                })
            
            df_adj = pd.DataFrame(adj_list)
            st.dataframe(df_adj, use_container_width=True)

            output_adj = io.BytesIO()
            with pd.ExcelWriter(output_adj, engine='xlsxwriter') as writer:
                df_adj.to_excel(writer, index=False, sheet_name='Adjusted_Recipe')
            
            st.download_button(
                label="📥 수정된 레시피 다운로드",
                data=output_adj.getvalue(),
                file_name=f"AECSL_Adjusted_{target_mass * ratio:.1f}g.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
