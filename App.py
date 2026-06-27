import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import json
import os
import io
import datetime

# --- 1. KONFIGURASI UTAMA ---
st.set_page_config(page_title="ERPOS Enterprise Industrial Suite", page_icon="🏬", layout="wide")
DATA_FILE = "data/erpos_cloud_data.json"

# --- 2. ENGINE DATABASE ---
def init_database():
    if not os.path.exists("data"): os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        default_data = {
            "mst_departments": [{"department_id": "DEP-PROD", "department_name": "Production"}],
            "mst_warehouses": [{"warehouse_id": "WH-HQ", "warehouse_name": "Gudang Pusat", "branch_id": "HQ"}],
            "mst_roles_permission": [
                {"role_id": "SUPERADMIN", "modules": ["Dashboard Utama", "WMS & Gudang", "📥 Pengadaan (PR/PO)", "⚙️ Master Data"], "actions": ["Read", "Create", "Edit", "Delete", "Cancel", "Import", "Export"]},
                {"role_id": "STAFF", "modules": ["Dashboard Utama", "📥 Pengadaan (PR/PO)"], "actions": ["Read", "Create"]}
            ],
            "mst_users": [
                {"user_id": "SA-001", "username": "superadmin", "password": "devpassword123", "role_id": "SUPERADMIN", "employee_name": "Developer System", "department_id": "DEP-PROD", "accessible_warehouses": ["WH-HQ"]}
            ],
            "mst_items": [], "mst_units": [], "mst_branches": [], "mst_suppliers": [],
            "mst_doc_settings": [{"doc_type": "PR-USER", "doc_name": "PR User", "initial_doc": "PR", "initial_company": "SRR", "last_year_month": "202606", "last_counter": 0}, {"doc_type": "PO", "doc_name": "PO", "initial_doc": "PO", "initial_company": "SRR", "last_year_month": "202606", "last_counter": 0}],
            "trn_purchase_requisitions": [], "trn_purchase_orders": []
        }
        with open(DATA_FILE, "w") as f: json.dump(default_data, f, indent=4)

init_database()

# --- 3. HELPER FUNCTIONS ---
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

def generate_document_number(doc_type_code):
    df_s = load_cloud_data("mst_doc_settings")
    idx = df_s[df_s['doc_type'] == doc_type_code].index
    if idx.empty: return f"{doc_type_code}-ERR"
    s = df_s.loc[idx[0]].to_dict()
    curr = datetime.datetime.now().strftime("%Y%m")
    ctr = int(s.get('last_counter', 0)) + 1 if str(s.get('last_year_month')) == curr else 1
    no = f"{s['initial_doc']}-{s['initial_company']}{curr}{str(ctr).zfill(6)}"
    df_s.loc[idx[0], ['last_year_month', 'last_counter']] = [curr, ctr]
    save_cloud_data(df_s, "mst_doc_settings")
    return no

# --- 4. LOGIN & SESSION ---
if 'logged_in' not in st.session_state: st.session_state.update({'logged_in': False, 'info': None, 'menu': "Dashboard Utama"})

