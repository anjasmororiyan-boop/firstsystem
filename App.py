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
        "mst_users": [
            {"user_id": "USR-001", "username": "riyan_owner", "password": "admin123", "role_id": "OWNER", "employee_name": "Riyan Anjasmoro"}
        ],
        "mst_units": [
            {"unit_id": "UOM-KG", "unit_name": "Kilogram", "Keterangan": "Satuan Massa Dasar"},
            {"unit_id": "UOM-GR", "unit_name": "Gram", "Keterangan": "Satuan Massa Kecil"},
            {"unit_id": "UOM-PCS", "unit_name": "Pieces", "Keterangan": "Satuan Roti Jadi"}
        ],
        "mst_uom_conversions": [
            {"conversion_id": "CNV-001", "from_uom": "UOM-KG", "to_uom": "UOM-GR", "operator": "Kali (*)", "factor": 1000}
        ],
        "mst_items": [
            {"item_id": "ITM-001", "item_name": "Tepung Terigu Cakra Kembar", "item_type": "Bahan Baku", "category": "Tepung", "uom_purchase": "UOM-KG", "uom_stock": "UOM-KG", "min_stock": 50, "functions": "Inventory, Purchase"},
            {"item_id": "ITM-002", "item_name": "Roti Sisir Mentega Signature", "item_type": "Barang Jadi", "category": "Roti", "uom_purchase": "UOM-PCS", "uom_stock": "UOM-PCS", "min_stock": 20, "functions": "Inventory, Sales, Item BOM"}
        ],
        "mst_branches": [
            {"branch_id": "SR-SOF0001-JS-01", "branch_name": "Supporting Office", "branch_type": "Head Office", "address": "Jl TB Simatupang"},
            {"branch_id": "SR-CKT0001-DP-01", "branch_name": "Central Production Depok", "branch_type": "Central Production", "address": "Area 700m2"}
        ],
        "mst_suppliers": [
            {"supplier_id": "SPL-001", "supplier_name": "PT Sumber Terigu Nusantara", "phone": "0812345678", "payment_terms": "COD"}
        ],
        # MASTER REGISTRASI DOKUMEN: Terkoneksi ke modul sistem secara dinamis
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
        df = pd.DataFrame(data.get(table_name, []))
        
        # FAIL-SAFE: Mengamankan error 'KeyError: functions' jika dataframe kosong atau kolom belum terbentuk
        if table_name == "mst_items":
            if df.empty:
                return pd.DataFrame(columns=["item_id", "item_name", "item_type", "category", "uom_purchase", "uom_stock", "min_stock", "functions"])
            if "functions" not in df.columns:
                df["functions"] = "Inventory, Purchase"
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

# --- ENGINE GENERATOR DOKUMEN UNIVERSAL DINAMIS ---
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
        user_match = df_users[(df_users['username'].astype(str).str.strip() == username_input.strip()) & 
                              (df_users['password'].astype(str).str.strip() == str(password_input).strip())]
        if not user_match.empty:
            user_data = user_match.iloc[0].to_dict()
            st.session_state['user_info'] = {
                'name': user_data['employee_name'], 'role': user_data['role_id']
            }
            st.session_state['logged_in'] = True
            st.session_state['active_menu'] = "📥 Pengadaan (PR)"
            st.rerun()
        else:
            st.error("Kredensial salah!")

