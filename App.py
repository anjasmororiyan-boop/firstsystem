import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import json
import os
import io
import datetime

# 1. KONFIGURASI UTAMA
st.set_page_config(page_title="ERPOS System - Enterprise Procurement", page_icon="🏬", layout="wide")

DATA_FILE = "data/erpos_cloud_data.json"

# --- ENGINE DATABASE CORE JSON (ENTERPRISE SKEMA) ---
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
        "mst_doc_settings": [
            {"doc_type": "PR", "doc_name": "Purchase Requisition", "initial_doc": "PR", "initial_company": "SRR", "last_year_month": "202606", "last_counter": 0}
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
        return pd.DataFrame(data.get(table_name, []))
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

# --- ENGINE GENERATOR NO DOKUMEN OTOMATIS (RESET TIAP BULAN BARU) ---
def generate_document_number(doc_type_code):
    df_settings = load_cloud_data("mst_doc_settings")
    if df_settings.empty:
        return f"{doc_type_code}-ERROR"
    
    idx = df_settings[df_settings['doc_type'] == doc_type_code].index
    if len(idx) == 0:
        return f"{doc_type_code}-MISSING"
    
    setting = df_settings.loc[idx[0]].to_dict()
    
    # Ambil waktu sekarang
    now = datetime.datetime.now()
    current_ym = now.strftime("%Y%m") # Hasil: 202606
    
    # Cek apakah sudah ganti bulan, jika ya reset counter ke 1
    if str(setting.get('last_year_month', '')) != current_ym:
        next_counter = 1
    else:
        next_counter = int(setting.get('last_counter', 0)) + 1
        
    # Sesuai Rumus: XX-XXXYYYYMMXXXXXX -> PR-SRR202606000001
    init_doc = str(setting['initial_doc']).strip().upper()[:2]
    init_comp = str(setting['initial_company']).strip().upper()[:3]
    str_counter = str(next_counter).zfill(6)
    
    formatted_number = f"{init_doc}-{init_comp}{current_ym}{str_counter}"
    
    # Simpan kembali counter terbaru ke database JSON
    df_settings.loc[idx[0], 'last_year_month'] = current_ym
    df_settings.loc[idx[0], 'last_counter'] = next_counter
    save_cloud_data(df_settings, "mst_doc_settings")
    
    return formatted_number

# 2. SESSION STATE MANAGEMENT
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
        
        # Penambahan Modul Menu Baru Pengadaan (PR)
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
        st.info("Sistem Operasional Cloud JSON Aktif 100%.")
        
    elif st.session_state['active_menu'] == "WMS & Gudang":
        st.title("📦 Warehouse Management System (WMS)")
        st.dataframe(load_cloud_data("mst_items"), use_container_width=True, hide_index=True)
        
    # ==================== MODUL BARU: PROCUREMENT PURCHASE REQUISITION (PR) ====================
    elif st.session_state['active_menu'] == "📥 Pengadaan (PR)":
        st.title("📥 Purchase Requisition (PR) Hub")
        st.markdown("Alur pembuatan permintaan pengadaan logistik barang hulu dari tiap departemen.")
        
        tab_create_pr, tab_history_pr = st.tabs(["➕ Buat PR Baru", "📋 Riwayat Dokumen PR"])
        
        with tab_create_pr:
            df_items = load_cloud_data("mst_items")
            df_branches = load_cloud_data("mst_branches")
            
            if df_items.empty:
                st.error("⚠️ Form terkunci! Belum ada data Master Item untuk dipilih dalam pengadaan.")
            else:
                # FILTER UTAMA: Hanya item yang memiliki filter fungsi 'Purchase' yang boleh dipesan di PR
                df_purchase_items = df_items[df_items['functions'].astype(str).str.contains("Purchase")]
                
                if df_purchase_items.empty:
                    st.warning("⚠️ Tidak ada item terdaftar yang memiliki fungsi 'Purchase' di Master Item!")
                    item_options = []
                else:
                    item_options = [f"{row['item_id']} - {row['item_name']} ({row['uom_purchase']})" for _, row in df_purchase_items.iterrows()]
                
                branch_options = [f"{row['branch_id']} - {row['branch_name']}" for _, row in df_branches.iterrows()] if not df_branches.empty else ["HQ - Head Office"]
                
                with st.form("form_create_pr", clear_on_submit=True):
                    st.subheader("Form Input Permintaan Barang (PR)")
                    
                    # Pembuatan No PR secara otomatis di balik layar saat disubmit
                    st.info("💡 Nomor Dokumen PR akan digenerate otomatis secara real-time oleh Master Setting saat form disubmit.")
                    
                    p_dept = st.selectbox("Departemen Peminta", ["Production (CP Hub)", "Warehouse & Logistics", "Kitchen Hub", "Retail Outlet"])
                    p_branch = st.selectbox("Lokasi Tujuan Pengiriman (*Target Branch*)", branch_options)
                    p_item_sel = st.selectbox("Pilih Item Barang (*Hanya Filter Purchase*)", item_options)
                    p_qty = st.number_input("Jumlah Qty yang Diminta", min_value=0.01, value=1.0, format="%.2f")
                    p_note = st.text_area("Keterangan Tambahan / Keperluan Urgensi")
                    
                    if st.form_submit_button("Submit & Cetak Dokumen PR"):
                        if not p_item_sel:
                            st.error("Pilihan item tidak valid!")
                        else:
                            # Ambil nomor dokumen real-time dari generator master
                            generated_pr_no = generate_document_number("PR")
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
                                "status": "PENDING APPROVAL",
                                "note": p_note.strip()
                            }
                            
                            df_pr_hist = load_cloud_data("trn_purchase_requisitions")
                            df_pr_updated = pd.concat([df_pr_hist, pd.DataFrame([new_pr_doc])], ignore_index=True)
                            
                            if save_cloud_data(df_pr_updated, "trn_purchase_requisitions"):
                                st.success(f"🎉 Sukses! Dokumen Permintaan Resmi berhasil diterbitkan dengan Nomor: **{generated_pr_no}**")
                                st.balloons()
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
        
        tab_core, tab_doc_master = st.tabs(["📁 CRUD Manual Komplet", "🔏 Master Setting No Dokumen"])
        
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
                # IMPROVEMENT FITUR 1: UPDATE FORM MASTER ITEM SESUAI FILTER PILIHAN MULTI-FUNGSI
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
                                
                            # IMPLEMENTASI SELEKSI PILIHAN MULTI-FUNGSI (BISA MEMILIH LEBIH DARI 1 FILTER)
                            st.markdown("**🎯 Filter Fungsi Operasional ERP Item**")
                            f_inv = st.checkbox("Inventory (Barang dihitung pergerakannya karena ada nilai cost)")
                            f_sal = st.checkbox("Sales (Item yang muncul di Item Price untuk POS / Jual)")
                            f_pur = st.checkbox("Purchase (Item yang dibeli dari pihak vendor supplier)")
                            f_bom = st.checkbox("Item BOM (Item hasil produksi berdasarkan Bill of Material)")
                            f_pkg = st.checkbox("Header Package (Nama paket, memuat harga tanpa nilai inventory)")
                            
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
                                        st.success("🎉 Master Item Multi-Fungsi berhasil terdaftar!"); st.rerun()

                # FORM MASTER LAINNYA TETAP AKTIF SECARA OTOMATIS
                elif pilih_tabel_core == "mst_units":
                    with st.form("form_uom", clear_on_submit=True):
                        u_id = st.text_input("unit_id"); u_name = st.text_input("unit_name"); u_ket = st.text_input("Keterangan")
                        if st.form_submit_button("Simpan UOM"):
                            new_row = pd.DataFrame([{"unit_id": u_id.upper(), "unit_name": u_name, "Keterangan": u_ket}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core): st.rerun()

                elif pilih_tabel_core == "mst_uom_conversions":
                    list_uom = load_cloud_data("mst_units")["unit_id"].tolist() if os.path.exists(DATA_FILE) else []
                    with st.form("form_cnv", clear_on_submit=True):
                        c_id = st.text_input("conversion_id")
                        c_from = st.selectbox("From UOM", list_uom)
                        c_to = st.selectbox("To UOM", list_uom)
                        c_op = st.selectbox("Operator", ["Kali (*)", "Bagi (/)"])
                        c_fac = st.number_input("Factor", min_value=0.001, value=1.0)
                        if st.form_submit_button("Simpan Konversi"):
                            new_row = pd.DataFrame([{"conversion_id": c_id.upper(), "from_uom": c_from, "to_uom": c_to, "operator": c_op, "factor": c_fac}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core): st.rerun()

                elif pilih_tabel_core == "mst_branches":
                    with st.form("form_br", clear_on_submit=True):
                        b_id = st.text_input("branch_id"); b_name = st.text_input("branch_name")
                        b_type = st.selectbox("branch_type", ["Outlet", "Central Production", "Head Office"]); b_addr = st.text_input("address")
                        if st.form_submit_button("Simpan Cabang"):
                            new_row = pd.DataFrame([{"branch_id": b_id, "branch_name": b_name, "branch_type": b_type, "address": b_addr}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core): st.rerun()

                elif pilih_tabel_core == "mst_suppliers":
                    with st.form("form_spl", clear_on_submit=True):
                        s_id = st.text_input("supplier_id"); s_name = st.text_input("supplier_name")
                        s_phone = st.text_input("phone"); s_terms = st.text_input("payment_terms")
                        if st.form_submit_button("Simpan Supplier"):
                            new_row = pd.DataFrame([{"supplier_id": s_id, "supplier_name": s_name, "phone": s_phone, "payment_terms": s_terms}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core): st.rerun()

            elif action_mode == "❌ Hapus Data Terpilih" and not df_core.empty:
                id_pilih_hapus = st.selectbox("Pilih ID Data yang Akan Dihapus", df_core[pk_col].tolist())
                if st.button("Konfirmasi Hapus Permanen", type="primary"):
                    if save_cloud_data(df_core[df_core[pk_col] != id_pilih_hapus], pilih_tabel_core): st.rerun()

        # --- IMPROVEMENT FITUR 2: MASTER SETTING PENOMORAN DOKUMEN (AUTOMATION DOC ENGINE) ---
        with tab_doc_master:
            st.subheader("🔏 Master Kustomisasi Pola Penomoran Dokumen (Auto-Numbering)")
            df_doc_settings = load_cloud_data("mst_doc_settings")
            st.dataframe(df_doc_settings, use_container_width=True, hide_index=True)
            
            with st.form("form_setting_doc"):
    st.markdown("**Edit Parameter Kode Pola Transaksi Terpusat**")
    sel_type = st.selectbox("Pilih Modul Transaksi", ["PR"])
    
    # Naikkan atau sesuaikan jika dibutuhkan, pastikan default value aman
    new_init_doc = st.text_input("1. Initial Document (2 Karakter)", value="PR")
    new_init_comp = st.text_input("2. Initial Perusahaan (3 Karakter)", value="SRR")
    
    st.caption("Pola Akhir Terbentuk: `XX-XXXYYYYMMXXXXXX` (Contoh: PR-SRR202606000001)")
    
    if st.form_submit_button("Simpan Master Pola Dokumen"):
        if len(new_init_doc).strip() == "" or len(new_init_comp).strip() == "":
            st.error("Gagal! Input initial tidak boleh kosong.")
        else:
            idx_set = df_doc_settings[df_doc_settings['doc_type'] == sel_type].index
            if len(idx_set) > 0:
                df_doc_settings.loc[idx_set[0], 'initial_doc'] = new_init_doc.upper().strip()
                df_doc_settings.loc[idx_set[0], 'initial_company'] = new_init_comp.upper().strip()
                save_cloud_data(df_doc_settings, "mst_doc_settings")
                st.success("Konfigurasi pola nomor urut dokumen resmi diperbarui!")
                st.rerun()
