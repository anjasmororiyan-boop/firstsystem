import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import json
import os
import io
import datetime

# --- KONFIGURASI UTAMA ---
st.set_page_config(page_title="ERPOS Enterprise", page_icon="🏬", layout="wide")
DATA_FILE = "data/erpos_cloud_data.json"

# --- DATABASE ENGINE ---
def init_database():
    if not os.path.exists("data"): os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        default_data = {
            "mst_departments": [{"department_id": "DEP-PROD", "department_name": "Production"}],
            "mst_warehouses": [{"warehouse_id": "WH-HQ", "warehouse_name": "Gudang Pusat", "branch_id": "HQ"}],
            "mst_users": [
                {"user_id": "SA-001", "username": "admin", "password": "123", "role_id": "OWNER", "employee_name": "Admin System", "department_id": "DEP-PROD", "accessible_warehouses": ["WH-HQ"]}
            ],
            "mst_items": [], "mst_units": [], "mst_branches": [], "mst_suppliers": [],
            "mst_doc_settings": [{"doc_type": "PR-USER", "doc_name": "PR User", "initial_doc": "PR", "initial_company": "SRR", "last_year_month": "202606", "last_counter": 0}, {"doc_type": "PO", "doc_name": "PO", "initial_doc": "PO", "initial_company": "SRR", "last_year_month": "202606", "last_counter": 0}],
            "trn_purchase_requisitions": [], "trn_purchase_orders": []
        }
        with open(DATA_FILE, "w") as f: json.dump(default_data, f, indent=4)

init_database()

# --- HELPER FUNCTIONS ---
def load_cloud_data(table_name):
    try:
        with open(DATA_FILE, "r") as f: data = json.load(f)
        return pd.DataFrame(data.get(table_name, []))
    except: return pd.DataFrame()

def save_cloud_data(df, table_name):
    try:
        with open(DATA_FILE, "r") as f: data = json.load(f)
        data[table_name] = df.to_dict(orient="records")
        with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)
        return True
    except: return False

# --- SESSION & LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.update({'logged_in': False, 'info': None})

if not st.session_state['logged_in']:
    st.title("Login Sistem")
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Login"):
        df_u = load_cloud_data("mst_users")
        match = df_u[(df_u['username'] == u) & (df_u['password'] == p)]
        if not match.empty:
            st.session_state.update({'logged_in': True, 'info': match.iloc[0].to_dict()})
            st.rerun()
        else: st.error("Login Gagal")
else:
    info = st.session_state['info']
    with st.sidebar:
        st.write(f"User: {info.get('employee_name')}")
        menu = option_menu("Navigasi", ["Dashboard", "Pengadaan", "Master Data"])
        if st.button("Logout"): st.session_state['logged_in'] = False; st.rerun()

    # --- ROUTING SEDERHANA ---
    if menu == "Dashboard":
        st.title("Dashboard")
        
    elif menu == "Pengadaan":
        t1, t2 = st.tabs(["Purchase Request", "Purchase Order (Single-Type)"])
        with t1:
            st.write("PR Module")
        with t2:
            st.write("PO Single-Type Multi-Item")
            items = load_cloud_data("mst_items")
            if not items.empty:
                t_type = st.selectbox("Pilih Tipe Item untuk PO", items['item_type'].unique())
                st.data_editor(pd.DataFrame([{"Item": "", "Qty": 1.0}]))
                if st.button("Simpan PO"): st.success("PO Diterbitkan")
    
    elif menu == "Master Data":
        tbl = st.selectbox("Pilih Tabel", ["mst_items", "mst_users", "mst_warehouses", "mst_departments"])
        st.dataframe(load_cloud_data(tbl))

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
