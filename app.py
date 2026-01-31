import streamlit as st
import pandas as pd
import math
import json
import os

# --- Config ---
ADMIN_PASSWORD = "1234"
DATA_FILE = "iec01_data.json"

# --- Default Data (ตามมาตรฐาน มอก./IEC 01) ---
DEFAULT_WIRES = [
    {"sz": 1.5, "od": 3.2}, {"sz": 2.5, "od": 3.8}, {"sz": 4.0, "od": 4.4},
    {"sz": 6.0, "od": 5.0}, {"sz": 10.0, "od": 6.0}, {"sz": 16.0, "od": 7.2},
    {"sz": 25.0, "od": 8.9}, {"sz": 35.0, "od": 10.1}, {"sz": 50.0, "od": 12.0},
    {"sz": 70.0, "od": 13.8}, {"sz": 95.0, "od": 16.0}, {"sz": 120.0, "od": 17.6},
    {"sz": 150.0, "od": 19.6}, {"sz": 185.0, "od": 22.0}, {"sz": 240.0, "od": 25.0},
    {"sz": 300.0, "od": 28.0}, {"sz": 400.0, "od": 32.5}
]

# ท่อตามขนาด มม. (Fix ไว้ตามตารางมาตรฐาน ไม่ต้องแก้บ่อย)
CONDUITS = [
    {"size": "15", "id": 15.8}, {"size": "20", "id": 20.9},
    {"size": "25", "id": 26.6}, {"size": "32", "id": 35.1},
    {"size": "40", "id": 40.9}, {"size": "50", "id": 52.5},
    {"size": "65", "id": 62.7}, {"size": "80", "id": 77.9},
    {"size": "90", "id": 90.1}, {"size": "100", "id": 102.3},
    {"size": "125", "id": 128.2}, {"size": "150", "id": 154.1}
]

# --- Functions ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_WIRES

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def calculate_max_wires(wire_od, conduit_id, fill_factor=0.40):
    wire_area = math.pi * ((wire_od / 2) ** 2)
    conduit_area = math.pi * ((conduit_id / 2) ** 2)
    max_area = conduit_area * fill_factor
    return math.floor(max_area / wire_area)

# --- App UI ---
st.set_page_config(page_title="IEC 01 Calculator", layout="wide")

st.title("⚡ IEC 01 Conduit Calculator")
st.markdown("โปรแกรมคำนวณขนาดท่อร้อยสายตามมาตรฐาน มอก.")

# Initialize Session State
if 'wires' not in st.session_state:
    st.session_state['wires'] = load_data()
if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# Tabs
tab1, tab2 = st.tabs(["🧮 ใช้งานคำนวณ", "🛠️ แก้ไขตาราง (Admin)"])

# === Tab 1: User Calculator ===
with tab1:
    st.markdown("### คำนวณหาขนาดท่อ")
    
    col1, col2, col3 = st.columns(3)
    
    # เตรียมข้อมูลสำหรับ Dropdown
    df_wires = pd.DataFrame(st.session_state['wires'])
    
    with col1:
        st.selectbox("ชนิดสายไฟ", ["IEC 01 (THW-A)"], disabled=True)
    with col2:
        selected_sz = st.selectbox("ขนาดสาย (sq.mm.)", df_wires['sz'])
    with col3:
        qty = st.number_input("จำนวนเส้น", min_value=1, value=1)
    
    # ดึงค่า OD ที่เลือก
    selected_wire = df_wires[df_wires['sz'] == selected_sz].iloc[0]
    current_od = selected_wire['od']
    
    if st.button("🔍 คำนวณขนาดท่อ", type="primary"):
        # Logic คำนวณ
        wire_area = math.pi * ((current_od / 2) ** 2) * qty
        
        results = []
        recommended = None
        
        for c in CONDUITS:
            conduit_area = math.pi * ((c['id'] / 2) ** 2)
            max_usable = conduit_area * 0.40 # 40% Fill
            percent_used = (wire_area / conduit_area) * 100
            
            status = "❌ แน่นเกินไป"
            if wire_area <= max_usable:
                status = "✅ ใช้ได้"
                if recommended is None:
                    recommended = c
            
            results.append({
                "ขนาดท่อ (mm)": c['size'],
                "พื้นที่ใช้งาน (%)": f"{percent_used:.2f}%",
                "สถานะ": status,
                "_percent": percent_used # เก็บไว้ sort
            })
            
        # แสดงผล
        if recommended:
            st.success(f"✅ **แนะนำให้ใช้ท่อขนาด: {recommended['size']} mm**")
            st.info(f"พื้นที่หน้าตัดสายรวม: {wire_area:.2f} sq.mm.")
        else:
            st.error("❌ ไม่พบขนาดท่อที่รองรับ (จำนวนสายมากเกินไป)")
            
        # ตารางรายละเอียด
        st.markdown("#### ตารางเปรียบเทียบขนาดท่อ")
        df_res = pd.DataFrame(results)
        st.dataframe(
            df_res[["ขนาดท่อ (mm)", "พื้นที่ใช้งาน (%)", "สถานะ"]],
            hide_index=True,
            use_container_width=True
        )

