import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Executive Dashboard & Business Planning 2027", layout="wide")

st.title("📊 ระบบบริหารงานและวิเคราะห์ข้อมูลลูกค้าเชิงลึก (แผนปี 2027)")
st.markdown("ระบบวิเคราะห์ยอดซื้อ ลูกค้าเก่า/ใหม่ ลูกค้าที่หายไป แยกตามสาขาและกลุ่มสินค้า (แสดงผลหน่วย: ล้านบาท / Mb)")

# --- ฟังก์ชันแปลงหน่วยเป็น ล้านบาท (Mb) ---
def format_mb(val):
    if pd.isna(val):
        return "0.00 Mb"
    return f"{val / 1_000_000:,.2f} Mb"

# --- 1. ส่วนอัปโหลดไฟล์ข้อมูล ---
st.sidebar.header("📁 1. อัปโหลดข้อมูล (CSV)")
uploaded_files = st.sidebar.file_uploader(
    "อัปโหลดไฟล์ข้อมูล (เช่น ลูกค้า 2025, 2026, หรือ พ.ย.-ธ.ค.)", 
    type=["csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    dfs_dict = {}
    data_list = []
    
    for file in uploaded_files:
        file.seek(0)
        df_temp = pd.read_csv(file)
        dfs_dict[file.name] = df_temp
        data_list.append(df_temp)
        
    df_all = pd.concat(data_list, ignore_index=True)
    
    required_cols = ['custcode', 'custname', 'saleareacode', 'กลุ่มสินค้า', 'ประเภทลูกค้า', 'รวม']
    missing_cols = [col for col in required_cols if col not in df_all.columns]
    
    if missing_cols:
        st.error(f"⚠️ ไฟล์ข้อมูลของคุณขาดคอลัมน์สำคัญเหล่านี้: {missing_cols}")
    else:
        # --- 2. ตัวกรองข้อมูล (Filters - แบบเลือกได้หลายช่อง) ---
        st.sidebar.header("🔍 2. ตัวกรองข้อมูล (เลือกได้หลายช่อง)")
        
        branches = sorted([str(x) for x in df_all['saleareacode'].dropna().unique()])
        selected_branches = st.sidebar.multiselect("เลือกสาขา (Sales Area)", branches, default=branches)
        
        cust_types = sorted([str(x) for x in df_all['ประเภทลูกค้า'].dropna().unique()])
        selected_cust_types = st.sidebar.multiselect("ประเภทลูกค้า", cust_types, default=cust_types)
        
        product_groups = sorted([str(x) for x in df_all['กลุ่มสินค้า'].dropna().unique()])
        selected_prod_groups = st.sidebar.multiselect("กลุ่มสินค้า", product_groups, default=product_groups)
        
        # กรองข้อมูลตามที่เลือก
        df_filtered = df_all.copy()
        if selected_branches:
            df_filtered = df_filtered[df_filtered['saleareacode'].astype(str).isin(selected_branches)]
        if selected_cust_types:
            df_filtered = df_filtered[df_filtered['ประเภทลูกค้า'].astype(str).isin(selected_cust_types)]
        if selected_prod_groups:
            df_filtered = df_filtered[df_filtered['กลุ่มสินค้า'].astype(str).isin(selected_prod_groups)]

        # --- 3. แสดงเนื้อหาหลัก (Dashboard Tabs) ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 ภาพรวมยอดขาย (Overview)", 
            "👥 วิเคราะห์ลูกค้า (New/Lost/Growth)", 
            "📦 วิเคราะห์กลุ่มสินค้า", 
            "🏢 เปรียบเทียบรายสาขา"
        ])
        
        # --- TAB 1 ---
        with tab1:
            st.subheader("📌 สรุปยอดขายรวมทั้งหมด (หน่วย: ล้านบาท)")
            total_rev = df_filtered['รวม'].sum()
            total_cash = df_filtered['CASH'].sum() if 'CASH' in df_filtered.columns else 0
            total_credit = df_filtered['CREDIT'].sum() if 'CREDIT' in df_filtered.columns else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("ยอดขายรวมสุทธิ", format_mb(total_rev))
            col2.metric("ยอดเงินสด (CASH)", format_mb(total_cash))
            col3.metric("ยอดสินเชื่อ (CREDIT)", format_mb(total_credit))
            
            st.divider()
            st.subheader("🏆 ลูกค้าที่มียอดซื้อสูงสุด 20 อันดับแรก")
            top_customers = df_filtered.groupby(['custcode', 'custname', 'saleareacode', 'ประเภทลูกค้า'])['รวม'].sum().reset_index()
            top_customers = top_customers.sort_values(by='รวม', ascending=False).head(20)
            top_customers['ยอดซื้อ (Mb)'] = top_customers['รวม'].apply(format_mb)
            
            display_top = top_customers[['custcode', 'custname', 'saleareacode', 'ประเภทลูกค้า', 'ยอดซื้อ (Mb)']]
            st.dataframe(display_top, use_container_width=True)

        # --- TAB 2 ---
        with tab2:
            st.subheader("👥 การเคลื่อนไหวของลูกค้า (Customer Movement Analysis)")
            st.markdown("เปรียบเทียบระหว่าง 2 ไฟล์ (เช่น เทียบปี 2025 และ 2026) พร้อมคำนวณ % การเติบโต")
            
            file_names = list(dfs_dict.keys())
            if len(file_names) >= 2:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    base_file_name = st.selectbox("เลือกไฟล์ฐานเดิม (ปีก่อน / 2025)", file_names, index=0)
                with col_f2:
                    comp_file_name = st.selectbox("เลือกไฟล์เปรียบเทียบ (ปีปัจจุบัน / 2026)", file_names, index=1 if len(file_names)>1 else 0)
                
                df_base = dfs_dict[base_file_name]
                df_comp = dfs_dict[comp_file_name]
                
                base_cust = df_base.groupby(['custcode', 'custname'])['รวม'].sum().reset_index().rename(columns={'รวม': 'ยอดซื้อปีก่อน'})
                comp_cust = df_comp.groupby(['custcode', 'custname'])['รวม'].sum().reset_index().rename(columns={'รวม': 'ยอดซื้อปีปัจจุบัน'})
                
                merged_cust = pd.merge(base_cust, comp_cust, on=['custcode', 'custname'], how='outer').fillna(0)
                
                def classify_customer(row):
                    if row['ยอดซื้อปีก่อน'] == 0:
                        return 'ลูกค้าใหม่ (New)'
                    elif row['ยอดซื้อปีปัจจุบัน'] == 0:
                        return 'ลูกค้าที่หายไป (Churned)'
                    elif row['ยอดซื้อปีปัจจุบัน'] > row['ยอดซื้อปีก่อน']:
                        return 'ลูกค้าเติบโตขึ้น (Growth)'
                    else:
                        return 'ลูกค้ายอดลดลง (Decline)'
                        
                merged_cust['สถานะลูกค้า'] = merged_cust.apply(classify_customer, axis=1)
                merged_cust['ผลต่างยอดซื้อ'] = merged_cust['ยอดซื้อปีปัจจุบัน'] - merged_cust['ยอดซื้อปีก่อน']
                
                # คำนวณ % Growth (ป้องกันการหารด้วย 0)
                merged_cust['% Growth'] = np.where(
                    merged_cust['ยอดซื้อปีก่อน'] > 0, 
                    ((merged_cust['ยอดซื้อปีปัจจุบัน'] - merged_cust['ยอดซื้อปีก่อน']) / merged_cust['ยอดซื้อปีก่อน']) * 100, 
                    100.0 if merged_cust['ยอดซื้อปีปัจจุบัน'] > 0 else 0.0
                )
                
                # แปลงหน่วยเป็น Mb เพื่อการแสดงผล
                merged_cust['ยอดปีก่อน (Mb)'] = merged_cust['ยอดซื้อปีก่อน'].apply(format_mb)
                merged_cust['ยอดปีปัจจุบัน (Mb)'] = merged_cust['ยอดซื้อปีปัจจุบัน'].apply(format_mb)
                merged_cust['ผลต่าง (Mb)'] = merged_cust['ผลต่างยอดซื้อ'].apply(format_mb)
                merged_cust['% Growth'] = merged_cust['% Growth'].map('{:,.2f}%'.format)
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("ลูกค้าใหม่", len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้าใหม่ (New)']))
                c2.metric("ลูกค้าที่หายไป", len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้าที่หายไป (Churned)']))
                c3.metric("ลูกค้าเติบโตขึ้น", len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้าเติบโตขึ้น (Growth)']))
                c4.metric("ลูกค้ายอดลดลง", len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้ายอดลดลง (Decline)']))
                
                st.markdown("---")
                status_filter = st.selectbox("กรองดูตามสถานะลูกค้า:", ['ทั้งหมด', 'ลูกค้าใหม่ (New)', 'ลูกค้าที่หายไป (Churned)', 'ลูกค้าเติบโตขึ้น (Growth)', 'ลูกค้ายอดลดลง (Decline)'])
                
                if status_filter != 'ทั้งหมด':
                    display_df = merged_cust[merged_cust['สถานะลูกค้า'] == status_filter]
                else:
                    display_df = merged_cust
                    
                final_display_cols = ['custcode', 'custname', 'สถานะลูกค้า', 'ยอดปีก่อน (Mb)', 'ยอดปีปัจจุบัน (Mb)', 'ผลต่าง (Mb)', '% Growth']
                st.dataframe(display_df[final_display_cols].sort_values(by='ผลต่างยอดซื้อ', ascending=False), use_container_width=True)
            else:
                st.info("💡 กรุณาอัปโหลดไฟล์ CSV อย่างน้อย 2 ไฟล์ขึ้นไป เพื่อเปิดใช้งานฟังก์ชันวิเคราะห์ลูกค้าใหม่/ลูกค้าหาย")

        # --- TAB 3 ---
        with tab3:
            st.subheader("📦 วิเคราะห์ยอดขายตามกลุ่มสินค้า (หน่วย: ล้านบาท)")
            prod_summary = df_filtered.groupby('กลุ่มสินค้า')['รวม'].sum().reset_index()
            prod_summary = prod_summary.sort_values(by='รวม', ascending=False)
            prod_summary['ยอดขาย (Mb)'] = prod_summary['รวม'].apply(format_mb)
            
            col_p1, col_p2 = st.columns([2, 1])
            with col_p1:
                st.dataframe(prod_summary[['กลุ่มสินค้า', 'ยอดขาย (Mb)']], use_container_width=True)
            with col_p2:
                st.markdown("### คำแนะนำสำหรับแผนปี 2027")
                st.info("ใช้ตรวจสอบสัดส่วนยอดขายรายกลุ่มสินค้าแบบหลายตัวเลือก เพื่อนำไปวางแผนสต็อกสินค้าและเป้าหมายการขายปีหน้าได้อย่างแม่นยำ")

        # --- TAB 4 ---
        with tab4:
            st.subheader("🏢 ผลการดำเนินงานแยกตามสาขา (Sales Area)")
            if 'saleareacode' in df_filtered.columns:
                branch_summary = df_filtered.groupby('saleareacode')['รวม'].sum().reset_index()
                branch_summary = branch_summary.sort_values(by='รวม', ascending=False)
                branch_summary['ยอดขาย (Mb)'] = branch_summary['รวม'].apply(format_mb)
                
                st.dataframe(branch_summary[['saleareacode', 'ยอดขาย (Mb)']], use_container_width=True)
                
                st.markdown("### เจาะลึกรายสาขาและกลุ่มสินค้า")
                branch_prod = df_filtered.groupby(['saleareacode', 'กลุ่มสินค้า'])['รวม'].sum().reset_index()
                branch_prod['ยอดขาย (Mb)'] = branch_prod['รวม'].apply(format_mb)
                st.dataframe(branch_prod[['saleareacode', 'กลุ่มสินค้า', 'ยอดขาย (Mb)']], use_container_width=True)

else:
    st.info("💡 โปรดอัปโหลดไฟล์ข้อมูล CSV ของคุณที่แถบด้านข้างซ้าย เพื่อเริ่มต้นใช้งานแอปพลิเคชัน")import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Executive Dashboard & Business Planning 2027", layout="wide")

st.title("📊 ระบบบริหารงานและวิเคราะห์ข้อมูลลูกค้าเชิงลึก (แผนปี 2027)")
st.markdown("ระบบวิเคราะห์ยอดซื้อ ลูกค้าเก่า/ใหม่ ลูกค้าที่หายไป แยกตามสาขาและกลุ่มสินค้า")

# --- 1. ส่วนอัปโหลดไฟล์ข้อมูล ---
st.sidebar.header("📁 1. อัปโหลดข้อมูล (CSV)")
uploaded_files = st.sidebar.file_uploader(
    "อัปโหลดไฟล์ข้อมูล (เช่น ลูกค้า 2025, 2026, หรือ พ.ย.-ธ.ค.)", 
    type=["csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    # โหลดไฟล์เก็บไว้ใน Dictionary เพื่อป้องกัน Error อ่านไฟล์ซ้ำ
    dfs_dict = {}
    data_list = []
    
    for file in uploaded_files:
        file.seek(0) # รีเซ็ตตำแหน่งไฟล์
        df_temp = pd.read_csv(file)
        dfs_dict[file.name] = df_temp
        data_list.append(df_temp)
        
    df_all = pd.concat(data_list, ignore_index=True)
    
    required_cols = ['custcode', 'custname', 'saleareacode', 'กลุ่มสินค้า', 'ประเภทลูกค้า', 'รวม']
    missing_cols = [col for col in required_cols if col not in df_all.columns]
    
    if missing_cols:
        st.error(f"⚠️ ไฟล์ข้อมูลของคุณขาดคอลัมน์สำคัญเหล่านี้: {missing_cols}")
    else:
        # --- 2. ตัวกรองข้อมูล (Filters) ---
        st.sidebar.header("🔍 2. ตัวกรองข้อมูล (Filters)")
        
        branches = ['ทุกสาขา'] + sorted([str(x) for x in df_all['saleareacode'].dropna().unique()])
        selected_branch = st.sidebar.selectbox("เลือกสาขา (Sales Area)", branches)
        
        cust_types = ['ทั้งหมด'] + sorted([str(x) for x in df_all['ประเภทลูกค้า'].dropna().unique()])
        selected_cust_type = st.sidebar.selectbox("ประเภทลูกค้า", cust_types)
        
        product_groups = ['ทุกกลุ่มสินค้า'] + sorted([str(x) for x in df_all['กลุ่มสินค้า'].dropna().unique()])
        selected_prod_group = st.sidebar.selectbox("กลุ่มสินค้า", product_groups)
        
        df_filtered = df_all.copy()
        if selected_branch != 'ทุกสาขา':
            df_filtered = df_filtered[df_filtered['saleareacode'].astype(str) == selected_branch]
        if selected_cust_type != 'ทั้งหมด':
            df_filtered = df_filtered[df_filtered['ประเภทลูกค้า'].astype(str) == selected_cust_type]
        if selected_prod_group != 'ทุกกลุ่มสินค้า':
            df_filtered = df_filtered[df_filtered['กลุ่มสินค้า'].astype(str) == selected_prod_group]

        # --- 3. แสดงเนื้อหาหลัก (Dashboard Tabs) ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 ภาพรวมยอดขาย (Overview)", 
            "👥 วิเคราะห์ลูกค้า (New/Lost/Growth)", 
            "📦 วิเคราะห์กลุ่มสินค้า", 
            "🏢 เปรียบเทียบรายสาขา"
        ])
        
        # --- TAB 1 ---
        with tab1:
            st.subheader("📌 สรุปยอดขายรวมทั้งหมด")
            total_rev = df_filtered['รวม'].sum()
            total_cash = df_filtered['CASH'].sum() if 'CASH' in df_filtered.columns else 0
            total_credit = df_filtered['CREDIT'].sum() if 'CREDIT' in df_filtered.columns else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("ยอดขายรวมสุทธิ", f"{total_rev:,.2f} บาท")
            col2.metric("ยอดเงินสด (CASH)", f"{total_cash:,.2f} บาท")
            col3.metric("ยอดสินเชื่อ (CREDIT)", f"{total_credit:,.2f} บาท")
            
            st.divider()
            st.subheader("🏆 ลูกค้าที่มียอดซื้อสูงสุด 20 อันดับแรก")
            top_customers = df_filtered.groupby(['custcode', 'custname', 'saleareacode', 'ประเภทลูกค้า'])['รวม'].sum().reset_index()
            top_customers = top_customers.sort_values(by='รวม', ascending=False).head(20)
            st.dataframe(top_customers, use_container_width=True)

        # --- TAB 2 ---
        with tab2:
            st.subheader("👥 การเคลื่อนไหวของลูกค้า (Customer Movement Analysis)")
            st.markdown("ส่วนนี้ใช้สำหรับวิเคราะห์เปรียบเทียบระหว่างชุดข้อมูล (เช่น เทียบปี 2025 และ 2026 เพื่อดูว่าลูกค้ากลุ่มไหนโต หายไป หรือเป็นลูกค้าใหม่)")
            
            file_names = list(dfs_dict.keys())
            if len(file_names) >= 2:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    base_file_name = st.selectbox("เลือกไฟล์ฐานเดิม (ปีก่อน / 2025)", file_names, index=0)
                with col_f2:
                    comp_file_name = st.selectbox("เลือกไฟล์เปรียบเทียบ (ปีปัจจุบัน / 2026)", file_names, index=1 if len(file_names)>1 else 0)
                
                df_base = dfs_dict[base_file_name]
                df_comp = dfs_dict[comp_file_name]
                
                base_cust = df_base.groupby(['custcode', 'custname'])['รวม'].sum().reset_index().rename(columns={'รวม': 'ยอดซื้อปีก่อน'})
                comp_cust = df_comp.groupby(['custcode', 'custname'])['รวม'].sum().reset_index().rename(columns={'รวม': 'ยอดซื้อปีปัจจุบัน'})
                
                merged_cust = pd.merge(base_cust, comp_cust, on=['custcode', 'custname'], how='outer').fillna(0)
                
                def classify_customer(row):
                    if row['ยอดซื้อปีก่อน'] == 0:
                        return 'ลูกค้าใหม่ (New)'
                    elif row['ยอดซื้อปีปัจจุบัน'] == 0:
                        return 'ลูกค้าที่หายไป (Churned)'
                    elif row['ยอดซื้อปีปัจจุบัน'] > row['ยอดซื้อปีก่อน']:
                        return 'ลูกค้าเติบโตขึ้น (Growth)'
                    else:
                        return 'ลูกค้ายอดลดลง (Decline)'
                        
                merged_cust['สถานะลูกค้า'] = merged_cust.apply(classify_customer, axis=1)
                merged_cust['ผลต่างยอดซื้อ'] = merged_cust['ยอดซื้อปีปัจจุบัน'] - merged_cust['ยอดซื้อปีก่อน']
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("ลูกค้าใหม่", len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้าใหม่ (New)']))
                c2.metric("ลูกค้าที่หายไป", len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้าที่หายไป (Churned)']))
                c3.metric("ลูกค้าเติบโตขึ้น", len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้าเติบโตขึ้น (Growth)']))
                c4.metric("ลูกค้ายอดลดลง", len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้ายอดลดลง (Decline)']))
                
                st.markdown("---")
                status_filter = st.selectbox("กรองดูตามสถานะลูกค้า:", ['ทั้งหมด', 'ลูกค้าใหม่ (New)', 'ลูกค้าที่หายไป (Churned)', 'ลูกค้าเติบโตขึ้น (Growth)', 'ลูกค้ายอดลดลง (Decline)'])
                
                if status_filter != 'ทั้งหมด':
                    display_df = merged_cust[merged_cust['สถานะลูกค้า'] == status_filter]
                else:
                    display_df = merged_cust
                    
                st.dataframe(display_df.sort_values(by='ผลต่างยอดซื้อ', ascending=False), use_container_width=True)
            else:
                st.info("💡 กรุณาอัปโหลดไฟล์ CSV อย่างน้อย 2 ไฟล์ขึ้นไป (เช่น ไฟล์ปี 2025 และ 2026) เพื่อเปิดใช้งานฟังก์ชันวิเคราะห์ลูกค้าใหม่/ลูกค้าหาย")

        # --- TAB 3 ---
        with tab3:
            st.subheader("📦 วิเคราะห์ยอดขายและการเติบโตตามกลุ่มสินค้า")
            prod_summary = df_filtered.groupby('กลุ่มสินค้า')['รวม'].sum().reset_index()
            prod_summary = prod_summary.sort_values(by='รวม', ascending=False)
            
            col_p1, col_p2 = st.columns([2, 1])
            with col_p1:
                st.dataframe(prod_summary, use_container_width=True)
            with col_p2:
                st.markdown("### คำแนะนำสำหรับแผนปี 2027")
                st.info("คุณสามารถดูสัดส่วนกลุ่มสินค้าที่ทำยอดขายสูงสุด เพื่อนำไปวางแผนสต็อกสินค้าและการทำโปรโมชั่นกระตุ้นยอดขายในปีถัดไป")

        # --- TAB 4 ---
        with tab4:
            st.subheader("🏢 ผลการดำเนินงานแยกตามสาขา (Sales Area)")
            if 'saleareacode' in df_filtered.columns:
                branch_summary = df_filtered.groupby('saleareacode')['รวม'].sum().reset_index()
                branch_summary = branch_summary.sort_values(by='รวม', ascending=False)
                st.dataframe(branch_summary, use_container_width=True)
                
                st.markdown("### เจาะลึกรายสาขาและกลุ่มสินค้า")
                branch_prod = df_filtered.groupby(['saleareacode', 'กลุ่มสินค้า'])['รวม'].sum().reset_index()
                st.dataframe(branch_prod, use_container_width=True)

else:
    st.info("💡 โปรดอัปโหลดไฟล์ข้อมูล CSV ของคุณที่แถบด้านข้างซ้าย เพื่อเริ่มต้นใช้งานแอปพลิเคชัน")
