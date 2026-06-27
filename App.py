import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import json
import os
import io

# 1. KONFIGURASI UTAMA
st.set_page_config(page_title="ERPOS System - Professional Enterprise", page_icon="🏬", layout="wide")

DATA_FILE = "data/erpos_cloud_data.json"

# --- SYSTEM INIT DATABASE ---
def init_database():
    default_data = {
        "mst_users": [
            {"user_id": "USR-001", "username": "riyan_owner", "password": "admin123", "role_id": "OWNER", "employee_name": "Riyan Anjasmoro"}
        ],
        "mst_units": [
            {"unit_id": "UOM-KG", "unit_name": "Kilogram", "Keterangan": "Satuan Massa Dasar"},
            {"unit_id": "UOM-GR", "unit_name": "Gram", "Keterangan": "Satuan Massa Kecil"},
            {"unit_id": "UOM-PCS", "unit_name": "Pieces", "Keterangan": "Satuan Barang Jadi/Eceran"},
            {"unit_id": "UOM-PACK", "unit_name": "Pack", "Keterangan": "Satuan Kemasan Grosis"}
        ],
        "mst_uom_conversions": [
            {"conversion_id": "CNV-001", "from_uom": "UOM-KG", "to_uom": "UOM-GR", "operator": "Kali (*)", "factor": 1000},
            {"conversion_id": "CNV-002", "from_uom": "UOM-PACK", "to_uom": "UOM-PCS", "operator": "Kali (*)", "factor": 24}
        ],
        "mst_items": [
            {"item_id": "ITM-001", "item_name": "Tepung Terigu Cakra Kembar", "item_type": "Bahan Baku", "category": "Tepung", "uom_purchase": "UOM-PACK", "uom_stock": "UOM-KG", "min_stock": 50}
        ],
        "mst_branches": [
            {"branch_id": "SR-SOF0001-JS-01", "branch_name": "Supporting Office", "branch_type": "Head Office", "address": "Jl TB Simatupang"},
            {"branch_id": "SR-CKT0001-DP-01", "branch_name": "Central Production Depok", "branch_type": "Central Production", "address": "Area Produksi 700m2"}
        ],
        "mst_suppliers": [
            {"supplier_id": "SPL-001", "supplier_name": "PT Sumber Terigu Nusantara", "phone": "0812345678", "payment_terms": "COD / Cash"}
        ]
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
        st.error(f"Gagal menyimpan data ke cloud storage: {e}")
        return False

# 2. SESSION STATE MANAGEMENT
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None
if 'active_menu' not in st.session_state:
    st.session_state['active_menu'] = "Dashboard Utama"

# --- LOGIN SCREEN ---
if not st.session_state['logged_in']:
    st.title("🔐 ERPOS System - Enterprise Master Data Suite")
    st.markdown("---")
    username_input = st.text_input("Username / ID Pengguna")
    password_input = st.text_input("Password Keamanan", type="password")
    
    if st.button("Masuk Ke Sistem ERPOS", type="primary", use_container_width=True):
        df_users = load_cloud_data("mst_users")
        user_match = df_users[(df_users['username'].astype(str).str.strip() == username_input.strip()) & 
                              (df_users['password'].astype(str).str.strip() == str(password_input).strip())]
        if not user_match.empty:
            user_data = user_match.iloc[0].to_dict()
            st.session_state['user_info'] = {
                'name': user_data['employee_name'], 'role': user_data['role_id'], 'is_owner': str(user_data['role_id']).upper() == "OWNER"
            }
            st.session_state['logged_in'] = True
            st.session_state['active_menu'] = "⚙️ Master Data"
            st.rerun()
        else:
            st.error("Kredensial salah!")

# --- MAIN SYSTEM PANEL ---
else:
    info = st.session_state['user_info']
    
    with st.sidebar:
        st.subheader("🏬 ERPOS Control Panel")
        st.caption(f"User: **{info['name']}** ({info['role']})")
        st.write("---")
        selected_menu = option_menu(
            menu_title="Navigasi Modul ERP",
            options=["Dashboard Utama", "WMS & Gudang", "⚙️ Master Data"],
            icons=["speedometer2", "box-seam", "database-gear"],
            menu_icon="layers-half",
            default_index=["Dashboard Utama", "WMS & Gudang", "⚙️ Master Data"].index(st.session_state['active_menu'])
        )
        if selected_menu != st.session_state['active_menu']:
            st.session_state['active_menu'] = selected_menu
            st.rerun()
        st.markdown("---")
        if st.button("🚪 Keluar Sistem", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.rerun()

    # --- ROUTER MODUL INTERFACE ---
    if st.session_state['active_menu'] == "Dashboard Utama":
        st.title("📊 Executive Dashboard & Analytics")
        st.info("Sistem Engine JSON sinkron sempurna.")
        
    elif st.session_state['active_menu'] == "WMS & Gudang":
        st.title("📦 Warehouse Management System (WMS)")
        st.subheader("Data Realtime Master Items Terdaftar")
        st.dataframe(load_cloud_data("mst_items"), use_container_width=True, hide_index=True)
        
    elif st.session_state['active_menu'] == "⚙️ Master Data":
        st.title("⚙️ Pusat Konfigurasi Master Data ERP")
        
        tab_core, tab_import = st.tabs(["📁 CRUD Manual Komplet", "📥 Bulk Import Data"])
        
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
                st.markdown(f"### Form Tambah Data Baru: `{pilih_tabel_core}`")
                
                # JALUR 1: FORM INPUT MASTER ITEMS (TERIKAT MATRIKS UOM)
                if pilih_tabel_core == "mst_items":
                    df_uom_master = load_cloud_data("mst_units")
                    if df_uom_master.empty:
                        st.error("⚠️ SISTEM ERP TERKUNCI: Anda wajib mengisi data di Master UOM (mst_units) terlebih dahulu sebelum bisa menambahkan Item Master baru.")
                    else:
                        list_uom = df_uom_master["unit_id"].dropna().astype(str).tolist()
                        with st.form("form_item_manual", clear_on_submit=True):
                            i_id = st.text_input("item_id (Contoh: ITM-004)")
                            i_name = st.text_input("item_name (Nama Barang)")
                            i_type = st.selectbox("item_type", ["Bahan Baku", "Barang Jadi", "WIP / Setengah Jadi"])
                            i_cat = st.text_input("category (Kategori)")
                            col_u1, col_u2 = st.columns(2)
                            with col_u1:
                                i_uom_purchase = st.selectbox("uom_purchase (Satuan Pembelian)", list_uom)
                            with col_u2:
                                i_uom_stock = st.selectbox("uom_stock (Satuan Stok Gudang)", list_uom)
                            i_min = st.number_input("min_stock", min_value=0, value=10)
                            
                            if st.form_submit_button("Simpan Item Master Baru"):
                                if i_id.strip() == "" or i_name.strip() == "":
                                    st.error("ID dan Nama Item wajib diisi!")
                                elif not df_core.empty and i_id in df_core["item_id"].astype(str).tolist():
                                    st.error("item_id sudah terdaftar!")
                                else:
                                    new_row = pd.DataFrame([{"item_id": i_id.strip(), "item_name": i_name.strip(), "item_type": i_type, "category": i_cat.strip(), "uom_purchase": i_uom_purchase, "uom_stock": i_uom_stock, "min_stock": i_min}])
                                    if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core):
                                        st.success("🎉 Sukses menyimpan Master Item baru!"); st.rerun()

                # JALUR 2: FORM INPUT MASTER UOM (`mst_units`)
                elif pilih_tabel_core == "mst_units":
                    with st.form("form_uom_manual", clear_on_submit=True):
                        u_id = st.text_input("unit_id (Contoh: UOM-BOX)")
                        u_name = st.text_input("unit_name (Nama Satuan)")
                        u_ket = st.text_input("Keterangan")
                        if st.form_submit_button("Simpan Master UOM Baru"):
                            if u_id.strip() == "": st.error("unit_id wajib diisi!")
                            else:
                                new_row = pd.DataFrame([{"unit_id": u_id.strip().upper(), "unit_name": u_name.strip(), "Keterangan": u_ket.strip()}])
                                if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core):
                                    st.success("🎉 Master UOM Berhasil Disimpan!"); st.rerun()

                # JALUR 3: FORM INPUT MASTER KONVERSI UOM (`mst_uom_conversions`) PERSIS SEPERTI GAMBAR ACUAN
                elif pilih_tabel_core == "mst_uom_conversions":
                    df_uom_master = load_cloud_data("mst_units")
                    if df_uom_master.empty:
                        st.error("⚠️ SISTEM TERKUNCI: Data Master UOM masih kosong. Isi Master UOM terlebih dahulu.")
                    else:
                        list_uom = df_uom_master["unit_id"].dropna().astype(str).tolist()
                        with st.form("form_conversion_manual", clear_on_submit=True):
                            c_id = st.text_input("conversion_id (Contoh: CNV-003)")
                            col_c1, col_c2 = st.columns(2)
                            with col_c1:
                                c_from = st.selectbox("From UOM (Unit Asal)", list_uom)
                                c_op = st.selectbox("Operator Operasi", ["Kali (*)", "Bagi (/)"])
                            with col_c2:
                                c_to = st.selectbox("To UOM (Unit Tujuan)", list_uom)
                                c_factor = st.number_input("Factor (Nilai Pengali/Pembagi)", min_value=0.0001, value=1.0, format="%.4f")
                            
                            if st.form_submit_button("Simpan Aturan Konversi Baru"):
                                if c_id.strip() == "": st.error("conversion_id wajib diisi!")
                                else:
                                    new_row = pd.DataFrame([{"conversion_id": c_id.strip().upper(), "from_uom": c_from, "to_uom": c_to, "operator": c_op, "factor": c_factor}])
                                    if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core):
                                        st.success("🎉 Aturan Konversi UOM Berhasil Didaftarkan!"); st.rerun()

                # JALUR 4 & 5: BRANCHES & SUPPLIERS
                elif pilih_tabel_core == "mst_branches":
                    with st.form("form_branch_manual", clear_on_submit=True):
                        b_id = st.text_input("branch_id"); b_name = st.text_input("branch_name")
                        b_type = st.selectbox("branch_type", ["Outlet", "Central Production", "Head Office"])
                        b_addr = st.text_input("address")
                        if st.form_submit_button("Simpan Cabang"):
                            new_row = pd.DataFrame([{"branch_id": b_id, "branch_name": b_name, "branch_type": b_type, "address": b_addr}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core): st.rerun()

                elif pilih_tabel_core == "mst_suppliers":
                    with st.form("form_supplier_manual", clear_on_submit=True):
                        s_id = st.text_input("supplier_id"); s_name = st.text_input("supplier_name")
                        s_phone = st.text_input("phone"); s_terms = st.text_input("payment_terms")
                        if st.form_submit_button("Simpan Supplier"):
                            new_row = pd.DataFrame([{"supplier_id": s_id, "supplier_name": s_name, "phone": s_phone, "payment_terms": s_terms}])
                            if save_cloud_data(pd.concat([df_core, new_row], ignore_index=True), pilih_tabel_core): st.rerun()

            elif action_mode == "❌ Hapus Data Terpilih" and not df_core.empty:
                id_pilih_hapus = st.selectbox("Pilih ID yang Akan Dihapus", df_core[pk_col].tolist())
                if st.button("Konfirmasi Hapus Permanen", type="primary"):
                    if save_cloud_data(df_core[df_core[pk_col] != id_pilih_hapus], pilih_tabel_core):
                        st.success("Data berhasil terhapus!"); st.rerun()

        # --- TAB 2: BULK IMPORT PERMANEN ANTI-LAG ---
        with tab_import:
            st.subheader("📥 Bulk Import System Terpusat (CSV Engine)")
            pilih_target_bulk = st.selectbox("Pilih Target Tabel Bulk", ["mst_items", "mst_units", "mst_uom_conversions", "mst_branches", "mst_suppliers"], key="sel_bulk_pro")
            headers_map = {
                "mst_items": ["item_id", "item_name", "item_type", "category", "uom_purchase", "uom_stock", "min_stock"],
                "mst_units": ["unit_id", "unit_name", "Keterangan"],
                "mst_uom_conversions": ["conversion_id", "from_uom", "to_uom", "operator", "factor"],
                "mst_branches": ["branch_id", "branch_name", "branch_type", "address"],
                "mst_suppliers": ["supplier_id", "supplier_name", "phone", "payment_terms"]
            }
            chosen_headers = headers_map.get(pilih_target_bulk)
            csv_buffer = io.StringIO()
            pd.DataFrame(columns=chosen_headers).to_csv(csv_buffer, index=False)
            st.download_button(label="📥 Download Template CSV Resmi", data=csv_buffer.getvalue(), file_name=f"template_{pilih_target_bulk}.csv", mime="text/csv")
            
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
                        if save_cloud_data(pd.concat([df_meta, df_upload], ignore_index=True).drop_duplicates(), pilih_target_bulk):
                            st.success("🎉 Seluruh data massal resmi masuk & terintegrasi penuh!"); st.rerun()
                except Exception as e: st.error(f"Gagal memproses file upload: {e}")
