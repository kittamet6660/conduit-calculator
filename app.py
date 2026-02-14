import streamlit as st
import pandas as pd
import math
import json
import os

# --- ตั้งค่าระบบ ---
ADMIN_PASSWORD = "1234"      # รหัสผ่านสำหรับ Admin
DATA_FILE = "iec_data_v2.json"  # เปลี่ยนชื่อไฟล์เล็กน้อยเพื่อไม่ให้ตีกับของเดิม

# --- ข้อมูลเริ่มต้น (Default Data) ---
# ค่า OD (mm) อ้างอิงมาตรฐานทั่วไป (เช่น Thai Yazaki)
DEFAULT_DATA = {
    "IEC 01 (THW)": [
        {"sz": 1.5, "od": 3.2}, {"sz": 2.5, "od": 3.8}, {"sz": 4.0, "od": 4.4},
        {"sz": 6.0, "od": 5.0}, {"sz": 10.0, "od": 6.0}, {"sz": 16.0, "od": 7.2},
        {"sz": 25.0, "od": 8.9}, {"sz": 35.0, "od": 10.1}, {"sz": 50.0, "od": 12.0},
        {"sz": 70.0, "od": 13.8}, {"sz": 95.0, "od": 16.0}, {"sz": 120.0, "od": 17.6},
        {"sz": 150.0, "od": 19.6}, {"sz": 185.0, "od": 22.0}, {"sz": 240.0, "od": 25.0},
        {"sz": 300.0, "od": 28.0}, {"sz": 400.0, "od": 32.5}
    ],
    "NYY 1/C (แกนเดี่ยว)": [
        {"sz": 1.0, "od": 10.5}, {"sz": 1.5, "od": 8.6}, {"sz": 2.5, "od": 9.0},
        {"sz": 4.0, "od": 9.4}, {"sz": 6.0, "od": 9.8}, {"sz": 10.0, "od": 10.5},
        {"sz": 16.0, "od": 11.0}, {"sz": 25.0, "od": 12.0}, {"sz": 35.0, "od": 13.0},
        {"sz": 50.0, "od": 14.5}, {"sz": 70.0, "od": 16.0}, {"sz": 95.0, "od": 17.0},
        {"sz": 120.0, "od": 19.0}, {"sz": 150.0, "od": 21.5}, {"sz": 185.0, "od": 23.0},
        {"sz": 240.0, "od": 26.0}, {"sz": 300.0, "od": 28.0}, {"sz": 400.0, "od": 31.5},
        {"sz": 500.0, "od": 35.0}
    ],
    "NYY 3/C (3 แกน)": [
        {"sz": 1.5, "od": 12.0}, {"sz": 2.5, "od": 13.0}, {"sz": 4.0, "od": 14.5},
        {"sz": 6.0, "od": 16.0}, {"sz": 10.0, "od": 18.0}, {"sz": 16.0, "od": 20.0},
        {"sz": 25.0, "od": 24.0}, {"sz": 35.0, "od": 26.5}, {"sz": 50.0, "od": 30.0},
        {"sz": 70.0, "od": 34.0}, {"sz": 95.0, "od": 38.0}, {"sz": 120.0, "od": 42.0},
        {"sz": 150.0, "od": 47.0}, {"sz": 185.0, "od": 52.0}, {"sz": 240.0, "od": 59.0},
        {"sz": 300.0, "od": 65.0}
    ],
    "NYY 4/C (4 แกน)": [
        {"sz": 1.5, "od": 13.0}, {"sz": 2.5, "od": 14.0}, {"sz": 4.0, "od": 15.5},
        {"sz": 6.0, "od": 17.0}, {"sz": 10.0, "od": 19.5}, {"sz": 16.0, "od": 21.5},
        {"sz": 25.0, "od": 26.0}, {"sz": 35.0, "od": 29.0}, {"sz": 50.0, "od": 34.0},
        {"sz": 70.0, "od": 38.5}, {"sz": 95.0, "od": 43.0}, {"sz": 120.0, "od": 47.5},
        {"sz": 150.0, "od": 53.0}, {"sz": 185.0, "od": 58.5}, {"sz": 240.0, "od": 66.0},
        {"sz": 300.0, "od": 73.0}
    ],
    "XLPE 1/C (CV 0.6/1kV)": [
        {"sz": 1.5, "od": 6.5}, {"sz": 2.5, "od": 7.0}, {"sz": 4.0, "od": 7.5},
        {"sz": 6.0, "od": 8.0}, {"sz": 10.0, "od": 9.0}, {"sz": 16.0, "od": 10.0},
        {"sz": 25.0, "od": 12.0}, {"sz": 35.0, "od": 13.0}, {"sz": 50.0, "od": 14.5},
        {"sz": 70.0, "od": 16.5}, {"sz": 95.0, "od": 18.5}, {"sz": 120.0, "od": 20.5},
        {"sz": 150.0, "od": 22.5}, {"sz": 185.0, "od": 25.0}, {"sz": 240.0, "od": 28.0},
        {"sz": 300.0, "od": 30.5}, {"sz": 400.0, "od": 34.0}
    ]
}

