import streamlit as st
import pandas as pd
import math
import json
import os

# --- ตั้งค่าระบบ ---
ADMIN_PASSWORD = "1234"      # รหัสผ่านสำหรับ Admin
DATA_FILE = "iec_data_v4.json"

# --- ข้อมูลเทคนิคและข้อแนะนำ (เพิ่มส่วนนี้) ---
WIRE_SPECS = {
    "IEC 01 (THW)": {
        "img": "iec01.png", # ชื่อไฟล์รูป
        "std": "มอก. 11 เล่ม 3-2553",
        "volt": "450/750 V",
        "temp": "70°C",
        "insulation": "PVC",
        "desc": "สายไฟฟ้าแกนเดี่ยว หุ้มฉนวน PVC ชั้นเดียว (ไม่มีเปลือกนอก)",
        "usage": [
            "✅ เดินในช่องเดินสาย (ท่อร้อยสาย, รางเดินสาย) ในสถานที่แห้ง",
            "✅ เดินลอยในอากาศ (ต้องยึดด้วยลูกถ้วย)",
            "❌ ห้ามร้อยท่อฝังดิน หรือฝังดินโดยตรง",
            "❌ ห้ามเดินบนรางเคเบิล (Cable Tray) (ยกเว้นขนาด 50 sq.mm ขึ้นไปและได้รับอนุญาต)"
        ]
    },
    "NYY": {
        "img": "nyy.png",
        "std": "มอก. 11 เล่ม 101-2553",
        "volt": "450/750 V",
        "temp": "70°C",
        "insulation": "PVC (ฉนวนและเปลือก)",
        "desc": "สายไฟฟ้าหุ้มฉนวนและเปลือก PVC (มีทั้งแกนเดี่ยวและหลายแกน)",
        "usage": [
            "✅ ใช้งานทั่วไป เดินลอยในอากาศ",
            "✅ ร้อยท่อฝังดิน หรือฝังดินโดยตรงได้",
            "✅ เดินบนรางเคเบิล (Cable Tray) ได้",
            "✅ ทนความชื้นและสภาพแวดล้อมได้ดีกว่า IEC 01"
        ]
    },
    "XLPE (CV)": {
        "img": "cv.png",
        "std": "IEC 60502-1",
        "volt": "0.6/1 kV",
        "temp": "90°C",
        "insulation": "XLPE (ฉนวน) / PVC (เปลือก)",
        "desc": "สายไฟฟ้ากำลังหุ้มฉนวน XLPE และเปลือก PVC",
        "usage": [
            "✅ จ่ายกระแสได้สูงกว่าสาย PVC (เนื่องจากทนความร้อนได้ 90°C)",
            "✅ ใช้ในวงจรประธาน (Main Feeder) หรือโรงงานอุตสาหกรรม",
            "✅ เดินบนรางเคเบิล (Cable Tray) หรือบันไดสาย (Wire Way)",
            "✅ ร้อยท่อฝังดิน หรือฝังดินโดยตรงได้"
        ]
    }
}

# --- ข้อมูล OD เริ่มต้น (Default Data) ---
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

# ขนาดท่อมาตรฐาน
CONDUITS = [
    {"size": "1/2\" (15mm)", "id": 15.8}, {"size": "3/4\" (20mm)", "id": 20.9},
    {"size": "1\" (25mm)", "id": 26.6}, {"size": "1-1/4\" (32mm)", "id": 35.1},
    {"size": "1-1/2\" (40mm)", "id": 40.9}, {"size": "2\" (50mm)", "id": 52.5},
    {"size": "2-1/2\" (65mm)", "id": 62.7}, {"size": "3\" (80mm)", "id": 77.9},
    {"size": "3-1/2\" (90mm)", "id": 90.1}, {"size": "4\" (100mm)", "id": 102.3},
    {"size": "5\" (125mm)", "id": 128.2}, {"size": "6\" (150mm)", "id": 154.1}
]

# --- ฟังก์ชัน ---
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

