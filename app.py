import streamlit as st
import pandas as pd
import math
import json
import os
from datetime import datetime, timedelta
from fpdf import FPDF
import tempfile
from PIL import Image

# --- ตั้งค่าระบบ ---
ADMIN_PASSWORD = "1234"
DATA_FILE = "iec_data_v13.json" # เปลี่ยนชื่อไฟล์เพื่อให้ระบบเคลียร์ข้อมูลเก่าที่มี NYY 3C/4C ทิ้ง
FONT_FILE = "THSarabunNew.ttf"

# --- ข้อมูลเทคนิค ---
WIRE_SPECS = {
    "IEC 01 (THW)": {
        "img": "iec01.png", 
        "std": "มอก. 11 เล่ม 3-2553",
        "volt": "450/750 V",
        "temp": "70°C",
        "insulation": "PVC",
        "desc": "สายแกนเดี่ยว หุ้มฉนวน PVC ชั้นเดียว",
        "usage": ["✅ เดินในท่อ/ราง ในที่แห้ง", "✅ เดินลอย (ยึดลูกถ้วย)", "❌ ห้ามฝังดิน", "❌ ห้ามลงรางเคเบิล (ยกเว้นขนาดใหญ่)"]
    },
    "NYY 1/C (แกนเดี่ยว)": {
        "img": "nyy.png",
        "std": "มอก. 11 เล่ม 101-2553",
        "volt": "450/750 V",
        "temp": "70°C",
        "insulation": "PVC (ฉนวน+เปลือก)",
        "desc": "สายหุ้มฉนวนและเปลือก PVC แกนเดี่ยว",
        "usage": ["✅ ใช้งานทั่วไป", "✅ ร้อยท่อฝังดิน/ฝังดินโดยตรง", "✅ เดินบนรางเคเบิล"]
    },
    "XLPE 1/C (CV 0.6/1kV)": {
        "img": "cv.png",
        "std": "IEC 60502-1",
        "volt": "0.6/1 kV",
        "temp": "90°C",
        "insulation": "XLPE/PVC",
        "desc": "สายกำลังหุ้มฉนวน XLPE เปลือก PVC",
        "usage": ["✅ จ่ายกระแสสูง (90°C)", "✅ วงจรประธาน/โรงงาน", "✅ ร้อยท่อฝังดิน/ฝังดินโดยตรง/บนรางเคเบิล"]
    }
}

# --- Default Data ---
DEFAULT_DATA = {
    "IEC 01 (THW)": [{"sz": 1.5, "od": 3.3}, {"sz": 2.5, "od": 4.0}, {"sz": 4.0, "od": 4.6}, {"sz": 6.0, "od": 5.2}, {"sz": 10.0, "od": 6.7}, {"sz": 16.0, "od": 7.8}, {"sz": 25.0, "od": 9.7}, {"sz": 35.0, "od": 10.9}, {"sz": 50.0, "od": 12.8}, {"sz": 70.0, "od": 14.6}, {"sz": 95.0, "od": 17.1}, {"sz": 120.0, "od": 18.8}, {"sz": 150.0, "od": 20.9}, {"sz": 185.0, "od": 23.3}, {"sz": 240.0, "od": 26.6}, {"sz": 300.0, "od": 29.6}, {"sz": 400.0, "od": 33.2}],
    "NYY 1/C (แกนเดี่ยว)": [{"sz": 1.0, "od": 8.8}, {"sz": 1.5, "od": 9.2}, {"sz": 2.5, "od": 9.8}, {"sz": 4.0, "od": 10.5}, {"sz": 6.0, "od": 11.0}, {"sz": 10.0, "od": 12.0}, {"sz": 16.0, "od": 13.0}, {"sz": 25.0, "od": 14.5}, {"sz": 35.0, "od": 16.0}, {"sz": 50.0, "od": 17.0}, {"sz": 70.0, "od": 19.0}, {"sz": 95.0, "od": 21.5}, {"sz": 120.0, "od": 23.0}, {"sz": 150.0, "od": 26.0}, {"sz": 185.0, "od": 28.0}, {"sz": 240.0, "od": 31.5}, {"sz": 300.0, "od": 35.0}, {"sz": 400.0, "od": 38.5}, {"sz": 500.0, "od": 43.0}],
    "XLPE 1/C (CV 0.6/1kV)": [{"sz": 1.5, "od": 6.5}, {"sz": 2.5, "od": 7.0}, {"sz": 4.0, "od": 7.5}, {"sz": 6.0, "od": 8.0}, {"sz": 10.0, "od": 8.5}, {"sz": 16.0, "od": 9.5}, {"sz": 25.0, "od": 11.5}, {"sz": 35.0, "od": 12.5}, {"sz": 50.0, "od": 14.0}, {"sz": 70.0, "od": 15.5}, {"sz": 95.0, "od": 17.5}, {"sz": 120.0, "od": 19.5}, {"sz": 150.0, "od": 21.5}, {"sz": 185.0, "od": 23.8}, {"sz": 240.0, "od": 26.5}, {"sz": 300.0, "od": 29.0}, {"sz": 400.0, "od": 32.5}, {"sz": 500.0, "od": 36.5}]
}

