import streamlit as st
import pandas as pd
import os
import io
import re

try:
    from github import Github
except ImportError:
    pass

DB_FILE = 'sales_database.csv'

st.set_page_config(page_title="Popular Group - Sales Dashboard", layout="wide", page_icon="📈")

# HARAMI BADASS CSS STYLING
st.markdown("""
<style>
    [data-testid="stMetricValue"] { color: #E20613 !important; font-weight: 900 !important; }
    .vip-box {
        background-color: #FFFFFF; border-left: 6px solid #E20613; padding: 15px; 
        border-radius: 8px; margin-top: 25px; margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(226, 6, 19, 0.1);
    }
    .vip-text { color: #E20613; font-weight: bold; font-size: 16px; }
</style>
""", unsafe_allow_html=True)

MASTER_SEQUENCE = [
    "JUNIOR 125 ML", "REAL FROOT 200 ML", "REAL FROOT RED GRAPES 200 ML", "REAL FROOT RED ANAAR 200 ML",
    "MAZA 200 ML", "MAZA ANAAR 200 ML", "MAZA 250 ML", "MAZA ANAAR 250 ML", "MAZA GUAVA 250 ML",
    "POPULAR 250 ML", "KOOL 250 ML", "POLLY 250 ML", "REAL FROOT NRGB 250 ML", "PFD NRGB 250 ML",
    "SUNCREST NRGB 250 ML", "REAL FROOT 1000 ML PRISMA", "REAL FROOT RED ANAAR 1000 ML", "REAL FROOT RED GRAPES 1000 ML",
    "REAL FROOT 1000 ML EXPORT", "REAL FROOT 1000 ML RED GRAPES", "REAL FROOT 1000 ML RED ANAAR", "MAZA PRISMA 1000 ML",
    "MAZA 1000 ML PRISMA", "MAZA PRISMA ANAAR 1000 ML", "M A 1000 ML", "NECTAR LITER PRISMA",
    "HOPE WATER 330 ML", "HOPE WATER 500 ML", "HOPE WATER 1500 ML", "HOPE WATER 6 LITER",
    "MAAZA PET 250 ML", "MAAZA PET 500 ML", "MAAZA PET 1000 ML", "MAZA FIZZY CAN 250 ML",
    "CHEETAH CAN 250 ML", "POP CSD 300 ML", "POP CSD 345 ML", "POP UP 345 ML", "POP COLA 345 ML",
    "POP CSD 1000 ML", "POP COLA 1 LTR", "POP CSD 1500 ML", "POP FRUITY FALVOUR 300 ML",
    "POP FRUITY FALVOUR 1500 ML", "POP OOLA 300 ML", "POP OOLA 1500 ML", "EXTREEM 250 ML", "MACHO 300ML",
    "FINISH GOODS", "0"
]

def get_empty_df():
    return pd.DataFrame(columns=['BDM', 'RSM', 'RSM_Original', 'TSO', 'Category', 'Flavours', 'Target', 'Achievement', 'Sales_2025', 'Value'])

if not os.path.exists(DB_FILE):
    df_init = get_empty_df()
    df_init.to_csv(DB_FILE, index=False)

def load_data():
    if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
        try:
            g = Github(st.secrets["GITHUB_TOKEN"])
            repo = g.get_repo(st.secrets["GITHUB_REPO"])
            contents = repo.get_contents(DB_FILE)
            return pd.read_csv(io.StringIO(contents.decoded_content.decode()))
        except Exception as e:
            st.sidebar.warning(f"Live DB Sync Error: {e}")
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return get_empty_df()

def save_data(df):
    df.to_csv(DB_FILE, index=False)
    if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
        try:
            g = Github(st.secrets["GITHUB_TOKEN"])
            repo = g.get_repo(st.secrets["GITHUB_REPO"])
            contents = repo.get_contents(DB_FILE)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            repo.update_file(contents.path, "Auto-update sales database", csv_buffer.getvalue(), contents.sha)
            st.toast("✅ Data securely synced to Cloud!")
        except Exception as e:
            st.error(f"Failed to sync with Cloud: {e}")

