import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Executive Dashboard & Business Planning 2027", layout="wide")

st.title("📊 ระบบบริหารงานและวิเคราะห์ข้อมูลลูกค้าเชิงลึก (แผนปี 2027)")
st.markdown("ระบบวิเคราะห์ยอดซื้อ (Cash/Credit) เปรียบเทียบ 3 ปี (2024-2026) แยกตามสาขาและกลุ่มสินค้า")

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
        # --- 2. ตัวกรองข้อมูล (Filters - แบบพิมพ์ค้นหาได้ st.multiselect) ---
        st.sidebar.header("🔍 2. ตัวกรองข้อมูลหลัก (พิมพ์ค้นหาได้)")
        
        branches = sorted([str(x) for x in df_all['saleareacode'].dropna().unique()])
        selected_branches = st.sidebar.multiselect("เลือกสาขา (Sales Area - พิมพ์ค้นหาได้)", branches, default=branches)
        
        cust_types = sorted([str(x) for x in df_all['ประเภทลูกค้า'].dropna().unique()])
        selected_cust_types = st.sidebar.multiselect("ประเภทลูกค้า (พิมพ์ค้นหาได้)", cust_types, default=cust_types)
        
        product_groups = sorted([str(x) for x in df_all['กลุ่มสินค้า'].dropna().unique()])
        selected_prod_groups = st.sidebar.multiselect("กลุ่มสินค้า (พิมพ์ค้นหาได้)", product_groups, default=product_groups)
        
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
            "📈 ภาพรวม & แยก Cash/Credit รายปี (3 ปี)", 
            "👥 วิเคราะห์ลูกค้า (Cash vs Credit)", 
            "📦 วิเคราะห์กลุ่มสินค้า (Cash vs Credit)", 
            "🏢 เปรียบเทียบรายสาขา (Cash vs Credit)"
        ])
        
        # จัดเรียงชื่อไฟล์/ปี จากเก่าไปใหม่เสมอ (เช่น 2024 -> 2025 -> 2026)
        file_names = sorted(list(dfs_dict.keys()))
        
        # --- TAB 1: ภาพรวม & แยก Cash/Credit รายปี ---
        with tab1:
            st.subheader("📌 สรุปภาพรวมยอดขายสุทธิทั้งหมด (ภายใต้ Filter ที่เลือก)")
            total_rev = df_filtered['รวม'].sum()
            total_cash = df_filtered['CASH'].sum() if 'CASH' in df_filtered.columns else 0
            total_credit = df_filtered['CREDIT'].sum() if 'CREDIT' in df_filtered.columns else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("ยอดขายรวมสุทธิ", format_smart(total_rev))
            col2.metric("ยอดเงินสด (CASH)", format_smart(total_cash))
            col3.metric("ยอดสินเชื่อ (CREDIT)", format_smart(total_credit))
            
            st.divider()
            st.subheader("📅 ภาพรวมรายปี แยกตาม Cash และ Credit")
            
            file_summary = []
            for fname in file_names:
                f_df = dfs_dict[fname]
                f_sub = f_df.copy()
                if selected_branches:
                    f_sub = f_sub[f_sub['saleareacode'].astype(str).isin(selected_branches)]
                if selected_cust_types:
                    f_sub = f_sub[f_sub['ประเภทลูกค้า'].astype(str).isin(selected_cust_types)]
                if selected_prod_groups:
                    f_sub = f_sub[f_sub['กลุ่มสินค้า'].astype(str).isin(selected_prod_groups)]
                
                s_rev = f_sub['รวม'].sum() if 'รวม' in f_sub.columns else 0
                s_cash = f_sub['CASH'].sum() if 'CASH' in f_sub.columns else 0
                s_credit = f_sub['CREDIT'].sum() if 'CREDIT' in f_sub.columns else 0
                
                file_summary.append({
                    'ชื่อไฟล์ / ปี': fname, 
                    'CASH': format_smart(s_cash),
                    'CREDIT': format_smart(s_credit),
                    'ยอดขายรวมสุทธิ': format_smart(s_rev)
                })
            
            df_file_sum = pd.DataFrame(file_summary)
            if not df_file_sum.empty:
                st.dataframe(df_file_sum, use_container_width=True)
            
            st.divider()
            st.subheader("🏆 ลูกค้าที่มียอดซื้อสูงสุด 20 อันดับแรก (แสดงเทรนด์ข้ามปี จากเก่าไปใหม่)")
            
            if len(file_names) >= 1:
                selected_top_file = st.selectbox("เลือกปีหลักที่ใช้จัดอันดับ Top 20:", file_names, index=len(file_names)-1, key="top_20_file")
                
                all_years_cust_list = []
                for fname in file_names:
                    f_df = dfs_dict[fname]
                    f_sub = f_df.copy()
                    if selected_branches:
                        f_sub = f_sub[f_sub['saleareacode'].astype(str).isin(selected_branches)]
                    if selected_cust_types:
                        f_sub = f_sub[f_sub['ประเภทลูกค้า'].astype(str).isin(selected_cust_types)]
                    if selected_prod_groups:
                        f_sub = f_sub[f_sub['กลุ่มสินค้า'].astype(str).isin(selected_prod_groups)]
                    
                    cust_agg = f_sub.groupby(['custcode', 'custname', 'saleareacode', 'ประเภทลูกค้า'])['รวม'].sum().reset_index()
                    cust_agg['Year'] = fname
                    all_years_cust_list.append(cust_agg)
                
                df_all_years = pd.concat(all_years_cust_list, ignore_index=True)
                
                pivot_trend = df_all_years.pivot_table(
                    index=['custcode', 'custname', 'saleareacode', 'ประเภทลูกค้า'], 
                    columns='Year', 
                    values='รวม', 
                    aggfunc='sum'
                ).reset_index().fillna(0)
                
                if selected_top_file in pivot_trend.columns:
                    pivot_trend = pivot_trend.sort_values(by=selected_top_file, ascending=False).head(20)
                else:
                    pivot_trend = pivot_trend.head(20)
                
                def get_trend_icon(row):
                    if len(file_names) >= 2:
                        first_val = row[file_names[0]]
                        last_val = row[file_names[-1]]
                        if last_val > first_val:
                            return "↗ เติบโตขึ้น"
                        elif last_val < first_val:
                            return "↘ ลดลง"
                        else:
                            return "- ทรงตัว"
                    return "-"

                pivot_trend['เทรนด์ (Trend)'] = pivot_trend.apply(get_trend_icon, axis=1)
                
                display_trend = pd.DataFrame()
                display_trend['รหัสลูกค้า'] = pivot_trend['custcode']
                display_trend['ชื่อลูกค้า'] = pivot_trend['custname']
                display_trend['สาขา'] = pivot_trend['saleareacode']
                display_trend['ประเภท'] = pivot_trend['ประเภทลูกค้า']
                
                # วนลูปเรียงตามลำดับปีจากเก่าไปใหม่เป๊ะๆ
                for y in file_names:
                    if y in pivot_trend.columns:
                        display_trend[f'ยอดซื้อ ({y})'] = pivot_trend[y].apply(format_smart)
                
                display_trend['เทรนด์ภาพรวม'] = pivot_trend['เทรนด์ (Trend)']
                
                st.dataframe(display_trend, use_container_width=True)
            else:
                st.info("💡 กรุณาอัปโหลดไฟล์ข้อมูลอย่างน้อย 1 ไฟล์")

        # --- TAB 2: วิเคราะห์ลูกค้า (Cash vs Credit & Breakdown by Type) ---
        with tab2:
            st.subheader("👥 การเคลื่อนไหวของลูกค้า (แยกตาม Cash / Credit และประเภทลูกค้า)")
            st.markdown("เปรียบเทียบระหว่าง 2 ไฟล์ พร้อมสรุปสถิติจำนวนลูกค้าภาพรวมและแยกตามประเภทลูกค้า (เช่น A1, A2, B1)")
            
            if len(file_names) >= 2:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    base_file_name = st.selectbox("เลือกไฟล์ฐานเดิม (ปีก่อน)", file_names, index=0, key="t2_base")
                with col_f2:
                    comp_file_name = st.selectbox("เลือกไฟล์เปรียบเทียบ (ปีปัจจุบัน)", file_names, index=1 if len(file_names)>1 else 0, key="t2_comp")
                
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

                cust_type_map_base = df_base_raw.groupby('custcode')['ประเภทลูกค้า'].first().to_dict()
                cust_type_map_comp = df_comp_raw.groupby('custcode')['ประเภทลูกค้า'].first().to_dict()
                
                base_cust = df_base_raw.groupby(['custcode', 'custname'])[['CASH', 'CREDIT', 'รวม']].sum().reset_index().rename(
                    columns={'CASH': 'Cash_ปีก่อน', 'CREDIT': 'Credit_ปีก่อน', 'รวม': 'ยอดซื้อปีก่อน'}
                )
                comp_cust = df_comp_raw.groupby(['custcode', 'custname'])[['CASH', 'CREDIT', 'รวม']].sum().reset_index().rename(
                    columns={'CASH': 'Cash_ปัจจุบัน', 'CREDIT': 'Credit_ปัจจุบัน', 'รวม': 'ยอดซื้อปีปัจจุบัน'}
                )
                
                merged_cust = pd.merge(base_cust, comp_cust, on=['custcode', 'custname'], how='outer').fillna(0)
                
                merged_cust['ประเภทลูกค้า'] = merged_cust['custcode'].map(cust_type_map_comp)
                merged_cust['ประเภทลูกค้า'] = merged_cust['ประเภทลูกค้า'].fillna(merged_cust['custcode'].map(cust_type_map_base)).fillna('ไม่ระบุ')
                
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
                
                merged_cust['Diff_Cash'] = merged_cust['Cash_ปัจจุบัน'] - merged_cust['Cash_ปีก่อน']
                merged_cust['Diff_Credit'] = merged_cust['Credit_ปัจจุบัน'] - merged_cust['Credit_ปีก่อน']
                
                n_new = len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้าใหม่ (New)'])
                n_lost = len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้าที่หายไป (Churned)'])
                n_growth = len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้าเติบโตขึ้น (Growth)'])
                n_decline = len(merged_cust[merged_cust['สถานะลูกค้า'] == 'ลูกค้ายอดลดลง (Decline)'])
                total_active_cust = len(merged_cust)
                
                st.markdown(f"**📌 สรุปสถิติลูกค้าภาพรวม (รวมทั้งหมด {total_active_cust} ราย)**")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🟢 ลูกค้าใหม่ (New)", f"{n_new:,} ราย")
                c2.metric("🔴 ลูกค้าที่หายไป (Lost)", f"{n_lost:,} ราย")
                c3.metric("📈 ลูกค้าเติบโตขึ้น (Growth)", f"{n_growth:,} ราย")
                c4.metric("📉 ลูกค้ายอดลดลง (Decline)", f"{n_decline:,} ราย")
                
                st.markdown("---")
                st.subheader("📊 สรุปจำนวนลูกค้าและการเคลื่อนไหว แยกตามประเภทลูกค้า (Customer Type Breakdown)")
                
                type_summary = merged_cust.groupby('ประเภทลูกค้า').agg(
                    total_cust=('custcode', 'count'),
                    new_cust=('สถานะลูกค้า', lambda x: sum(x == 'ลูกค้าใหม่ (New)')),
                    lost_cust=('สถานะลูกค้า', lambda x: sum(x == 'ลูกค้าที่หายไป (Churned)')),
                    growth_cust=('สถานะลูกค้า', lambda x: sum(x == 'ลูกค้าเติบโตขึ้น (Growth)')),
                    decline_cust=('สถานะลูกค้า', lambda x: sum(x == 'ลูกค้ายอดลดลง (Decline)')),
                    total_rev=('ยอดซื้อปีปัจจุบัน', 'sum')
                ).reset_index()
                
                type_summary = type_summary.sort_values(by='total_rev', ascending=False)
                
                display_type_summary = pd.DataFrame()
                display_type_summary['ประเภทลูกค้า'] = type_summary['ประเภทลูกค้า']
                display_type_summary['จำนวนทั้งหมด'] = type_summary['total_cust']
                display_type_summary['ลูกค้าใหม่'] = type_summary['new_cust']
                display_type_summary['ลูกค้าที่หายไป'] = type_summary['lost_cust']
                display_type_summary['เติบโตขึ้น'] = type_summary['growth_cust']
                display_type_summary['ยอดลดลง'] = type_summary['decline_cust']
                display_type_summary['ยอดรวมปีปัจจุบัน'] = type_summary['total_rev'].apply(format_smart)
                
                st.dataframe(display_type_summary, use_container_width=True)
                
                st.markdown("---")
                status_filter = st.selectbox("กรองดูตารางรายชื่อลูกค้าตามสถานะ:", ['ทั้งหมด', 'ลูกค้าใหม่ (New)', 'ลูกค้าที่หายไป (Churned)', 'ลูกค้าเติบโตขึ้น (Growth)', 'ลูกค้ายอดลดลง (Decline)'])
                
                if status_filter != 'ทั้งหมด':
                    display_df = merged_cust[merged_cust['สถานะลูกค้า'] == status_filter].copy()
                else:
                    display_df = merged_cust.copy()
                    
                display_df = display_df.sort_values(by='ผลต่างยอดซื้อ', ascending=False)
                
                display_cust_table = pd.DataFrame()
                display_cust_table['รหัสลูกค้า'] = display_df['custcode']
                display_cust_table['ชื่อลูกค้า'] = display_df['custname']
                display_cust_table['ประเภทลูกค้า'] = display_df['ประเภทลูกค้า']
                display_cust_table['สถานะลูกค้า'] = display_df['สถานะลูกค้า']
                display_cust_table['Cash (ปีก่อน -> ปัจจุบัน)'] = display_df['Cash_ปีก่อน'].apply(format_smart) + " -> " + display_df['Cash_ปัจจุบัน'].apply(format_smart)
                display_cust_table['Cash ส่วนต่าง (Δ)'] = display_df['Diff_Cash'].apply(format_smart)
                display_cust_table['Credit (ปีก่อน -> ปัจจุบัน)'] = display_df['Credit_ปีก่อน'].apply(format_smart) + " -> " + display_df['Credit_ปัจจุบัน'].apply(format_smart)
                display_cust_table['Credit ส่วนต่าง (Δ)'] = display_df['Diff_Credit'].apply(format_smart)
                display_cust_table['ยอดรวมส่วนต่าง (Δ)'] = display_df['ผลต่างยอดซื้อ'].apply(format_smart)
                
                st.dataframe(display_cust_table, use_container_width=True)
            else:
                st.info("💡 กรุณาอัปโหลดไฟล์ CSV อย่างน้อย 2 ไฟล์ขึ้นไป เพื่อเปิดใช้งานฟังก์ชันวิเคราะห์เปรียบเทียบ")

        # --- TAB 3: วิเคราะห์กลุ่มสินค้า (Cash vs Credit) ---
        with tab3:
            st.subheader("📦 วิเคราะห์กลุ่มสินค้า แยกตาม Cash และ Credit (เปรียบเทียบ 2 ไฟล์)")
            
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
                
                grp_base = df_pb.groupby('กลุ่มสินค้า')[['CASH', 'CREDIT', 'รวม']].sum().reset_index().rename(
                    columns={'CASH': 'Cash_ปีก่อน', 'CREDIT': 'Credit_ปีก่อน', 'รวม': 'รวม_ปีก่อน'}
                )
                grp_comp = df_pc.groupby('กลุ่มสินค้า')[['CASH', 'CREDIT', 'รวม']].sum().reset_index().rename(
                    columns={'CASH': 'Cash_ปัจจุบัน', 'CREDIT': 'Credit_ปัจจุบัน', 'รวม': 'รวม_ปัจจุบัน'}
                )
                
                merged_grp = pd.merge(grp_base, grp_comp, on='กลุ่มสินค้า', how='outer').fillna(0)
                
                merged_grp['Diff_Cash'] = merged_grp['Cash_ปัจจุบัน'] - merged_grp['Cash_ปีก่อน']
                merged_grp['Diff_Credit'] = merged_grp['Credit_ปัจจุบัน'] - merged_grp['Credit_ปีก่อน']
                merged_grp['Diff_Total'] = merged_grp['รวม_ปัจจุบัน'] - merged_grp['รวม_ปีก่อน']
                
                merged_grp = merged_grp.sort_values(by='Diff_Total', ascending=False)
                
                display_grp = pd.DataFrame()
                display_grp['กลุ่มสินค้า'] = merged_grp['กลุ่มสินค้า']
                display_grp['Cash (ปีก่อน -> ปัจจุบัน)'] = merged_grp['Cash_ปีก่อน'].apply(format_smart) + " -> " + merged_grp['Cash_ปัจจุบัน'].apply(format_smart)
                display_grp['Cash ส่วนต่าง (Δ)'] = merged_grp['Diff_Cash'].apply(format_smart)
                display_grp['Credit (ปีก่อน -> ปัจจุบัน)'] = merged_grp['Credit_ปีก่อน'].apply(format_smart) + " -> " + merged_grp['Credit_ปัจจุบัน'].apply(format_smart)
                display_grp['Credit ส่วนต่าง (Δ)'] = merged_grp['Diff_Credit'].apply(format_smart)
                display_grp['ยอดรวมส่วนต่าง (Δ)'] = merged_grp['Diff_Total'].apply(format_smart)
                
                st.dataframe(display_grp, use_container_width=True)
            else:
                st.info("💡 กรุณาอัปโหลดไฟล์อย่างน้อย 2 ไฟล์เพื่อใช้งานฟังก์ชันเปรียบเทียบกลุ่มสินค้า")

        # --- TAB 4: เปรียบเทียบรายสาขา (Cash vs Credit) ---
        with tab4:
            st.subheader("🏢 ผลการดำเนินงานแยกตามสาขา (Cash vs Credit แยกตามส่วนต่าง)")
            
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
                
                branch_base = df_bb.groupby('saleareacode')[['CASH', 'CREDIT', 'รวม']].sum().reset_index().rename(
                    columns={'CASH': 'Cash_ปีก่อน', 'CREDIT': 'Credit_ปีก่อน', 'รวม': 'รวม_ปีก่อน'}
                )
                branch_comp = df_bc.groupby('saleareacode')[['CASH', 'CREDIT', 'รวม']].sum().reset_index().rename(
                    columns={'CASH': 'Cash_ปัจจุบัน', 'CREDIT': 'Credit_ปัจจุบัน', 'รวม': 'รวม_ปัจจุบัน'}
                )
                
                merged_branch = pd.merge(branch_base, branch_comp, on='saleareacode', how='outer').fillna(0)
                
                merged_branch['Diff_Cash'] = merged_branch['Cash_ปัจจุบัน'] - merged_branch['Cash_ปีก่อน']
                merged_branch['Diff_Credit'] = merged_branch['Credit_ปัจจุบัน'] - merged_branch['Credit_ปีก่อน']
                merged_branch['Diff_Total'] = merged_branch['รวม_ปัจจุบัน'] - merged_branch['รวม_ปีก่อน']
                
                merged_branch = merged_branch.sort_values(by='Diff_Total', ascending=False)
                
                display_branch = pd.DataFrame()
                display_branch['สาขา (Sales Area)'] = merged_branch['saleareacode']
                display_branch['Cash (ปีก่อน -> ปัจจุบัน)'] = merged_branch['Cash_ปีก่อน'].apply(format_smart) + " -> " + merged_branch['Cash_ปัจจุบัน'].apply(format_smart)
                display_branch['Cash ส่วนต่าง (Δ)'] = merged_branch['Diff_Cash'].apply(format_smart)
                display_branch['Credit (ปีก่อน -> ปัจจุบัน)'] = merged_branch['Credit_ปีก่อน'].apply(format_smart) + " -> " + merged_branch['Credit_ปัจจุบัน'].apply(format_smart)
                display_branch['Credit ส่วนต่าง (Δ)'] = merged_branch['Diff_Credit'].apply(format_smart)
                display_branch['ยอดรวมส่วนต่าง (Δ)'] = merged_branch['Diff_Total'].apply(format_smart)
                
                st.dataframe(display_branch, use_container_width=True)
            else:
                st.info("💡 กรุณาอัปโหลดไฟล์อย่างน้อย 2 ไฟล์เพื่อใช้งานฟังก์ชันเปรียบเทียบรายสาขา")

else:
    st.info("💡 โปรดอัปโหลดไฟล์ข้อมูล CSV (รองรับข้อมูลปี 2024, 2025 และ 2026) ที่แถบด้านข้างซ้าย เพื่อเริ่มต้นใช้งานแอปพลิเคชัน")
