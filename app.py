import streamlit as st
import pandas as pd
import math
import json
import os

# --- ตั้งค่าระบบ ---
ADMIN_PASSWORD = "1234"      # รหัสผ่านสำหรับ Admin
DATA_FILE = "iec_data_v7.json"  # เปลี่ยนชื่อไฟล์เป็น v7

# --- ข้อมูลเทคนิคและข้อแนะนำ (สำหรับ Tab Datasheet) ---
WIRE_SPECS = {
    "IEC 01 (THW)": {
        "img": "iec01.png", 
        "std": "มอก. 11 เล่ม 3-2553",
        "volt": "450/750 V",
        "temp": "70°C",
        "insulation": "PVC",
        "desc": "สายไฟฟ้าแกนเดี่ยว หุ้มฉนวน PVC ชั้นเดียว (ไม่มีเปลือกนอก)",
        "usage": [
            "✅ เดินในช่องเดินสาย (ท่อร้อยสาย, รางเดินสาย) ในสถานที่แห้ง",
            "✅ เดินลอยในอากาศ (ต้องยึดด้วยลูกถ้วย)",
            "❌ ห้ามร้อยท่อฝังดิน หรือฝังดินโดยตรง",
            "❌ ห้ามเดินบนรางเคเบิล (Cable Tray) (ยกเว้นขนาด 50 sq.mm ขึ้นไป)"
        ]
    },
    "NYY 1/C (แกนเดี่ยว)": {
        "img": "nyy.png",
        "std": "มอก. 11 เล่ม 101-2553",
        "volt": "450/750 V",
        "temp": "70°C",
        "insulation": "PVC (ฉนวนและเปลือก)",
        "desc": "สายไฟฟ้าหุ้มฉนวนและเปลือก PVC แกนเดี่ยว",
        "usage": [
            "✅ ใช้งานทั่วไป เดินลอยในอากาศ",
            "✅ ร้อยท่อฝังดิน หรือฝังดินโดยตรงได้",
            "✅ เดินบนรางเคเบิล (Cable Tray) ได้"
        ]
    },
    "NYY 3/C (3 แกน)": {
        "img": "NYY-3C.jpg", # ใช้รูปเดียวกับ NYY ปกติ
        "std": "มอก. 11 เล่ม 101-2553",
        "volt": "450/750 V",
        "temp": "70°C",
        "insulation": "PVC",
        "desc": "สายไฟฟ้าหุ้มฉนวนและเปลือก PVC แบบ 3 แกน",
        "usage": ["✅ เหมาะสำหรับระบบ 3 เฟส", "✅ ร้อยท่อฝังดิน/ฝังดินโดยตรง/บนรางเคเบิล"]
    },
    "NYY 4/C (4 แกน)": {
        "img": "NYY-4C.jpg",
        "std": "มอก. 11 เล่ม 101-2553",
        "volt": "450/750 V",
        "temp": "70°C",
        "insulation": "PVC",
        "desc": "สายไฟฟ้าหุ้มฉนวนและเปลือก PVC แบบ 4 แกน",
        "usage": ["✅ เหมาะสำหรับระบบ 3 เฟส 4 สาย", "✅ ร้อยท่อฝังดิน/ฝังดินโดยตรง/บนรางเคเบิล"]
    },
    "XLPE 1/C (CV 0.6/1kV)": {
        "img": "cv.png",
        "std": "IEC 60502-1",
        "volt": "0.6/1 kV",
        "temp": "90°C",
        "insulation": "XLPE/PVC",
        "desc": "สายไฟฟ้ากำลังหุ้มฉนวน XLPE และเปลือก PVC",
        "usage": [
            "✅ จ่ายกระแสได้สูง (ทนร้อน 90°C)",
            "✅ ใช้ในวงจรประธาน โรงงานอุตสาหกรรม",
            "✅ ร้อยท่อฝังดิน/ฝังดินโดยตรง/บนรางเคเบิล"
        ]
    }
}