def clean_category_name(cat):
    cat = str(cat).strip()
    if cat.lower() == 'finished goods':
        return 'FINISH GOODS'
    return cat

def calculate_metrics(df):
    df['Balance'] = df['Target'] - df['Achievement']
    df['Ach %'] = df.apply(lambda row: (row['Achievement'] / row['Target']) * 100 if row['Target'] > 0 else 0, axis=1)
    df['Growth over Last Year %'] = df.apply(lambda row: ((row['Achievement'] - row['Sales_2025']) / row['Sales_2025']) * 100 if row['Sales_2025'] > 0 else 0, axis=1)
    
    cols = ['Category', 'Flavours', 'Target', 'Achievement', 'Balance', 'Ach %', 'Sales_2025', 'Growth over Last Year %', 'Value']
    return df[[c for c in cols if c in df.columns]]

def enforce_master_sequence(df_grouped):
    df_filtered = df_grouped[df_grouped['Category'].isin(MASTER_SEQUENCE)].copy()
    df_filtered['Category_Cat'] = pd.Categorical(df_filtered['Category'], categories=MASTER_SEQUENCE, ordered=True)
    df_sorted = df_filtered.sort_values('Category_Cat').drop(columns=['Category_Cat']).reset_index(drop=True)
    if 'Flavours' in df_sorted.columns:
        df_sorted['Flavours'] = df_sorted['Flavours'].fillna("").replace("None", "")
    return df_sorted

def highlight_badass_style(df):
    def highlight_total(row):
        if row['Category'] in ['GRAND TOTAL', 'TOTAL']:
            return ['background-color: #FFE5E5; color: #E20613; font-weight: bold; border-top: 2px solid #E20613;'] * len(row)
        return [''] * len(row)
    
    def color_negative_red(val):
        try:
            if float(val) < 0: return 'color: #E20613; font-weight: bold;'
            if float(val) > 0: return 'color: #008000; font-weight: bold;'
        except: pass
        return ''
        
    styled = df.style.apply(highlight_total, axis=1) \
                     .map(color_negative_red, subset=['Balance']) \
                     .format({
                        'Target': '{:,.0f}', 'Achievement': '{:,.0f}', 'Balance': '{:,.0f}',
                        'Sales_2025': '{:,.0f}', 'Value': 'Rs {:,.2f}',
                        'Ach %': '{:.2f}%', 'Growth over Last Year %': '{:.2f}%'
                     })
    return styled


