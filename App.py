import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import json
import os
import io
import datetime

# 1. KONFIGURASI UTAMA
st.set_page_config(page_title="ERPOS System - Enterprise Engine", page_icon="🏬", layout="wide")

DATA_FILE = "data/erpos_cloud_data.json"

# --- ENGINE DATABASE CORE JSON ---
def init_database():
    default_data = {
        "mst_departments": [
            {"department_id": "DEP-PROD", "department_name": "Production & Central Kitchen"},
            {"department_id": "DEP-WH", "department_name": "Warehouse & Logistics"},
            {"department_id": "DEP-RET", "department_name": "Retail Outlet & Sales"}
        ],
        "mst_warehouses": [
            {"warehouse_id": "WH-CP-RAW", "warehouse_name": "Gudang Bahan Baku CP Depok", "branch_id": "SR-CKT0001-DP-01"},
            {"warehouse_id": "WH-CP-WIP", "warehouse_name": "Gudang Setengah Jadi / Finishing", "branch_id": "SR-CKT0001-DP-01"},
            {"warehouse_id": "WH-HQ-DIST", "warehouse_name": "Gudang Distribusi Pusat Jakarta", "branch_id": "SR-SOF0001-JS-01"}
        ],
        "mst_users": [
            {
                "user_id": "USR-001", 
                "username": "riyan_owner", 
                "password": "admin123", 
                "role_id": "OWNER", 
                "employee_name": "Riyan Anjasmoro",
                "department_id": "DEP-PROD",
                "accessible_warehouses": ["WH-CP-RAW", "WH-CP-WIP", "WH-HQ-DIST"]
            },
            {
                "user_id": "USR-002", 
                "username": "staff_wh", 
                "password": "user123", 
                "role_id": "STAFF", 
                "employee_name": "Budi Logistik",
                "department_id": "DEP-WH",
                "accessible_warehouses": ["WH-CP-RAW"]
            }
        ],
        "mst_units": [
            {"unit_id": "UOM-KG", "unit_name": "Kilogram", "Keterangan": "Satuan Massa Dasar"},
            {"unit_id": "UOM-PCS", "unit_name": "Pieces", "Keterangan": "Satuan Roti Jadi"}
        ],
        "mst_uom_conversions": [
            {"conversion_id": "CNV-001", "from_uom": "UOM-KG", "to_uom": "UOM-GR", "operator": "Kali (*)", "factor": 1000}
        ],
        "mst_items": [
            {"item_id": "ITM-001", "item_name": "Tepung Terigu Cakra Kembar", "item_type": "Bahan Baku", "category": "Tepung", "uom_purchase": "UOM-KG", "uom_stock": "UOM-KG", "min_stock": 50, "functions": "Inventory, Purchase"}
        ],
        "mst_branches": [
            {"branch_id": "SR-SOF0001-JS-01", "branch_name": "Supporting Office", "branch_type": "Head Office", "address": "Jl TB Simatupang"},
            {"branch_id": "SR-CKT0001-DP-01", "branch_name": "Central Production Depok", "branch_type": "Central Production", "address": "Area 700m2"}
        ],
        "mst_suppliers": [
            {"supplier_id": "SPL-001", "supplier_name": "PT Sumber Terigu Nusantara", "phone": "0812345678", "payment_terms": "COD"}
        ],
        "mst_doc_settings": [
            {"doc_type": "PR-USER", "doc_name": "Purchase Request User", "initial_doc": "PR", "initial_company": "SRR", "last_year_month": "202606", "last_counter": 0},
            {"doc_type": "PR-PURCHASING", "doc_name": "Purchase Request Purchasing", "initial_doc": "PP", "initial_company": "SRR", "last_year_month": "202606", "last_counter": 0},
            {"doc_type": "PO", "doc_name": "Purchase Order", "initial_doc": "PO", "initial_company": "SRR", "last_year_month": "202606", "last_counter": 0},
            {"doc_type": "GR", "doc_name": "Goods Receipt / Penerimaan", "initial_doc": "GR", "initial_company": "SRR", "last_year_month": "202606", "last_counter": 0}
        ],
        "trn_purchase_requisitions": []
    }
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump(default_data, f, indent=4)

init_database()

