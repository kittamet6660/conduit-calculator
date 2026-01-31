import streamlit as st
import pandas as pd
import math
import json
import os

# --- ตั้งค่าระบบ ---
ADMIN_PASSWORD = "1234"      # รหัสผ่านสำหรับแก้ไข
DATA_FILE = "iec_data.json"  # ชื่อไฟล์ที่จะบันทึกข้อมูลเก็บไว้

# --- ข้อมูลเริ่มต้น (Default) ---
# สายไฟ IEC 01 (THW)
DEFAULT_WIRES = [
    {"sz": 1.5, "od": 3.2}, {"sz": 2.5, "od": 3.8}, {"sz": 4.0, "od": 4.4},
    {"sz": 6.0, "od": 5.0}, {"sz": 10.0, "od": 6.0}, {"sz": 16.0, "od": 7.2},
    {"sz": 25.0, "od": 8.9}, {"sz": 35.0, "od": 10.1}, {"sz": 50.0, "od": 12.0},
    {"sz": 70.0, "od": 13.8}, {"sz": 95.0, "od": 16.0}, {"sz": 120.0, "od": 17.6},
    {"sz": 150.0, "od": 19.6}, {"sz": 185.0, "od": 22.0}, {"sz": 240.0, "od": 25.0},
    {"sz": 300.0, "od": 28.0}, {"sz": 400.0, "od": 32.5}
]

# ขนาดท่อ (mm) ตามมาตรฐาน
CONDUITS = [
    {"size": "15", "id": 15.8}, {"size": "20", "id": 20.9},
    {"size": "25", "id": 26.6}, {"size": "32", "id": 35.1},
    {"size": "40", "id": 40.9}, {"size": "50", "id": 52.5},
    {"size": "65", "id": 62.7}, {"size": "80", "id": 77.9},
    {"size": "90", "id": 90.1}, {"size": "100", "id": 102.3},
    {"size": "125", "id": 128.2}, {"size": "150", "id": 154.1}
]

# --- ฟังก์ชันจัดการข้อมูล ---
def load_data():
    """โหลดข้อมูลจากไฟล์ JSON ถ้าไม่มีให้ใช้ค่า Default"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return DEFAULT_WIRES
    return DEFAULT_WIRES

def save_data(data):
    """บันทึกข้อมูลลงไฟล์ JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def calc_max_wires(wire_od, conduit_id):
    """คำนวณจำนวนเส้นสูงสุด (Fill 40%)"""
    wire_area = math.pi * ((wire_od / 2) ** 2)
    conduit_area = math.pi * ((conduit_id / 2) ** 2)
    usable_area = conduit_area * 0.40  # 40% Standard Fill
    return math.floor(usable_area / wire_area)

# --- ส่วนหน้าจอหลัก (UI) ---
st.set_page_config(page_title="IEC 01 Calculator", layout="wide")

st.title("⚡ IEC 01 Conduit Calculator")
st.caption("โปรแกรมคำนวณและปรับแต่งมาตรฐานท่อร้อยสาย")

# โหลดข้อมูลเข้า Session State
if 'wires' not in st.session_state:
    st.session_state['wires'] = load_data()
if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# สร้าง Tabs
tab1, tab2 = st.tabs(["🧮 ใช้งานคำนวณ", "🛠️ แก้ไขตาราง (Admin)"])