# --- FASE 2: APLIKASI UTAMA ---
else:
    info = st.session_state['user_info']
    
    with st.sidebar:
        st.subheader("🏬 ERPOS Control Panel")
        st.caption(f"User: **{info['name']}** ({info['role']})")
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

    # --- MODUL ROUTER ---
    if st.session_state['active_menu'] == "Dashboard Utama":
        st.title("📊 Executive Dashboard & Analytics")
        st.info("Sistem Engine JSON Terkoneksi 100%.")
        
    elif st.session_state['active_menu'] == "WMS & Gudang":
        st.title("📦 Warehouse Management System (WMS)")
        st.dataframe(load_cloud_data("mst_items"), use_container_width=True, hide_index=True)
        
    # ==================== MODUL: PROCUREMENT PURCHASE REQUISITION (PR-USER) ====================
    elif st.session_state['active_menu'] == "📥 Pengadaan (PR)":
        st.title("📥 Purchase Requisition (PR) Hub")
        
        tab_create_pr, tab_history_pr = st.tabs(["➕ Buat PR Baru", "📋 Riwayat Dokumen PR"])
        
        with tab_create_pr:
            df_items = load_cloud_data("mst_items")
            df_branches = load_cloud_data("mst_branches")
            df_check_setting = load_cloud_data("mst_doc_settings")
            
            # Konek secara langsung ke modul PR-USER
            pr_setting = df_check_setting[df_check_setting["doc_type"] == "PR-USER"]
            
            if df_items.empty:
                st.error("⚠️ Form terkunci! Belum ada data Master Item untuk dipilih dalam pengadaan.")
            elif pr_setting.empty:
                st.error("❌ TRANSAKSI TERKUNCI: Modul transaksi 'PR-USER' belum diaktifkan di Master Data Pola Nomor Dokumen!")
            else:
                setting_details = pr_setting.iloc[0].to_dict()
                st.success(f"🔗 Modul Aktif Terhubung Resmi dengan Pola: `{setting_details['initial_doc']}-{setting_details['initial_company']}YYYYMMXXXXXX`")
                
                # Saringan anti-error 'functions' column
                df_purchase_items = df_items[df_items['functions'].astype(str).str.contains("Purchase", na=False)]
                if df_purchase_items.empty:
                    st.warning("⚠️ Tidak ada item terdaftar yang memiliki fungsi 'Purchase' di Master Item!")
                    item_options = []
                else:
                    item_options = [f"{row['item_id']} - {row['item_name']} ({row['uom_purchase']})" for _, row in df_purchase_items.iterrows()]
                
                branch_options = [f"{row['branch_id']} - {row['branch_name']}" for _, row in df_branches.iterrows()] if not df_branches.empty else ["HQ - Head Office"]
                
                with st.form("form_create_pr", clear_on_submit=True):
                    st.subheader("Create Purchase Request User")
                    
                    p_dept = st.selectbox("Department *", ["Production (CP Hub)", "Warehouse & Logistics", "Kitchen Hub", "Retail Outlet"])
                    p_branch = st.selectbox("Company Branch *", branch_options)
                    p_item_sel = st.selectbox("Select Item (*Purchase Function Filter*)", item_options)
                    p_qty = st.number_input("Qty *", min_value=0.01, value=1.0, format="%.2f")
                    p_note = st.text_area("Remark (Catatan Tambahan)")
                    
                    if st.form_submit_button("Save As Draft / Submit PR"):
                        if not p_item_sel:
                            st.error("Pilihan item tidak boleh kosong!")
                        else:
                            # Memanggil generator nomor yang terkoneksi langsung ke modul PR-USER
                            generated_pr_no = generate_document_number("PR-USER")
                            
                            selected_item_id = p_item_sel.split(" - ")[0]
                            target_branch_id = p_branch.split(" - ")[0] if " - " in p_branch else p_branch
                            
                            new_pr_doc = {
                                "pr_number": generated_pr_no,
                                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "department": p_dept,
                                "target_branch": target_branch_id,
                                "item_id": selected_item_id,
                                "qty_requested": p_qty,
                                "created_by": info['name'],
                                "status": "DRAFT/PENDING",
                                "remark": p_note.strip()
                            }
                            
                            df_pr_hist = load_cloud_data("trn_purchase_requisitions")
                            df_pr_updated = pd.concat([df_pr_hist, pd.DataFrame([new_pr_doc])], ignore_index=True)
                            
                            if save_cloud_data(df_pr_updated, "trn_purchase_requisitions"):
                                st.success(f"🎉 Sukses! Dokumen Purchase Request User diterbitkan dengan Nomor: **{generated_pr_no}**")
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
                ["mst_items", "mst_units", "mst_uom_conversions", "mst_branches", "mst_suppliers"], 
                key="sel_core_pro"
            )
            df_core = load_cloud_data(pilih_tabel_core)
            st.subheader(f"Data Live Tabel `{pilih_tabel_core}`")
            st.dataframe(df_core, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            action_mode = st.radio("Pilih Operasi Data", ["➕ Tambah Data Baru", "❌ Hapus Data Terpilih"], horizontal=True)
            pk_col = df_core.columns[0] if not df_core.empty else 'id'
            
            if action_mode == "➕ Tambah Data Baru":
                if pilih_tabel_core == "mst_items":
                    df_uom_master = load_cloud_data("mst_units")
                    if df_uom_master.empty:
                        st.error("⚠️ Data Master UOM (mst_units) kosong! Wajib isi UOM terlebih dahulu.")
                    else:
                        list_uom = df_uom_master["unit_id"].dropna().astype(str).tolist()
                        with st.form("form_item_manual", clear_on_submit=True):
                            i_id = st.text_input("item_id (Contoh: ITM-003)")
                            i_name = st.text_input("item_name (Nama Barang)")
                            i_type = st.selectbox("item_type", ["Bahan Baku", "Barang Jadi", "WIP / Setengah Jadi"])
                            i_cat = st.text_input("category (Kategori)")
                            
                            col_u1, col_u2 = st.columns(2)
                            with col_u1:
                                i_uom_purchase = st.selectbox("uom_purchase (Satuan Pembelian)", list_uom)
                            with col_u2:
                                i_uom_stock = st.selectbox("uom_stock (Satuan Stok Gudang)", list_uom)
                                
                            st.markdown("**🎯 Filter Fungsi Operasional ERP Item**")
                            f_inv = st.checkbox("Inventory")
                            f_sal = st.checkbox("Sales")
                            f_pur = st.checkbox("Purchase")
                            f_bom = st.checkbox("Item BOM")
                            f_pkg = st.checkbox("Header Package")
                            
                            i_min = st.number_input("min_stock", min_value=0, value=10)
                            
                            if st.form_submit_button("Simpan Item Master Baru"):
                                selected_functions = []
                                if f_inv: selected_functions.append("Inventory")
                                if f_sal: selected_functions.append("Sales")
                                if f_pur: selected_functions.append("Purchase")
                                if f_bom: selected_functions.append("Item BOM")
                                if f_pkg: selected_functions.append("Header Package")
                                
                                function_str = ", ".join(selected_functions) if selected_functions else "Expense"
                                
                                if i_id.strip() == "" or i_name.strip() == "":
                                    st.error("ID dan Nama Item wajib diisi!")
                                else:
                                    new_row = pd.DataFrame([{"item_id": i_id.strip().upper(), "item_name": i_name.strip(), "item_type": i_type, "category": i_cat.strip(), "uom_purchase": i_uom_purchase, "uom_stock": i_uom_stock, "min_stock": i_min, "functions": function_str}])
                                    if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core):
                                        st.success("🎉 Master Item Berhasil Ditambahkan!")
                                        st.rerun()

                elif pilih_tabel_core == "mst_units":
                    with st.form("form_uom", clear_on_submit=True):
                        u_id = st.text_input("unit_id")
                        u_name = st.text_input("unit_name")
                        u_ket = st.text_input("Keterangan")
                        if st.form_submit_button("Simpan UOM"):
                            new_row = pd.DataFrame([{"unit_id": u_id.upper(), "unit_name": u_name, "Keterangan": u_ket}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core):
                                st.rerun()

                elif pilih_tabel_core == "mst_uom_conversions":
                    list_uom = load_cloud_data("mst_units")["unit_id"].tolist()
                    with st.form("form_cnv", clear_on_submit=True):
                        c_id = st.text_input("conversion_id")
                        c_from = st.selectbox("From UOM", list_uom)
                        c_to = st.selectbox("To UOM", list_uom)
                        c_op = st.selectbox("Operator", ["Kali (*)", "Bagi (/)"])
                        c_fac = st.number_input("Factor", min_value=0.001, value=1.0)
                        if st.form_submit_button("Simpan Konversi"):
                            new_row = pd.DataFrame([{"conversion_id": c_id.upper(), "from_uom": c_from, "to_uom": c_to, "operator": c_op, "factor": c_fac}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core):
                                st.rerun()

                elif pilih_tabel_core == "mst_branches":
                    with st.form("form_br", clear_on_submit=True):
                        b_id = st.text_input("branch_id")
                        b_name = st.text_input("branch_name")
                        b_type = st.selectbox("branch_type", ["Outlet", "Central Production", "Head Office"])
                        b_addr = st.text_input("address")
                        if st.form_submit_button("Simpan Cabang"):
                            new_row = pd.DataFrame([{"branch_id": b_id, "branch_name": b_name, "branch_type": b_type, "address": b_addr}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core):
                                st.rerun()

                elif pilih_tabel_core == "mst_suppliers":
                    with st.form("form_spl", clear_on_submit=True):
                        s_id = st.text_input("supplier_id")
                        s_name = st.text_input("supplier_name")
                        s_phone = st.text_input("phone")
                        s_terms = st.text_input("payment_terms")
                        if st.form_submit_button("Simpan Supplier"):
                            new_row = pd.DataFrame([{"supplier_id": s_id, "supplier_name": s_name, "phone": s_phone, "payment_terms": s_terms}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core):
                                st.rerun()

            elif action_mode == "❌ Hapus Data Terpilih" and not df_core.empty:
                id_pilih_hapus = st.selectbox("Pilih ID Data yang Akan Dihapus", df_core[pk_col].tolist())
                if st.button("Konfirmasi Hapus Permanen", type="primary"):
                    if save_cloud_data(df_core[df_core[pk_col] != id_pilih_hapus], pilih_tabel_core):
                        st.rerun()

        with tab_import:
            st.subheader("📥 Bulk Import System Terpusat (CSV Engine)")
            pilih_target_bulk = st.selectbox("Pilih Target Tabel Bulk", ["mst_items", "mst_units", "mst_uom_conversions", "mst_branches", "mst_suppliers", "mst_doc_settings"], key="sel_bulk_pro")
            
            headers_map = {
                "mst_items": ["item_id", "item_name", "item_type", "category", "uom_purchase", "uom_stock", "min_stock", "functions"],
                "mst_units": ["unit_id", "unit_name", "Keterangan"],
                "mst_uom_conversions": ["conversion_id", "from_uom", "to_uom", "operator", "factor"],
                "mst_branches": ["branch_id", "branch_name", "branch_type", "address"],
                "mst_suppliers": ["supplier_id", "supplier_name", "phone", "payment_terms"],
                "mst_doc_settings": ["doc_type", "doc_name", "initial_doc", "initial_company", "last_year_month", "last_counter"]
            }
            
            chosen_headers = headers_map.get(pilih_target_bulk)
            csv_buffer = io.StringIO()
            pd.DataFrame(columns=chosen_headers).to_csv(csv_buffer, index=False)
            
            st.download_button(
                label=f"📥 Download Template CSV Resmi ({pilih_target_bulk})", 
                data=csv_buffer.getvalue(), 
                file_name=f"template_{pilih_target_bulk}.csv", 
                mime="text/csv"
            )
            
            st.markdown("---")
            file_unggah = st.file_uploader("Unggah File Hasil Pengisian Template (.csv)", type=["csv", "txt"])
            if file_unggah is not None:
                try:
                    df_upload = pd.read_csv(file_unggah)
                    st.write("📋 Pratinjau Data Unggahan:")
                    st.dataframe(df_upload.head(), use_container_width=True, hide_index=True)
                    
                    if st.button("Eksekusi Gabungkan Data Massal", type="primary"):
                        df_meta = load_cloud_data(pilih_target_bulk)
                        df_meta.columns = df_meta.columns.astype(str).str.strip()
                        df_upload.columns = df_upload.columns.astype(str).str.strip()
                        
                        df_combined = pd.concat([df_meta, df_upload], ignore_index=True).drop_duplicates()
                        if save_cloud_data(df_combined, pilih_target_bulk):
                            st.success("🎉 Seluruh data massal resmi masuk & terintegrasi penuh!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Gagal memproses file upload: {e}")

        # ==================== MASTER SETTING PENOMORAN DOKUMEN (INTERLOCKING RESMI) ====================
        with tab_doc_master:
            st.subheader("🔏 Master Kustomisasi Pola Penomoran Dokumen (Direct Interlocking)")
            df_doc_settings = load_cloud_data("mst_doc_settings")
            st.dataframe(df_doc_settings, use_container_width=True, hide_index=True)
            
            with st.form("form_setting_doc_dynamic"):
                st.markdown("**⚙️ Pengaturan Parameter Cetak Nomor Dokumen Sistem**")
                
                # SELEKSI KETAT DROPDOWN: Menampilkan modul-modul transaksi resmi yang berjalan di ERP
                LIST_MODUL_RESMI = ["PR-USER", "PR-PURCHASING", "PO", "GR"]
                d_type = st.selectbox("Pilih Modul Transaksi Sistem (Konek Otomatis)", LIST_MODUL_RESMI)
                
                # Deteksi data terpasang default
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
                with col_d1:
                    d_init_doc = st.text_input("Initial Kode Dokumen (Maks 3 Huruf)", value=default_init_doc).upper().strip()
                with col_d2:
                    d_init_comp = st.text_input("Initial Kode Perusahaan (Maks 4 Huruf)", value=default_init_comp).upper().strip()
                
                if st.form_submit_button("Simpan & Hubungkan Modul"):
                    if not d_init_doc or not d_init_comp:
                        st.error("Gagal! Parameter tidak boleh kosong.")
                    else:
                        if df_doc_settings.empty:
                            df_doc_settings = pd.DataFrame(columns=["doc_type", "doc_name", "initial_doc", "initial_company", "last_year_month", "last_counter"])
                        
                        idx_match = df_doc_settings[df_doc_settings['doc_type'] == d_type].index
                        
                        if len(idx_match) > 0:
                            df_doc_settings.loc[idx_match[0], 'doc_name'] = d_name
                            df_doc_settings.loc[idx_match[0], 'initial_doc'] = d_init_doc
                            df_doc_settings.loc[idx_match[0], 'initial_company'] = d_init_comp
                        else:
                            new_setting_row = {
                                "doc_type": d_type, "doc_name": d_name, "initial_doc": d_init_doc, "initial_company": d_init_comp,
                                "last_year_month": datetime.datetime.now().strftime("%Y%m"), "last_counter": 0
                            }
                            df_doc_settings = pd.concat([df_doc_settings, pd.DataFrame([new_setting_row])], ignore_index=True)
                            
                        if save_cloud_data(df_doc_settings, "mst_doc_settings"):
                            st.success(f"🎉 Hubungan antar-modul untuk `{d_type}` resmi terhubung!")
                            st.rerun()