# ขนาดท่อมาตรฐาน (mm) - ใช้ ID (Inner Diameter) ในการคำนวณ
CONDUITS = [
    {"size": "1/2\" (15mm)", "id": 15.8}, {"size": "3/4\" (20mm)", "id": 20.9},
    {"size": "1\" (25mm)", "id": 26.6}, {"size": "1-1/4\" (32mm)", "id": 35.1},
    {"size": "1-1/2\" (40mm)", "id": 40.9}, {"size": "2\" (50mm)", "id": 52.5},
    {"size": "2-1/2\" (65mm)", "id": 62.7}, {"size": "3\" (80mm)", "id": 77.9},
    {"size": "3-1/2\" (90mm)", "id": 90.1}, {"size": "4\" (100mm)", "id": 102.3},
    {"size": "5\" (125mm)", "id": 128.2}, {"size": "6\" (150mm)", "id": 154.1}
]

# --- ฟังก์ชันระบบ ---
def load_data():
    """โหลดข้อมูลจากไฟล์ JSON ถ้าไม่มีให้ใช้ค่า Default"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # ตรวจสอบว่ามีคีย์ครบไหม (เผื่อไฟล์เก่าไม่มีตารางใหม่)
                for key in DEFAULT_DATA:
                    if key not in data:
                        data[key] = DEFAULT_DATA[key]
                return data
        except:
            return DEFAULT_DATA
    return DEFAULT_DATA

def save_data(data):
    """บันทึกข้อมูลลงไฟล์ JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_fill_factor(qty):
    """คืนค่า % พื้นที่ใช้งานที่อนุญาต ตามจำนวนเส้น"""
    if qty == 1:
        return 0.53  # 1 เส้น: 53%
    elif qty == 2:
        return 0.31  # 2 เส้น: 31%
    else:
        return 0.40  # 3 เส้นขึ้นไป: 40%

def calc_max_wires(wire_od, conduit_id):
    """คำนวณจำนวนเส้นสูงสุดที่ใส่ได้ โดยเช็คเงื่อนไข 53/31/40%"""
    wire_area = math.pi * ((wire_od / 2) ** 2)
    conduit_area = math.pi * ((conduit_id / 2) ** 2)
    
    max_w = 0
    
    # 1. เช็คกรณี 1 เส้น (53%)
    if wire_area <= (conduit_area * 0.53):
        max_w = 1
    
    # 2. เช็คกรณี 2 เส้น (31%)
    # ต้องเช็คว่าพื้นที่สาย 2 เส้น น้อยกว่า 31% ของท่อไหม
    if (2 * wire_area) <= (conduit_area * 0.31):
        max_w = 2
        
    # 3. เช็คกรณี 3 เส้นขึ้นไป (40%)
    # คำนวณว่าที่ 40% ใส่ได้กี่เส้น
    max_3_plus = math.floor((conduit_area * 0.40) / wire_area)
    
    # สรุปผล: เลือกจำนวนที่มากที่สุดที่เป็นไปได้ตามกฎ
    if max_3_plus >= 3:
        return max_3_plus
    elif max_w == 2:
        return 2
    else:
        return max_w