def load_cloud_data(table_name):
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        
        if table_name not in data:
            data[table_name] = []
            
        df = pd.DataFrame(data.get(table_name, []))
        
        if table_name == "mst_items":
            if df.empty:
                return pd.DataFrame(columns=["item_id", "item_name", "item_type", "category", "uom_purchase", "uom_stock", "min_stock", "functions"])
            if "functions" not in df.columns:
                df["functions"] = "Inventory, Purchase"
                
        elif table_name == "mst_users":
            if df.empty:
                return pd.DataFrame(columns=["user_id", "username", "password", "role_id", "employee_name", "department_id", "accessible_warehouses"])
            
            if "department_id" not in df.columns:
                df["department_id"] = "DEP-WH"
                
            # FIX SOLUSI VALUEERROR: Menggunakan penugasan baris per baris yang aman bagi Pandas untuk kolom berisi list []
            if "accessible_warehouses" not in df.columns:
                df["accessible_warehouses"] = None
                df["accessible_warehouses"] = df["accessible_warehouses"].apply(lambda x: [])
                
        elif table_name == "mst_warehouses":
            if df.empty:
                return pd.DataFrame(columns=["warehouse_id", "warehouse_name", "branch_id"])
                
        elif table_name == "mst_departments":
            if df.empty:
                return pd.DataFrame(columns=["department_id", "department_name"])
                
        return df
    except Exception:
        return pd.DataFrame()

def save_cloud_data(df, table_name):
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        data[table_name] = df.to_dict(orient="records")
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Gagal simpan data cloud: {e}")
        return False

def generate_document_number(doc_type_code):
    df_settings = load_cloud_data("mst_doc_settings")
    if df_settings.empty:
        return f"{doc_type_code}-ERROR"
    
    idx = df_settings[df_settings['doc_type'] == doc_type_code].index
    if len(idx) == 0:
        return None
    
    setting = df_settings.loc[idx[0]].to_dict()
    now = datetime.datetime.now()
    current_ym = now.strftime("%Y%m")
    
    if str(setting.get('last_year_month', '')) != current_ym:
        next_counter = 1
    else:
        next_counter = int(setting.get('last_counter', 0)) + 1
        
    init_doc = str(setting.get('initial_doc', doc_type_code)).strip().upper()
    init_comp = str(setting.get('initial_company', 'SRR')).strip().upper()
    str_counter = str(next_counter).zfill(6)
    
    formatted_number = f"{init_doc}-{init_comp}{current_ym}{str_counter}"
    
    df_settings.loc[idx[0], 'last_year_month'] = current_ym
    df_settings.loc[idx[0], 'last_counter'] = next_counter
    save_cloud_data(df_settings, "mst_doc_settings")
    
    return formatted_number

# 3. SESSION STATE MANAGEMENT
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None
if 'active_menu' not in st.session_state:
    st.session_state['active_menu'] = "Dashboard Utama"

# --- FASE 1: GERBANG LOGIN ---
if not st.session_state['logged_in']:
    st.title("🔐 ERPOS System - Enterprise Procurement Core")
    username_input = st.text_input("Username / ID Pengguna")
    password_input = st.text_input("Password Keamanan", type="password")
    
    if st.button("Masuk Ke Sistem ERPOS", type="primary", use_container_width=True):
        df_users = load_cloud_data("mst_users")
        if not df_users.empty:
            user_match = df_users[(df_users['username'].astype(str).str.strip() == username_input.strip()) & 
                                  (df_users['password'].astype(str).str.strip() == str(password_input).strip())]
            if not user_match.empty:
                user_data = user_match.iloc[0].to_dict()
                
                user_wh = user_data.get('accessible_warehouses', [])
                if isinstance(user_wh, str):
                    user_wh = [x.strip() for x in user_wh.split(",") if x.strip()]
                elif not isinstance(user_wh, list):
                    user_wh = []
                    
                st.session_state['user_info'] = {
                    'id': user_data['user_id'],
                    'name': user_data['employee_name'], 
                    'role': user_data['role_id'],
                    'dept_id': user_data.get('department_id', 'DEP-WH'),
                    'warehouses': user_wh
                }
                st.session_state['logged_in'] = True
                st.session_state['active_menu'] = "📥 Pengadaan (PR)"
                st.rerun()
            else:
                st.error("Kredensial salah!")
        else:
            st.error("Data master user kosong di sistem!")