# ==========================================
# Tab 1: ผู้ใช้งานทั่วไป (User)
# ==========================================
with tab1:
    # สร้างโหมดการคำนวณ (Radio Button)
    calc_mode = st.radio(
        "เลือกโหมดการคำนวณ:",
        ["🅰️ หาขนาดท่อ (ใส่จำนวนเส้น)", "🅱️ หาจำนวนสาย (ใส่ขนาดท่อ)"],
        horizontal=True
    )
    st.write("---")

    df_wires = pd.DataFrame(st.session_state['wires'])

    # --- MODE A: หาขนาดท่อ (เหมือนเดิม) ---
    if calc_mode == "🅰️ หาขนาดท่อ (ใส่จำนวนเส้น)":
        st.subheader("🅰️ คำนวณหาขนาดท่อที่เหมาะสม")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.selectbox("ชนิดสายไฟ", ["IEC 01 (THW-A)"], disabled=True, key="a_type")
        with col2:
            selected_sz = st.selectbox("ขนาดสาย (sq.mm.)", df_wires['sz'], key="a_sz")
        with col3:
            qty = st.number_input("จำนวนเส้น", min_value=1, value=1, key="a_qty")
        
        current_od = df_wires[df_wires['sz'] == selected_sz].iloc[0]['od']
        
        if st.button("🚀 คำนวณขนาดท่อ", type="primary"):
            wire_area = math.pi * ((current_od / 2) ** 2) * qty
            results = []
            best_option = None
            
            for c in CONDUITS:
                conduit_area = math.pi * ((c['id'] / 2) ** 2)
                max_usable = conduit_area * 0.40
                percent_used = (wire_area / conduit_area) * 100
                status = "❌ แน่นเกิน"
                if wire_area <= max_usable:
                    status = "✅ ใช้ได้"
                    if best_option is None: best_option = c
                
                results.append({
                    "ขนาดท่อ (mm)": c['size'],
                    "พื้นที่ใช้งาน (%)": f"{percent_used:.2f}%",
                    "สถานะ": status
                })
                
            if best_option:
                st.success(f"✅ แนะนำท่อขนาด: **{best_option['size']} mm**")
                st.info(f"พื้นที่หน้าตัดรวม: {wire_area:.2f} sq.mm. (คิดเป็น {(wire_area / (math.pi*((best_option['id']/2)**2)) * 100):.2f}% ของท่อ)")
            else:
                st.error("❌ ไม่มีท่อขนาดใดรองรับ")
            
            st.dataframe(pd.DataFrame(results), hide_index=True, use_container_width=True)

    # --- MODE B: หาจำนวนสาย (ฟีเจอร์ใหม่) ---
    else:
        st.subheader("🅱️ คำนวณหาจำนวนสายสูงสุด")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # เลือกขนาดสาย
            selected_sz_b = st.selectbox("เลือกขนาดสาย (sq.mm.)", df_wires['sz'], key="b_sz")
        with col2:
            # เลือกขนาดท่อ
            conduit_options = [c['size'] for c in CONDUITS]
            selected_conduit_size = st.selectbox("เลือกขนาดท่อ (mm)", conduit_options, key="b_conduit")
        
        # ดึงข้อมูล
        wire_data = df_wires[df_wires['sz'] == selected_sz_b].iloc[0]
        conduit_data = next(c for c in CONDUITS if c['size'] == selected_conduit_size)
        
        if st.button("🔢 คำนวณจำนวนเส้น", type="primary"):
            # คำนวณ
            max_wires = calc_max_wires(wire_data['od'], conduit_data['id'])
            
            # แสดงผลตัวใหญ่ๆ
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #e8f5e9; border-radius: 10px; border: 2px solid #4caf50;">
                <h2 style="color: #2e7d32; margin:0;">ใส่ได้สูงสุด: {max_wires} เส้น</h2>
                <p style="margin:0; color: #555;">(สำหรับสาย {selected_sz_b} sq.mm. ในท่อ {selected_conduit_size} mm)</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            st.info(f"💡 หมายเหตุ: คำนวณจากพื้นที่หน้าตัดสาย (รวมฉนวน OD {wire_data['od']} mm) เทียบกับ 40% ของพื้นที่ท่อ")

# ==========================================
# Tab 2: ผู้ดูแลระบบ (Admin & Calibration)
# ==========================================
with tab2:
    st.header("ปรับแต่งค่ามาตรฐาน (Calibration)")
    
    if not st.session_state['is_admin']:
        pwd = st.text_input("รหัสผ่าน Admin", type="password")
        if st.button("เข้าสู่ระบบ"):
            if pwd == ADMIN_PASSWORD:
                st.session_state['is_admin'] = True
                st.rerun()
            else:
                st.error("รหัสผ่านไม่ถูกต้อง")
    else:
        if st.button("ออกจากระบบ", type="secondary"):
            st.session_state['is_admin'] = False
            st.rerun()
            
        st.warning("💡 **วิธีจูนค่า:** แก้ไขตัวเลข **OD** ในตารางฝั่งซ้าย -> ตารางผลลัพธ์ฝั่งขวาจะเปลี่ยนทันที")
        
        col_editor, col_simulation = st.columns([1, 2])
        
        with col_editor:
            st.subheader("1. แก้ไข OD สายไฟ")
            edited_df = st.data_editor(
                df_wires,
                column_config={
                    "sz": st.column_config.NumberColumn("ขนาด (sq.mm)", disabled=True),
                    "od": st.column_config.NumberColumn("OD (mm)", format="%.2f", step=0.1)
                },
                hide_index=True,
                height=600,
                key="editor"
            )
            
            if st.button("💾 บันทึกการเปลี่ยนแปลง"):
                new_data = edited_df.to_dict('records')
                st.session_state['wires'] = new_data
                save_data(new_data)
                st.success("บันทึกเรียบร้อย!")

        with col_simulation:
            st.subheader("2. ผลลัพธ์จำนวนเส้น (จำลอง)")
            st.caption("เทียบกับตารางมาตรฐาน (คำนวณที่ Fill Factor 40%)")
            
            sim_rows = []
            for index, row in edited_df.iterrows():
                sim_row = {"ขนาดสาย (mm²)": row['sz']}
                for c in CONDUITS:
                    max_w = calc_max_wires(row['od'], c['id'])
                    sim_row[c['size']] = max_w if max_w > 0 else "-"
                sim_rows.append(sim_row)
            
            st.dataframe(
                pd.DataFrame(sim_rows),
                hide_index=True,
                use_container_width=True,
                height=600
            )

        st.write("---")
        if st.button("⚠️ รีเซ็ตค่าเริ่มต้น (Factory Reset)"):
            st.session_state['wires'] = DEFAULT_WIRES
            save_data(DEFAULT_WIRES)
            st.rerun()