# --- ตั้งค่าหน้าเว็บ (UI) ---
st.set_page_config(page_title="โปรแกรมคำนวณท่อร้อยสาย", layout="wide")

st.title("⚡ โปรแกรมคำนวณท่อร้อยสาย (IEC/NYY/XLPE)")
st.caption("คำนวณตามมาตรฐาน วสท. (Fill Factor: 1เส้น=53%, 2เส้น=31%, 3เส้น+=40%)")

# โหลดข้อมูลเข้า Session State
if 'wire_db' not in st.session_state:
    st.session_state['wire_db'] = load_data()
if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# สร้าง Tabs
tab1, tab2 = st.tabs(["🧮 ใช้งานคำนวณ", "🛠️ แก้ไขข้อมูล (Admin)"])

# ==========================================
# Tab 1: หน้าคำนวณสำหรับผู้ใช้
# ==========================================
with tab1:
    calc_mode = st.radio(
        "เลือกโหมดการคำนวณ:",
        ["🅰️ หาขนาดท่อ (ใส่จำนวนเส้น)", "🅱️ หาจำนวนสาย (ใส่ขนาดท่อ)"],
        horizontal=True
    )
    st.write("---")

    # ส่วนเลือกสายไฟ
    col_type, col_sz = st.columns(2)
    with col_type:
        wire_type = st.selectbox("เลือกชนิดสายไฟ", list(st.session_state['wire_db'].keys()))
    
    df_wires = pd.DataFrame(st.session_state['wire_db'][wire_type])
    
    with col_sz:
        selected_sz = st.selectbox("ขนาดสาย (sq.mm.)", df_wires['sz'])

    # ดึงค่า OD ของสายที่เลือก
    current_od = df_wires[df_wires['sz'] == selected_sz].iloc[0]['od']

    # --- MODE A: หาขนาดท่อ ---
    if calc_mode == "🅰️ หาขนาดท่อ (ใส่จำนวนเส้น)":
        qty = st.number_input("จำนวนเส้นที่ต้องการร้อย", min_value=1, value=1)
        
        # แสดงข้อมูลสรุป
        st.info(f"🔹 สาย: {wire_type} | ขนาด: {selected_sz} sq.mm. | OD: {current_od} mm | จำนวน: {qty} เส้น")
        
        if st.button("🚀 คำนวณขนาดท่อ", type="primary"):
            wire_area = math.pi * ((current_od / 2) ** 2)
            total_wire_area = wire_area * qty
            
            # หาว่าจำนวนเส้นนี้ ต้องใช้ Fill Factor เท่าไหร่ (53/31/40)
            fill_limit = get_fill_factor(qty)
            
            results = []
            best_option = None
            
            for c in CONDUITS:
                conduit_area = math.pi * ((c['id'] / 2) ** 2)
                max_usable = conduit_area * fill_limit # พื้นที่ที่อนุญาตให้ใช้
                percent_used = (total_wire_area / conduit_area) * 100
                
                status = "❌ แน่นเกิน"
                if total_wire_area <= max_usable:
                    status = "✅ ใช้ได้"
                    if best_option is None: best_option = c
                
                results.append({
                    "ขนาดท่อ": c['size'],
                    "ID (mm)": c['id'],
                    "พื้นที่ใช้งานจริง (%)": f"{percent_used:.2f}%",
                    "เกณฑ์ที่ยอมรับ (%)": f"{fill_limit*100:.0f}%",
                    "สถานะ": status
                })
                
            if best_option:
                st.success(f"✅ แนะนำท่อขนาด: **{best_option['size']}**")
                st.write(f"ใช้พื้นที่จริง **{total_wire_area:.2f}** sq.mm. (จากพื้นที่ที่ยอมรับได้ **{(math.pi*((best_option['id']/2)**2)*fill_limit):.2f}** sq.mm.)")
            else:
                st.error("❌ ไม่มีท่อขนาดใดรองรับ (แน่นเกินไป)")
            
            st.dataframe(pd.DataFrame(results), hide_index=True, use_container_width=True)

    # --- MODE B: หาจำนวนสายสูงสุด ---
    else:
        conduit_options = [c['size'] for c in CONDUITS]
        selected_conduit_size = st.selectbox("เลือกขนาดท่อ", conduit_options)
        
        conduit_data = next(c for c in CONDUITS if c['size'] == selected_conduit_size)
        
        if st.button("🔢 คำนวณจำนวนเส้น", type="primary"):
            # คำนวณจำนวนเส้นสูงสุดตามกฎ 53/31/40
            max_wires = calc_max_wires(current_od, conduit_data['id'])
            
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #e8f5e9; border-radius: 10px; border: 2px solid #4caf50;">
                <h2 style="color: #2e7d32; margin:0;">ใส่ได้สูงสุด: {max_wires} เส้น</h2>
                <p style="margin:0; color: #555;">(สาย {wire_type} {selected_sz} sq.mm. ในท่อ {selected_conduit_size})</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            st.info("💡 หมายเหตุ: ระบบคำนวณตามกฎ: 1 เส้น(53%), 2 เส้น(31%), 3 เส้นขึ้นไป(40%)")

