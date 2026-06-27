import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import os
import io
import openpyxl

# 1. KONFIGURASI UTAMA & THEME ERP ENTERPRISE
st.set_page_config(page_title="ERPOS System - Enterprise Edition", page_icon="🏬", layout="wide")

DB_PATH = "data/erpos_database.xlsx"

# --- ENGINE UTAMA MANAJEMEN BERKAS ERP (ANTI FILE-LOCKING STREAM IO) ---
def load_data(sheet_name):
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "rb") as f:
                file_bytes = f.read()
            return pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df, sheet_name):
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        if not os.path.exists(DB_PATH):
            wb = openpyxl.Workbook()
            wb.save(DB_PATH)
            
        with open(DB_PATH, "rb") as f:
            file_bytes = f.read()
            
        book = openpyxl.load_workbook(io.BytesIO(file_bytes))
        
        with pd.ExcelWriter(DB_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            writer.workbook = book
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        return True
    except Exception as e:
        st.error(f"Sistem Gagal Menyimpan ke Excel Pusat: {e}")
        return False

# 2. STATE ROUTING MANAJEMEN SESSION OPERASIONAL
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None
if 'active_menu' not in st.session_state:
    st.session_state['active_menu'] = "Dashboard Utama"

# --- FASE 1: GERBANG OTENTIKASI UTAMA (LOGIN) ---
if not st.session_state['logged_in']:
    st.title("🔐 ERPOS System - Enterprise Core Management")
    st.markdown("---")
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.container(border=True):
            st.subheader("Login Karyawan Terpusat")
            username_input = st.text_input("Username / ID Pengguna", key="login_username")
            password_input = st.text_input("Password Keamanan", type="password", key="login_password")
            
            if st.button("Masuk Ke Sistem ERPOS", type="primary", use_container_width=True):
                if username_input.strip() == "riyan_owner" and password_input.strip() == "admin123":
                    st.session_state['user_info'] = {
                        'name': "Riyan Anjasmoro",
                        'role': "OWNER",
                        'branch_id': "SR-SOF0001-JS-01",
                        'branch_name': "Supporting Office",
                        'is_owner': True
                    }
                    st.session_state['logged_in'] = True
                    st.session_state['active_menu'] = "⚙️ Master Data"
                    st.rerun()
                else:
                    df_users = load_data("mst_users")
                    if not df_users.empty:
                        user_match = df_users[(df_users['username'].astype(str).str.strip() == username_input.strip()) & 
                                              (df_users['password'].astype(str).str.strip() == str(password_input).strip())]
                        if not user_match.empty:
                            user_data = user_match.iloc[0].to_dict()
                            st.session_state['user_info'] = {
                                'name': user_data['employee_name'],
                                'role': user_data['role_id'],
                                'branch_id': user_data['assigned_branch'],
                                'branch_name': "Operational Branch",
                                'is_owner': str(user_data['role_id']).upper() == "OWNER"
                            }
                            st.session_state['logged_in'] = True
                            st.session_state['active_menu'] = "Dashboard Utama"
                            st.rerun()
                        else:
                            st.error("Kredensial salah! Periksa kembali Username & Password.")
                    else:
                        st.error("Database pengguna kosong atau tidak terbaca!")

# --- FASE 2: PANEL UTAMA ERPOS ENTERPRISE ---
else:
    info = st.session_state['user_info']
    is_owner = info.get('is_owner', False)
    
    menu_options = ["Dashboard Utama"]
    menu_icons = ["speedometer2"]
    
    if is_owner:
        menu_options.extend(["WMS & Gudang", "Pusat Produksi (WIP)", "Keuangan & Konsolidasi", "Mesin Kasir (POS)", "⚙️ Master Data"])
        menu_icons.extend(["box-seam", "tools", "wallet2", "calculator", "database-gear"])

    with st.sidebar:
        st.subheader("🏬 ERPOS Control Panel")
        st.caption(f"Karyawan: **{info['name']}** | Otoritas: **{info['role']}**")
        st.write("---")
        
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
        if st.button("🚪 Keluar Sistem ERPOS", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.session_state['active_menu'] = "Dashboard Utama"
            st.rerun()

    # --- ANTARMUKA HALAMAN ---
    if st.session_state['active_menu'] == "Dashboard Utama":
        st.title("📊 Executive Dashboard & Analytics")
        st.info("Selamat datang kembali di sistem kendali pusat ERPOS.")
        
    elif st.session_state['active_menu'] == "WMS & Gudang":
        st.title("📦 Warehouse Management System (WMS)")
        df_items = load_data("mst_items")
        st.dataframe(df_items, use_container_width=True, hide_index=True)
        
    elif st.session_state['active_menu'] == "Pusat Produksi (WIP)":
        st.title("🏭 Pusat Produksi Hub (Work-In-Progress)")
        df_mutations = load_data("trn_stock_mutations")
        st.dataframe(df_mutations, use_container_width=True, hide_index=True)

    elif st.session_state['active_menu'] == "Keuangan & Konsolidasi":
        st.title("💰 Modul Keuangan & Neraca Konsolidasi")
        
    elif st.session_state['active_menu'] == "Mesin Kasir (POS)":
        st.title("🧮 Mesin Kasir (Point of Sales)")

    elif st.session_state['active_menu'] == "⚙️ Master Data":
        st.title("⚙️ Pusat Konfigurasi Master Data ERP")
        
        tab_core, tab_import, tab_permission = st.tabs([
            "📁 Master Data Core (CRUD Manual)", "📥 Bulk Import Data Massal", "🔒 Permission Access Matrix"
        ])
        
        # --- TAB 1: CRUD MANUAL VALIDASI SELEKTIF & INTERAKTIF ---
        with tab_core:
            pilih_tabel_core = st.selectbox(
                "Pilih Tabel Komponen Bisnis", 
                ["mst_items", "mst_branches", "mst_units", "mst_suppliers"], 
                key="sel_core"
            )
            df_core = load_data(pilih_tabel_core)
            
            st.subheader(f"Data Live Tabel `{pilih_tabel_core}`")
            st.dataframe(df_core, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            action_mode = st.radio("Pilih Tindakan Operasional Data", ["➕ Submit (Tambah Data Baru)", "✏️ Edit Baris Data", "❌ Delete (Hapus Data)"], horizontal=True, key="action_core")
            
            # Pengunci nama kolom kunci utama dinamis (Primary Key)
            pk_col = df_core.columns[0] if not df_core.empty else 'id'
            
            if action_mode == "➕ Submit (Tambah Data Baru)":
                st.markdown(f"### Form Input Data Baru `{pilih_tabel_core}`")
                
                # JALUR 1: FORM KHUSUS INPUT MASTER ITEMS (DENGAN KUNCI RELASI MULTI-UOM)
                if pilih_tabel_core == "mst_items":
                    df_uom_master = load_data("mst_units")
                    
                    # VALIDASI ERP KRITIKAL: Cek ketersediaan Unit Master sebelum input Item
                    if df_uom_master.empty:
                        st.error("⚠️ SISTEM TERKUNCI: Anda belum bisa menginput Data Master Item karena Data Satuan Ukur (mst_units) masih kosong! Silakan isi tabel `mst_units` terlebih dahulu.")
                    else:
                        # Ambil daftar unit_id dari kolom pertama sheet mst_units
                        uom_id_col = df_uom_master.columns[0]
                        list_uom = df_uom_master[uom_id_col].dropna().astype(str).tolist()
                        
                        with st.form("form_items_manual", clear_on_submit=True):
                            i_id = st.text_input("item_id (Contoh: ITM-004)")
                            i_name = st.text_input("item_name (Nama Barang)")
                            i_type = st.selectbox("item_type", ["Bahan Baku", "Barang Jadi", "WIP / Setengah Jadi"])
                            i_cat = st.text_input("category (Kategori)")
                            
                            st.markdown("---")
                            st.markdown("**⚙️ Pengaturan Multi-UOM & Relasi Konversi**")
                            col_u1, col_u2 = st.columns(2)
                            with col_u1:
                                i_uom_purchase = st.selectbox("uom_purchase (Satuan Pembelian ke Supplier/Vendor)", list_uom)
                            with col_u2:
                                i_uom_stock = st.selectbox("uom_stock (Satuan Penyimpanan Dasar di Gudang/WIP)", list_uom)
                            
                            st.caption("💡 Pastikan faktor konversi antar satuan ukur ini sudah Anda atur di dalam tabel master `mst_units`.")
                            st.markdown("---")
                            
                            i_min = st.number_input("min_stock (Batas Minimum Stok)", min_value=0, value=10)
                            
                            if st.form_submit_button("Simpan Item Baru Ke Sistem"):
                                if i_id.strip() == "" or i_name.strip() == "":
                                    st.error("item_id dan item_name wajib diisi!")
                                elif not df_core.empty and i_id in df_core[pk_col].astype(str).tolist():
                                    st.error(f"ID '{i_id}' sudah terdaftar dalam sistem!")
                                else:
                                    new_item = {
                                        "item_id": i_id.strip(), "item_name": i_name.strip(), "item_type": i_type,
                                        "category": i_cat.strip(), "uom_purchase": i_uom_purchase,
                                        "uom_stock": i_uom_stock, "min_stock": i_min
                                    }
                                    df_new_row = pd.DataFrame([new_item])
                                    df_core_updated = pd.concat([df_core, df_new_row], ignore_index=True).drop_duplicates(subset=['item_id'])
                                    if save_data(df_core_updated, pilih_tabel_core):
                                        st.success("🎉 Sukses! Item baru dengan Multi-UOM terelasi berhasil disimpan.")
                                        st.rerun()
                
                # JALUR 2: FORM OTOMATIS BERDASARKAN SKEMA UNTUK MODUL LAIN (TABEL CORE BERJALAN LANCAR)
                else:
                    # Ambil fallback list kolom resmi jika sheet kosong agar field input tetap muncul
                    fallback_headers = {
                        "mst_branches": ["branch_id (ID Cabang)", "branch_name (Nama Lokasi)", "branch_type (Tipe)", "address (Alamat)"],
                        "mst_units": ["unit_id", "unit_name", "base_unit", "conversion_factor", "Keterangan"],
                        "mst_suppliers": ["supplier_id", "supplier_name", "phone", "payment_terms"]
                    }
                    
                    kolom_form = list(df_core.columns) if not df_core.empty else fallback_headers.get(pilih_tabel_core, ["id", "nama"])
                    
                    with st.form("form_universal_manual", clear_on_submit=True):
                        inputs_manual = {}
                        # Loop otomatis memunculkan seluruh field input berdasarkan judul kolom tabel
                        for col in kolom_form:
                            inputs_manual[col] = st.text_input(f"Isi data untuk kolom: `{col}`", key=f"inp_{pilih_tabel_core}_{col}")
                        
                        if st.form_submit_button(f"Simpan Data Baru ke `{pilih_tabel_core}`"):
                            # Deteksi PK dinamis untuk validasi anti-kosong
                            target_pk = kolom_form[0]
                            if inputs_manual[target_pk].strip() == "":
                                st.error(f"Kolom Kunci Utama `{target_pk}` wajib diisi!")
                            else:
                                df_new_univ = pd.DataFrame([inputs_manual])
                                # Jika data live kosong, gunakan struktur kolom bentukan baru
                                if df_core.empty:
                                    df_core_updated = df_new_univ
                                else:
                                    df_core_updated = pd.concat([df_core, df_new_univ], ignore_index=True)
                                    
                                if save_data(df_core_updated, pilih_tabel_core):
                                    st.success(f"🎉 Sukses! Data baru berhasil ditambahkan ke tabel {pilih_tabel_core}.")
                                    st.rerun()
                                    
            elif action_mode == "✏️ Edit Baris Data":
                if not df_core.empty:
                    id_pilih_edit = st.selectbox("Pilih ID Data yang Akan Diubah", df_core[pk_col].tolist(), key="sb_edit")
                    baris_edit = df_core[df_core[pk_col] == id_pilih_edit].iloc[0]
                    
                    with st.form("form_core_edit"):
                        edit_inputs = {}
                        for col in df_core.columns:
                            if col == pk_col:
                                st.info(f"Mengunci ID Utama: {id_pilih_edit}")
                                edit_inputs[col] = id_pilih_edit
                            else:
                                edit_inputs[col] = st.text_input(f"Ubah Nilai {col}", value=str(baris_edit[col]), key=f"ed_{pilih_tabel_core}_{col}")
                                
                        if st.form_submit_button("Simpan Perubahan Data"):
                            for col in df_core.columns:
                                df_core.loc[df_core[pk_col] == id_pilih_edit, col] = edit_inputs[col]
                            if save_data(df_core, pilih_tabel_core):
                                st.success("Perubahan Data Berhasil Disimpan!")
                                st.rerun()
                else:
                    st.info("Tabel ini kosong, belum ada data yang bisa diedit.")
                    
            elif action_mode == "❌ Delete (Hapus Data)":
                if not df_core.empty:
                    id_pilih_hapus = st.selectbox("Pilih ID Data yang Akan Dihapus", df_core[pk_col].tolist(), key="sb_del")
                    if st.button("Konfirmasi Hapus Data Secara Permanen", type="primary"):
                        df_core = df_core[df_core[pk_col] != id_pilih_hapus]
                        if save_data(df_core, pilih_tabel_core):
                            st.success(f"Data ID '{id_pilih_hapus}' berhasil dihapus!")
                            st.rerun()
                else:
                    st.info("Tabel kosong, tidak ada data untuk dihapus.")

        # --- TAB 2: BULK IMPORT MULTI FORMAT ---
        with tab_import:
            st.subheader("📥 Bulk Import System Terpusat")
            pilih_target_bulk = st.selectbox("Pilih Target Tabel Bulk Import", ["mst_items", "mst_branches", "mst_suppliers"], key="sel_bulk")
            
            headers_map = {
                "mst_items": ["item_id", "item_name", "item_type", "category", "uom_purchase", "uom_stock", "min_stock"],
                "mst_branches": ["branch_id (ID Cabang)", "branch_name (Nama Lokasi)", "branch_type (Tipe)", "address (Alamat)"],
                "mst_suppliers": ["supplier_id", "supplier_name", "phone", "payment_terms"]
            }
            
            df_current_meta = load_data(pilih_target_bulk)
            chosen_headers = list(df_current_meta.columns) if not df_current_meta.empty else headers_map.get(pilih_target_bulk)
                
            template_buffer = io.BytesIO()
            with pd.ExcelWriter(template_buffer, engine='openpyxl') as tmpl_writer:
                pd.DataFrame(columns=chosen_headers).to_excel(tmpl_writer, index=False, sheet_name="Template")
            
            st.download_button(
                label="📥 Download Template Excel Resmi", 
                data=template_buffer.getvalue(), 
                file_name=f"template_import_{pilih_target_bulk}.xlsx", 
                mime="application/vnd.ms-excel"
            )
            
            file_unggah = st.file_uploader("Unggah File Hasil Pengisian Template", type=["xlsx", "xls", "csv", "txt"], key="file_bulk_uploader")
            
            if file_unggah is not None:
                try:
                    try:
                        df_upload_baru = pd.read_excel(file_unggah)
                    except Exception:
                        file_unggah.seek(0)
                        df_upload_baru = pd.read_csv(file_unggah, sep=None, engine='python')
                        
                    st.write("📋 Pratinjau Data Unggahan:")
                    st.dataframe(df_upload_baru.head(), use_container_width=True, hide_index=True)
                    
                    if st.button("Eksekusi Gabungkan Data Masuk", type="primary"):
                        df_meta = load_data(pilih_target_bulk)
                        if df_meta.empty:
                            df_meta = pd.DataFrame(columns=chosen_headers)
                            
                        df_meta.columns = df_meta.columns.astype(str).str.strip()
                        df_upload_baru.columns = df_upload_baru.columns.astype(str).str.strip()
                        
                        df_gabung_final = pd.concat([df_meta, df_upload_baru], ignore_index=True).drop_duplicates()
                        if save_data(df_gabung_final, pilih_target_bulk):
                            st.success("🎉 Seluruh data massal resmi diintegrasikan ke Excel Pusat!")
                            st.rerun()
                except Exception as err:
                    st.error(f"Gagal memproses berkas! Error: {err}")

        # --- TAB 3: PERMISSION ACCESS MATRIX ---
        with tab_permission:
            st.subheader("🔒 Matriks Otentikasi Hak Akses Menu Jabatan")
            df_r = load_data("mst_roles_permission")
            
            if not df_r.empty:
                role_col = df_r.columns[0]
                pilih_role_akses = st.selectbox("Pilih Jabatan Pengaturan Otoritas", df_r[role_col].tolist())
                row_p = df_r[df_r[role_col] == pilih_role_akses].iloc[0].to_dict()
                
                c_dash = st.checkbox("Izinkan Akses Dashboard Utama", value=bool(row_p.get('allow_dashboard', False)), key="p1")
                c_wms = st.checkbox("Izinkan Akses WMS & Gudang Inventory", value=bool(row_p.get('allow_wms_inventory', False)), key="p2")
                c_prod = st.checkbox("Izinkan Akses Pusat Produksi (WIP)", value=bool(row_p.get('allow_production_hub', False)), key="p3")
                c_fin = st.checkbox("Izinkan Akses Keuangan & Konsolidasi", value=bool(row_p.get('allow_finance', False)), key="chk_fin_p")
                
                if st.button("Simpan Otentikasi Hak Akses Baru", type="primary"):
                    df_r.loc[df_r[role_col] == pilih_role_akses, 'allow_dashboard'] = c_dash
                    df_r.loc[df_r[role_col] == pilih_role_akses, 'allow_wms_inventory'] = c_wms
                    df_r.loc[df_r[role_col] == pilih_role_akses, 'allow_production_hub'] = c_prod
                    df_r.loc[df_r[role_col] == pilih_role_akses, 'allow_finance'] = c_fin
                    
                    if save_data(df_r, "mst_roles_permission"):
                        st.success("Matriks Otoritas Keamanan Berhasil Diperbarui Pusat!")
                        st.rerun()
            else:
                st.info("Tabel parameter `mst_roles_permission` tidak ditemukan.")