def get_fill_factor(qty):
    if qty == 1: return 0.53
    elif qty == 2: return 0.31
    else: return 0.40

def calc_max_wires(wire_od, conduit_id):
    wire_area = math.pi * ((wire_od / 2) ** 2)
    conduit_area = math.pi * ((conduit_id / 2) ** 2)
    max_w = 0
    if wire_area <= (conduit_area * 0.53): max_w = 1
    if (2 * wire_area) <= (conduit_area * 0.31): max_w = 2
    max_3_plus = math.floor((conduit_area * 0.40) / wire_area)
    
    if max_3_plus >= 3: return max_3_plus
    elif max_w == 2: return 2
    else: return max_w

# --- UI Setup ---
st.set_page_config(page_title="โปรแกรมคำนวณท่อร้อยสาย", layout="wide")

st.title("⚡ โปรแกรมคำนวณท่อร้อยสาย (IEC/NYY/XLPE)")
st.caption("คำนวณตามมาตรฐาน วสท. (Fill Factor: 1เส้น=53%, 2เส้น=31%, 3เส้น+=40%)")

if 'wire_db' not in st.session_state:
    st.session_state['wire_db'] = load_data()
if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# เพิ่ม Tab ใหม่ตรงนี้
tab1, tab2, tab3 = st.tabs(["🧮 ใช้งานคำนวณ", "ℹ️ ข้อมูลสายไฟ (Datasheet)", "🛠️ แก้ไขข้อมูล (Admin)"])

# ==========================================
# Tab 1: หน้าคำนวณ (เหมือนเดิม)
# ==========================================
with tab1:
    calc_mode = st.radio(
        "เลือกโหมดการคำนวณ:",
        ["🅰️ หาขนาดท่อ (ใส่จำนวนเส้น)", "🅱️ หาจำนวนสาย (ใส่ขนาดท่อ)"],
        horizontal=True
    )
    st.write("---")

    col_type, col_sz = st.columns(2)
    with col_type:
        wire_type = st.selectbox("เลือกชนิดสายไฟ", list(st.session_state['wire_db'].keys()))
    
    df_wires = pd.DataFrame(st.session_state['wire_db'][wire_type])
    
    with col_sz:
        selected_sz = st.selectbox("ขนาดสาย (sq.mm.)", df_wires['sz'])

    current_od = df_wires[df_wires['sz'] == selected_sz].iloc[0]['od']

    if calc_mode == "🅰️ หาขนาดท่อ (ใส่จำนวนเส้น)":
        qty = st.number_input("จำนวนเส้นที่ต้องการร้อย", min_value=1, value=1)
        st.info(f"🔹 สาย: {wire_type} | ขนาด: {selected_sz} sq.mm. | OD: {current_od} mm | จำนวน: {qty} เส้น")
        
        if st.button("🚀 คำนวณขนาดท่อ", type="primary"):
            wire_area = math.pi * ((current_od / 2) ** 2)
            total_wire_area = wire_area * qty
            fill_limit = get_fill_factor(qty)
            
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
                    "ID (mm)": c['id'],
                    "พื้นที่ใช้งานจริง (%)": f"{percent_used:.2f}%",
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
        selected_conduit_size = st.selectbox("เลือกขนาดท่อ", conduit_options)
        conduit_data = next(c for c in CONDUITS if c['size'] == selected_conduit_size)
        
        if st.button("🔢 คำนวณจำนวนเส้น", type="primary"):
            max_wires = calc_max_wires(current_od, conduit_data['id'])
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #e8f5e9; border-radius: 10px; border: 2px solid #4caf50;">
                <h2 style="color: #2e7d32; margin:0;">ใส่ได้สูงสุด: {max_wires} เส้น</h2>
                <p style="margin:0; color: #555;">(สาย {wire_type} {selected_sz} sq.mm. ในท่อ {selected_conduit_size})</p>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# Tab 2: ข้อมูลสายไฟ (Datasheet) **เพิ่มใหม่**