# --- FASE 2: APLIKASI UTAMA ---
else:
    info = st.session_state['user_info']
    
    with st.sidebar:
        st.subheader("🏬 ERPOS Control Panel")
        st.caption(f"User: **{info['name']}** ({info['role']})")
        
        df_d_info = load_cloud_data("mst_departments")
        dept_name = info['dept_id']
        if not df_d_info.empty and 'department_id' in df_d_info.columns and info['dept_id'] in df_d_info['department_id'].values:
            dept_name = df_d_info[df_d_info['department_id'] == info['dept_id']]['department_name'].values[0]
            
        st.caption(f"Dept: **{dept_name}**")
        st.caption(f"Akses Gudang: `{', '.join(info['warehouses']) if info['warehouses'] else 'TIDAK ADA AKSES'}`")
        st.write("---")
        
        selected_menu = option_menu(
            menu_title="Navigasi Modul ERP",
            options=["Dashboard Utama", "WMS & Gudang", "📥 Pengadaan (PR)", "⚙️ Master Data"],
            icons=["speedometer2", "box-seam", "cart-check", "database-gear"],
            menu_icon="layers-half",
            default_index=["Dashboard Utama", "WMS & Gudang", "📥 Pengadaan (PR)", "⚙️ Master Data"].index(st.session_state['active_menu'])
        )
        if selected_menu != st.session_state['active_menu']:
            st.session_state['active_menu'] = selected_menu
            st.rerun()
        st.markdown("---")
        if st.button("🚪 Keluar Sistem", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.rerun()

    if st.session_state['active_menu'] == "Dashboard Utama":
        st.title("📊 Executive Dashboard & Analytics")
        st.info("Sistem Engine JSON Terkoneksi 100%.")
        
    elif st.session_state['active_menu'] == "WMS & Gudang":
        st.title("📦 Warehouse Management System (WMS)")
        st.subheader("Gudang yang Dapat Anda Akses:")
        df_wh_all = load_cloud_data("mst_warehouses")
        if not df_wh_all.empty:
            df_wh_accessible = df_wh_all[df_wh_all['warehouse_id'].isin(info['warehouses'])]
            st.dataframe(df_wh_accessible, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada gudang terdaftar.")
            
    # ==================== MODUL: PROCUREMENT PURCHASE REQUISITION (PR-USER) ====================
    elif st.session_state['active_menu'] == "📥 Pengadaan (PR)":
        st.title("📥 Purchase Requisition (PR) Hub")
        
        tab_create_pr, tab_history_pr = st.tabs(["➕ Buat PR Baru", "📋 Riwayat Dokumen PR"])
        
        with tab_create_pr:
            df_items = load_cloud_data("mst_items")
            df_branches = load_cloud_data("mst_branches")
            df_check_setting = load_cloud_data("mst_doc_settings")
            df_wh = load_cloud_data("mst_warehouses")
            
            pr_setting = df_check_setting[df_check_setting["doc_type"] == "PR-USER"] if not df_check_setting.empty else pd.DataFrame()
            
            if df_items.empty:
                st.error("⚠️ Form terkunci! Belum ada data Master Item.")
            elif pr_setting.empty:
                st.error("❌ TRANSAKSI TERKUNCI: Modul transaksi 'PR-USER' belum diaktifkan di Master Data!")
            else:
                setting_details = pr_setting.iloc[0].to_dict()
                st.success(f"🔗 Modul Aktif Terhubung Resmi dengan Pola: `{setting_details['initial_doc']}-{setting_details['initial_company']}YYYYMMXXXXXX`")
                
                df_purchase_items = df_items[df_items['functions'].astype(str).str.contains("Purchase", na=False)] if 'functions' in df_items.columns else df_items
                item_options = [f"{row['item_id']} - {row['item_name']} ({row['uom_purchase']})" for _, row in df_purchase_items.iterrows()] if not df_purchase_items.empty else []
                branch_options = [f"{row['branch_id']} - {row['branch_name']}" for _, row in df_branches.iterrows()] if not df_branches.empty else []
                
                df_my_wh = df_wh[df_wh['warehouse_id'].isin(info['warehouses'])] if not df_wh.empty else pd.DataFrame()
                wh_options = [f"{row['warehouse_id']} - {row['warehouse_name']}" for _, row in df_my_wh.iterrows()] if not df_my_wh.empty else ["Tidak ada akses gudang"]
                
                with st.form("form_create_pr", clear_on_submit=True):
                    st.subheader("Create Purchase Request User")
                    st.text_input("Department Terkunci (Sesuai User)", value=info['dept_id'], disabled=True)
                    p_branch = st.selectbox("Company Branch Target *", branch_options)
                    p_wh = st.selectbox("Target Storage Warehouse Akses Anda *", wh_options)
                    p_item_sel = st.selectbox("Select Item", item_options)
                    p_qty = st.number_input("Qty *", min_value=0.01, value=1.0, format="%.2f")
                    p_note = st.text_area("Remark (Catatan Tambahan)")
                    
                    if st.form_submit_button("Save As Draft / Submit PR"):
                        if not p_item_sel or "Tidak ada" in p_wh or not p_branch:
                            st.error("Pilihan item, branch atau gudang tidak boleh kosong!")
                        else:
                            generated_pr_no = generate_document_number("PR-USER")
                            selected_item_id = p_item_sel.split(" - ")[0]
                            target_branch_id = p_branch.split(" - ")[0]
                            target_wh_id = p_wh.split(" - ")[0]
                            
                            new_pr_doc = {
                                "pr_number": generated_pr_no,
                                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "department_id": info['dept_id'],
                                "target_branch": target_branch_id,
                                "target_warehouse": target_wh_id,
                                "item_id": selected_item_id,
                                "qty_requested": p_qty,
                                "created_by": info['name'],
                                "status": "DRAFT/PENDING",
                                "remark": p_note.strip()
                            }
                            
                            df_pr_hist = load_cloud_data("trn_purchase_requisitions")
                            df_pr_updated = pd.concat([df_pr_hist, pd.DataFrame([new_pr_doc])], ignore_index=True)
                            
                            if save_cloud_data(df_pr_updated, "trn_purchase_requisitions"):
                                st.success(f"🎉 Sukses! Dokumen Purchase Request User terbit otomatis: **{generated_pr_no}**")
                                st.rerun()
                                
        with tab_history_pr:
            st.subheader("Data Monitor Log Transaksi Permintaan Pembelian (PR)")
            df_pr_all = load_cloud_data("trn_purchase_requisitions")
            if not df_pr_all.empty:
                st.dataframe(df_pr_all, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada rekam data dokumen PR yang diterbitkan bulan ini.")

    # ==================== MODUL PARAMETER MASTER DATA ====================
    elif st.session_state['active_menu'] == "⚙️ Master Data":
        st.title("⚙️ Pusat Konfigurasi Master Data ERP")
        
        tab_core, tab_import, tab_doc_master = st.tabs(["📁 CRUD Manual Komplet", "📥 Bulk Import Data", "🔏 Master Setting No Dokumen"])
        
        with tab_core:
            pilih_tabel_core = st.selectbox(
                "Pilih Tabel Komponen Master", 
                ["mst_departments", "mst_warehouses", "mst_users", "mst_items", "mst_units", "mst_branches", "mst_suppliers"], 
                key="sel_core_pro"
            )
            df_core = load_cloud_data(pilih_tabel_core)
            st.subheader(f"Data Live Tabel `{pilih_tabel_core}`")
            if not df_core.empty:
                st.dataframe(df_core, use_container_width=True, hide_index=True)
            else:
                st.info("Tabel ini masih kosong.")
            
            st.markdown("---")
            action_mode = st.radio("Pilih Operasi Data", ["➕ Tambah Data Baru", "❌ Hapus Data Terpilih"], horizontal=True)
            pk_col = df_core.columns[0] if not df_core.empty else 'id'
            
            if action_mode == "➕ Tambah Data Baru":
                if pilih_tabel_core == "mst_departments":
                    with st.form("form_dept", clear_on_submit=True):
                        d_id = st.text_input("Department ID (Contoh: DEP-QA)")
                        d_name = st.text_input("Department Name")
                        if st.form_submit_button("Simpan Departemen"):
                            if d_id.strip() == "" or d_name.strip() == "":
                                st.error("ID dan Nama Departemen wajib diisi!")
                            else:
                                new_row = pd.DataFrame([{"department_id": d_id.upper().strip(), "department_name": d_name.strip()}])
                                if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core):
                                    st.rerun()
                
                elif pilih_tabel_core == "mst_warehouses":
                    df_br = load_cloud_data("mst_branches")
                    br_list = df_br['branch_id'].tolist() if not df_br.empty else ["SR-SOF0001-JS-01"]
                    with st.form("form_wh", clear_on_submit=True):
                        w_id = st.text_input("Warehouse ID (Contoh: WH-CK-PACK)")
                        w_name = st.text_input("Warehouse Name")
                        w_br = st.selectbox("Hubungkan ke Cabang (Branch)", br_list)
                        if st.form_submit_button("Simpan Gudang"):
                            if w_id.strip() == "" or w_name.strip() == "":
                                st.error("ID dan Nama Gudang wajib diisi!")
                            else:
                                new_row = pd.DataFrame([{"warehouse_id": w_id.upper().strip(), "warehouse_name": w_name.strip(), "branch_id": w_br}])
                                if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core):
                                    st.rerun()
                
                elif pilih_tabel_core == "mst_users":
                    df_dept_opt = load_cloud_data("mst_departments")
                    df_wh_opt = load_cloud_data("mst_warehouses")
                    
                    dept_list = df_dept_opt['department_id'].tolist() if not df_dept_opt.empty else ["DEP-WH"]
                    wh_list = df_wh_opt['warehouse_id'].tolist() if not df_wh_opt.empty else []
                    
                    with st.form("form_user_new", clear_on_submit=True):
                        u_id = st.text_input("User/Employee ID")
                        u_name = st.text_input("Nama Lengkap Karyawan")
                        u_user = st.text_input("Username Login")
                        u_pass = st.text_input("Password", type="password")
                        u_role = st.selectbox("Role Hak Akses Menu", ["OWNER", "MANAGER", "STAFF"])
                        u_dept = st.selectbox("Hubungkan ke Departemen", dept_list)
                        
                        st.markdown("**🔒 Otorisasi Hak Akses Gudang (Bisa Pilih Lebih dari Satu):**")
                        u_wh_selected = st.multiselect("Pilih Gudang Terkait", wh_list)
                        
                        if st.form_submit_button("Simpan User & Akses"):
                            if u_id.strip() == "" or u_user.strip() == "" or u_pass.strip() == "":
                                st.error("ID User, Username, dan Password wajib diisi!")
                            else:
                                # FIX DATA FRAME CONCAT PADA OBJECT LIST: membungkus baris data baru ke dalam format list record mentah sebelum diubah ke DataFrame
                                new_user_data = {
                                    "user_id": u_id.upper().strip(),
                                    "username": u_user.strip(),
                                    "password": u_pass.strip(),
                                    "role_id": u_role,
                                    "employee_name": u_name.strip(),
                                    "department_id": u_dept,
                                    "accessible_warehouses": u_wh_selected
                                }
                                df_core_records = df_core.to_dict(orient="records")
                                df_core_records.append(new_user_data)
                                if save_cloud_data(pd.DataFrame(df_core_records), pilih_tabel_core):
                                    st.success("🎉 User Baru Berhasil Didaftarkan!")
                                    st.rerun()

                elif pilih_tabel_core == "mst_items":
                    df_uom_master = load_cloud_data("mst_units")
                    list_uom = df_uom_master["unit_id"].dropna().astype(str).tolist() if not df_uom_master.empty else ["UOM-PCS"]
                    with st.form("form_item_manual", clear_on_submit=True):
                        i_id = st.text_input("item_id")
                        i_name = st.text_input("item_name")
                        i_type = st.selectbox("item_type", ["Bahan Baku", "Barang Jadi", "WIP / Setengah Jadi"])
                        i_cat = st.text_input("category")
                        i_uom_purchase = st.selectbox("uom_purchase", list_uom)
                        i_uom_stock = st.selectbox("uom_stock", list_uom)
                        i_min = st.number_input("min_stock", min_value=0, value=10)
                        if st.form_submit_button("Simpan Item"):
                            new_row = pd.DataFrame([{"item_id": i_id.upper(), "item_name": i_name, "item_type": i_type, "category": i_cat, "uom_purchase": i_uom_purchase, "uom_stock": i_uom_stock, "min_stock": i_min, "functions": "Inventory, Purchase"}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core): st.rerun()

                elif pilih_tabel_core == "mst_units":
                    with st.form("form_uom", clear_on_submit=True):
                        u_id = st.text_input("unit_id")
                        u_name = st.text_input("unit_name")
                        if st.form_submit_button("Simpan UOM"):
                            new_row = pd.DataFrame([{"unit_id": u_id.upper(), "unit_name": u_name, "Keterangan": ""}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core): st.rerun()

                elif pilih_tabel_core == "mst_branches":
                    with st.form("form_br", clear_on_submit=True):
                        b_id = st.text_input("branch_id")
                        b_name = st.text_input("branch_name")
                        if st.form_submit_button("Simpan Cabang"):
                            new_row = pd.DataFrame([{"branch_id": b_id, "branch_name": b_name, "branch_type": "Outlet", "address": ""}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core): st.rerun()

                elif pilih_tabel_core == "mst_suppliers":
                    with st.form("form_spl", clear_on_submit=True):
                        s_id = st.text_input("supplier_id")
                        s_name = st.text_input("supplier_name")
                        if st.form_submit_button("Simpan Supplier"):
                            new_row = pd.DataFrame([{"supplier_id": s_id, "supplier_name": s_name, "phone": "", "payment_terms": "COD"}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core): st.rerun()

            elif action_mode == "❌ Hapus Data Terpilih" and not df_core.empty:
                id_pilih_hapus = st.selectbox("Pilih ID Data yang Akan Dihapus", df_core[pk_col].tolist())
                if st.button("Konfirmasi Hapus Permanen", type="primary"):
                    if save_cloud_data(df_core[df_core[pk_col] != id_pilih_hapus], pilih_tabel_core):
                        st.rerun()

        with tab_import:
            st.subheader("📥 Bulk Import System Terpusat (CSV Engine)")
            pilih_target_bulk = st.selectbox("Pilih Target Tabel Bulk", ["mst_departments", "mst_warehouses", "mst_users", "mst_items"], key="sel_bulk_pro")
            st.info(f"Silakan buat file CSV dengan header kolom yang sesuai dengan skema tabel `{pilih_target_bulk}` untuk melakukan penggabungan data massal.")

        # ==================== MASTER SETTING PENOMORAN DOKUMEN (INTERLOCKING RESMI) ====================
        with tab_doc_master:
            st.subheader("🔏 Master Kustomisasi Pola Penomoran Dokumen (Direct Interlocking)")
            df_doc_settings = load_cloud_data("mst_doc_settings")
            if not df_doc_settings.empty:
                st.dataframe(df_doc_settings, use_container_width=True, hide_index=True)
            
            with st.form("form_setting_doc_dynamic"):
                st.markdown("**⚙️ Pengaturan Parameter Cetak Nomor Dokumen Sistem**")
                LIST_MODUL_RESMI = ["PR-USER", "PR-PURCHASING", "PO", "GR"]
                d_type = st.selectbox("Pilih Modul Transaksi Sistem (Konek Otomatis)", LIST_MODUL_RESMI)
                
                if not df_doc_settings.empty and d_type in df_doc_settings["doc_type"].astype(str).tolist():
                    current_row = df_doc_settings[df_doc_settings["doc_type"] == d_type].iloc[0].to_dict()
                    default_name = current_row.get("doc_name", d_type)
                    default_init_doc = current_row.get("initial_doc", d_type[:2])
                    default_init_comp = current_row.get("initial_company", "SRR")
                else:
                    default_name = f"Modul {d_type}"
                    default_init_doc = d_type[:2]
                    default_init_comp = "SRR"
                
                d_name = st.text_input("Nama Panjang Modul Transaksi", value=default_name)
                col_d1, col_d2 = st.columns(2)
                with col_d1: d_init_doc = st.text_input("Initial Kode Dokumen (Maks 3 Huruf)", value=default_init_doc).upper().strip()
                with col_d2: d_init_comp = st.text_input("Initial Kode Perusahaan (Maks 4 Huruf)", value=default_init_comp).upper().strip()
                
                if st.form_submit_button("Simpan & Hubungkan Modul"):
                    if not d_init_doc or not d_init_comp: st.error("Gagal! Parameter tidak boleh kosong.")
                    else:
                        if df_doc_settings.empty: df_doc_settings = pd.DataFrame(columns=["doc_type", "doc_name", "initial_doc", "initial_company", "last_year_month", "last_counter"])
                        idx_match = df_doc_settings[df_doc_settings['doc_type'] == d_type].index
                        if len(idx_match) > 0:
                            df_doc_settings.loc[idx_match[0], 'doc_name'] = d_name
                            df_doc_settings.loc[idx_match[0], 'initial_doc'] = d_init_doc
                            df_doc_settings.loc[idx_match[0], 'initial_company'] = d_init_comp
                        else:
                            new_setting_row = {"doc_type": d_type, "doc_name": d_name, "initial_doc": d_init_doc, "initial_company": d_init_comp, "last_year_month": datetime.datetime.now().strftime("%Y%m"), "last_counter": 0}
                            df_doc_settings = pd.concat([df_doc_settings, pd.DataFrame([new_setting_row])], ignore_index=True)
                        if save_cloud_data(df_doc_settings, "mst_doc_settings"):
                            st.success(f"🎉 Hubungan antar-modul untuk `{d_type}` resmi terhubung!")
                            st.rerun()