# --- ข้อมูล OD เริ่มต้น (Updated ตามข้อมูลใหม่) ---
DEFAULT_DATA = {
    "IEC 01 (THW)": [
        {"sz": 1.5, "od": 3.3}, {"sz": 2.5, "od": 4.0}, {"sz": 4.0, "od": 4.6},
        {"sz": 6.0, "od": 5.2}, {"sz": 10.0, "od": 6.7}, {"sz": 16.0, "od": 7.8},
        {"sz": 25.0, "od": 9.7}, {"sz": 35.0, "od": 10.9}, {"sz": 50.0, "od": 12.8},
        {"sz": 70.0, "od": 14.6}, {"sz": 95.0, "od": 17.1}, {"sz": 120.0, "od": 18.8},
        {"sz": 150.0, "od": 20.9}, {"sz": 185.0, "od": 23.3}, {"sz": 240.0, "od": 26.6},
        {"sz": 300.0, "od": 29.6}, {"sz": 400.0, "od": 33.2}
    ],
    "NYY 1/C (แกนเดี่ยว)": [
        {"sz": 1.0, "od": 8.8}, {"sz": 1.5, "od": 9.2}, {"sz": 2.5, "od": 9.8},
        {"sz": 4.0, "od": 10.5}, {"sz": 6.0, "od": 11.0}, {"sz": 10.0, "od": 12.0},
        {"sz": 16.0, "od": 13.0}, {"sz": 25.0, "od": 14.5}, {"sz": 35.0, "od": 16.0},
        {"sz": 50.0, "od": 17.0}, {"sz": 70.0, "od": 19.0}, {"sz": 95.0, "od": 21.5},
        {"sz": 120.0, "od": 23.0}, {"sz": 150.0, "od": 26.0}, {"sz": 185.0, "od": 28.0},
        {"sz": 240.0, "od": 31.5}, {"sz": 300.0, "od": 35.0}, {"sz": 400.0, "od": 38.5},
        {"sz": 500.0, "od": 43.0}
    ],
    "NYY 3/C (3 แกน)": [
        {"sz": 1.0, "od": 13.0}, {"sz": 1.5, "od": 13.5}, {"sz": 2.5, "od": 15.0},
        {"sz": 4.0, "od": 16.5}, {"sz": 6.0, "od": 18.0}, {"sz": 10.0, "od": 20.5},
        {"sz": 16.0, "od": 24.5}, {"sz": 25.0, "od": 28.5}, {"sz": 35.0, "od": 31.5},
        {"sz": 50.0, "od": 36.0}, {"sz": 70.0, "od": 40.5}, {"sz": 95.0, "od": 46.0},
        {"sz": 120.0, "od": 50.5}, {"sz": 150.0, "od": 56.0}, {"sz": 185.0, "od": 61.5},
        {"sz": 240.0, "od": 69.0}, {"sz": 300.0, "od": 76.0}
    ],
    "NYY 4/C (4 แกน)": [
        {"sz": 1.0, "od": 14.0}, {"sz": 1.5, "od": 14.5}, {"sz": 2.5, "od": 16.0},
        {"sz": 4.0, "od": 17.5}, {"sz": 6.0, "od": 19.0}, {"sz": 10.0, "od": 23.0},
        {"sz": 16.0, "od": 26.5}, {"sz": 25.0, "od": 31.0}, {"sz": 35.0, "od": 36.0},
        {"sz": 50.0, "od": 39.5}, {"sz": 70.0, "od": 44.5}, {"sz": 95.0, "od": 51.5},
        {"sz": 120.0, "od": 56.0}, {"sz": 150.0, "od": 62.0}, {"sz": 185.0, "od": 68.0},
        {"sz": 240.0, "od": 76.5}, {"sz": 300.0, "od": 85.0}
    ],
    "XLPE 1/C (CV 0.6/1kV)": [
        {"sz": 1.5, "od": 6.5}, {"sz": 2.5, "od": 7.0}, {"sz": 4.0, "od": 7.5},
        {"sz": 6.0, "od": 8.0}, {"sz": 10.0, "od": 8.5}, {"sz": 16.0, "od": 9.5},
        {"sz": 25.0, "od": 11.5}, {"sz": 35.0, "od": 12.5}, {"sz": 50.0, "od": 14.0},
        {"sz": 70.0, "od": 15.5}, {"sz": 95.0, "od": 17.5}, {"sz": 120.0, "od": 19.5},
        {"sz": 150.0, "od": 21.5}, {"sz": 185.0, "od": 23.8}, {"sz": 240.0, "od": 26.5},
        {"sz": 300.0, "od": 29.0}, {"sz": 400.0, "od": 32.5}, {"sz": 500.0, "od": 36.5}
    ]
}

# --- ข้อมูลขนาดท่อมาตรฐาน (Conduits) ---
CONDUITS = [
    {"size": "1/2\" (15mm)", "id": 15.8}, {"size": "3/4\" (20mm)", "id": 20.9},
    {"size": "1\" (25mm)", "id": 26.6}, {"size": "1-1/4\" (32mm)", "id": 35.1},
    {"size": "1-1/2\" (40mm)", "id": 40.9}, {"size": "2\" (50mm)", "id": 52.5},
    {"size": "2-1/2\" (65mm)", "id": 62.7}, {"size": "3\" (80mm)", "id": 77.9},
    {"size": "3-1/2\" (90mm)", "id": 90.1}, {"size": "4\" (100mm)", "id": 102.3},
    {"size": "5\" (125mm)", "id": 128.2}, {"size": "6\" (150mm)", "id": 154.1}
]