# === Tab 2: Admin Calibration ===
with tab2:
    st.markdown("### 🛠️ ปรับแต่งค่ามาตรฐาน (Calibration)")
    
    # Login Section
    if not st.session_state['is_admin']:
        password = st.text_input("รหัสผ่าน Admin", type="password")
        if st.button("เข้าสู่ระบบ"):
            if password == ADMIN_PASSWORD:
                st.session_state['is_admin'] = True
                st.rerun()
            else:
                st.error("รหัสผ่านไม่ถูกต้อง")
    else:
        # Logout Button
        if st.button("ออกจากระบบ", type="secondary"):
            st.session_state['is_admin'] = False
            st.rerun()
            
        st.warning("💡 **วิธีใช้:** แก้ไขค่า **OD (mm)** ในตารางด้านบน -> ตารางจำนวนเส้นด้านล่างจะคำนวณใหม่ทันที")
        
        col_edit, col_view = st.columns([1, 2])
        
        # 1. ตารางแก้ไข (Editor)
        with col_edit:
            st.markdown("#### 1. แก้ไข OD สายไฟ")
            df_editor = pd.DataFrame(st.session_state['wires'])
            
            # ใช้ st.data_editor เพื่อให้แก้ค่าได้
            edited_df = st.data_editor(
                df_editor,
                column_config={
                    "sz": "ขนาด (sq.mm)",
                    "od": st.column_config.NumberColumn("OD (mm)", format="%.2f", min_value=0.1, step=0.1)
                },
                hide_index=True,
                num_rows="dynamic",
                key="editor"
            )
            
            # ปุ่มบันทึก
            if st.button("💾 บันทึกค่าใหม่"):
                # Convert DataFrame กลับเป็น List of Dict และบันทึก
                new_data = edited_df.to_dict('records')
                st.session_state['wires'] = new_data
                save_data(new_data)
                st.success("บันทึกข้อมูลเรียบร้อย!")
                # st.rerun() # ไม่ต้อง rerun ก็ได้ เพราะ data_editor อัปเดต state แล้ว

        # 2. ตารางผลลัพธ์ (Simulation View)
        with col_view:
            st.markdown("#### 2. ผลลัพธ์จำนวนเส้น (จำลอง)")
            st.markdown("*เทียบกับตารางมาตรฐาน มอก. (Fill Factor 40%)*")
            
            # สร้างตาราง Matrix: Rows=WireSize, Cols=ConduitSize
            sim_data = []
            
            # ใช้ข้อมูลจาก edited_df (Real-time) มาคำนวณ
            for index, row in edited_df.iterrows():
                row_data = {"ขนาดสาย": row['sz']} # Column แรก
                
                for c in CONDUITS:
                    # คำนวณจำนวนเส้นสูงสุด
                    max_wires = calculate_max_wires(row['od'], c['id'])
                    # ถ้าเป็น 0 ให้โชว์ -
                    row_data[c['size']] = max_wires if max_wires > 0 else "-"
                
                sim_data.append(row_data)
            
            df_sim = pd.DataFrame(sim_data)
            
            # แสดงตารางแบบ Static (ดูอย่างเดียว)
            st.dataframe(
                df_sim, 
                hide_index=True,
                use_container_width=True
            )
            
        st.markdown("---")
        if st.button("⚠️ รีเซ็ตค่าเริ่มต้น (Factory Reset)"):
            st.session_state['wires'] = DEFAULT_WIRES
            save_data(DEFAULT_WIRES)
            st.rerun()