def generate_excel_export(db):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        header_format = workbook.add_format({'bold': True, 'bg_color': '#E20613', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        bold_bg = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1})
        text_format = workbook.add_format({'border': 1})
        num_format = workbook.add_format({'border': 1, 'num_format': '#,##0'})
        val_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        pct_format = workbook.add_format({'border': 1, 'num_format': '0.00%'})
        total_row_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D9E1F2', 'num_format': '#,##0'})
        total_val_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D9E1F2', 'num_format': '#,##0.00'})
        total_pct_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D9E1F2', 'num_format': '0.00%'})
        
        def write_table_to_sheet(sheet, df_table, start_row, title_dict):
            current_row = start_row
            for k, v in title_dict.items():
                sheet.write(current_row, 0, k, workbook.add_format({'bold': True, 'font_color': '#E20613'}))
                sheet.write(current_row, 1, str(v), workbook.add_format({'bold': True}))
                current_row += 1
            cols = ['Category', 'Flavours', 'Target', 'Achievement', 'Balance', 'Ach %', 'Sales 2025', 'Growth over Last Year %', 'Value']
            for col_num, value in enumerate(cols):
                sheet.write(current_row, col_num, value, header_format)
            current_row += 1
            for index, row in df_table.iterrows():
                is_total = (row['Category'] == 'GRAND TOTAL' or row['Category'] == 'TOTAL')
                c_txt = bold_bg if is_total else text_format
                c_num = total_row_format if is_total else num_format
                c_val = total_val_format if is_total else val_format
                c_pct = total_pct_format if is_total else pct_format
                sheet.write(current_row, 0, row['Category'], c_txt)
                sheet.write(current_row, 1, row.get('Flavours', ''), c_txt)
                sheet.write_number(current_row, 2, row['Target'], c_num)
                sheet.write_number(current_row, 3, row['Achievement'], c_num)
                sheet.write_number(current_row, 4, row['Balance'], c_num)
                try: ach_val = float(str(row['Ach %']).strip('%'))/100
                except: ach_val = 0
                try: growth_val = float(str(row['Growth over Last Year %']).strip('%'))/100
                except: growth_val = 0
                
                sheet.write_number(current_row, 5, ach_val, c_pct)
                sheet.write_number(current_row, 6, row['Sales_2025'], c_num)
                sheet.write_number(current_row, 7, growth_val, c_pct)
                sheet.write_number(current_row, 8, row['Value'], c_val)
                current_row += 1
            sheet.set_column('A:A', 35)
            sheet.set_column('B:B', 15)
            sheet.set_column('C:I', 15)
            return current_row + 2

        if not db.empty:
            bdm_name = db['BDM'].iloc[0]
            worksheet_bdm = writer.book.add_worksheet('BDM')
            summary_bdm = db.groupby(['Category', 'Flavours'], dropna=False, as_index=False).sum(numeric_only=True)
            summary_bdm = enforce_master_sequence(summary_bdm)
            summary_bdm = calculate_metrics(summary_bdm)
            total_bdm = pd.DataFrame([{'Category': 'GRAND TOTAL', 'Flavours': '', 'Target': summary_bdm['Target'].sum(), 'Achievement': summary_bdm['Achievement'].sum(), 'Sales_2025': summary_bdm['Sales_2025'].sum(), 'Value': summary_bdm['Value'].sum()}])
            total_bdm = calculate_metrics(total_bdm)
            summary_bdm = pd.concat([summary_bdm, total_bdm], ignore_index=True)
            next_row = write_table_to_sheet(worksheet_bdm, summary_bdm, 0, {'BDM:': bdm_name, 'RSM/ASM:': 'ALL RSMs'})
            rsms = db['RSM'].unique()
            for r in rsms:
                rsm_data = db[db['RSM'] == r]
                rsm_grouped = rsm_data.groupby(['Category', 'Flavours'], dropna=False, as_index=False).sum(numeric_only=True)
                rsm_display = enforce_master_sequence(rsm_grouped)
                rsm_display = calculate_metrics(rsm_display)
                rsm_total = pd.DataFrame([{'Category': 'TOTAL', 'Flavours': '', 'Target': rsm_display['Target'].sum(), 'Achievement': rsm_display['Achievement'].sum(), 'Sales_2025': rsm_display['Sales_2025'].sum(), 'Value': rsm_display['Value'].sum()}])
                rsm_total = calculate_metrics(rsm_total)
                next_row = write_table_to_sheet(worksheet_bdm, rsm_total, next_row, {'RSM/ASM:': r})
            
            for r in rsms:
                rsm_sheet_name = str(r)[:31]
                worksheet_rsm = writer.book.add_worksheet(rsm_sheet_name)
                rsm_data = db[db['RSM'] == r]
                rsm_grouped = rsm_data.groupby(['Category', 'Flavours'], dropna=False, as_index=False).sum(numeric_only=True)
                rsm_display = enforce_master_sequence(rsm_grouped)
                rsm_display = calculate_metrics(rsm_display)
                rsm_total_row = pd.DataFrame([{'Category': 'GRAND TOTAL', 'Flavours': '', 'Target': rsm_display['Target'].sum(), 'Achievement': rsm_display['Achievement'].sum(), 'Sales_2025': rsm_display['Sales_2025'].sum(), 'Value': rsm_display['Value'].sum()}])
                rsm_total_row = calculate_metrics(rsm_total_row)
                rsm_display = pd.concat([rsm_display, rsm_total_row], ignore_index=True)
                n_row = write_table_to_sheet(worksheet_rsm, rsm_display, 0, {'BDM:': bdm_name, 'RSM/ASM:': r})
                tsos = rsm_data['TSO'].unique()
                for t in tsos:
                    tso_data = rsm_data[rsm_data['TSO'] == t]
                    tso_grouped = tso_data.groupby(['Category', 'Flavours'], dropna=False, as_index=False).sum(numeric_only=True)
                    tso_display = enforce_master_sequence(tso_grouped)
                    tso_display = calculate_metrics(tso_display)
                    tso_total_row = pd.DataFrame([{'Category': 'TOTAL', 'Flavours': '', 'Target': tso_display['Target'].sum(), 'Achievement': tso_display['Achievement'].sum(), 'Sales_2025': tso_display['Sales_2025'].sum(), 'Value': tso_display['Value'].sum()}])
                    tso_total_row = calculate_metrics(tso_total_row)
                    tso_display = pd.concat([tso_display, tso_total_row], ignore_index=True)
                    n_row = write_table_to_sheet(worksheet_rsm, tso_display, n_row, {'BDM:': bdm_name, 'RSM/ASM:': r, 'TSO:': t})
                    
    processed_data = output.getvalue()
    return processed_data