# --- ข้อมูลขนาดรางเดินสาย (Wire Way) ---
# Format: {"size": "WxH", "area": w*h}
WIREWAYS = [
    {"size": "50x75 mm", "area": 50 * 75},
    {"size": "50x100 mm", "area": 50 * 100},
    {"size": "75x100 mm", "area": 75 * 100},
    {"size": "100x100 mm", "area": 100 * 100},
    {"size": "100x150 mm", "area": 100 * 150},
    {"size": "100x200 mm", "area": 100 * 200},
    {"size": "100x250 mm", "area": 100 * 250},
    {"size": "100x300 mm", "area": 100 * 300},
    {"size": "150x300 mm", "area": 150 * 300}
]

# --- ฟังก์ชันจัดการข้อมูล ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key in DEFAULT_DATA:
                    if key not in data:
                        data[key] = DEFAULT_DATA[key]
                return data
        except:
            return DEFAULT_DATA
    return DEFAULT_DATA

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ฟังก์ชันคำนวณ % Fill Factor ของท่อ (53/31/40 Rule)
def get_conduit_fill_limit(qty):
    if qty == 1: return 0.53
    elif qty == 2: return 0.31
    else: return 0.40

# ฟังก์ชันคำนวณจำนวนเส้นในท่อ
def calc_conduit_max_wires(wire_od, conduit_id):
    wire_area = math.pi * ((wire_od / 2) ** 2)
    conduit_area = math.pi * ((conduit_id / 2) ** 2)
    max_w = 0
    if wire_area <= (conduit_area * 0.53): max_w = 1
    if (2 * wire_area) <= (conduit_area * 0.31): max_w = 2
    max_3_plus = math.floor((conduit_area * 0.40) / wire_area)
    if max_3_plus >= 3: return max_3_plus
    elif max_w == 2: return 2
    else: return max_w

# ฟังก์ชันคำนวณจำนวนเส้นใน Wire Way (Standard 20% Fill)
def calc_wireway_max_wires(wire_od, wireway_area):
    wire_area = math.pi * ((wire_od / 2) ** 2)
    usable_area = wireway_area * 0.20 # Wireway ใช้พื้นที่ได้ 20%
    return math.floor(usable_area / wire_area)

# --- UI Setup ---
st.set_page_config(page_title="โปรแกรมคำนวณสายไฟ", layout="wide")

st.title("⚡ โปรแกรมคำนวณท่อร้อยสาย & Wire Way")
st.caption("มาตรฐาน วสท./IEC | ท่อร้อยสาย (53/31/40%) | รางเดินสาย Wireway (20%) by Krittamet.tho")

# Initialize Session State
if 'wire_db' not in st.session_state:
    st.session_state['wire_db'] = load_data()
if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "⚪ ท่อร้อยสาย (Conduit)", 
    "⬜ รางเดินสาย (Wire Way)", 
    "ℹ️ ข้อมูลสายไฟ", 
    "🛠️ Admin"
])