# ==========================================
# Tab 2: Admin Panel (แก้ไขข้อมูล)
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
        col_logout, col_reset = st.columns([1, 5])
        with col_logout:
            if st.button("ออกจากระบบ"):
                st.session_state['is_admin'] = False
                st.rerun()
        
        st.write("---")
        
        # เลือกตารางที่จะแก้
        edit_type = st.selectbox("เลือกตารางสายไฟที่ต้องการแก้ไข:", list(st.session_state['wire_db'].keys()))
        
        df_edit = pd.DataFrame(st.session_state['wire_db'][edit_type])
        
        col_editor, col_preview = st.columns([1, 1])
        
        with col_editor:
            st.subheader(f"📝 แก้ไข OD: {edit_type}")
            edited_df = st.data_editor(
                df_edit,
                column_config={
                    "sz": st.column_config.NumberColumn("ขนาด (sq.mm)", disabled=True),
                    "od": st.column_config.NumberColumn("OD (mm)", format="%.2f", step=0.1)
                },
                hide_index=True,
                height=500,
                key="editor"
            )
            
            if st.button("💾 บันทึกการเปลี่ยนแปลง"):
                # อัปเดตข้อมูลลง Session State และบันทึกไฟล์
                st.session_state['wire_db'][edit_type] = edited_df.to_dict('records')
                save_data(st.session_state['wire_db'])
                st.success(f"บันทึกข้อมูล {edit_type} เรียบร้อย!")

        with col_preview:
            st.subheader("🔍 จำลองผลลัพธ์ (Max Wires)")
            st.caption("ลองคำนวณจำนวนเส้นสูงสุดที่ใส่ได้ในท่อแต่ละขนาด (ตามกฎ 53/31/40)")
            
            sim_rows = []
            for index, row in edited_df.iterrows():
                sim_row = {"ขนาดสาย": row['sz']}
                # แสดงแค่บางท่อเพื่อไม่ให้รกเกินไป
                sample_conduits = [c for c in CONDUITS if c['size'] in ['1/2" (15mm)', '1" (25mm)', '2" (50mm)', '4" (100mm)']]
                for c in sample_conduits:
                    max_w = calc_max_wires(row['od'], c['id'])
                    sim_row[c['size']] = max_w if max_w > 0 else "-"
                sim_rows.append(sim_row)
            
            st.dataframe(pd.DataFrame(sim_rows), hide_index=True, use_container_width=True)

        st.write("---")
        if st.button("⚠️ Factory Reset (ล้างค่าทั้งหมดกลับเป็นค่าเริ่มต้น)"):
            st.session_state['wire_db'] = DEFAULT_DATA
            save_data(DEFAULT_DATA)
            st.rerun()