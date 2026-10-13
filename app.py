import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Executive Dashboard & Business Planning 2027", layout="wide")

st.title("📊 ระบบบริหารงานและวิเคราะห์ข้อมูลลูกค้าเชิงลึก (แผนปี 2027)")
st.markdown("ระบบวิเคราะห์ยอดซื้อ ลูกค้าเก่า/ใหม่/หายไป เปรียบเทียบ 3 ปี (2024-2026) แยกตามสาขาและกลุ่มสินค้า")

# --- ฟังก์ชันแสดงตัวเลขฉลาด (Smart Number Formatting) ---
def format_smart(val):
    if pd.isna(val) or val == 0:
        return "0.00"
    abs_val = abs(val)
    if abs_val >= 1_000_000:
        return f"{val / 1_000_000:,.2f} Mb"
    elif abs_val >= 1_000:
        return f"{val / 1_000:,.2f} K"
    else:
        return f"{val:,.2f}"

# --- 1. ส่วนอัปโหลดไฟล์ข้อมูล ---
st.sidebar.header("📁 1. อัปโหลดข้อมูล (CSV)")
uploaded_files = st.sidebar.file_uploader(
    "อัปโหลดไฟล์ข้อมูล (รองรับปี 2024, 2025, 2026 หรือรายเดือน)", 
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
        # --- 2. ตัวกรองข้อมูล (Filters - แบบเลือกหลายช่อง) ---
        st.sidebar.header("🔍 2. ตัวกรองข้อมูลหลัก (Link ถึงกัน)")
        
        branches = sorted([str(x) for x in df_all['saleareacode'].dropna().unique()])
        selected_branches = st.sidebar.multiselect("เลือกสาขา (Sales Area)", branches, default=branches)
        
        cust_types = sorted([str(x) for x in df_all['ประเภทลูกค้า'].dropna().unique()])
        selected_cust_types = st.sidebar.multiselect("ประเภทลูกค้า", cust_types, default=cust_types)
        
        product_groups = sorted([str(x) for x in df_all['กลุ่มสินค้า'].dropna().unique()])
        selected_prod_groups = st.sidebar.multiselect("กลุ่มสินค้า", product_groups, default=product_groups)
        
        # กรองข้อมูลภาพรวม
        df_filtered = df_all.copy()
        if selected_branches:
            df_filtered = df_filtered[df_filtered['saleareacode'].astype(str).isin(selected_branches)]
        if selected_cust_types:
            df_filtered = df_filtered[df_filtered['ประเภทลูกค้า'].astype(str).isin(selected_cust_types)]
        if selected_prod_groups:
            df_filtered = df_filtered[df_filtered['กลุ่มสินค้า'].astype(str).isin(selected_prod_groups)]

        # --- 3. แสดงเนื้อหาหลัก (Dashboard Tabs) ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 ภาพรวมยอดขาย & เปรียบเทียบปี", 
            "👥 วิเคราะห์ลูกค้าเชิงลึก (New/Lost/Growth)", 
            "📦 วิเคราะห์กลุ่มสินค้าเทียบปี", 
            "🏢 เปรียบเทียบรายสาขาเทียบปี"
        ])
        
        # --- TAB 1: ภาพรวมยอดขาย & แยกปี ---
        with tab1:
            st.subheader("📌 สรุปภาพรวมยอดขายสุทธิทั้งหมด")
            total_rev = df_filtered['รวม'].sum()
            total_cash = df_filtered['CASH'].sum() if 'CASH' in df_filtered.columns else 0
            total_credit = df_filtered['CREDIT'].sum() if 'CREDIT' in df_filtered.columns else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("ยอดขายรวมสุทธิ", format_smart(total_rev))
            col2.metric("ยอดเงินสด (CASH)", format_smart(total_cash))
            col3.metric("ยอดสินเชื่อ (CREDIT)", format_smart(total_credit))
            
            st.divider()
            st.subheader("📅 เปรียบเทียบยอดขายแยกตามไฟล์ข้อมูล (ตัวแทนรายปี)")
            
            # สรุปยอดตามชื่อไฟล์ (ซึ่งปกติจะแยกตามปี เช่น 2024, 2025, 2026)
            file_summary = []
            for fname, f_df in dfs_dict.items():
                # กรองตามฟิลเตอร์หลักด้วยเพื่อให้ข้อมูล Link กัน
                f_sub = f_df.copy()
                if selected_branches:
                    f_sub = f_sub[f_sub['saleareacode'].astype(str).isin(selected_branches)]
                if selected_cust_types:
                    f_sub = f_sub[f_sub['ประเภทลูกค้า'].astype(str).isin(selected_cust_types)]
                if selected_prod_groups:
                    f_sub = f_sub[f_sub['กลุ่มสินค้า'].astype(str).isin(selected_prod_groups)]
                
                sum_val = f_sub['รวม'].sum() if 'รวม' in f_sub.columns else 0
                file_summary.append({'ชื่อไฟล์ / ปี': fname, 'ยอดขายรวม': sum_val})
            
            df_file_sum = pd.DataFrame(file_summary)
            if not df_file_sum.empty:
                df_file_sum['ยอดขาย (Smart Format)'] = df_file_sum['ยอดขายรวม'].apply(format_smart)
                st.dataframe(df_file_sum[['ชื่อไฟล์ / ปี', 'ยอดขาย (Smart Format)']], use_container_width=True)
            
            st.subheader("🏆 ลูกค้าที่มียอดซื้อสูงสุด 20 อันดับแรก (ภายใต้ Filter ที่เลือก)")
            top_customers = df_filtered.groupby(['custcode', 'custname', 'saleareacode', 'ประเภทลูกค้า'])['รวม'].sum().reset_index()
            top_customers = top_customers.sort_values(by='รวม', ascending=False).head(20)
            top_customers['ยอดซื้อ'] = top_customers['รวม'].apply(format_smart)
            st.dataframe(top_customers[['custcode', 'custname', 'saleareacode', 'ประเภทลูกค้า', 'ยอดซื้อ']], use_container_width=True)

        # --- TAB 2: วิเคราะห์ลูกค้าเชิงลึก (New/Lost/Growth) ---
        with tab2:
            st.subheader("👥 การเคลื่อนไหวของลูกค้า (Customer Movement & Summary)")
            st.markdown("เลือก 2 ไฟล์เพื่อเทียบการเติบโต พร้อมสรุปสถิติจำนวนลูกค้าตาม Filter ที่เลือก")
            
            file_names = list(dfs_dict.keys())
            if len(file_names) >= 2:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    base_file_name = st.selectbox("เลือกไฟล์ฐานเดิม (เช่น 2024 หรือ 2025)", file_names, index=0)
                with col_f2:
                    comp_file_name = st.selectbox("เลือกไฟล์เปรียบเทียบ (เช่น 2025 หรือ 2026)", file_names, index=1 if len(file_names)>1 else 0)
                
                # ดึงข้อมูลมา Filter ตามที่ผู้ใช้เลือกใน Sidebar ก่อนนำมาเทียบ
                df_base_raw = dfs_dict[base_file_name]
                df_comp_raw = dfs_dict[comp_file_name]
                
                if selected_branches:
                    df_base_raw = df_base_raw[df_base_raw['saleareacode'].astype(str).isin(selected_branches)]
                    df_comp_raw = df_comp_raw[df_comp_raw['saleareacode'].astype(str).isin(selected_branches)]
                if selected_cust_types:
                    df_base_raw = df_base_raw[df_base_raw['ประเภทลูกค้า'].astype(str).isin(selected_cust_types)]
                    df_comp_raw = df_comp_raw[df_comp_raw['ประเภทลูกค้า'].astype(str).isin(selected_cust_types)]
                if selected_prod_groups:
                    df_base_raw = df_base_raw[df_base_raw['กลุ่มสินค้า'].astype(str).isin(selected_prod_groups)]
                    df_comp_raw = df_comp_raw[df_comp_raw['กลุ่มสินค้า'].astype(str).isin(selected_prod_groups)]

                base_cust = df_base_raw.groupby(['custcode', 'custname'])['รวม'].sum().reset_index().rename(columns={'รวม': 'ยอดซื้อปีก่อน'})
                comp_cust = df_comp_raw.groupby(['custcode', 'custname'])['รวม'].sum().reset_index().rename(columns={'รวม': 'ยอดซื้อปีปัจจุบัน'})
                
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
                
                def calc_growth(row):
                    prev = row['ยอดซื้อปีก่อน']
                    curr = row['ยอดซื้อปีปัจจุบัน']
                    if prev > 0:
                        return ((curr - prev) / prev) * 100
                    elif curr > 0:
                        return 100.0
                    else:
                        return 0.0

                merged_cust['% Growth'] = merged_cust.apply(calc_growth, axis=1)
                
                # สรุป Metric ตาม Filter ปัจจุบัน
                n_new = len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้าใหม่ (New)'])
                n_lost = len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้าที่หายไป (Churned)'])
                n_growth = len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้าเติบโตขึ้น (Growth)'])
                n_decline = len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้ายอดลดลง (Decline)'])
                total_active_cust = len(merged_cust)
                
                st.markdown(f"**📌 สรุปสถิติลูกค้าภายใต้ Filter ที่เลือก (รวมทั้งหมด {total_active_cust} ราย)**")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🟢 ลูกค้าใหม่ (New)", f"{n_new:,} ราย")
                c2.metric("🔴 ลูกค้าที่หายไป (Lost)", f"{n_lost:,} ราย")
                c3.metric("📈 ลูกค้าเติบโตขึ้น (Growth)", f"{n_growth:,} ราย")
                c4.metric("📉 ลูกค้ายอดลดลง (Decline)", f"{n_decline:,} ราย")
                
                st.markdown("---")
                status_filter = st.selectbox("กรองดูตารางตามสถานะลูกค้า:", ['ทั้งหมด', 'ลูกค้าใหม่ (New)', 'ลูกค้าที่หายไป (Churned)', 'ลูกค้าเติบโตขึ้น (Growth)', 'ลูกค้ายอดลดลง (Decline)'])
                
                if status_filter != 'ทั้งหมด':
                    display_df = merged_cust[merged_cust['สถานะลูกค้า'] == status_filter].copy()
                else:
                    display_df = merged_cust.copy()
                    
                display_df = display_df.sort_values(by='ผลต่างยอดซื้อ', ascending=False)
                display_df['ยอดปีก่อน'] = display_df['ยอดซื้อปีก่อน'].apply(format_smart)
                display_df['ยอดปีปัจจุบัน'] = display_df['ยอดซื้อปีปัจจุบัน'].apply(format_smart)
                display_df['ผลต่างยอด'] = display_df['ผลต่างยอดซื้อ'].apply(format_smart)
                display_df['% Growth'] = display_df['% Growth'].map('{:,.2f}%'.format)
                
                final_cols = ['custcode', 'custname', 'สถานะลูกค้า', 'ยอดปีก่อน', 'ยอดปีปัจจุบัน', 'ผลต่างยอด', '% Growth']
                st.dataframe(display_df[final_cols], use_container_width=True)
            else:
                st.info("💡 กรุณาอัปโหลดไฟล์ CSV อย่างน้อย 2 ไฟล์ขึ้นไป เพื่อเปิดใช้งานฟังก์ชันวิเคราะห์เปรียบเทียบ")

        # --- TAB 3: วิเคราะห์กลุ่มสินค้าเทียบปี ---
        with tab3:
            st.subheader("📦 วิเคราะห์ยอดขายรายกลุ่มสินค้า (เปรียบเทียบระหว่างไฟล์/ปี)")
            
            file_names = list(dfs_dict.keys())
            if len(file_names) >= 2:
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    p_base = st.selectbox("เลือกไฟล์ตั้งต้น (ปีก่อน)", file_names, index=0, key="p_base")
                with col_p2:
                    p_comp = st.selectbox("เลือกไฟล์เปรียบเทียบ (ปีปัจจุบัน)", file_names, index=1 if len(file_names)>1 else 0, key="p_comp")
                
                df_pb = dfs_dict[p_base]
                df_pc = dfs_dict[p_comp]
                
                if selected_branches:
                    df_pb = df_pb[df_pb['saleareacode'].astype(str).isin(selected_branches)]
                    df_pc = df_pc[df_pc['saleareacode'].astype(str).isin(selected_branches)]
                if selected_cust_types:
                    df_pb = df_pb[df_pb['ประเภทลูกค้า'].astype(str).isin(selected_cust_types)]
                    df_pc = df_pc[df_pc['ประเภทลูกค้า'].astype(str).isin(selected_cust_types)]
                
                grp_base = df_pb.groupby('กลุ่มสินค้า')['รวม'].sum().reset_index().rename(columns={'รวม': 'ยอดปีก่อน'})
                grp_comp = df_pc.groupby('กลุ่มสินค้า')['รวม'].sum().reset_index().rename(columns={'รวม': 'ยอดปีปัจจุบัน'})
                
                merged_grp = pd.merge(grp_base, grp_comp, on='กลุ่มสินค้า', how='outer').fillna(0)
                merged_grp['ผลต่าง'] = merged_grp['ยอดปีปัจจุบัน'] - merged_grp['ยอดปีก่อน']
                merged_grp['% Growth'] = np.where(merged_grp['ยอดปีก่อน'] > 0, ((merged_grp['ยอดปีปัจจุบัน'] - merged_grp['ยอดปีก่อน']) / merged_grp['ยอดปีก่อน']) * 100, 100.0)
                
                merged_grp = merged_grp.sort_values(by='ยอดปีปัจจุบัน', ascending=False)
                merged_grp['ยอดปีก่อน'] = merged_grp['ยอดปีก่อน'].apply(format_smart)
                merged_grp['ยอดปีปัจจุบัน'] = merged_grp['ยอดปีปัจจุบัน'].apply(format_smart)
                merged_grp['ผลต่าง'] = merged_grp['ผลต่าง'].apply(format_smart)
                merged_grp['% Growth'] = merged_grp['% Growth'].map('{:,.2f}%'.format)
                
                st.dataframe(merged_grp, use_container_width=True)
            else:
                st.info("💡 กรุณาอัปโหลดไฟล์อย่างน้อย 2 ไฟล์เพื่อใช้งานฟังก์ชันเปรียบเทียบกลุ่มสินค้า")

        # --- TAB 4: เปรียบเทียบรายสาขาเทียบปี ---
        with tab4:
            st.subheader("🏢 ผลการดำเนินงานแยกตามสาขา (Sales Area Comparison)")
            
            file_names = list(dfs_dict.keys())
            if len(file_names) >= 2:
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    b_base = st.selectbox("เลือกไฟล์ตั้งต้น (ปีก่อน)", file_names, index=0, key="b_base")
                with col_b2:
                    b_comp = st.selectbox("เลือกไฟล์เปรียบเทียบ (ปีปัจจุบัน)", file_names, index=1 if len(file_names)>1 else 0, key="b_comp")
                
                df_bb = dfs_dict[b_base]
                df_bc = dfs_dict[b_comp]
                
                if selected_cust_types:
                    df_bb = df_bb[df_bb['ประเภทลูกค้า'].astype(str).isin(selected_cust_types)]
                    df_bc = df_bc[df_bc['ประเภทลูกค้า'].astype(str).isin(selected_cust_types)]
                if selected_prod_groups:
                    df_bb = df_bb[df_bb['กลุ่มสินค้า'].astype(str).isin(selected_prod_groups)]
                    df_bc = df_bc[df_bc['กลุ่มสินค้า'].astype(str).isin(selected_prod_groups)]
                
                branch_base = df_bb.groupby('saleareacode')['รวม'].sum().reset_index().rename(columns={'รวม': 'ยอดปีก่อน'})
                branch_comp = df_bc.groupby('saleareacode')['รวม'].sum().reset_index().rename(columns={'รวม': 'ยอดปีปัจจุบัน'})
                
                merged_branch = pd.merge(branch_base, branch_comp, on='saleareacode', how='outer').fillna(0)
                merged_branch['ผลต่าง'] = merged_branch['ยอดปีปัจจุบัน'] - merged_branch['ยอดปีก่อน']
                merged_branch['% Growth'] = np.where(merged_branch['ยอดปีก่อน'] > 0, ((merged_branch['ยอดปีปัจจุบัน'] - merged_branch['ยอดปีก่อน']) / merged_branch['ยอดปีก่อน']) * 100, 100.0)
                
                merged_branch = merged_branch.sort_values(by='ยอดปีปัจจุบัน', ascending=False)
                merged_branch['ยอดปีก่อน'] = merged_branch['ยอดปีก่อน'].apply(format_smart)
                merged_branch['ยอดปีปัจจุบัน'] = merged_branch['ยอดปีปัจจุบัน'].apply(format_smart)
                merged_branch['ผลต่าง'] = merged_branch['ผลต่าง'].apply(format_smart)
                merged_branch['% Growth'] = merged_branch['% Growth'].map('{:,.2f}%'.format)
                
                st.dataframe(merged_branch, use_container_width=True)
            else:
                st.info("💡 กรุณาอัปโหลดไฟล์อย่างน้อย 2 ไฟล์เพื่อใช้งานฟังก์ชันเปรียบเทียบรายสาขา")

else:
    st.info("💡 โปรดอัปโหลดไฟล์ข้อมูล CSV (รองรับข้อมูลปี 2024, 2025 และ 2026) ที่แถบด้านข้างซ้าย เพื่อเริ่มต้นใช้งานแอปพลิเคชัน")