# ==========================================
with tab2:
    st.header("📄 ข้อมูลเทคนิคและข้อแนะนำการใช้งาน")
    
    # ตัวเลือกสาย (Map ชื่อจากตัวแปร WIRE_SPECS)
    # เราจัดกลุ่ม NYY ทั้งหมดให้โชว์ข้อมูลเดียวกัน (เพราะสเปกเหมือนกันต่างแค่แกน)
    spec_options = ["IEC 01 (THW)", "NYY", "XLPE (CV)"]
    selected_spec = st.selectbox("เลือกชนิดสายที่ต้องการดูข้อมูล:", spec_options)
    
    info = WIRE_SPECS.get(selected_spec)
    
    if info:
        col_img, col_info = st.columns([1, 2])
        
        with col_img:
            # โชว์รูปภาพ (ถ้ามีไฟล์)
            if os.path.exists(info['img']):
                st.image(info['img'], caption=f"ลักษณะสาย {selected_spec}", use_container_width=True)
            else:
                st.warning(f"⚠️ ไม่พบไฟล์รูปภาพ ({info['img']})\n\nกรุณานำไฟล์รูปมาวางในโฟลเดอร์เดียวกับโปรแกรม")
        
        with col_info:
            st.subheader(f"📌 {selected_spec}")
            st.write(f"**รายละเอียด:** {info['desc']}")
            
            # ตารางข้อมูลเทคนิค
            tech_data = {
                "มาตรฐาน (Standard)": info['std'],
                "พิกัดแรงดัน (Voltage)": info['volt'],
                "อุณหภูมิใช้งาน (Temp)": info['temp'],
                "ชนิดฉนวน": info['insulation']
            }
            st.table(pd.DataFrame(tech_data.items(), columns=["หัวข้อ", "รายละเอียด"]))
            
            st.subheader("✅ ข้อแนะนำการใช้งาน")
            for item in info['usage']:
                st.write(item)

# ==========================================
# Tab 3: Admin (เหมือนเดิม)
# ==========================================
with tab3:
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
        if st.button("ออกจากระบบ"):
            st.session_state['is_admin'] = False
            st.rerun()
        st.write("---")
        
        edit_type = st.selectbox("เลือกตารางสายไฟที่ต้องการแก้ไข:", list(st.session_state['wire_db'].keys()))
        df_edit = pd.DataFrame(st.session_state['wire_db'][edit_type])
        
        col_editor, col_preview = st.columns([1, 1])
        with col_editor:
            st.subheader(f"📝 แก้ไข OD: {edit_type}")
            edited_df = st.data_editor(
                df_edit,
                column_config={
                    "sz": st.column_config.NumberColumn("ขนาด", disabled=True),
                    "od": st.column_config.NumberColumn("OD", format="%.2f", step=0.1)
                },
                hide_index=True, height=500, key="editor"
            )
            if st.button("💾 บันทึกการเปลี่ยนแปลง"):
                st.session_state['wire_db'][edit_type] = edited_df.to_dict('records')
                save_data(st.session_state['wire_db'])
                st.success("บันทึกเรียบร้อย!")

        with col_preview:
            st.subheader("🔍 จำลองผลลัพธ์")
            sim_rows = []
            for index, row in edited_df.iterrows():
                sim_row = {"ขนาด": row['sz']}
                sample_conduits = [c for c in CONDUITS if c['size'] in ['1/2" (15mm)', '1" (25mm)', '2" (50mm)', '4" (100mm)']]
                for c in sample_conduits:
                    max_w = calc_max_wires(row['od'], c['id'])
                    sim_row[c['size']] = max_w if max_w > 0 else "-"
                sim_rows.append(sim_row)
            st.dataframe(pd.DataFrame(sim_rows), hide_index=True, use_container_width=True)

        st.write("---")
        if st.button("⚠️ Factory Reset"):
            st.session_state['wire_db'] = DEFAULT_DATA
            save_data(DEFAULT_DATA)
            st.rerun()