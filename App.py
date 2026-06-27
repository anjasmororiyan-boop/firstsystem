import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import os
import io
import openpyxl

# 1. KONFIGURASI UTAMA & THEME ERP ENTERPRISE
st.set_page_config(page_title="ERPOS System - Enterprise Edition", page_icon="🏬", layout="wide")

DB_PATH = "data/erpos_database.xlsx"

# --- ENGINE MUTLAK MANAJEMEN BERKAS ERP (FAIL-SAFE BASE IO) ---
def load_data(sheet_name):
    if os.path.exists(DB_PATH):
        try:
            # Membaca berkas via byte stream untuk menghindari file locking di server cloud
            with open(DB_PATH, "rb") as f:
                return pd.read_excel(f, sheet_name=sheet_name)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df, sheet_name):
    try:
        # Gunakan mode 'a' jika berkas ada, jika tidak buat berkas baru
        if os.path.exists(DB_PATH):
            with pd.ExcelWriter(DB_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            with pd.ExcelWriter(DB_PATH, engine='openpyxl', mode='w') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        return True
    except Exception as e:
        st.error(f"Sistem Gagal Mengomit ke Excel Pusat: {e}")
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
                # Jalur Otentikasi Utama Pengaman (Bypass Owner Master)
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
                            
                            # Deteksi nama kolom cabang secara adaptif
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
                            st.error("Kredensial salah! Periksa kembali Username & Password.")
                    else:
                        st.error("Database pengguna kosong atau tidak terbaca!")

# --- FASE 2: PANEL UTAMA ERPOS ENTERPRISE ---
else:
    info = st.session_state['user_info']
    is_owner = info.get('is_owner', False)
    
    # 3. DINAMIS ROUTING MENU BERDASARKAN OTORITAS JABATAN
    menu_options = ["Dashboard Utama"]
    menu_icons = ["speedometer2"]
    
    if is_owner:
        menu_options.extend(["WMS & Gudang", "Pusat Produksi (WIP)", "Keuangan & Konsolidasi", "Mesin Kasir (POS)", "⚙️ Master Data"])
        menu_icons.extend(["box-seam", "tools", "wallet2", "calculator", "database-gear"])
    else:
        if info['role'] in ["CASHIER"]:
            menu_options.append("Mesin Kasir (POS)")
            menu_icons.append("calculator")
        elif info['role'] in ["HUB_MANAGER"]:
            menu_options.extend(["WMS & Gudang", "Pusat Produksi (WIP)"])
            menu_icons.extend(["box-seam", "tools"])
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

    # --- ANTARMUKA OPERASIONAL TIAP MODUL ---
    if st.session_state['active_menu'] == "Dashboard Utama":
        st.title("📊 Executive Dashboard & Analytics")
        st.subheader(f"Pusat Kendali Operasional Cabang: {info['branch_name']}")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric(label="Status Server ERPOS", value="ONLINE", delta="Sinkronisasi Sempurna")
        with col_m2:
            st.metric(label="Kode Penugasan Cabang", value=info.get('branch_id', 'HQ'))
        with col_m3:
            st.metric(label="Tingkat Otoritas Akses", value=info['role'])
        
    elif st.session_state['active_menu'] == "WMS & Gudang":
        st.title("📦 Warehouse Management System (WMS)")
        st.subheader("Katalog Data Barang Terdaftar (`mst_items`)")
        df_items = load_data("mst_items")
        if not df_items.empty:
            st.dataframe(df_items, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data barang terdaftar di dalam gudang.")
        
    elif st.session_state['active_menu'] == "Pusat Produksi (WIP)":
        st.title("🏭 Pusat Produksi Hub (Work-In-Progress)")
        st.subheader("Log Rekaman Mutasi & Alur Stok")
        df_mutations = load_data("trn_stock_mutations")
        if not df_mutations.empty:
            st.dataframe(df_mutations, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada transaksi log mutasi produksi.")

    elif st.session_state['active_menu'] == "Keuangan & Konsolidasi":
        st.title("💰 Modul Keuangan & Neraca Konsolidasi")
        st.info("Sistem Pembukuan Konsolidasi Pusat Siap Menerima Data Penjualan.")
        
    elif st.session_state['active_menu'] == "Mesin Kasir (POS)":
        st.title("🧮 Mesin Kasir (Point of Sales)")
        st.write(f"Kasir Aktif: **{info['name']}** | Lokasi Outlet: **{info['branch_name']}**")
        st.button("Buka Kasir Shift Baru", type="primary")

    elif st.session_state['active_menu'] == "⚙️ Master Data":
        st.title("⚙️ Pusat Konfigurasi Master Data ERP")
        st.markdown("Kelola seluruh entitas inti perusahaan secara terpusat, aman, dan mutakhir.")
        
        tab_core, tab_field, tab_import, tab_permission = st.tabs([
            "📁 Master Data Core (CRUD)", "➕ Kustomisasi Field Global", "📥 Bulk Import Data Massal", "🔒 Permission Access Matrix"
        ])
        
        # --- TAB 1: OPERASI DATA UTAMA (CRUD LENGKAP + EXPORT) ---
        with tab_core:
            pilih_tabel_core = st.selectbox("Pilih Tabel Komponen Bisnis", ["mst_branches", "mst_units", "mst_suppliers", "mst_items"], key="sel_core")
            df_core = load_data(pilih_tabel_core)
            
            st.subheader(f"Data Live Tabel `{pilih_tabel_core}`")
            col_exp1, col_exp2 = st.columns([4, 1])
            with col_exp1:
                st.dataframe(df_core, use_container_width=True, hide_index=True)
            with col_exp2:
                # Fitur Unduh Ekspor Data Berjalan Lancar
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as excel_writer:
                    df_core.to_excel(excel_writer, index=False, sheet_name=pilih_tabel_core)
                st.download_button(label="📥 Export ke Excel", data=buffer.getvalue(), file_name=f"export_{pilih_tabel_core}.xlsx", mime="application/vnd.ms-excel", use_container_width=True, key=f"dl_{pilih_tabel_core}")
            
            st.markdown("---")
            action_mode = st.radio("Pilih Tindakan Operasional Data", ["➕ Submit (Tambah Data Baru)", "✏️ Edit Baris Data", "❌ Delete (Hapus Data)"], horizontal=True, key="action_core")
            pk_col = df_core.columns[0] if not df_core.empty else ''
            
            if action_mode == "➕ Submit (Tambah Data Baru)" and pk_col:
                with st.form("form_core_submit", clear_on_submit=True):
                    inputs = {}
                    for col in df_core.columns:
                        inputs[col] = st.text_input(f"Isi data kolom: {col}", key=f"add_{pilih_tabel_core}_{col}")
                    if st.form_submit_button("Submit Data Baru"):
                        if inputs[pk_col].strip() == "":
                            st.error(f"Kolom Kunci Utama `{pk_col}` wajib diisi.")
                        elif inputs[pk_col] in df_core[pk_col].astype(str).tolist():
                            st.error("Data dengan ID tersebut sudah ada!")
                        else:
                            new_row = pd.DataFrame([[inputs[c] for c in df_core.columns]], columns=df_core.columns)
                            df_core = pd.concat([df_core, new_row], ignore_index=True)
                            if save_data(df_core, pilih_tabel_core):
                                st.success("Data Baru Berhasil Ditambahkan!")
                                st.rerun()
                            
            elif action_mode == "✏️ Edit Baris Data" and pk_col:
                if not df_core.empty:
                    id_pilih_edit = st.selectbox("Pilih ID Data Utama yang Akan Diubah", df_core[pk_col].tolist(), key="sb_edit")
                    baris_edit = df_core[df_core[pk_col] == id_pilih_edit].iloc[0]
                    
                    with st.form("form_core_edit"):
                        edit_inputs = {}
                        for col in df_core.columns:
                            if col == pk_col:
                                st.info(f"Mengunci ID Utama: {id_pilih_edit}")
                                edit_inputs[col] = id_pilih_edit
                            else:
                                edit_inputs[col] = st.text_input(f"Ubah Nilai {col}", value=str(baris_edit[col]), key=f"ed_{pilih_tabel_core}_{col}")
                                
                        if st.form_submit_button("Simpan Perubahan Data Terpilih"):
                            for col in df_core.columns:
                                df_core.loc[df_core[pk_col] == id_pilih_edit, col] = edit_inputs[col]
                            if save_data(df_core, pilih_tabel_core):
                                st.success("Perubahan Data Berhasil Disimpan!")
                                st.rerun()
                else:
                    st.info("Tabel kosong, tidak ada data untuk diubah.")
                    
            elif action_mode == "❌ Delete (Hapus Data)" and pk_col:
                if not df_core.empty:
                    id_pilih_hapus = st.selectbox("Pilih ID Data yang Akan Dihapus Permanen", df_core[pk_col].tolist(), key="sb_del")
                    if st.button("Konfirmasi Hapus Data Secara Permanen", type="primary", key="btn_confirm_del"):
                        df_core = df_core[df_core[pk_col] != id_pilih_hapus]
                        if save_data(df_core, pilih_tabel_core):
                            st.success(f"Data dengan ID '{id_pilih_hapus}' Telah Dihapus Silang!")
                            st.rerun()
                else:
                    st.info("Tabel kosong, tidak ada data untuk dihapus.")

        # --- TAB 2: FITUR SUNTIK KOLOM BARU SECARA GLOBAL ---
        with tab_field:
            st.subheader("➕ Kustomisasi Struktur Kolom Global (Universal Field Injection)")
            st.markdown("Fitur canggih untuk menyuntikkan kolom informasi baru ke dalam skema tabel Excel secara otomatis.")
            if os.path.exists(DB_PATH):
                try:
                    wb = openpyxl.load_workbook(DB_PATH)
                    daftar_sheet_global = wb.sheetnames
                    wb.close()
                    
                    pilih_sheet_universal = st.selectbox("Pilih Tabel Target Kustomisasi", daftar_sheet_global, key="sel_sheet_univ")
                    nama_kolom_global = st.text_input("Ketik Nama Kolom Baru (Gunakan huruf kecil atau underscore)", key="input_col_univ").strip()
                    
                    if st.button("Eksekusi Suntik Kolom Baru", type="primary", key="btn_univ_col"):
                        if not nama_kolom_global:
                            st.error("Nama kolom baru tidak boleh kosong!")
                        else:
                            df_univ = load_data(pilih_sheet_universal)
                            if nama_kolom_global in df_univ.columns:
                                st.error(f"Kolom `{nama_kolom_global}` sudah ada di skema.")
                            else:
                                df_univ[nama_kolom_global] = ""
                                if save_data(df_univ, pilih_sheet_universal):
                                    st.success(f"Kolom Baru `{nama_kolom_global}` Sukses Disuntikkan Ke Tabel `{pilih_sheet_universal}`!")
                                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal memuat struktur skema data: {e}")
            else:
                st.error("File database utamanya hilang!")

        # --- TAB 3: SISTEM BULK IMPORT MASSAL (ANTI-LOG & MULTI FORMAT) ---
        with tab_import:
            st.subheader("📥 Bulk Import System Terpusat (Enterprise Version)")
            st.markdown("Unggah ribuan data bisnis sekaligus secara aman melalui file template.")
            pilih_target_bulk = st.selectbox("Pilih Target Tabel Bulk Import", ["mst_items", "mst_branches", "mst_suppliers"], key="sel_bulk")
            
            # Peta Kunci Header Cadangan Sistem
            headers_map = {
                "mst_items": ["item_id", "item_name", "item_type", "category", "uom_id", "min_stock"],
                "mst_branches": ["branch_id", "branch_name", "branch_type", "address"],
                "mst_suppliers": ["supplier_id", "supplier_name", "phone", "payment_terms"]
            }
            
            df_current_meta = load_data(pilih_target_bulk)
            chosen_headers = list(df_current_meta.columns) if not df_current_meta.empty else headers_map.get(pilih_target_bulk, ["id", "name"])
                
            # Pembuatan berkas template pengisian data resmi
            template_buffer = io.BytesIO()
            with pd.ExcelWriter(template_buffer, engine='openpyxl') as tmpl_writer:
                pd.DataFrame(columns=chosen_headers).to_excel(tmpl_writer, index=False, sheet_name="Template")
            
            st.download_button(
                label="📥 Download Template Excel Resmi", 
                data=template_buffer.getvalue(), 
                file_name=f"template_import_{pilih_target_bulk}.xlsx", 
                mime="application/vnd.ms-excel", 
                key="btn_dl_tmpl"
            )
            
            # Mendukung pengunggahan multi-format fleksibel demi memangkas dependensi kompresi zip
            file_unggah = st.file_uploader("Unggah File Hasil Pengisian Template", type=["xlsx", "xls", "csv", "txt"], key="file_bulk_uploader")
            
            if file_unggah is not None:
                try:
                    # ENGINE PARSER INTEGRATIF: Mengamankan pembacaan data teks maupun biner secara berurutan
                    try:
                        df_upload_baru = pd.read_excel(file_unggah)
                    except Exception:
                        try:
                            file_unggah.seek(0)
                            df_upload_baru = pd.read_csv(file_unggah, sep=None, engine='python')
                        except Exception:
                            file_unggah.seek(0)
                            raw_data = file_unggah.read().decode("utf-8", errors="ignore")
                            df_upload_baru = pd.read_csv(io.StringIO(raw_data))
                        
                    st.write("📋 Pratinjau Data Unggahan Masuk:")
                    st.dataframe(df_upload_baru.head(), use_container_width=True, hide_index=True)
                    
                    if st.button("Eksekusi Gabungkan Data Masuk", type="primary", key="btn_commit_bulk"):
                        df_meta = load_data(pilih_target_bulk)
                        
                        if df_meta is None or df_meta.empty:
                            df_meta = pd.DataFrame(columns=chosen_headers)
                            
                        # Standarisasi string kolom dari whitespace tersembunyi
                        df_meta.columns = df_meta.columns.astype(str).str.strip()
                        df_upload_baru.columns = df_upload_baru.columns.astype(str).str.strip()
                        
                        if list(df_upload_baru.columns) == list(df_meta.columns):
                            df_gabung_final = pd.concat([df_meta, df_upload_baru], ignore_index=True).drop_duplicates()
                            if save_data(df_gabung_final, pilih_target_bulk):
                                st.success("🎉 Sukses! Seluruh data massal resmi diintegrasikan ke Excel Pusat!")
                                st.rerun()
                        else:
                            st.error("Struktur Kolom Berbeda! Pastikan baris judul (header) sama dengan template resmi sistem.")
                except Exception as err:
                    st.error(f"Gagal memproses berkas unggahan! Error: {err}")

        # --- TAB 4: PERMISSION MATRIX CHECKLIST AKSES JABATAN ---
        with tab_permission:
            st.subheader("🔒 Matriks Otentikasi Hak Akses Menu Jabatan (Permission Matrix)")
            st.markdown("Konfigurasi modul operasional hulu-ke-hilir untuk setiap level jabatan karyawan secara visual.")
            df_r = load_data("mst_roles_permission")
            
            if not df_r.empty:
                role_col = df_r.columns[0]
                pilih_role_akses = st.selectbox("Pilih Jabatan Pengaturan Otoritas", df_r[role_col].tolist(), key="sel_perm_role")
                
                row_p = df_r[df_r[role_col] == pilih_role_akses].iloc[0].to_dict()
                
                c_dash = st.checkbox("Izinkan Akses Dashboard Utama", value=bool(row_p.get('allow_dashboard', False)), key="chk_p1")
                c_wms = st.checkbox("Izinkan Akses WMS & Gudang Inventory", value=bool(row_p.get('allow_wms_inventory', False)), key="chk_p2")
                c_prod = st.checkbox("Izinkan Akses Pusat Produksi (WIP)", value=bool(row_p.get('allow_production_hub', False)), key="chk_p3")
                c_fin = st.checkbox("Izinkan Akses Keuangan & Konsolidasi", value=bool(row_p.get('allow_finance', False)), key="chk_p4")
                
                if st.button("Simpan Otentikasi Hak Akses Baru", type="primary", key="btn_save_perm"):
                    df_r.loc[df_r[role_col] == pilih_role_akses, 'allow_dashboard'] = c_dash
                    df_r.loc[df_r[role_col] == pilih_role_akses, 'allow_wms_inventory'] = c_wms
                    df_r.loc[df_r[role_col] == pilih_role_akses, 'allow_production_hub'] = c_prod
                    df_r.loc[df_r[role_col] == pilih_role_akses, 'allow_finance'] = c_fin
                    
                    if save_data(df_r, "mst_roles_permission"):
                        st.success(f"Matriks Otoritas Keamanan Jabatan `{pilih_role_akses}` Berhasil Diperbarui Pusat!")
                        st.rerun()
            else:
                st.info("Tabel parameter `mst_roles_permission` tidak terdeteksi di database.")