# --- STATE MANAGEMENT ---
if 'menu_selection' not in st.session_state:
    st.session_state['menu_selection'] = "📝 Add Raw Data"

def menu_changed():
    st.session_state['menu_selection'] = st.session_state['menu_widget']

if 'text_key' not in st.session_state:
    st.session_state['text_key'] = 0


# --- STREAMLIT UI ---

if os.path.exists('logo.png'):
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image('logo.png', width=120)
    with col2:
        st.markdown("<h1 style='color: #E20613; margin-top: 15px;'>POPULAR GROUP - MASTER SALES DASHBOARD</h1>", unsafe_allow_html=True)
else:
    st.title("🔴 POPULAR GROUP - MASTER SALES DASHBOARD")

st.markdown("---")

menu = st.sidebar.selectbox(
    "Navigate Dashboard", 
    ["📝 Add Raw Data", "📋 RSM Summary", "📈 BDM Summary", "⚙️ Database Management"],
    index=["📝 Add Raw Data", "📋 RSM Summary", "📈 BDM Summary", "⚙️ Database Management"].index(st.session_state['menu_selection']),
    key='menu_widget',
    on_change=menu_changed
)

st.sidebar.markdown("---")
if os.path.exists('logo.png'):
    st.sidebar.image('logo.png', use_container_width=True)