CONDUITS = [{"size": "1/2\" (15mm)", "id": 15.8}, {"size": "3/4\" (20mm)", "id": 20.9}, {"size": "1\" (25mm)", "id": 26.6}, {"size": "1-1/4\" (32mm)", "id": 35.1}, {"size": "1-1/2\" (40mm)", "id": 40.9}, {"size": "2\" (50mm)", "id": 52.5}, {"size": "2-1/2\" (65mm)", "id": 62.7}, {"size": "3\" (80mm)", "id": 77.9}, {"size": "3-1/2\" (90mm)", "id": 90.1}, {"size": "4\" (100mm)", "id": 102.3}, {"size": "5\" (125mm)", "id": 128.2}, {"size": "6\" (150mm)", "id": 154.1}]

WIREWAYS = [
    {"size": "50x75 mm", "area": 3750}, {"size": "50x100 mm", "area": 5000},
    {"size": "75x100 mm", "area": 7500}, {"size": "100x100 mm", "area": 10000},
    {"size": "100x150 mm", "area": 15000}, {"size": "100x200 mm", "area": 20000},
    {"size": "100x250 mm", "area": 25000}, {"size": "100x300 mm", "area": 30000},
    {"size": "150x300 mm", "area": 45000}
]

# --- Functions ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key in DEFAULT_DATA:
                    if key not in data: data[key] = DEFAULT_DATA[key]
                return data
        except: return DEFAULT_DATA
    return DEFAULT_DATA

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def calc_wire_area(wire_type, wire_size, qty, db):
    wires = db[wire_type]
    od = 0
    for w in wires:
        if w['sz'] == wire_size:
            od = w['od']
            break
    area = math.pi * ((od / 2) ** 2) * qty
    return area, od

# --- Helper: Get Thai Time ---
def get_thai_time():
    # เวลาปัจจุบัน (UTC) + 7 ชั่วโมง
    return datetime.utcnow() + timedelta(hours=7)