# ==========================================
# Tab 1: คำนวณท่อร้อยสาย (Conduit)
# ==========================================
with tab1:
    st.header("⚪ คำนวณท่อร้อยสาย (Conduit)")
    calc_mode = st.radio(
        "เลือกโหมดท่อ:",
        ["🅰️ หาขนาดท่อ (ใส่จำนวนเส้น)", "🅱️ หาจำนวนสาย (ใส่ขนาดท่อ)"],
        horizontal=True, key="conduit_mode"
    )
    st.write("---")

    col_type, col_sz = st.columns(2)
    with col_type:
        wire_type = st.selectbox("เลือกชนิดสายไฟ", list(st.session_state['wire_db'].keys()), key="c_type")
    
    df_wires = pd.DataFrame(st.session_state['wire_db'][wire_type])
    
    with col_sz:
        selected_sz = st.selectbox("ขนาดสาย (sq.mm.)", df_wires['sz'], key="c_sz")

    current_od = df_wires[df_wires['sz'] == selected_sz].iloc[0]['od']

    if calc_mode == "🅰️ หาขนาดท่อ (ใส่จำนวนเส้น)":
        qty = st.number_input("จำนวนเส้น", min_value=1, value=1, key="c_qty")
        st.info(f"🔹 สาย: {wire_type} | ขนาด: {selected_sz} sq.mm. | OD: {current_od} mm | จำนวน: {qty} เส้น")
        
        if st.button("🚀 คำนวณขนาดท่อ", type="primary", key="btn_c_calc"):
            wire_area = math.pi * ((current_od / 2) ** 2)
            total_wire_area = wire_area * qty
            fill_limit = get_conduit_fill_limit(qty)
            
            results = []
            best_option = None
            
            for c in CONDUITS:
                conduit_area = math.pi * ((c['id'] / 2) ** 2)
                max_usable = conduit_area * fill_limit
                percent_used = (total_wire_area / conduit_area) * 100
                status = "❌ แน่นเกิน"
                if total_wire_area <= max_usable:
                    status = "✅ ใช้ได้"
                    if best_option is None: best_option = c
                
                results.append({
                    "ขนาดท่อ": c['size'],
                    "พื้นที่ใช้งาน (%)": f"{percent_used:.2f}%",
                    "เกณฑ์ (%)": f"{fill_limit*100:.0f}%",
                    "สถานะ": status
                })
                
            if best_option:
                st.success(f"✅ แนะนำท่อขนาด: **{best_option['size']}**")
            else:
                st.error("❌ ไม่มีท่อขนาดใดรองรับ")
            st.dataframe(pd.DataFrame(results), hide_index=True, use_container_width=True)

    else: # Mode B
        conduit_options = [c['size'] for c in CONDUITS]
        selected_conduit_size = st.selectbox("เลือกขนาดท่อ", conduit_options, key="c_conduit_sel")
        conduit_data = next(c for c in CONDUITS if c['size'] == selected_conduit_size)
        
        if st.button("🔢 คำนวณจำนวนเส้น", type="primary", key="btn_c_max"):
            max_wires = calc_conduit_max_wires(current_od, conduit_data['id'])
            st.success(f"ใส่ได้สูงสุด: **{max_wires} เส้น**")
            st.caption(f"(ในท่อ {selected_conduit_size})")

# ==========================================
# Tab 2: คำนวณรางเดินสาย (Wire Way) **NEW**
# ==========================================
with tab2:
    st.header("⬜ คำนวณรางเดินสาย (Wire Way)")
    ww_mode = st.radio(
        "เลือกโหมดราง:",
        ["🅰️ หารางที่เหมาะสม (ใส่จำนวนเส้น)", "🅱️ หาจำนวนสาย (ใส่ขนาดราง)"],
        horizontal=True, key="ww_mode"
    )
    st.write("---")
    
    col_w_type, col_w_sz = st.columns(2)
    with col_w_type:
        ww_wire_type = st.selectbox("เลือกชนิดสายไฟ", list(st.session_state['wire_db'].keys()), key="w_type")
    
    df_ww_wires = pd.DataFrame(st.session_state['wire_db'][ww_wire_type])
    
    with col_w_sz:
        ww_selected_sz = st.selectbox("ขนาดสาย (sq.mm.)", df_ww_wires['sz'], key="w_sz")
        
    ww_current_od = df_ww_wires[df_ww_wires['sz'] == ww_selected_sz].iloc[0]['od']
    
    if ww_mode == "🅰️ หารางที่เหมาะสม (ใส่จำนวนเส้น)":
        ww_qty = st.number_input("จำนวนเส้น", min_value=1, value=1, key="w_qty")
        st.info(f"🔹 สาย: {ww_wire_type} | ขนาด: {ww_selected_sz} sq.mm. | OD: {ww_current_od} mm | จำนวน: {ww_qty} เส้น")
        
        if st.button("🚀 คำนวณขนาดราง", type="primary", key="btn_w_calc"):
            wire_area = math.pi * ((ww_current_od / 2) ** 2)
            total_area = wire_area * ww_qty
            
            results = []
            best_ww = None
            
            for w in WIREWAYS:
                max_usable = w['area'] * 0.20 # 20% Fill Factor Rule
                percent = (total_area / w['area']) * 100
                status = "❌ แน่นเกิน"
                if total_area <= max_usable:
                    status = "✅ ใช้ได้"
                    if best_ww is None: best_ww = w
                
                results.append({
                    "ขนาดราง (mm)": w['size'],
                    "พื้นที่ราง (mm²)": w['area'],
                    "พื้นที่สายรวม (mm²)": f"{total_area:.1f}",
                    "% Fill": f"{percent:.2f}%",
                    "สถานะ": status
                })
            
            if best_ww:
                st.success(f"✅ แนะนำรางขนาด: **{best_ww['size']}**")
                st.write(f"ใช้พื้นที่สายรวม **{total_area:.2f}** mm² (คิดเป็น {(total_area/best_ww['area']*100):.2f}% ของราง)")
                st.caption("*เกณฑ์มาตรฐานรางเดินสาย: พื้นที่หน้าตัดสายรวมไม่เกิน 20% ของพื้นที่ราง")
            else:
                st.error("❌ ไม่มีรางขนาดใดรองรับ (เกิน 20% ของพื้นที่ราง)")
            
            st.dataframe(pd.DataFrame(results), hide_index=True, use_container_width=True)
            
    else: # Mode B
        ww_options = [w['size'] for w in WIREWAYS]
        selected_ww_size = st.selectbox("เลือกขนาดราง (Wire Way)", ww_options, key="w_ww_sel")
        ww_data = next(w for w in WIREWAYS if w['size'] == selected_ww_size)
        
        if st.button("🔢 คำนวณจำนวนเส้น", type="primary", key="btn_w_max"):
            max_wires = calc_wireway_max_wires(ww_current_od, ww_data['area'])
            st.success(f"ใส่ได้สูงสุด: **{max_wires} เส้น**")
            st.caption(f"(ในรางขนาด {selected_ww_size} ที่ Fill Factor 20%)")