if not st.session_state['logged_in']:
    st.title("🔐 Login ERPOS")
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
    df_perm = load_cloud_data("mst_roles_permission")
    role = info.get('role_id')
    perm = df_perm[df_perm['role_id'] == role].iloc[0].to_dict() if not df_perm.empty and role in df_perm['role_id'].values else {"modules": ["Dashboard Utama"], "actions": ["Read"]}
    
    with st.sidebar:
        st.write(f"User: {info.get('employee_name')}")
        sel = option_menu("Menu Utama", options=perm.get('modules'), default_index=0)
        if st.button("Logout"): st.session_state['logged_in'] = False; st.rerun()

    # --- 5. RENDER MODULES ---
    if sel == "Dashboard Utama":
        st.title("📊 Dashboard")
    elif sel == "📥 Pengadaan (PR/PO)":
        st.title("📥 Procurement Management")
        t1, t2 = st.tabs(["Purchase Request", "Purchase Order (Single-Type)"])
        with t2:
            # Logic PO Single-Type Multi-Item
            items = load_cloud_data("mst_items")
            if not items.empty:
                t_key = st.selectbox("Pilih Tipe Item untuk PO", items['item_type'].unique())
                grid = st.data_editor(pd.DataFrame([{"Item": "", "Qty": 1.0}]))
                if st.button("Simpan PO"): st.success("PO Diterbitkan")
    elif sel == "⚙️ Master Data":
        st.title("⚙️ Master Data")
        tbl = st.selectbox("Pilih Tabel", ["mst_items", "mst_users", "mst_warehouses", "mst_departments"])
        st.dataframe(load_cloud_data(tbl), use_container_width=True)
        if st.button("Import Data"): st.info("Fitur Import Aktif")
    # ==================== MODUL: OPERATIONS PROCUREMENT (PR & PO) ====================
    elif st.session_state['active_menu'] == "📥 Pengadaan (PR/PO)":
        st.title("📥 Procurement & Logistics Hub")
        tab_create_pr, tab_create_po, tab_history_po = st.tabs(["📋 Purchase Requisition (PR)", "➕ Buat PO Baru (Single-Type)", "📜 Monitor Riwayat Dokumen PO"])
        
        df_items = load_cloud_data("mst_items")
        df_branches = load_cloud_data("mst_branches")
        df_wh = load_cloud_data("mst_warehouses")
        df_suppliers = load_cloud_data("mst_suppliers")
        
        # 1. TAB PURCHASE REQUISITION USER
        with tab_create_pr:
            if "Create" not in allowed_actions:
                st.error("🔒 Akses Ditolak: Anda tidak memiliki izin untuk membuat dokumen PR.")
            else:
                pr_setting = load_cloud_data("mst_doc_settings")
                pr_setting = pr_setting[pr_setting["doc_type"] == "PR-USER"] if not pr_setting.empty else pd.DataFrame()
                
                if df_items.empty: st.error("⚠️ Master Item kosong.")
                elif pr_setting.empty: st.error("❌ Modul PR-USER belum aktif di master parameter setting.")
                else:
                    df_purchase_items = df_items[df_items['functions'].astype(str).str.contains("Purchase", na=False)] if 'functions' in df_items.columns else df_items
                    
                    # 🎯 FITUR FILTER ITEM TYPE DI PR
                    st.markdown("##### 🔍 Saring Ketersediaan Item Berdasarkan Type")
                    avail_types = ["Semua Tipe"] + df_purchase_items["item_type"].dropna().unique().tolist() if not df_purchase_items.empty else ["Semua Tipe"]
                    sel_type_filter = st.selectbox("Saring Tipe Item", avail_types, key="pr_type_filter_core")
                    
                    if sel_type_filter != "Semua Tipe":
                        df_purchase_items = df_purchase_items[df_purchase_items["item_type"] == sel_type_filter]
                        
                    item_options = [f"{row['item_id']} - {row['item_name']} ({row['uom_purchase']})" for _, row in df_purchase_items.iterrows()] if not df_purchase_items.empty else []
                    branch_options = [f"{row['branch_id']} - {row['branch_name']}" for _, row in df_branches.iterrows()] if not df_branches.empty else []
                    df_my_wh = df_wh[df_wh['warehouse_id'].isin(info.get('warehouses', []))] if not df_wh.empty else pd.DataFrame()
                    wh_options = [f"{row['warehouse_id']} - {row['warehouse_name']}" for _, row in df_my_wh.iterrows()] if not df_my_wh.empty else ["Tidak ada akses gudang"]
                    
                    with st.form("form_create_pr", clear_on_submit=True):
                        st.subheader("Form Create Purchase Request User")
                        st.text_input("Departemen Peminta (Terkunci Sesuai Akun)", value=info.get('dept_id'), disabled=True)
                        p_branch = st.selectbox("Target Branch Penerimaan *", branch_options)
                        p_wh = st.selectbox("Target Gudang Penyimpanan / Storage *", wh_options)
                        p_item_sel = st.selectbox("Pilih Item Barang *", item_options)
                        p_qty = st.number_input("Jumlah Qty Permintaan *", min_value=0.01, value=1.0)
                        p_note = st.text_area("Remark / Keperluan Catatan Operasional")
                        
                        if st.form_submit_button("Submit & Cetak PR"):
                            if not p_item_sel or "Tidak ada" in p_wh or not p_branch: st.error("Lengkapi seluruh field bertanda bintang!")
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
                                    st.success(f"🎉 Sukses menerbitkan PR Resmi: {generated_pr_no}"); st.rerun()
                                    
            st.markdown("---")
            st.subheader("📋 Log Monitor Riwayat PR Terdaftar")
            st.dataframe(load_cloud_data("trn_purchase_requisitions"), use_container_width=True, hide_index=True)

        # 2. TAB BUAT PURCHASE ORDER BARU (INTERLOCKING MULTI-ITEM SINGLE-TYPE)
        with tab_create_po:
            st.subheader("Form Penerbitan Dokumen Purchase Order (PO)")
            if "Create" not in allowed_actions:
                st.error("🔒 Akses Ditolak: Hak tindakan Anda tidak diizinkan menerbitkan dokumen PO.")
            elif df_items.empty or df_suppliers.empty:
                st.error("⚠️ Master Data Item atau Supplier terdeteksi masih kosong.")
            else:
                supplier_opts = [f"{s['supplier_id']} - {s['supplier_name']}" for _, s in df_suppliers.iterrows()]
                p_supplier = st.selectbox("Pilih Vendor Supplier Utama *", supplier_opts)
                
                st.markdown("---")
                st.markdown("#### 🛒 Matriks Detail Barang PO (Wajib 1 Tipe yang Sama / Single Type)")
                
                list_types = df_items["item_type"].dropna().unique().tolist()
                selected_po_type = st.selectbox("Kunci Validasi Tipe Item PO Ini *", list_types, help="Sistem mengunci tabel grid hanya memunculkan tipe yang dipilih.")
                
                # Filter item dinamis berdasarkan tipe yang dikunci
                df_filtered_items = df_items[df_items["item_type"] == selected_po_type]
                item_dropdown_list = [f"{row['item_id']} - {row['item_name']}" for _, row in df_filtered_items.iterrows()]
                
                if 'po_items_grid' not in st.session_state:
                    st.session_state['po_items_grid'] = pd.DataFrame([{"Item": "", "Qty Order": 1.0, "Harga Satuan": 0.0}])
                    
                st.info(f"⚡ **Interlocking Engine Connect**: Menampilkan {len(df_filtered_items)} item berkategori tipe `{selected_po_type}`.")
                
                edited_df = st.data_editor(
                    st.session_state['po_items_grid'], 
                    num_rows="dynamic", 
                    use_container_width=True,
                    column_config={
                        "Item": st.column_config.SelectboxColumn("Pilih Komponen Item *", options=item_dropdown_list, width="medium"),
                        "Qty Order": st.column_config.NumberColumn("Qty Pengadaan *", min_value=0.01, format="%.2f"),
                        "Harga Satuan": st.column_config.NumberColumn("Harga Beli Satuan (Rp) *", min_value=0.0)
                    }
                )
                
                if st.button("🚀 Sahkan & Daftarkan Transaksi PO", type="primary"):
                    valid_rows = edited_df[edited_df["Item"].str.strip() != ""]
                    
                    if valid_rows.empty:
                        st.error("❌ Transaksi Batal: Harap isi minimal satu baris item barang belanja resmi!")
                    else:
                        generated_po_no = generate_document_number("PO")
                        supplier_id = p_supplier.split(" - ")[0]
                        po_item_records = []
                        all_types_match = True
                        
                        for _, row in valid_rows.iterrows():
                            sel_item_id = row["Item"].split(" - ")[0]
                            db_item_row = df_items[df_items["item_id"] == sel_item_id].iloc[0]
                            
                            if db_item_row["item_type"] != selected_po_type:
                                all_types_match = False
                                break
                                
                            po_item_records.append({
                                "item_id": sel_item_id,
                                "item_name": db_item_row["item_name"],
                                "qty": float(row["Qty Order"]),
                                "price": float(row["Harga Satuan"]),
                                "total_line": float(row["Qty Order"] * row["Harga Satuan"])
                            })
                            
                        if not all_types_match:
                            st.error("❌ System Intercepted: Terdeteksi manipulasi tipe item yang tidak sesuai dengan kunci PO!")
                        else:
                            new_po_document = {
                                "po_number": generated_po_no,
                                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "supplier_id": supplier_id,
                                "item_type_restriction": selected_po_type,
                                "items_detail": po_item_records,
                                "total_transaction": sum(item["total_line"] for item in po_item_records),
                                "created_by": info.get('name'),
                                "status": "OPEN/APPROVED"
                            }
                            df_po_history = load_cloud_data("trn_purchase_orders")
                            if save_cloud_data(pd.concat([df_po_history, pd.DataFrame([new_po_document])], ignore_index=True), "trn_purchase_orders"):
                                st.success(f"🎉 Sukses Besar! PO Resmi Terbit: **{generated_po_no}** bermuatan {len(po_item_records)} item Tipe `{selected_po_type}`.")
                                if 'po_items_grid' in st.session_state: del st.session_state['po_items_grid']
                                st.rerun()

        # 3. TAB ARSIP RIWAYAT TRANSAKSI PO DENGAN ACTION CONTROLLER
        with tab_history_po:
            st.subheader("Arsip Dokumen Transaksi Purchase Order Berjalan")
            df_po_show = load_cloud_data("trn_purchase_orders")
            
            if "Export" in allowed_actions and not df_po_show.empty:
                csv_po = io.StringIO()
                df_po_show.to_csv(csv_po, index=False)
                st.download_button(label="📥 Download Data PO ke CSV (Export)", data=csv_po.getvalue(), file_name="export_po.csv", mime="text/csv")
                
            if not df_po_show.empty:
                for idx, row in df_po_show.iterrows():
                    col_det, col_ed, col_cx, col_de = st.columns([5, 1, 1, 1])
                    with col_det:
                        st.write(f"📄 **{row['po_number']}** | Supplier ID: {row['supplier_id']} | Tipe Kunci: `{row['item_type_restriction']}` | Nilai: **Rp {row['total_transaction']:,}** | Status: `{row['status']}`")
                    with col_ed:
                        if "Edit" in allowed_actions and st.button("✏️ Edit", key=f"po_ed_{row['po_number']}"): st.info("Form perubahan baris po aktif.")
                    with col_cx:
                        if "Cancel" in allowed_actions and row['status'] != "CANCELLED":
                            if st.button("🚫 Cancel", key=f"po_cx_{row['po_number']}"):
                                df_po_show.loc[idx, 'status'] = "CANCELLED"
                                save_cloud_data(df_po_show, "trn_purchase_orders"); st.rerun()
                    with col_de:
                        if "Delete" in allowed_actions and st.button("❌ Hapus", key=f"po_de_{row['po_number']}"):
                            df_po_show = df_po_show.drop(idx)
                            save_cloud_data(df_po_show, "trn_purchase_orders"); st.rerun()
            else: st.info("Belum ada arsip berkas PO terkoleksi.")

    # ==================== MODUL PARAMETER MASTER DATA GLOBAL CORE ====================
    elif st.session_state['active_menu'] == "⚙️ Master Data":
        st.title("⚙️ Pusat Konfigurasi Master Data ERP Terpusat")
        tab_core, tab_import, tab_permission, tab_doc_master = st.tabs(["📁 CRUD Manual Komplet", "📥 Bulk Import Data Massal", "🔒 Role & Action Permission Matrix", "🔏 Master Setting No Dokumen"])
        
        with tab_core:
            # MEMASTIKAN SELURUH TABEL LAMA DARI HULU KE HILIR AKTIF 100%
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
                if "Create" not in allowed_actions: st.error("🔒 Akses Ditolak: Peran jabatan Anda dilarang input manual.")
                else:
                    if pilih_tabel_core == "mst_departments":
                        with st.form("form_dept", clear_on_submit=True):
                            d_id = st.text_input("Department ID (Contoh: DEP-QA)")
                            d_name = st.text_input("Department Name")
                            if st.form_submit_button("Simpan Departemen"):
                                if d_id and d_name:
                                    save_cloud_data(pd.concat([df_core, pd.DataFrame([{"department_id": d_id.upper().strip(), "department_name": d_name.strip()}])], ignore_index=True), pilih_tabel_core); st.rerun()
                                    
                    elif pilih_tabel_core == "mst_warehouses":
                        df_br = load_cloud_data("mst_branches")
                        br_list = df_br['branch_id'].tolist() if not df_br.empty else ["SR-SOF0001-JS-01"]
                        with st.form("form_wh", clear_on_submit=True):
                            w_id = st.text_input("Warehouse ID (Contoh: WH-CP-RAW)")
                            w_name = st.text_input("Warehouse Name")
                            w_br = st.selectbox("Branch Terkait", br_list)
                            if st.form_submit_button("Simpan Gudang"):
                                if w_id and w_name:
                                    save_cloud_data(pd.concat([df_core, pd.DataFrame([{"warehouse_id": w_id.upper().strip(), "warehouse_name": w_name, "branch_id": w_br}])], ignore_index=True), pilih_tabel_core); st.rerun()
                                    
                    elif pilih_tabel_core == "mst_users":
                        dept_list = load_cloud_data("mst_departments")['department_id'].tolist()
                        wh_list = load_cloud_data("mst_warehouses")['warehouse_id'].tolist()
                        with st.form("form_user_new", clear_on_submit=True):
                            u_id = st.text_input("User ID"); u_name = st.text_input("Nama Karyawan"); u_user = st.text_input("Username"); u_pass = st.text_input("Password")
                            u_role = st.selectbox("Role Izin", ["OWNER", "MANAGER", "STAFF"]); u_dept = st.selectbox("Department", dept_list)
                            u_wh_selected = st.multiselect("Pilih Otoritas Gudang Akses Karyawan", wh_list)
                            if st.form_submit_button("Simpan Akun User"):
                                if u_id and u_user and u_pass:
                                    new_u = {"user_id": u_id.upper(), "username": u_user, "password": u_pass, "role_id": u_role, "employee_name": u_name, "department_id": u_dept, "accessible_warehouses": u_wh_selected}
                                    records = df_core.to_dict(orient="records"); records.append(new_u)
                                    save_cloud_data(pd.DataFrame(records), pilih_tabel_core); st.rerun()

                    elif pilih_tabel_core == "mst_items":
                        list_uom = load_cloud_data("mst_units")["unit_id"].tolist() if not load_cloud_data("mst_units").empty else ["UOM-PCS"]
                        with st.form("form_item_manual", clear_on_submit=True):
                            i_id = st.text_input("item_id"); i_name = st.text_input("item_name"); i_type = st.selectbox("item_type", ["Bahan Baku", "Barang Jadi", "WIP / Setengah Jadi"])
                            i_cat = st.text_input("category"); i_uom_p = st.selectbox("uom_purchase", list_uom); i_uom_s = st.selectbox("uom_stock", list_uom)
                            f_inv = st.checkbox("Inventory"); f_sal = st.checkbox("Sales"); f_pur = st.checkbox("Purchase"); f_bom = st.checkbox("Item BOM"); f_pkg = st.checkbox("Header Package")
                            if st.form_submit_button("Simpan Item Baru"):
                                fns = [k for k, v in {"Inventory": f_inv, "Sales": f_sal, "Purchase": f_pur, "Item BOM": f_bom, "Header Package": f_pkg}.items() if v]
                                new_i = {"item_id": i_id.upper(), "item_name": i_name, "item_type": i_type, "category": i_cat, "uom_purchase": i_uom_p, "uom_stock": i_uom_s, "min_stock": 10, "functions": ", ".join(fns)}
                                save_cloud_data(pd.concat([df_core, pd.DataFrame([new_i])], ignore_index=True), pilih_tabel_core); st.rerun()

                    elif pilih_tabel_core == "mst_units":
                        with st.form("form_uom", clear_on_submit=True):
                            u_id = st.text_input("unit_id (Contoh: UOM-BOX)"); u_name = st.text_input("unit_name")
                            u_ket = st.text_input("Keterangan")
                            if st.form_submit_button("Simpan UOM"):
                                if u_id: save_cloud_data(pd.concat([df_core, pd.DataFrame([{"unit_id": u_id.upper(), "unit_name": u_name, "Keterangan": u_ket}])], ignore_index=True), pilih_tabel_core); st.rerun()

                    elif pilih_tabel_core == "mst_uom_conversions":
                        list_uom = load_cloud_data("mst_units")["unit_id"].tolist()
                        with st.form("form_cnv", clear_on_submit=True):
                            c_id = st.text_input("conversion_id")
                            c_from = st.selectbox("From UOM (Unit Asal)", list_uom)
                            c_to = st.selectbox("To UOM (Unit Tujuan)", list_uom)
                            c_op = st.selectbox("Operator Operasi", ["Kali (*)", "Bagi (/)"])
                            c_fac = st.number_input("Factor Nilai Konversi", min_value=0.0001, value=1.0, format="%.4f")
                            if st.form_submit_button("Simpan Aturan Konversi UOM"):
                                if c_id: save_cloud_data(pd.concat([df_core, pd.DataFrame([{"conversion_id": c_id.upper(), "from_uom": c_from, "to_uom": c_to, "operator": c_op, "factor": c_fac}])], ignore_index=True), pilih_tabel_core); st.rerun()

                    elif pilih_tabel_core == "mst_branches":
                        with st.form("form_br", clear_on_submit=True):
                            b_id = st.text_input("branch_id"); b_name = st.text_input("branch_name")
                            b_type = st.selectbox("branch_type", ["Outlet", "Central Production", "Head Office"]); b_addr = st.text_input("address")
                            if st.form_submit_button("Simpan Cabang Baru"):
                                if b_id: save_cloud_data(pd.concat([df_core, pd.DataFrame([{"branch_id": b_id.upper(), "branch_name": b_name, "branch_type": b_type, "address": b_addr}])], ignore_index=True), pilih_tabel_core); st.rerun()

                    elif pilih_tabel_core == "mst_suppliers":
                        with st.form("form_spl", clear_on_submit=True):
                            s_id = st.text_input("supplier_id"); s_name = st.text_input("supplier_name")
                            s_phone = st.text_input("phone"); s_terms = st.text_input("payment_terms")
                            if st.form_submit_button("Simpan Data Supplier"):
                                if s_id: save_cloud_data(pd.concat([df_core, pd.DataFrame([{"supplier_id": s_id.upper(), "supplier_name": s_name, "phone": s_phone, "payment_terms": s_terms}])], ignore_index=True), pilih_tabel_core); st.rerun()

            elif action_mode == "❌ Hapus Data Terpilih" and not df_core.empty:
                if "Delete" not in allowed_actions: st.error("🔒 Izin Delete ditolak.")
                else:
                    sel_del_id = st.selectbox("Pilih ID Baris Hapus", df_core[pk_col].tolist())
                    if st.button("Konfirmasi Hapus Permanen"):
                        save_cloud_data(df_core[df_core[pk_col] != sel_del_id], pilih_tabel_core); st.rerun()

        # ==================== KELENGKAPAN FITUR AMAN: BULK IMPORT DENGAN TEMPLATE MAKSIMAL UNTUK SEMUA TABEL ====================
        with tab_import:
            st.subheader("📥 Bulk Import System Terpusat - Akses Semua Tabel Master")
            if "Import" not in allowed_actions: 
                st.error("🔒 Hak akses bulk import untuk role Anda tidak aktif.")
            else:
                pilih_target_bulk = st.selectbox(
                    "Pilih Target Tabel Bulk", 
                    ["mst_departments", "mst_warehouses", "mst_users", "mst_items", "mst_units", "mst_uom_conversions", "mst_branches", "mst_suppliers"], 
                    key="sel_bulk_pro"
                )
                
                templates = {
                    "mst_departments": ["department_id", "department_name"], 
                    "mst_warehouses": ["warehouse_id", "warehouse_name", "branch_id"], 
                    "mst_users": ["user_id", "username", "password", "role_id", "employee_name", "department_id"], 
                    "mst_items": ["item_id", "item_name", "item_type", "category", "uom_purchase", "uom_stock", "min_stock", "functions"],
                    "mst_units": ["unit_id", "unit_name", "Keterangan"],
                    "mst_uom_conversions": ["conversion_id", "from_uom", "to_uom", "operator", "factor"],
                    "mst_branches": ["branch_id", "branch_name", "branch_type", "address"],
                    "mst_suppliers": ["supplier_id", "supplier_name", "phone", "payment_terms"]
                }
                
                kolom_template = templates[pilih_target_bulk]
                csv_string = io.StringIO()
                pd.DataFrame(columns=kolom_template).to_csv(csv_string, index=False)
                st.download_button(label=f"📥 Download Template CSV Resmi {pilih_target_bulk}", data=csv_string.getvalue(), file_name=f"template_{pilih_target_bulk}.csv", mime="text/csv")
                
                uploaded_file = st.file_uploader("Unggah Berkas CSV Anda", type=["csv"])
                if uploaded_file is not None:
                    df_upload = pd.read_csv(uploaded_file)
                    missing_cols = [col for col in kolom_template if col not in df_upload.columns]
                    
                    if missing_cols:
                        st.error(f"❌ Header salah! Kolom yang hilang: {missing_cols}")
                    else:
                        st.write("📋 Pratinjau 5 Data Pertama:")
                        st.dataframe(df_upload.head(5), use_container_width=True)
                        if st.button("🚀 Konfirmasi Gabungkan Data Massal ke Cloud Storage", type="primary"):
                            df_curr = load_cloud_data(pilih_target_bulk)
                            if pilih_target_bulk == "mst_users" and "accessible_warehouses" not in df_upload.columns:
                                df_upload["accessible_warehouses"] = None; df_upload["accessible_warehouses"] = df_upload["accessible_warehouses"].apply(lambda x: [])
                            save_cloud_data(pd.concat([df_curr, df_upload], ignore_index=True).drop_duplicates(subset=[kolom_template[0]], keep="last"), pilih_target_bulk); st.success("Import Berhasil!"); st.rerun()

        # ==================== TAB: ROLE & ACTION MATRIX OTORITAS TINDAKAN DINAMIS ====================
        with tab_permission:
            st.subheader("🔒 Matriks Kontrol Otoritas Menu & Tindakan (Role & Action Matrix)")
            df_roles = load_cloud_data("mst_roles_permission")
            st.dataframe(df_roles, use_container_width=True, hide_index=True)
            
            if not df_roles.empty:
                st.markdown("---")
                sel_role = st.selectbox("Pilih Role Jabatan yang Akan Dikonfigurasi", df_roles["role_id"].tolist(), key="sb_sel_role_perm")
                r_data = df_roles[df_roles["role_id"] == sel_role].iloc[0].to_dict()
                
                with st.form("form_role_action_perm_matrix"):
                    st.markdown(f"##### 📑 Pengaturan Hak Akses Modul Menu (`{sel_role}`)")
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        chk_m_dash = st.checkbox("Dashboard Utama", value="Dashboard Utama" in r_data.get('modules', []))
                        chk_m_wms = st.checkbox("WMS & Gudang", value="WMS & Gudang" in r_data.get('modules', []))
                    with col_m2:
                        chk_m_pr = st.checkbox("📥 Pengadaan (PR/PO)", value="📥 Pengadaan (PR/PO)" in r_data.get('modules', []))
                        chk_m_master = st.checkbox("⚙️ Master Data", value="⚙️ Master Data" in r_data.get('modules', []))
                        
                    st.markdown(f"##### ⚡ Pengaturan Otoritas Tindakan Dokumen / Action (`{sel_role}`)")
                    col_a1, col_a2, col_a3 = st.columns(3)
                    with col_a1:
                        chk_a_read = st.checkbox("Read (Melihat Data)", value="Read" in r_data.get('actions', []))
                        chk_a_create = st.checkbox("Create (Tambah/Submit)", value="Create" in r_data.get('actions', []))
                    with col_a2:
                        chk_a_edit = st.checkbox("Edit (Ubah Baris)", value="Edit" in r_data.get('actions', []))
                        chk_a_del = st.checkbox("Delete (Hapus)", value="Delete" in r_data.get('actions', []))
                    with col_a3:
                        chk_a_cxl = st.checkbox("Cancel (Batalkan Status)", value="Cancel" in r_data.get('actions', []))
                        chk_a_imp = st.checkbox("Import (Bulk CSV)", value="Import" in r_data.get('actions', []))
                        chk_a_exp = st.checkbox("Export (Download CSV)", value="Export" in r_data.get('actions', []))
                        
                    if st.form_submit_button("Simpan Konfigurasi Matriks Otoritas"):
                        new_modules = []
                        if chk_m_dash: new_modules.append("Dashboard Utama")
                        if chk_m_wms: new_modules.append("WMS & Gudang")
                        if chk_m_pr: new_modules.append("📥 Pengadaan (PR/PO)")
                        if chk_m_master: new_modules.append("⚙️ Master Data")
                        
                        new_actions = []
                        if chk_a_read: new_actions.append("Read")
                        if chk_a_create: new_actions.append("Create")
                        if chk_a_edit: new_actions.append("Edit")
                        if chk_a_del: new_actions.append("Delete")
                        if chk_a_cxl: new_actions.append("Cancel")
                        if chk_a_imp: new_actions.append("Import")
                        if chk_a_exp: new_actions.append("Export")
                        
                        df_roles.loc[df_roles["role_id"] == sel_role, "modules"] = None
                        df_roles.loc[df_roles["role_id"] == sel_role, "modules"] = df_roles["modules"].apply(lambda x: new_modules)
                        
                        df_roles.loc[df_roles["role_id"] == sel_role, "actions"] = None
                        df_roles.loc[df_roles["role_id"] == sel_role, "actions"] = df_roles["actions"].apply(lambda x: new_actions)
                        
                        if save_cloud_data(df_roles, "mst_roles_permission"):
                            st.success(f"🎉 Matriks Otoritas Tindakan & Modul untuk Role `{sel_role}` Berhasil Diperbarui!"); st.rerun()

        # ==================== MASTER SETTING PENOMORAN DOKUMEN DIRECT INTERLOCKING ====================
        with tab_doc_master:
            st.subheader("🔏 Master Kustomisasi Pola Penomoran Dokumen (Direct Interlocking)")
            df_doc_settings = load_cloud_data("mst_doc_settings")
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
                            st.success(f"🎉 Hubungan antar-modul untuk `{d_type}` resmi terhubung!"); st.rerun()
if st.sidebar.button("RESET DATABASE KE DEFAULT"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        st.warning("Database dihapus, silakan Refresh halaman (F5)!")
        st.rerun()
