import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import os
import io

# 1. KONFIGURASI UTAMA
st.set_page_config(page_title="ERPOS System - Enterprise", page_icon="🏬", layout="wide")

DB_PATH = "data/erpos_database.xlsx"

# --- FUNGSI AMAN UNTUK LOAD DATA ---
def load_data(sheet_name):
    if os.path.exists(DB_PATH):
        try:
            return pd.read_excel(DB_PATH, sheet_name=sheet_name)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df, sheet_name):
    with pd.ExcelWriter(DB_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

# 2. SISTEM ROUTING & SESSION STATE ANTI LOG OUT
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None
if 'active_menu' not in st.session_state:
    st.session_state['active_menu'] = "Dashboard Utama"

# --- FASE 1: LOGIN ---
if not st.session_state['logged_in']:
    st.title("🔐 ERPOS System - Enterprise Core")
    username_input = st.text_input("Username", key="login_username")
    password_input = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Masuk Ke Sistem", type="primary", key="btn_login"):
        # JALUR PENGAMAN MANDIRI
        if username_input.strip() == "riyan_owner" and password_input.strip() == "admin123":
            st.session_state['user_info'] = {
                'name': "Riyan Anjasmoro",
                'role': "OWNER",
                'branch_id': "SR-SOF0001-JS-01",
                'branch_name': "Supporting Office",
                'is_owner': True
            }
            st.session_state['logged_in'] = True
            st.session_state['active_menu'] = "Dashboard Utama"
            st.rerun()
        else:
            df_users = load_data("mst_users")
            df_branches = load_data("mst_branches")
            
            if not df_users.empty:
                user_match = df_users[(df_users['username'].astype(str).str.strip() == username_input.strip()) & 
                                      (df_users['password'].astype(str).str.strip() == str(password_input).strip())]
                
                if not user_match.empty:
                    user_data = user_match.iloc[0].to_dict()
                    
                    branch_id_col = 'branch_id' if 'branch_id' in df_branches.columns else df_branches.columns[0] if not df_branches.empty else ''
                    branch_name_col = 'branch_name' if 'branch_name' in df_branches.columns else df_branches.columns[1] if len(df_branches.columns) > 1 else ''
                    
                    branch_match = df_branches[df_branches[branch_id_col].astype(str).str.strip() == str(user_data['assigned_branch']).strip()] if branch_id_col else pd.DataFrame()
                    branch_info = branch_match.iloc[0].to_dict() if not branch_match.empty else {}
                    
                    st.session_state['user_info'] = {
                        'name': user_data['employee_name'],
                        'role': user_data['role_id'],
                        'branch_id': user_data['assigned_branch'],
                        'branch_name': branch_info.get(branch_name_col, 'Kantor Pusat / Unknown'),
                        'is_owner': str(user_data['role_id']).upper() == "OWNER"
                    }
                    st.session_state['logged_in'] = True
                    st.session_state['active_menu'] = "Dashboard Utama"
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
            else:
                st.error("Database pengguna kosong atau gagal dimuat!")

# --- FASE 2: APLIKASI UTAMA ---
else:
    info = st.session_state['user_info']
    is_owner = info.get('is_owner', False)
    
    # MEMBANGUN MENU UTAMA SECARA FAIL-SAFE
    menu_options = ["Dashboard Utama"]
    menu_icons = ["speedometer2"]
    
    # Jika dia OWNER, langsung buka semua tanpa cek sheet Excel permission matrix
    if is_owner:
        menu_options.extend(["WMS & Gudang", "Pusat Produksi (WIP)", "Keuangan & Konsolidasi", "Mesin Kasir (POS)", "⚙️ Master Data"])
        menu_icons.extend(["box-seam", "tools", "wallet2", "calculator", "database-gear"])
    else:
        # Untuk staff non-owner, berikan modul POS default sementara waktu
        if info['role'] in ["CASHIER"]:
            menu_options.append("Mesin Kasir (POS)")
            menu_icons.append("calculator")
        else:
            menu_options.append("WMS & Gudang")
            menu_icons.append("box-seam")

    with st.sidebar:
        st.subheader("🏬 ERPOS Control Panel")
        st.caption(f"Karyawan: **{info['name']}**")
        st.caption(f"Jabatan: **{info['role']}**")
        st.caption(f"Penugasan: **{info['branch_name']}**")
        st.write("---")
        
        selected_menu = option_menu(
            menu_title="Navigasi Modul",
            options=menu_options,
            icons=menu_icons,
            menu_icon="layers-half",
            default_index=menu_options.index(st.session_state['active_menu']) if st.session_state['active_menu'] in menu_options else 0
        )
        if selected_menu != st.session_state['active_menu']:
            st.session_state['active_menu'] = selected_menu
            st.rerun()
            
        st.markdown("---")
        if st.button("🚪 Keluar Sistem", use_container_width=True, key="btn_logout"):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.session_state['active_menu'] = "Dashboard Utama"
            st.rerun()

    # --- CONTROLLER INTERFACE MODUL ---
    if st.session_state['active_menu'] == "Dashboard Utama":
        st.title("📊 Ringkasan Eksekutif Bisnis")
        st.subheader(f"Sistem Kendali Utama Cabang: {info['branch_name']}")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric(label="Status Server", value="ONLINE", delta="Sinkron Terpusat")
        with col_m2:
            st.metric(label="Lokasi Cabang", value=info.get('branch_id', 'HQ'))
        with col_m3:
            st.metric(label="Level Otoritas", value=info['role'])
        
    elif st.session_state['active_menu'] == "WMS & Gudang":
        st.title("📦 Warehouse Management System (WMS)")
        st.subheader("Katalog Data Barang / Stok Terdaftar")
        df_items = load_data("mst_items")
        if not df_items.empty:
            st.dataframe(df_items, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data barang di sheet `mst_items`.")
        
    elif st.session_state['active_menu'] == "Pusat Produksi (WIP)":
        st.title("🏭 Pusat Produksi Hub (Work-In-Progress)")
        st.subheader("Log Rekaman Mutasi & Alur Stok")
        df_mutations = load_data("trn_stock_mutations")
        if not df_mutations.empty:
            st.dataframe(df_mutations, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada transaksi mutasi di sheet `trn_stock_mutations`.")

    elif st.session_state['active_menu'] == "Keuangan & Konsolidasi":
        st.title("💰 Modul Keuangan & Neraca Konsolidasi")
        st.info("Akses pembukuan internal terkunci aman. Sistem siap mengonsolidasikan jurnal kas outlet.")
        
    elif st.session_state['active_menu'] == "Mesin Kasir (POS)":
        st.title("🧮 Mesin Kasir (Point of Sales)")
        st.write(f"Kasir Aktif: **{info['name']}** | Lokasi Outlet: **{info['branch_name']}**")
        st.button("Buka Kasir Baru (Mulai Shift)", type="primary")

    elif st.session_state['active_menu'] == "⚙️ Master Data":
        st.title("⚙️ Manajemen Pusat Data Terpusat")
        
        tab_core, tab_field, tab_import = st.tabs([
            "📁 Master Data Core (CRUD)", "➕ Kustomisasi Field", "📥 Bulk Import Data"
        ])
        
        with tab_core:
            pilih_tabel_core = st.selectbox("Pilih Tabel Core", ["mst_branches", "mst_units", "mst_suppliers", "mst_items"], key="sel_core")
            df_core = load_data(pilih_tabel_core)
            
            st.subheader(f"Data Live Tabel `{pilih_tabel_core}`")
            st.dataframe(df_core, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            action_mode = st.radio("Operasi Data", ["➕ Tambah Data", "❌ Hapus Data"], horizontal=True, key="action_core")
            pk_col = df_core.columns[0] if not df_core.empty else ''
            
            if action_mode == "➕ Tambah Data" and pk_col:
                with st.form("form_core_submit"):
                    inputs = {}
                    for col in df_core.columns:
                        inputs[col] = st.text_input(f"Isi {col}", key=f"add_{pilih_tabel_core}_{col}")
                    if st.form_submit_button("Submit Data Baru"):
                        if inputs[pk_col].strip() == "":
                            st.error("Kolom Kunci Utama wajib diisi.")
                        else:
                            new_row = pd.DataFrame([[inputs[c] for c in df_core.columns]], columns=df_core.columns)
                            df_core = pd.concat([df_core, new_row], ignore_index=True)
                            save_data(df_core, pilih_tabel_core)
                            st.success("Data Berhasil Ditambahkan!")
                            st.rerun()
                            
            elif action_mode == "❌ Hapus Data" and pk_col:
                if not df_core.empty:
                    id_pilih_hapus = st.selectbox("Pilih ID yang Akan Dihapus", df_core[pk_col].tolist(), key="sb_del")
                    if st.button("Konfirmasi Hapus Permanen", type="primary"):
                        df_core = df_core[df_core[pk_col] != id_pilih_hapus]
                        save_data(df_core, pilih_tabel_core)
                        st.success(f"Data ID '{id_pilih_hapus}' Berhasil Dihapus!")
                        st.rerun()

        with tab_field:
            st.subheader("➕ Tambah Kolom Baru Secara Global")
            try:
                import openpyxl
                wb = openpyxl.load_workbook(DB_PATH)
                sheets_global = wb.sheetnames
                wb.close()
                
                pilih_sheet_univ = st.selectbox("Pilih Target Tabel", sheets_global, key="sel_univ")
                nama_kolom_baru = st.text_input("Nama Kolom Baru (Gunakan underscore, tanpa spasi)", key="in_col_univ").strip()
                
                if st.button("Suntik Kolom Baru", type="primary"):
                    if nama_kolom_baru:
                        df_univ = load_data(pilih_sheet_univ)
                        if nama_kolom_baru in df_univ.columns:
                            st.error("Kolom sudah terdaftar!")
                        else:
                            df_univ[nama_kolom_baru] = ""
                            save_data(df_univ, pilih_sheet_univ)
                            st.success(f"Kolom `{nama_kolom_baru}` Berhasil Disuntikkan!")
                            st.rerun()
            except Exception as e:
                st.error(f"Gagal memuat struktur file: {e}")

        with tab_import:
            st.subheader("📥 Bulk Import Massal")
            pilih_target_bulk = st.selectbox("Pilih Modul Tujuan Upload", ["mst_items", "mst_branches", "mst_suppliers"], key="sel_bulk")
            df_meta = load_data(pilih_target_bulk)
            
            file_unggah = st.file_uploader("Upload File Excel Hasil Pengisian", type=["xlsx"], key="file_bulk_uploader")
            if file_unggah is not None:
                try:
                    df_upload_baru = pd.read_excel(file_unggah)
                    st.write("Pratinjau Data Unggahan:")
                    st.dataframe(df_upload_baru.head(), use_container_width=True, hide_index=True)
                    
                    if st.button("Gabungkan Data ke Sistem", type="primary"):
                        if list(df_upload_baru.columns) == list(df_meta.columns):
                            df_gabung = pd.concat([df_meta, df_upload_baru], ignore_index=True).drop_duplicates()
                            save_data(df_gabung, pilih_target_bulk)
                            st.success("Bulk Import Massal Berhasil Terintegrasi!")
                            st.rerun()
                        else:
                            st.error("Susunan kolom berkas tidak sama dengan struktur tabel master data!")
                except Exception as err:
                    st.error(f"Gagal memproses berkas: {err}")
