import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import json
import os
import io

# 1. KONFIGURASI UTAMA
st.set_page_config(page_title="ERPOS System - Professional Cloud Edition", page_icon="🏬", layout="wide")

# MENGGUNAKAN FILE DATA BERBASIS JSON (ANTI-LOCKING & RINGAN DI SERVER CLOUD)
DATA_FILE = "data/erpos_cloud_data.json"

# --- ENGINE DATABASE CADANGAN INTERNAL (FAIL-SAFE CLOUD JSON) ---
def init_database():
    """Inisialisasi database master data awal jika file JSON belum terbentuk"""
    default_data = {
        "mst_users": [
            {"user_id": "USR-001", "username": "riyan_owner", "password": "admin123", "role_id": "OWNER", "employee_name": "Riyan Anjasmoro"}
        ],
        "mst_units": [
            {"unit_id": "UOM-KG", "unit_name": "Kilogram", "base_unit": "kg", "conversion_factor": 1, "Keterangan": "Satuan dasar gudang"},
            {"unit_id": "UOM-GR", "unit_name": "Gram", "base_unit": "kg", "conversion_factor": 0.001, "Keterangan": "Digunakan di resep"},
            {"unit_id": "UOM-PCS", "unit_name": "Pieces", "base_unit": "pcs", "conversion_factor": 1, "Keterangan": "Satuan barang jadi"}
        ],
        "mst_items": [
            {"item_id": "ITM-001", "item_name": "Tepung Terigu Cakra Kembar", "item_type": "Bahan Baku", "category": "Tepung", "uom_purchase": "UOM-KG", "uom_stock": "UOM-KG", "min_stock": 50},
            {"item_id": "ITM-002", "item_name": "Mentega Anchor", "item_type": "Bahan Baku", "category": "Mentega", "uom_purchase": "UOM-KG", "uom_stock": "UOM-KG", "min_stock": 10}
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

# Jalankan inisialisasi file json
init_database()

def load_cloud_data(table_name):
    """Membaca data tabel dari file JSON aman"""
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return pd.DataFrame(data.get(table_name, []))
    except Exception:
        return pd.DataFrame()

def save_cloud_data(df, table_name):
    """Menyimpan data tabel kembali ke file JSON aman"""
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        
        # Konversi dataframe kembali ke format list dict JSON
        data[table_name] = df.to_dict(orient="records")
        
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan data sistem: {e}")
        return False

# 2. SISTEM ROUTING & OPERASIONAL SESSION STATE
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None
if 'active_menu' not in st.session_state:
    st.session_state['active_menu'] = "Dashboard Utama"

# --- FASE 1: LOGIN ---
if not st.session_state['logged_in']:
    st.title("🔐 ERPOS System - High Availability Cloud Engine")
    st.markdown("---")
    
    username_input = st.text_input("Username / ID Pengguna", key="login_username")
    password_input = st.text_input("Password Keamanan", type="password", key="login_password")
    
    if st.button("Masuk Ke Sistem ERPOS", type="primary", use_container_width=True):
        df_users = load_cloud_data("mst_users")
        
        # Pengecekan aman anti-conflict
        user_match = df_users[(df_users['username'].astype(str).str.strip() == username_input.strip()) & 
                              (df_users['password'].astype(str).str.strip() == str(password_input).strip())]
        
        if not user_match.empty:
            user_data = user_match.iloc[0].to_dict()
            st.session_state['user_info'] = {
                'name': user_data['employee_name'],
                'role': user_data['role_id'],
                'branch_name': "Pusat Kendali Utama",
                'is_owner': str(user_data['role_id']).upper() == "OWNER"
            }
            st.session_state['logged_in'] = True
            st.session_state['active_menu'] = "⚙️ Master Data"
            st.rerun()
        else:
            st.error("Username atau Password salah!")

# --- FASE 2: APLIKASI UTAMA ---
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
        if st.button("🚪 Keluar Sistem ERPOS", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.rerun()

    # --- ROUTER HALAMAN INTERFACE ---
    if st.session_state['active_menu'] == "Dashboard Utama":
        st.title("📊 Executive Dashboard & Analytics")
        st.success("Sistem berjalan dengan lancar menggunakan Cloud JSON Database!")
        
    elif st.session_state['active_menu'] == "WMS & Gudang":
        st.title("📦 Warehouse Management System (WMS)")
        df_items = load_cloud_data("mst_items")
        st.dataframe(df_items, use_container_width=True, hide_index=True)
        
    elif st.session_state['active_menu'] == "⚙️ Master Data":
        st.title("⚙️ Pusat Pengaturan Master Data Terpusat")
        
        tab_core, tab_import = st.tabs(["📁 CRUD Manual Lengkap", "📥 Bulk Import Data"])
        
        with tab_core:
            # Pilihan modul master data hulu ke hilir
            pilih_tabel_core = st.selectbox(
                "Pilih Tabel Komponen Bisnis", 
                ["mst_items", "mst_units", "mst_branches", "mst_suppliers"], 
                key="sel_core_pro"
            )
            df_core = load_cloud_data(pilih_tabel_core)
            
            st.subheader(f"Data Live Tabel `{pilih_tabel_core}`")
            st.dataframe(df_core, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            action_mode = st.radio("Pilih Operasi Data", ["➕ Tambah Data Baru", "❌ Hapus Data"], horizontal=True)
            
            if action_mode == "➕ Tambah Data Baru":
                st.markdown(f"### Form Tambah Data Manual: `{pilih_tabel_core}`")
                
                # JALUR UTAMA 1: FORM KHUSUS INPUT MASTER ITEMS YANG TERIKAT KETAT DENGAN MASTER UOM
                if pilih_tabel_core == "mst_items":
                    df_uom_master = load_cloud_data("mst_units")
                    
                    if df_uom_master.empty:
                        st.error("⚠️ AKSER ERP TERKUNCI: Data Master UOM (mst_units) Anda kosong! Anda wajib mengisi & mensetting tabel `mst_units` terlebih dahulu sebelum menginput Item Master.")
                    else:
                        list_uom = df_uom_master["unit_id"].dropna().astype(str).tolist()
                        
                        with st.form("form_item_cloud_manual", clear_on_submit=True):
                            i_id = st.text_input("item_id (Contoh: ITM-003)")
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
                                    st.error("item_id ini sudah terdaftar di sistem!")
                                else:
                                    new_row = pd.DataFrame([{
                                        "item_id": i_id.strip(), "item_name": i_name.strip(), "item_type": i_type,
                                        "category": i_cat.strip(), "uom_purchase": i_uom_purchase, "uom_stock": i_uom_stock, "min_stock": i_min
                                    }])
                                    df_final = pd.concat([df_core, new_row], ignore_index=True)
                                    if save_cloud_data(df_final, pilih_tabel_core):
                                        st.success("🎉 Berhasil menyimpan Master Item baru ke database cloud!")
                                        st.rerun()
                                        
                # JALUR UTAMA 2: FORM DINAMIS OTOMATIS UNTUK MASTER UNITS (UOM)
                elif pilih_tabel_core == "mst_units":
                    with st.form("form_uom_manual", clear_on_submit=True):
                        u_id = st.text_input("unit_id (Contoh: UOM-KG)")
                        u_name = st.text_input("unit_name (Nama Satuan)")
                        u_base = st.text_input("base_unit (Satuan Dasar)")
                        u_conv = st.number_input("conversion_factor", min_value=0.0, value=1.0, format="%.4f")
                        u_ket = st.text_input("Keterangan")
                        
                        if st.form_submit_button("Simpan UOM Baru"):
                            if u_id.strip() == "":
                                st.error("unit_id wajib diisi!")
                            else:
                                new_row = pd.DataFrame([{
                                    "unit_id": u_id.strip(), "unit_name": u_name.strip(), "base_unit": u_base.strip(), "conversion_factor": u_conv, "Keterangan": u_ket.strip()
                                }])
                                df_final = pd.concat([df_core, new_row], ignore_index=True)
                                if save_cloud_data(df_final, pilih_tabel_core):
                                    st.success("🎉 Sukses! Master Satuan UOM berhasil didaftarkan.")
                                    st.rerun()

                # JALUR UTAMA 3: FORM DINAMIS UNTUK CABANG (BRANCHES)
                elif pilih_tabel_core == "mst_branches":
                    with st.form("form_branch_manual", clear_on_submit=True):
                        b_id = st.text_input("branch_id (Contoh: BR-OUT01)")
                        b_name = st.text_input("branch_name (Nama Lokasi)")
                        b_type = st.selectbox("branch_type", ["Outlet", "Central Production", "Head Office"])
                        b_addr = st.text_input("address (Alamat)")
                        
                        if st.form_submit_button("Simpan Cabang Baru"):
                            if b_id.strip() == "":
                                st.error("branch_id wajib diisi!")
                            else:
                                new_row = pd.DataFrame([{
                                    "branch_id": b_id.strip(), "branch_name": b_name.strip(), "branch_type": b_type, "address": b_addr.strip()
                                }])
                                df_final = pd.concat([df_core, new_row], ignore_index=True)
                                if save_cloud_data(df_final, pilih_tabel_core):
                                    st.success("🎉 Sukses! Cabang baru berhasil disimpan.")
                                    st.rerun()

                # JALUR UTAMA 4: FORM DINAMIS UNTUK VENDOR SUPPLIERS
                elif pilih_tabel_core == "mst_suppliers":
                    with st.form("form_supplier_manual", clear_on_submit=True):
                        s_id = st.text_input("supplier_id (Contoh: SPL-003)")
                        s_name = st.text_input("supplier_name (Nama Vendor)")
                        s_phone = st.text_input("phone (Nomor Kontak)")
                        s_terms = st.text_input("payment_terms (Sistem Pembayaran)")
                        
                        if st.form_submit_button("Simpan Supplier Baru"):
                            if s_id.strip() == "":
                                st.error("supplier_id wajib diisi!")
                            else:
                                new_row = pd.DataFrame([{
                                    "supplier_id": s_id.strip(), "supplier_name": s_name.strip(), "phone": s_phone.strip(), "payment_terms": s_terms.strip()
                                }])
                                df_final = pd.concat([df_core, new_row], ignore_index=True)
                                if save_cloud_data(df_final, pilih_tabel_core):
                                    st.success("🎉 Sukses! Data vendor supplier baru tersimpan.")
                                    st.rerun()
                                    
            elif action_mode == "❌ Hapus Data":
                pk_col = df_core.columns[0] if not df_core.empty else 'id'
                if not df_core.empty:
                    id_pilih_hapus = st.selectbox("Pilih ID Data yang Akan Dihapus Permanen", df_core[pk_col].tolist())
                    if st.button("Konfirmasi Hapus Permanen", type="primary"):
                        df_final = df_core[df_core[pk_col] != id_pilih_hapus]
                        if save_cloud_data(df_final, pilih_tabel_core):
                            st.success("Data berhasil dihapus!")
                            st.rerun()
                else:
                    st.info("Tabel ini kosong.")

        # --- TAB 2: BULK IMPORT PERMANEN ANTI-LOCKING ---
        with tab_import:
            st.subheader("📥 Bulk Import System Terpusat (CSV Engine)")
            st.markdown("Unggah ribuan data master sekaligus menggunakan file template text/csv yang aman tanpa dependensi biner Excel.")
            pilih_target_bulk = st.selectbox("Pilih Target Tabel Bulk", ["mst_items", "mst_branches", "mst_suppliers", "mst_units"], key="sel_bulk_pro")
            
            headers_map = {
                "mst_items": ["item_id", "item_name", "item_type", "category", "uom_purchase", "uom_stock", "min_stock"],
                "mst_branches": ["branch_id", "branch_name", "branch_type", "address"],
                "mst_suppliers": ["supplier_id", "supplier_name", "phone", "payment_terms"],
                "mst_units": ["unit_id", "unit_name", "base_unit", "conversion_factor", "Keterangan"]
            }
            
            chosen_headers = headers_map.get(pilih_target_bulk)
            
            # Download Template CSV
            csv_buffer = io.StringIO()
            pd.DataFrame(columns=chosen_headers).to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download Template CSV Resmi", 
                data=csv_buffer.getvalue(), 
                file_name=f"template_{pilih_target_bulk}.csv", 
                mime="text/csv"
            )
            
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
                        
                        df_gabung = pd.concat([df_meta, df_upload], ignore_index=True).drop_duplicates()
                        if save_cloud_data(df_gabung, pilih_target_bulk):
                            st.success("🎉 Seluruh data massal resmi masuk & terintegrasi penuh!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Gagal memproses file upload: {e}")