# --- ฟังก์ชันสร้าง PDF ---
def create_pdf(wires_list, total_area, result_name, percent_fill, mode_name, logo_upload=None, inspector_name="", inspector_pos="", custom_date_str=""):
    pdf = FPDF()
    pdf.add_page()
    
    # Check Font
    has_font = False
    if os.path.exists(FONT_FILE):
        try:
            pdf.add_font('Thai', '', FONT_FILE, uni=True) 
            pdf.set_font('Thai', '', 16)
            has_font = True
        except: pass
    
    if not has_font:
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Error: Font THSarabunNew.ttf not found", ln=True, align='C')

    # ตัวแปรสำหรับจัดการตำแหน่ง Y เริ่มต้น
    current_y = 15 # ระยะห่างขอบบนมาตรฐาน

    # ============================
    # 1. LOGO (Centered Header)
    # ============================
    if logo_upload is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(logo_upload.getbuffer())
                tmp_path = tmp.name
            
            img = Image.open(tmp_path)
            img_w, img_h = img.size
            
            # กรอบที่ต้องการ (หน่วย mm)
            max_w_mm = 40
            max_h_mm = 30
            
            ratio = min(max_w_mm / img_w, max_h_mm / img_h)
            final_w = img_w * ratio
            final_h = img_h * ratio
            
            # กึ่งกลางหน้า A4 (210mm)
            page_width = 210
            center_x = (page_width - final_w) / 2
            
            # วาดรูป
            pdf.image(tmp_path, x=center_x, y=10, w=final_w, h=final_h)
            
            # อัปเดตตำแหน่ง Y ให้ขยับลงมา
            current_y = 10 + final_h + 5 
            
            os.unlink(tmp_path)
            
        except Exception as e:
            pdf.ln(10)
            print(f"Logo error: {e}")

    # 2. Header & Date
    pdf.set_y(current_y)
    
    pdf.set_font('Thai' if has_font else 'Arial', '', 24)
    pdf.cell(0, 10, f"ใบรายงานการคำนวณ: {mode_name}", 0, 1, 'C')
    
    # --- ใช้วันที่อัตโนมัติ (รับค่ามาจากปุ่มกด) ---
    pdf.set_font('Thai' if has_font else 'Arial', '', 14)
    
    if custom_date_str:
        date_to_show = custom_date_str
    else:
        # Fallback กรณีไม่ได้ส่งค่ามา
        date_to_show = get_thai_time().strftime("%d/%m/%Y %H:%M")
    
    pdf.cell(0, 8, f"วันที่จัดทำ: {date_to_show}", 0, 1, 'C')
    
    # ตีเส้นคั่น
    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # 3. Reference Images
    pdf.set_font('Thai' if has_font else 'Arial', '', 16)
    pdf.cell(0, 10, "1. ชนิดสายไฟที่เลือกใช้ (Reference)", 0, 1)
    
    unique_types = list(set([w['type'] for w in wires_list]))
    x_start = 10
    y_start = pdf.get_y()
    max_h = 0
    
    for w_type in unique_types:
        spec = WIRE_SPECS.get(w_type)
        if spec and os.path.exists(spec['img']):
            pdf.image(spec['img'], x=x_start, y=y_start, w=25, h=25)
            pdf.set_xy(x_start, y_start + 26)
            pdf.set_font('Thai' if has_font else 'Arial', '', 12)
            pdf.multi_cell(25, 5, w_type, align='C')
            x_start += 35
            max_h = 40
            
    if max_h > 0: pdf.set_y(y_start + max_h)
    else: pdf.ln(5)
    
    # 4. Table Data
    pdf.set_font('Thai' if has_font else 'Arial', '', 16)
    pdf.cell(0, 10, "2. รายละเอียดการคำนวณ", 0, 1)
    
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(80, 8, "ชนิดสายไฟ", 1, 0, 'C', True)
    pdf.cell(40, 8, "ขนาด (sq.mm)", 1, 0, 'C', True)
    pdf.cell(30, 8, "จำนวน (เส้น)", 1, 0, 'C', True)
    pdf.cell(40, 8, "พื้นที่รวม (sq.mm)", 1, 1, 'C', True)
    
    for w in wires_list:
        pdf.cell(80, 8, f"{w['type']}", 1)
        pdf.cell(40, 8, f"{w['sz']}", 1, 0, 'C')
        pdf.cell(30, 8, f"{w['qty']}", 1, 0, 'C')
        pdf.cell(40, 8, f"{w['area']:.2f}", 1, 1, 'R')
    
    pdf.ln(5)
    
    # 5. Result
    pdf.set_fill_color(230, 255, 230)
    pdf.rect(10, pdf.get_y(), 190, 35, 'F')
    
    pdf.set_xy(15, pdf.get_y() + 5)
    pdf.set_font('Thai' if has_font else 'Arial', '', 16)
    pdf.cell(100, 8, f"พื้นที่หน้าตัดสายรวมทั้งหมด:", 0)
    pdf.cell(0, 8, f"{total_area:.2f} sq.mm.", 0, 1)
    
    pdf.set_x(15)
    pdf.set_font('Thai' if has_font else 'Arial', '', 20)
    pdf.set_text_color(0, 100, 0)
    
    target_label = "ขนาดท่อ/ราง ที่ใช้" if "สูงสุด" in mode_name else ("ขนาดท่อที่แนะนำ" if "Conduit" in mode_name else "ขนาดรางที่แนะนำ")
    pdf.cell(100, 10, f"{target_label}:", 0)
    pdf.cell(0, 10, f"{result_name}", 0, 1)
    
    pdf.set_x(15)
    pdf.set_font('Thai' if has_font else 'Arial', '', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(100, 8, f"คิดเป็นพื้นที่ใช้งาน (Fill Factor):", 0)
    pdf.cell(0, 8, f"{percent_fill}", 0, 1)
    
    pdf.ln(15)
    
    # 6. Signature (Center Aligned)
    current_y = pdf.get_y()
    if current_y < 230:
        pdf.set_y(230) 
    else:
        pdf.ln(10)
        
    pdf.set_font('Thai' if has_font else 'Arial', '', 14)
    
    insp_n = inspector_name if inspector_name.strip() else ""
    insp_p = inspector_pos if inspector_pos.strip() else ""

    center_x = 160 
    box_width = 70 
    start_x = center_x - (box_width / 2)
    
    # 1. หัวข้อ
    pdf.set_x(start_x)
    pdf.cell(box_width, 8, "ผู้ตรวจสอบ", 0, 1, 'C')
    
    # 2. พื้นที่เซ็น
    pdf.ln(10)
    pdf.set_draw_color(0, 0, 0) 
    line_y = pdf.get_y()
    pdf.line(center_x - 20, line_y, center_x + 20, line_y) 
    pdf.ln(2)
    
    # 3. ชื่อ
    pdf.set_x(start_x)
    if insp_n:
        pdf.cell(box_width, 8, f"({insp_n})", 0, 1, 'C')
    else:
        pdf.cell(box_width, 8, "(......................................................)", 0, 1, 'C')
        
    # 4. ตำแหน่ง
    pdf.set_x(start_x)
    if insp_p:
        pdf.cell(box_width, 8, insp_p, 0, 1, 'C')
    else:
        pdf.cell(box_width, 8, "......................................................", 0, 1, 'C')
    
    return bytes(pdf.output())

# --- UI Setup ---
st.set_page_config(page_title="โปรแกรมคำนวณสายไฟ", layout="wide")

st.title("⚡ โปรแกรมคำนวณท่อร้อยสาย & Wire Way")

# --- คำนวณเวลาไทย (Auto) ---
bkk_now = get_thai_time()
formatted_date_str = bkk_now.strftime("%d/%m/%Y %H:%M")

with st.sidebar:
    st.header("⚙️ ตั้งค่า Report (PDF)")
    uploaded_logo = st.file_uploader("อัปโหลดโลโก้ (หัวกระดาษ)", type=['png', 'jpg', 'jpeg'])
    st.write("---")
    inspector_name = st.text_input("ชื่อผู้ตรวจสอบ", placeholder="เช่น นายสมชาย ใจดี", value="นายสมหมาย อะไรเอ่ย")
    inspector_pos = st.text_input("ตำแหน่ง", placeholder="เช่น วิศวกรไฟฟ้า", value="พนักงานตรวจสอบ 1")
    st.info("ℹ️ รายชื่อจะแสดงกึ่งกลางท้ายกระดาษ")
    
    # (เอา Date picker ออกแล้ว)

if 'wire_db' not in st.session_state: st.session_state['wire_db'] = load_data()
if 'is_admin' not in st.session_state: st.session_state['is_admin'] = False
if 'conduit_rows' not in st.session_state: st.session_state['conduit_rows'] = [{'id': 0}]
if 'conduit_counter' not in st.session_state: st.session_state['conduit_counter'] = 1
if 'wireway_rows' not in st.session_state: st.session_state['wireway_rows'] = [{'id': 0}]
if 'wireway_counter' not in st.session_state: st.session_state['wireway_counter'] = 1

tab1, tab2, tab3, tab4 = st.tabs(["⚪ ท่อร้อยสาย", "⬜ รางเดินสาย", "ℹ️ ข้อมูล", "🛠️ Admin"])

# ==========================================
# Tab 1: ท่อร้อยสาย
# ==========================================
with tab1:
    st.header("⚪ คำนวณท่อร้อยสาย (40%)")
    mode = st.radio("โหมด:", ["🅰️ คำนวณขนาดท่อ (Mix)", "🅱️ หาจำนวนสาย (Single)"], key="c_mode")
    st.write("---")

    if mode.startswith("🅰️"):
        selected_wires = []
        for i, row in enumerate(st.session_state['conduit_rows']):
            c1, c2, c3, c4 = st.columns([2.5, 1.5, 1.5, 0.5])
            with c1: w_type = st.selectbox(f"สาย #{i+1}", list(st.session_state['wire_db'].keys()), key=f"ct_{row['id']}")
            with c2: w_sz = st.selectbox(f"ขนาด #{i+1}", [w['sz'] for w in st.session_state['wire_db'][w_type]], key=f"cs_{row['id']}")
            with c3: w_qty = st.number_input(f"จำนวน #{i+1}", 1, key=f"cq_{row['id']}")
            with c4: 
                if len(st.session_state['conduit_rows']) > 1 and st.button("🗑️", key=f"cd_{row['id']}"):
                    st.session_state['conduit_rows'].pop(i); st.rerun()
            area, _ = calc_wire_area(w_type, w_sz, w_qty, st.session_state['wire_db'])
            selected_wires.append({'type': w_type, 'sz': w_sz, 'qty': w_qty, 'area': area})

        if st.button("➕ เพิ่มสาย"): 
            st.session_state['conduit_rows'].append({'id': st.session_state['conduit_counter']}); st.session_state['conduit_counter'] += 1; st.rerun()
        
        st.write("---")
        if st.button("🚀 คำนวณ", type="primary"):
            total_area = sum(w['area'] for w in selected_wires)
            st.info(f"พื้นที่รวม: **{total_area:.2f} sq.mm.**")
            
            best_c = None
            results = []
            for c in CONDUITS:
                c_area = math.pi * ((c['id']/2)**2)
                limit = c_area * 0.40
                pct = (total_area/c_area)*100
                status = "✅" if total_area <= limit else "❌"
                if total_area <= limit and best_c is None: best_c = c
                results.append({"ขนาด": c['size'], "ใช้จริง": f"{pct:.2f}%", "ผล": status})
            
            if best_c:
                st.success(f"✅ แนะนำ: **{best_c['size']}**")
                
                # PDF Generation (Mode A)
                pdf_bytes = create_pdf(
                    selected_wires, 
                    total_area, 
                    best_c['size'], 
                    f"{(total_area/(math.pi*(best_c['id']/2)**2)*100):.2f}%", 
                    "ท่อร้อยสาย (Conduit) - คำนวณขนาด",
                    logo_upload=uploaded_logo,
                    inspector_name=inspector_name,
                    inspector_pos=inspector_pos,
                    custom_date_str=formatted_date_str
                )
                st.download_button("📄 ดาวน์โหลด PDF Report", data=pdf_bytes, file_name="conduit_report_size.pdf", mime="application/pdf")
            else: st.error("ไม่มีท่อรองรับ")
            st.dataframe(pd.DataFrame(results), hide_index=True)
            
    else:
        # Mode B: Conduit
        c1, c2 = st.columns(2)
        with c1: wt = st.selectbox("สาย", list(st.session_state['wire_db'].keys()))
        with c2: ws = st.selectbox("ขนาด", [w['sz'] for w in st.session_state['wire_db'][wt]])
        cp = st.selectbox("เลือกท่อ", [c['size'] for c in CONDUITS])
        
        if st.button("คำนวณจำนวนสูงสุด"):
            # 1. คำนวณ
            wire_area, od = calc_wire_area(wt, ws, 1, st.session_state['wire_db']) # พื้นที่ต่อ 1 เส้น
            pid = next(c['id'] for c in CONDUITS if c['size']==cp)
            conduit_total_area = math.pi*((pid/2)**2)
            usable_area = conduit_total_area * 0.40
            
            max_w = math.floor(usable_area / wire_area)
            st.success(f"ได้สูงสุด: {max_w} เส้น")
            
            # 2. สร้าง PDF Report
            if max_w > 0:
                total_used_area = wire_area * max_w
                pct = (total_used_area / conduit_total_area) * 100
                
                # เตรียมข้อมูลใส่ตาราง (1 รายการ)
                wires_for_pdf = [{'type': wt, 'sz': ws, 'qty': max_w, 'area': total_used_area}]
                
                pdf_bytes = create_pdf(
                    wires_for_pdf, 
                    total_used_area, 
                    cp, 
                    f"{pct:.2f}%", 
                    "ท่อร้อยสาย (Conduit) - หาจำนวนสายสูงสุด",
                    logo_upload=uploaded_logo,
                    inspector_name=inspector_name,
                    inspector_pos=inspector_pos,
                    custom_date_str=formatted_date_str
                )
                st.download_button("📄 ดาวน์โหลด PDF Report", data=pdf_bytes, file_name="conduit_report_max.pdf", mime="application/pdf")

# ==========================================
# Tab 2: Wireway
# ==========================================
with tab2:
    st.header("⬜ คำนวณรางเดินสาย (20%)")
    mode_w = st.radio("โหมด:", ["🅰️ หาราง (Mix)", "🅱️ หาจำนวน (Single)"], key="w_mode")
    st.write("---")

    if mode_w.startswith("🅰️"):
        sel_ww_wires = []
        for i, row in enumerate(st.session_state['wireway_rows']):
            c1, c2, c3, c4 = st.columns([2.5, 1.5, 1.5, 0.5])
            with c1: wt = st.selectbox(f"สาย #{i+1}", list(st.session_state['wire_db'].keys()), key=f"wt_{row['id']}")
            with c2: ws = st.selectbox(f"ขนาด #{i+1}", [w['sz'] for w in st.session_state['wire_db'][wt]], key=f"ws_{row['id']}")
            with c3: wq = st.number_input(f"จำนวน #{i+1}", 1, key=f"wq_{row['id']}")
            with c4:
                 if len(st.session_state['wireway_rows']) > 1 and st.button("🗑️", key=f"wd_{row['id']}"):
                    st.session_state['wireway_rows'].pop(i); st.rerun()
            area, _ = calc_wire_area(wt, ws, wq, st.session_state['wire_db'])
            sel_ww_wires.append({'type': wt, 'sz': ws, 'qty': wq, 'area': area})

        if st.button("➕ เพิ่มสาย", key="add_ww"): 
            st.session_state['wireway_rows'].append({'id': st.session_state['wireway_counter']}); st.session_state['wireway_counter'] += 1; st.rerun()

        st.write("---")
        if st.button("🚀 คำนวณ", type="primary", key="cal_ww"):
            tot_area = sum(w['area'] for w in sel_ww_wires)
            st.info(f"พื้นที่รวม: **{tot_area:.2f} sq.mm.**")
            
            best_ww = None
            res_ww = []
            for w in WIREWAYS:
                limit = w['area'] * 0.20
                pct = (tot_area/w['area'])*100
                stt = "✅" if tot_area <= limit else "❌"
                if tot_area <= limit and best_ww is None: best_ww = w
                res_ww.append({"ขนาด": w['size'], "ใช้จริง": f"{pct:.2f}%", "ผล": stt})
            
            if best_ww:
                st.success(f"✅ แนะนำ: **{best_ww['size']}**")
                
                # PDF Generation (Mode A)
                pdf_bytes = create_pdf(
                    sel_ww_wires, 
                    tot_area, 
                    best_ww['size'], 
                    f"{(tot_area/best_ww['area']*100):.2f}%", 
                    "รางเดินสาย (Wireway) - คำนวณขนาด",
                    logo_upload=uploaded_logo,
                    inspector_name=inspector_name,
                    inspector_pos=inspector_pos,
                    custom_date_str=formatted_date_str
                )
                st.download_button("📄 ดาวน์โหลด PDF Report", data=pdf_bytes, file_name="wireway_report_size.pdf", mime="application/pdf")
            else: st.error("ไม่มีรางรองรับ")
            st.dataframe(pd.DataFrame(res_ww), hide_index=True)
            
    else:
        # Mode B: Wireway
        c1, c2 = st.columns(2)
        with c1: wt = st.selectbox("สาย", list(st.session_state['wire_db'].keys()), key="wwb_t")
        with c2: ws = st.selectbox("ขนาด", [w['sz'] for w in st.session_state['wire_db'][wt]], key="wwb_s")
        ww_sel = st.selectbox("เลือกราง", [w['size'] for w in WIREWAYS])
        
        if st.button("คำนวณจำนวนสูงสุด", key="wwb_btn"):
            # 1. คำนวณ
            wire_area, od = calc_wire_area(wt, ws, 1, st.session_state['wire_db'])
            ww_area = next(w['area'] for w in WIREWAYS if w['size']==ww_sel)
            usable_area = ww_area * 0.20
            
            max_w = math.floor(usable_area / wire_area)
            st.success(f"ได้สูงสุด: {max_w} เส้น")
            
            # 2. สร้าง PDF Report
            if max_w > 0:
                total_used_area = wire_area * max_w
                pct = (total_used_area / ww_area) * 100
                
                wires_for_pdf = [{'type': wt, 'sz': ws, 'qty': max_w, 'area': total_used_area}]
                
                pdf_bytes = create_pdf(
                    wires_for_pdf, 
                    total_used_area, 
                    ww_sel, 
                    f"{pct:.2f}%", 
                    "รางเดินสาย (Wireway) - หาจำนวนสายสูงสุด",
                    logo_upload=uploaded_logo,
                    inspector_name=inspector_name,
                    inspector_pos=inspector_pos,
                    custom_date_str=formatted_date_str
                )
                st.download_button("📄 ดาวน์โหลด PDF Report", data=pdf_bytes, file_name="wireway_report_max.pdf", mime="application/pdf")

# --- Tab 3, 4 (เหมือนเดิม) ---
with tab3:
    st.header("📚 ข้อมูลจำเพาะทางเทคนิค")
    st.write("เลือกชนิดสายไฟเพื่อดูรายละเอียด")
    
    selected_wire_type = st.selectbox("เลือกชนิดสายไฟ:", list(WIRE_SPECS.keys()))
    inf = WIRE_SPECS[selected_wire_type]
    
    st.markdown("---")
    
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        if os.path.exists(inf['img']):
            st.image(inf['img'], caption=selected_wire_type, use_container_width=True)
        else:
            st.warning(f"⚠️ ไม่พบไฟล์รูปภาพ: {inf['img']}")
            
    with c2:
        st.subheader(f"📌 {selected_wire_type}")
        st.info(inf['desc']) 
        
        st.markdown("#### ⚙️ คุณสมบัติ:")
        st.markdown(f"**📜 มาตรฐาน:** {inf['std']}")
        st.markdown(f"**⚡ พิกัดแรงดัน:** {inf['volt']}")
        st.markdown(f"**🌡️ อุณหภูมิใช้งาน:** {inf['temp']}")
        st.markdown(f"**🛡️ ฉนวน:** {inf['insulation']}")
        
        st.markdown("#### 🛠️ ลักษณะการติดตั้ง:")
        for item in inf['usage']:
            if "❌" in item:
                st.error(item.replace("❌", "").strip(), icon="❌")
            else:
                st.success(item.replace("✅", "").strip(), icon="✅")

with tab4:
    st.header("Admin")
    if not st.session_state['is_admin']:
        if st.button("Login") and st.text_input("Pwd", type="password") == ADMIN_PASSWORD:
            st.session_state['is_admin'] = True; st.rerun()
    else:
        if st.button("Logout"): st.session_state['is_admin'] = False; st.rerun()
        edt = st.selectbox("Table", list(st.session_state['wire_db'].keys()))
        df = pd.DataFrame(st.session_state['wire_db'][edt])
        new_d = st.data_editor(df, num_rows="dynamic")
        if st.button("Save"): st.session_state['wire_db'][edt] = new_d.to_dict('records'); save_data(st.session_state['wire_db']); st.success("Saved")