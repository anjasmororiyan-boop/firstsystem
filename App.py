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
        # MASTER AKSES ROLE BARU (MATRIKS OTORISASI MENU)
        "mst_roles_permission": [
            {"role_id": "OWNER", "allow_dashboard": True, "allow_wms": True, "allow_pr": True, "allow_master": True},
            {"role_id": "MANAGER", "allow_dashboard": True, "allow_wms": True, "allow_pr": True, "allow_master": False},
            {"role_id": "STAFF", "allow_dashboard": True, "allow_wms": False, "allow_pr": True, "allow_master": False}
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
        
        if table_name == "mst_items" and not df.empty and "functions" not in df.columns:
            df["functions"] = "Inventory, Purchase"
                
        elif table_name == "mst_users" and not df.empty:
            if "department_id" not in df.columns:
                df["department_id"] = "DEP-WH"
            if "accessible_warehouses" not in df.columns:
                df["accessible_warehouses"] = None
                df["accessible_warehouses"] = df["accessible_warehouses"].apply(lambda x: [])
                
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
    if df_settings.empty: return f"{doc_type_code}-ERROR"
    idx = df_settings[df_settings['doc_type'] == doc_type_code].index
    if len(idx) == 0: return None
    
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
                    'id': user_data.get('user_id', 'USR-UNKNOWN'),
                    'name': user_data.get('employee_name', 'Unknown Employee'), 
                    'role': user_data.get('role_id', 'STAFF'),
                    'dept_id': user_data.get('department_id', 'DEP-WH'),
                    'warehouses': user_wh
                }
                st.session_state['logged_in'] = True
                
                # Cek menu pertama yang diizinkan untuk di-rerun otomatis
                df_perm = load_cloud_data("mst_roles_permission")
                role = user_data.get('role_id', 'STAFF')
                r_perm = df_perm[df_perm['role_id'] == role].iloc[0].to_dict() if not df_perm.empty and role in df_perm['role_id'].values else {}
                
                if r_perm.get('allow_dashboard', True): st.session_state['active_menu'] = "Dashboard Utama"
                elif r_perm.get('allow_pr', True): st.session_state['active_menu'] = "📥 Pengadaan (PR)"
                else: st.session_state['active_menu'] = "WMS & Gudang"
                
                st.rerun()
            else:
                st.error("Kredensial salah!")
        else:
            st.error("Data master user kosong di sistem!")