# EXPORT BUTTON
db = load_data()
if not db.empty:
    st.sidebar.markdown("### 📥 Export Reports")
    excel_data = generate_excel_export(db)
    st.sidebar.download_button(
        label="💾 Download Master Sheet V4 (Excel)",
        data=excel_data,
        file_name="Popular_Group_Master_Summary_V4.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.sidebar.markdown("---")
if st.sidebar.button("🚨 RESET ALL DATA"):
    df_init = pd.DataFrame(columns=['BDM', 'RSM', 'RSM_Original', 'TSO', 'Category', 'Flavours', 'Target', 'Achievement', 'Sales_2025', 'Value'])
    save_data(df_init)
    st.sidebar.success("✅ Database Completely Cleared!")
    st.rerun()

if menu == "📝 Add Raw Data":
    st.header("Step 1: Paste Raw Data")
    st.write("Bilkul Excel jesa flow: Jo RSM select karoge, data usi mein jayega!")
    
    rsm_name = st.selectbox("Kaunsi RSM mein data daalna hai?", ["RSM 1", "RSM 2", "RSM 3", "RSM 4", "RSM 5"])
    
    dynamic_key = f"raw_text_{st.session_state['text_key']}"
    raw_data = st.text_area("Yahan Raw Data Paste karein", height=300, key=dynamic_key)
    
    if st.button("Save Data", type="primary"):
        if not raw_data.strip():
            st.error("Data paste karna zaroori hai!")
        else:
            try:
                lines = raw_data.split('\n')
                ext_bdm = "Company BDM"
                ext_rsm_original = "Unknown RSM"
                ext_tso = "Unknown TSO"
                start_idx = 0
                for i, line in enumerate(lines):
                    clean_line = re.sub(r'\t+', ' ', line).strip()
                    if clean_line.upper().startswith("BDM:"):
                        ext_bdm = clean_line.split("BDM:", 1)[1].strip()
                    elif clean_line.upper().startswith("RSM/ASM:"):
                        ext_rsm_original = clean_line.split("RSM/ASM:", 1)[1].strip()
                    elif clean_line.upper().startswith("TSO:"):
                        ext_tso = clean_line.split("TSO:", 1)[1].strip()
                    elif 'Category' in line or 'category' in line.lower():
                        start_idx = i
                        break
                
                clean_data = '\n'.join(lines[start_idx:])
                df_paste = pd.read_csv(io.StringIO(clean_data), sep='\t')
                
                cols = df_paste.columns
                def find_col(keywords):
                    for c in cols:
                        for kw in keywords:
                            if kw.lower() in str(c).lower():
                                return c
                    return None
                
                col_cat = find_col(['category'])
                col_flav = find_col(['flavour', 'flavors'])
                col_target = find_col(['target'])
                col_ach = find_col(['achievement', 'achieve'])
                col_sales = find_col(['sales', '2025'])
                col_val = find_col(['value'])
                
                if not col_cat or not col_target or not col_ach:
                    st.error("❌ Data mein Category, Target ya Achievement ke headers nahi milay.")
                else:
                    df_clean = pd.DataFrame({
                        'BDM': ext_bdm,
                        'RSM': rsm_name, 
                        'RSM_Original': ext_rsm_original, 
                        'TSO': ext_tso,
                        'Category': df_paste[col_cat].apply(clean_category_name),
                        'Flavours': df_paste[col_flav].fillna("") if col_flav else "",
                        'Target': pd.to_numeric(df_paste[col_target].astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce').fillna(0),
                        'Achievement': pd.to_numeric(df_paste[col_ach].astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce').fillna(0),
                        'Sales_2025': pd.to_numeric(df_paste[col_sales].astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce').fillna(0) if col_sales else 0,
                        'Value': pd.to_numeric(df_paste[col_val].astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce').fillna(0) if col_val else 0,
                    })
                    df_clean = df_clean[(df_clean['Category'] != '') & (df_clean['Category'].notna())]
                    df_grouped = df_clean.groupby(['BDM', 'RSM', 'RSM_Original', 'TSO', 'Category', 'Flavours'], dropna=False, as_index=False).sum()
                    
                    if not db.empty and 'RSM_Original' not in db.columns:
                        db['RSM_Original'] = "Unknown"
                    if not db.empty and 'RSM' in db.columns and 'TSO' in db.columns:
                        db = db[~((db['RSM'] == rsm_name) & (db['TSO'] == ext_tso))]
                    
                    db = pd.concat([db, df_grouped], ignore_index=True)
                    save_data(db)
                    
                    st.session_state['text_key'] += 1
                    st.success(f"✅ Data Saved in {rsm_name}! (TSO Name: {ext_tso} auto-detected)")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Ghalti aagai data read karne mein: {str(e)}")

elif menu == "📋 RSM Summary":
    st.header("Step 2: RSM Master Summary & TSO Details")
    
    rsm_name = st.selectbox("Select RSM to view", ["RSM 1", "RSM 2", "RSM 3", "RSM 4", "RSM 5"])
    
    if db.empty or db[db['RSM'] == rsm_name].empty:
        st.warning(f"No data found in {rsm_name} yet.")
    else:
        rsm_data = db[db['RSM'] == rsm_name]
        
        st.markdown(f"""
        <div class="vip-box" style="margin-bottom: 20px;">
            <div class="vip-text" style="font-size: 20px;">📌 MASTER SUMMARY (Auto-Updated)</div>
            <hr style="margin: 10px 0px; border-color: #E20613; opacity: 0.2;">
            <strong>BDM:</strong> {rsm_data['BDM'].iloc[0]}<br>
            <strong>RSM/ASM:</strong> {rsm_name}<br>
            <strong>TSO:</strong> {rsm_data['TSO'].nunique()} TSOs
        </div>
        """, unsafe_allow_html=True)
        
        summary = rsm_data.groupby(['Category', 'Flavours'], dropna=False, as_index=False).sum(numeric_only=True)
        summary = enforce_master_sequence(summary)
        summary = calculate_metrics(summary)
        
        # --- NEW DAD-IMPRESSING KPI DASHBOARD ---
        t_target = summary['Target'].sum()
        t_ach = summary['Achievement'].sum()
        t_val = summary['Value'].sum()
        t_2025 = summary['Sales_2025'].sum()
        ach_pct = (t_ach/t_target*100) if t_target > 0 else 0
        grw_pct = ((t_ach-t_2025)/t_2025*100) if t_2025 > 0 else 0
        
        st.markdown("### 🌟 BUSINESS HIGHLIGHTS")
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Total Sales Value", f"Rs {t_val:,.0f}", f"{grw_pct:.1f}% vs Last Year")
        c2.metric("🎯 Total Achievement", f"{t_ach:,.0f} Cases", f"{ach_pct:.1f}% of Target")
        c3.metric("📦 Remaining Balance", f"{(t_target - t_ach):,.0f} Cases")
        
        st.caption("Target Achievement Progress:")
        st.progress(min(int(ach_pct), 100))
        st.markdown("<br>", unsafe_allow_html=True)
        # ----------------------------------------
        
        total_row = pd.DataFrame([{'Category': 'GRAND TOTAL', 'Flavours': '', 'Target': t_target, 'Achievement': t_ach, 'Sales_2025': t_2025, 'Value': t_val}])
        total_row = calculate_metrics(total_row)
        summary_disp = pd.concat([summary, total_row], ignore_index=True)
        
        st.dataframe(highlight_badass_style(summary_disp), use_container_width=True, height=600, hide_index=True)
        
        # --- NEW TOP PRODUCTS CHART ---
        st.markdown("#### 📈 Top 5 Best Selling Products")
        top5 = summary[summary['Category'] != '0'].sort_values('Value', ascending=False).head(5)
        if not top5.empty:
            st.bar_chart(top5.set_index('Category')['Value'], color="#E20613", height=250)
        # ------------------------------
        
        st.markdown("---")
        st.subheader("📊 INDIVIDUAL TSO SUMMARY LIST")
        tsos = rsm_data['TSO'].unique()
        for t in tsos:
            tso_data = rsm_data[rsm_data['TSO'] == t]
            tso_bdm = tso_data['BDM'].iloc[0]
            tso_rsm = tso_data['RSM_Original'].iloc[0] if 'RSM_Original' in tso_data.columns else rsm_name
                
            st.markdown(f"""
            <div class="vip-box">
                <span class="vip-text">BDM:</span> {tso_bdm} &nbsp;|&nbsp; 
                <span class="vip-text">RSM/ASM:</span> {tso_rsm} &nbsp;|&nbsp; 
                <span class="vip-text">TSO:</span> {t}
            </div>
            """, unsafe_allow_html=True)
            
            tso_grouped = tso_data.groupby(['Category', 'Flavours'], dropna=False, as_index=False).sum(numeric_only=True)
            tso_display = enforce_master_sequence(tso_grouped)
            tso_display = calculate_metrics(tso_display)
            
            tso_total = pd.DataFrame([{'Category': 'TOTAL', 'Flavours': '', 'Target': tso_display['Target'].sum(), 'Achievement': tso_display['Achievement'].sum(), 'Sales_2025': tso_display['Sales_2025'].sum(), 'Value': tso_display['Value'].sum()}])
            tso_total = calculate_metrics(tso_total)
            tso_display = pd.concat([tso_display, tso_total], ignore_index=True)
            
            st.dataframe(highlight_badass_style(tso_display), use_container_width=True, hide_index=True)

elif menu == "📈 BDM Summary":
    st.header("Step 3: BDM Grand Summary (All RSMs)")
    
    if db.empty:
        st.warning("No data found in the database yet.")
    else:
        bdm_list = db['BDM'].unique().tolist()
        if len(bdm_list) > 1:
            bdm_name = st.selectbox("Select BDM", ["All BDMs"] + bdm_list)
        else:
            bdm_name = "All BDMs"
            
        if bdm_name != "All BDMs":
            db = db[db['BDM'] == bdm_name]
            
        st.markdown(f"""
        <div class="vip-box" style="margin-bottom: 20px;">
            <div class="vip-text" style="font-size: 20px;">📌 BDM MASTER SUMMARY</div>
            <hr style="margin: 10px 0px; border-color: #E20613; opacity: 0.2;">
            <strong>Showing grand total for {db['RSM'].nunique()} RSMs and {db['TSO'].nunique()} TSOs.</strong>
        </div>
        """, unsafe_allow_html=True)
        
        summary = db.groupby(['Category', 'Flavours'], dropna=False, as_index=False).sum(numeric_only=True)
        summary = enforce_master_sequence(summary)
        summary = calculate_metrics(summary)
        
        # --- NEW DAD-IMPRESSING KPI DASHBOARD ---
        t_target = summary['Target'].sum()
        t_ach = summary['Achievement'].sum()
        t_val = summary['Value'].sum()
        t_2025 = summary['Sales_2025'].sum()
        ach_pct = (t_ach/t_target*100) if t_target > 0 else 0
        grw_pct = ((t_ach-t_2025)/t_2025*100) if t_2025 > 0 else 0
        
        st.markdown("### 🌟 BDM BUSINESS HIGHLIGHTS")
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Total Value Generated", f"Rs {t_val:,.0f}", f"{grw_pct:.1f}% vs Last Year")
        c2.metric("🎯 Total Achievement", f"{t_ach:,.0f} Cases", f"{ach_pct:.1f}% of Target")
        c3.metric("📦 Remaining Balance", f"{(t_target - t_ach):,.0f} Cases")
        
        st.caption("Overall Target Achievement Progress:")
        st.progress(min(int(ach_pct), 100))
        st.markdown("<br>", unsafe_allow_html=True)
        # ----------------------------------------
        
        total_row = pd.DataFrame([{'Category': 'GRAND TOTAL', 'Flavours': '', 'Target': t_target, 'Achievement': t_ach, 'Sales_2025': t_2025, 'Value': t_val}])
        total_row = calculate_metrics(total_row)
        summary_disp = pd.concat([summary, total_row], ignore_index=True)
        
        st.dataframe(highlight_badass_style(summary_disp), use_container_width=True, height=600, hide_index=True)
        
        st.markdown("---")
        st.subheader("📊 INDIVIDUAL RSM SUMMARY LIST")
        rsms = db['RSM'].unique()
        for r in rsms:
            rsm_data = db[db['RSM'] == r]
            
            st.markdown(f"""
            <div class="vip-box">
                <span class="vip-text">RSM/ASM:</span> {r}
            </div>
            """, unsafe_allow_html=True)
            
            rsm_grouped = rsm_data.groupby(['Category', 'Flavours'], dropna=False, as_index=False).sum(numeric_only=True)
            rsm_display = enforce_master_sequence(rsm_grouped)
            rsm_display = calculate_metrics(rsm_display)
            
            rsm_total = pd.DataFrame([{'Category': 'TOTAL', 'Flavours': '', 'Target': rsm_display['Target'].sum(), 'Achievement': rsm_display['Achievement'].sum(), 'Sales_2025': rsm_display['Sales_2025'].sum(), 'Value': rsm_display['Value'].sum()}])
            rsm_total = calculate_metrics(rsm_total)
            
            st.dataframe(highlight_badass_style(rsm_total), use_container_width=True, hide_index=True)

elif menu == "⚙️ Database Management":
    st.header("Database Management")
    st.write(f"Total products in Database: {len(db)}")
    st.dataframe(db)