# ==========================================
# Tab 3: ข้อมูลสายไฟ
# ==========================================
with tab3:
    st.header("📄 ข้อมูลเทคนิคและข้อแนะนำ")
    
    spec_options = list(WIRE_SPECS.keys())
    # Map ชื่อใน DB กับ Spec (เผื่อชื่อไม่ตรงเป๊ะ)
    spec_key_map = {k: k for k in spec_options} 
    # ปรับจูนให้ NYY ทุกแกนชี้ไปที่ NYY ตัวเดียวกัน หรือแยกถ้ามีข้อมูลแยก
    
    selected_spec_key = st.selectbox("เลือกชนิดสาย:", spec_options)
    info = WIRE_SPECS.get(selected_spec_key)
    
    if info:
        col_img, col_space, col_info = st.columns([1, 0.1, 1.5])
        
        with col_img:
            if os.path.exists(info['img']):
                st.image(info['img'], caption=f"ลักษณะสาย {selected_spec_key}", use_container_width=True)
            else:
                st.warning(f"⚠️ ไม่พบไฟล์รูป {info['img']}")
        
        with col_info:
            st.subheader(f"📌 {selected_spec_key}")
            st.write(f"**รายละเอียด:** {info['desc']}")
            
            tech_data = {
                "มาตรฐาน": info['std'],
                "แรงดัน": info['volt'],
                "อุณหภูมิ": info['temp'],
                "ฉนวน": info['insulation']
            }
            st.table(pd.DataFrame(tech_data.items(), columns=["หัวข้อ", "รายละเอียด"]))
            
            st.subheader("✅ ข้อแนะนำการใช้งาน")
            for item in info['usage']:
                st.write(item)

# ==========================================
# Tab 4: Admin
# ==========================================
with tab4:
    st.header("ปรับแต่งค่ามาตรฐาน")
    if not st.session_state['is_admin']:
        pwd = st.text_input("รหัสผ่าน Admin", type="password")
        if st.button("เข้าสู่ระบบ"):
            if pwd == ADMIN_PASSWORD:
                st.session_state['is_admin'] = True
                st.rerun()
            else:
                st.error("รหัสผ่านไม่ถูกต้อง")
    else:
        if st.button("ออกจากระบบ"):
            st.session_state['is_admin'] = False
            st.rerun()
        st.write("---")
        
        edit_type = st.selectbox("เลือกตารางแก้ไข:", list(st.session_state['wire_db'].keys()), key="adm_sel")
        df_edit = pd.DataFrame(st.session_state['wire_db'][edit_type])
        
        edited_df = st.data_editor(
            df_edit,
            column_config={
                "sz": st.column_config.NumberColumn("ขนาด", disabled=True),
                "od": st.column_config.NumberColumn("OD", format="%.2f", step=0.1)
            },
            hide_index=True, use_container_width=True, key="adm_editor"
        )
        if st.button("💾 บันทึกการเปลี่ยนแปลง"):
            st.session_state['wire_db'][edit_type] = edited_df.to_dict('records')
            save_data(st.session_state['wire_db'])
            st.success("บันทึกเรียบร้อย!")
        
        if st.button("⚠️ Factory Reset"):
            st.session_state['wire_db'] = DEFAULT_DATA
            save_data(DEFAULT_DATA)
            st.rerun()