# --- FASE 2: APLIKASI UTAMA ---
else:
    info = st.session_state['user_info']
    
    # ⚙️ LOGIKA HAK AKSES MENU DINAMIS BERDASARKAN PARAMETER ROLE
    df_perm = load_cloud_data("mst_roles_permission")
    user_role = info.get('role', 'STAFF')
    role_perm = df_perm[df_perm['role_id'] == user_role].iloc[0].to_dict() if not df_perm.empty and user_role in df_perm['role_id'].values else {"allow_dashboard": True, "allow_wms": False, "allow_pr": True, "allow_master": False}
    
    menu_options = []
    menu_icons = []
    
    if role_perm.get('allow_dashboard', True):
        menu_options.append("Dashboard Utama"); menu_icons.append("speedometer2")
    if role_perm.get('allow_wms', True):
        menu_options.append("WMS & Gudang"); menu_icons.append("box-seam")
    if role_perm.get('allow_pr', True):
        menu_options.append("📥 Pengadaan (PR)"); menu_icons.append("cart-check")
    if role_perm.get('allow_master', True):
        menu_options.append("⚙️ Master Data"); menu_icons.append("database-gear")
        
    # Jika menu aktif tidak ada di daftar menu yang diizinkan, force reset
    if st.session_state['active_menu'] not in menu_options and menu_options:
        st.session_state['active_menu'] = menu_options[0]

    with st.sidebar:
        st.subheader("🏬 ERPOS Control Panel")
        st.caption(f"User: **{info.get('name')}** | Role: ` {info.get('role')} `")
        df_d_info = load_cloud_data("mst_departments")
        current_dept_id = info.get('dept_id', 'DEP-WH')
        dept_name = df_d_info[df_d_info['department_id'] == current_dept_id]['department_name'].values[0] if not df_d_info.empty and current_dept_id in df_d_info['department_id'].values else current_dept_id
        st.caption(f"Dept: **{dept_name}**")
        st.caption(f"Akses Gudang: `{', '.join(info.get('warehouses')) if info.get('warehouses') else 'TIDAK ADA'}`")
        st.write("---")
        
        if menu_options:
            selected_menu = option_menu(
                menu_title="Navigasi Modul ERP",
                options=menu_options,
                icons=menu_icons,
                menu_icon="layers-half",
                default_index=menu_options.index(st.session_state['active_menu']) if st.session_state['active_menu'] in menu_options else 0
            )
            if selected_menu != st.session_state['active_menu']:
                st.session_state['active_menu'] = selected_menu
                st.rerun()
        st.markdown("---")
        if st.button("🚪 Keluar Sistem", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.rerun()

    # --- ROUTER MENU TAMPILAN ---
    if st.session_state['active_menu'] == "Dashboard Utama":
        st.title("📊 Executive Dashboard & Analytics")
        st.info("Sistem Engine JSON Terkoneksi 100%.")
        
    elif st.session_state['active_menu'] == "WMS & Gudang":
        st.title("📦 Warehouse Management System (WMS)")
        df_wh_all = load_cloud_data("mst_warehouses")
        if not df_wh_all.empty:
            df_wh_accessible = df_wh_all[df_wh_all['warehouse_id'].isin(info.get('warehouses', []))]
            st.dataframe(df_wh_accessible, use_container_width=True, hide_index=True)
        else: st.info("Belum ada gudang terdaftar.")
            
    elif st.session_state['active_menu'] == "📥 Pengadaan (PR)":
        st.title("📥 Purchase Requisition (PR) Hub")
        tab_create_pr, tab_history_pr = st.tabs(["➕ Buat PR Baru", "📋 Riwayat Dokumen PR"])
        
        with tab_create_pr:
            df_items = load_cloud_data("mst_items")
            df_branches = load_cloud_data("mst_branches")
            df_wh = load_cloud_data("mst_warehouses")
            pr_setting = load_cloud_data("mst_doc_settings")
            pr_setting = pr_setting[pr_setting["doc_type"] == "PR-USER"] if not pr_setting.empty else pd.DataFrame()
            
            if df_items.empty: st.error("⚠️ Master Item kosong.")
            elif pr_setting.empty: st.error("❌ Modul PR-USER belum aktif di setting.")
            else:
                df_purchase_items = df_items[df_items['functions'].astype(str).str.contains("Purchase", na=False)] if 'functions' in df_items.columns else df_items
                item_options = [f"{row['item_id']} - {row['item_name']} ({row['uom_purchase']})" for _, row in df_purchase_items.iterrows()] if not df_purchase_items.empty else []
                branch_options = [f"{row['branch_id']} - {row['branch_name']}" for _, row in df_branches.iterrows()] if not df_branches.empty else []
                df_my_wh = df_wh[df_wh['warehouse_id'].isin(info.get('warehouses', []))] if not df_wh.empty else pd.DataFrame()
                wh_options = [f"{row['warehouse_id']} - {row['warehouse_name']}" for _, row in df_my_wh.iterrows()] if not df_my_wh.empty else ["Tidak ada akses"]
                
                with st.form("form_create_pr", clear_on_submit=True):
                    st.subheader("Create Purchase Request User")
                    st.text_input("Department Terkunci", value=info.get('dept_id'), disabled=True)
                    p_branch = st.selectbox("Company Branch Target *", branch_options)
                    p_wh = st.selectbox("Target Storage Warehouse *", wh_options)
                    p_item_sel = st.selectbox("Select Item", item_options)
                    p_qty = st.number_input("Qty *", min_value=0.01, value=1.0)
                    p_note = st.text_area("Remark")
                    
                    if st.form_submit_button("Submit PR"):
                        if not p_item_sel or "Tidak ada" in p_wh or not p_branch: st.error("Lengkapi form!")
                        else:
                            generated_pr_no = generate_document_number("PR-USER")
                            new_pr_doc = {
                                "pr_number": generated_pr_no, "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "department_id": info.get('dept_id'), "target_branch": p_branch.split(" - ")[0],
                                "target_warehouse": p_wh.split(" - ")[0], "item_id": p_item_sel.split(" - ")[0],
                                "qty_requested": p_qty, "created_by": info.get('name'), "status": "PENDING", "remark": p_note.strip()
                            }
                            df_pr_hist = load_cloud_data("trn_purchase_requisitions")
                            if save_cloud_data(pd.concat([df_pr_hist, pd.DataFrame([new_pr_doc])], ignore_index=True), "trn_purchase_requisitions"):
                                st.success(f"🎉 PR Berhasil diterbitkan: {generated_pr_no}"); st.rerun()
                                
        with tab_history_pr:
            st.dataframe(load_cloud_data("trn_purchase_requisitions"), use_container_width=True, hide_index=True)

    # ==================== MODUL PARAMETER MASTER DATA ====================
    elif st.session_state['active_menu'] == "⚙️ Master Data":
        st.title("⚙️ Pusat Konfigurasi Master Data ERP")
        
        tab_core, tab_import, tab_permission, tab_doc_master = st.tabs(["📁 CRUD Manual Komplet", "📥 Bulk Import Data Massal", "🔒 Permission Access Matrix", "🔏 Master Setting No Dokumen"])
        
        with tab_core:
            pilih_tabel_core = st.selectbox(
                "Pilih Tabel Komponen Master", 
                ["mst_departments", "mst_warehouses", "mst_users", "mst_items", "mst_units", "mst_uom_conversions", "mst_branches", "mst_suppliers"], 
                key="sel_core_pro"
            )
            df_core = load_cloud_data(pilih_tabel_core)
            st.dataframe(df_core, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            action_mode = st.radio("Pilih Operasi Data", ["➕ Tambah Data Baru", "❌ Hapus Data Terpilih"], horizontal=True)
            pk_col = df_core.columns[0] if not df_core.empty else 'id'
            
            if action_mode == "➕ Tambah Data Baru":
                if pilih_tabel_core == "mst_departments":
                    with st.form("form_dept", clear_on_submit=True):
                        d_id = st.text_input("Department ID"); d_name = st.text_input("Department Name")
                        if st.form_submit_button("Simpan"):
                            if d_id and d_name:
                                save_cloud_data(pd.concat([df_core, pd.DataFrame([{"department_id": d_id.upper().strip(), "department_name": d_name}])], ignore_index=True), pilih_tabel_core); st.rerun()
                
                elif pilih_tabel_core == "mst_warehouses":
                    df_br = load_cloud_data("mst_branches")
                    br_list = df_br['branch_id'].tolist() if not df_br.empty else ["SR-SOF0001-JS-01"]
                    with st.form("form_wh", clear_on_submit=True):
                        w_id = st.text_input("Warehouse ID"); w_name = st.text_input("Warehouse Name"); w_br = st.selectbox("Branch", br_list)
                        if st.form_submit_button("Simpan Gudang"):
                            if w_id and w_name:
                                save_cloud_data(pd.concat([df_core, pd.DataFrame([{"warehouse_id": w_id.upper().strip(), "warehouse_name": w_name, "branch_id": w_br}])], ignore_index=True), pilih_tabel_core); st.rerun()
                
                elif pilih_tabel_core == "mst_users":
                    dept_list = load_cloud_data("mst_departments")['department_id'].tolist()
                    wh_list = load_cloud_data("mst_warehouses")['warehouse_id'].tolist()
                    with st.form("form_user_new", clear_on_submit=True):
                        u_id = st.text_input("User ID"); u_name = st.text_input("Nama"); u_user = st.text_input("Username"); u_pass = st.text_input("Password")
                        u_role = st.selectbox("Role", ["OWNER", "MANAGER", "STAFF"]); u_dept = st.selectbox("Department", dept_list)
                        u_wh_selected = st.multiselect("Pilih Gudang Akses", wh_list)
                        if st.form_submit_button("Simpan User"):
                            new_u = {"user_id": u_id.upper(), "username": u_user, "password": u_pass, "role_id": u_role, "employee_name": u_name, "department_id": u_dept, "accessible_warehouses": u_wh_selected}
                            records = df_core.to_dict(orient="records"); records.append(new_u)
                            save_cloud_data(pd.DataFrame(records), pilih_tabel_core); st.success("User Terdaftar"); st.rerun()

                elif pilih_tabel_core == "mst_items":
                    list_uom = load_cloud_data("mst_units")["unit_id"].tolist() if not load_cloud_data("mst_units").empty else ["UOM-PCS"]
                    with st.form("form_item_manual", clear_on_submit=True):
                        i_id = st.text_input("item_id"); i_name = st.text_input("item_name"); i_type = st.selectbox("item_type", ["Bahan Baku", "Barang Jadi"])
                        i_cat = st.text_input("category"); i_uom_p = st.selectbox("uom_purchase", list_uom); i_uom_s = st.selectbox("uom_stock", list_uom)
                        f_inv = st.checkbox("Inventory"); f_sal = st.checkbox("Sales"); f_pur = st.checkbox("Purchase")
                        if st.form_submit_button("Simpan Item"):
                            fns = [k for k, v in {"Inventory": f_inv, "Sales": f_sal, "Purchase": f_pur}.items() if v]
                            new_i = {"item_id": i_id.upper(), "item_name": i_name, "item_type": i_type, "category": i_cat, "uom_purchase": i_uom_p, "uom_stock": i_uom_s, "min_stock": 10, "functions": ", ".join(fns)}
                            save_cloud_data(pd.concat([df_core, pd.DataFrame([new_i])], ignore_index=True), pilih_tabel_core); st.rerun()

            elif action_mode == "❌ Hapus Data Terpilih" and not df_core.empty:
                if st.button("Konfirmasi Hapus Permanen"):
                    save_cloud_data(df_core[df_core[pk_col] != st.selectbox("Pilih ID Hapus", df_core[pk_col].tolist())], pilih_tabel_core); st.rerun()

        # ==================== IMPLEMENTASI BULK IMPORT ====================
        with tab_import:
            pilih_target_bulk = st.selectbox("Pilih Target Tabel Bulk", ["mst_departments", "mst_warehouses", "mst_users", "mst_items"], key="sel_bulk_pro")
            templates = {"mst_departments": ["department_id", "department_name"], "mst_warehouses": ["warehouse_id", "warehouse_name", "branch_id"], "mst_users": ["user_id", "username", "password", "role_id", "employee_name", "department_id"], "mst_items": ["item_id", "item_name", "item_type", "category", "uom_purchase", "uom_stock", "min_stock", "functions"]}
            
            csv_string = io.StringIO()
            pd.DataFrame(columns=templates[pilih_target_bulk]).to_csv(csv_string, index=False)
            st.download_button(label=f"📥 Download Template CSV {pilih_target_bulk}", data=csv_string.getvalue(), file_name=f"template_{pilih_target_bulk}.csv", mime="text/csv")
            
            uploaded_file = st.file_uploader("Unggah CSV", type=["csv"])
            if uploaded_file is not None:
                df_upload = pd.read_csv(uploaded_file)
                if st.button("🚀 Konfirmasi Import Massal"):
                    df_curr = load_cloud_data(pilih_target_bulk)
                    if pilih_target_bulk == "mst_users" and "accessible_warehouses" not in df_upload.columns:
                        df_upload["accessible_warehouses"] = None; df_upload["accessible_warehouses"] = df_upload["accessible_warehouses"].apply(lambda x: [])
                    save_cloud_data(pd.concat([df_curr, df_upload], ignore_index=True).drop_duplicates(subset=[templates[pilih_target_bulk][0]], keep="last"), pilih_target_bulk); st.success("Import Berhasil"); st.rerun()

        # ==================== TAB BARU: PERMISSION ACCESS MATRIX ====================
        with tab_permission:
            st.subheader("🔒 Matriks Hak Akses Otoritas Menu Jabatan (Role Permission)")
            df_roles = load_cloud_data("mst_roles_permission")
            st.dataframe(df_roles, use_container_width=True, hide_index=True)
            
            if not df_roles.empty:
                sel_role = st.selectbox("Pilih Jabatan yang Akan Dikonfigurasi Aksesnya", df_roles["role_id"].tolist())
                r_data = df_roles[df_roles["role_id"] == sel_role].iloc[0].to_dict()
                
                with st.form("form_role_perm"):
                    c_dash = st.checkbox("Izinkan Akses Dashboard Utama", value=bool(r_data.get('allow_dashboard', True)))
                    c_wms = st.checkbox("Izinkan Akses WMS & Gudang Inventory", value=bool(r_data.get('allow_wms', True)))
                    c_pr = st.checkbox("Izinkan Akses Modul 📥 Pengadaan (PR)", value=bool(r_data.get('allow_pr', True)))
                    c_master = st.checkbox("Izinkan Akses Modul ⚙️ Master Data", value=bool(r_data.get('allow_master', True)))
                    
                    if st.form_submit_button("Simpan Matriks Otoritas Hak Akses"):
                        df_roles.loc[df_roles["role_id"] == sel_role, "allow_dashboard"] = c_dash
                        df_roles.loc[df_roles["role_id"] == sel_role, "allow_wms"] = c_wms
                        df_roles.loc[df_roles["role_id"] == sel_role, "allow_pr"] = c_pr
                        df_roles.loc[df_roles["role_id"] == sel_role, "allow_master"] = c_master
                        
                        if save_cloud_data(df_roles, "mst_roles_permission"):
                            st.success(f"🎉 Sukses Memperbarui Hak Akses Menu Untuk Role `{sel_role}`!")
                            st.rerun()

        # ==================== MASTER SETTING PENOMORAN DOKUMEN ====================
        with tab_doc_master:
            df_doc_settings = load_cloud_data("mst_doc_settings")
            st.dataframe(df_doc_settings, use_container_width=True, hide_index=True)
            with st.form("form_setting_doc_dynamic"):
                d_type = st.selectbox("Pilih Modul Transaksi Sistem (Konek Otomatis)", ["PR-USER", "PR-PURCHASING", "PO", "GR"])
                d_name = st.text_input("Nama Panjang Modul Transaksi")
                d_init_doc = st.text_input("Initial Kode Dokumen (Maks 3 Huruf)").upper().strip()
                d_init_comp = st.text_input("Initial Kode Perusahaan (Maks 4 Huruf)").upper().strip()
                
                if st.form_submit_button("Simpan & Hubungkan Modul"):
                    if d_init_doc and d_init_comp:
                        idx_match = df_doc_settings[df_doc_settings['doc_type'] == d_type].index
                        if len(idx_match) > 0:
                            df_doc_settings.loc[idx_match[0], 'initial_doc'] = d_init_doc
                            df_doc_settings.loc[idx_match[0], 'initial_company'] = d_init_comp
                        save_cloud_data(df_doc_settings, "mst_doc_settings"); st.success("Modul Terhubung!"); st.rerun()
