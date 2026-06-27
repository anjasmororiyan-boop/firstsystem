import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import os
import datetime
import io

# 1. KONFIGURASI UTAMA
st.set_page_config(page_title="ERPOS System - Enterprise", page_icon="🏬", layout="wide")

DB_PATH = "data/erpos_database.xlsx"

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
        df_users = load_data("mst_users")
        df_roles = load_data("mst_roles_permission")
        df_branches = load_data("mst_branches")
        
        if not df_users.empty:
            user_match = df_users[(df_users['username'] == username_input) & (df_users['password'] == str(password_input))]
            
            if not user_match.empty:
                user_data = user_match.iloc[0].to_dict()
                
                branch_id_col = 'branch_id (ID Cabang)' if 'branch_id (ID Cabang)' in df_branches.columns else df_branches.columns[0]
                branch_name_col = 'branch_name (Nama Lokasi)' if 'branch_name (Nama Lokasi)' in df_branches.columns else df_branches.columns[1]
                branch_type_col = 'branch_type (Tipe)' if 'branch_type (Tipe)' in df_branches.columns else df_branches.columns[2]
                role_id_col = 'role_id (Jabatan)' if 'role_id (Jabatan)' in df_roles.columns else df_roles.columns[0]
                
                branch_info = df_branches[df_branches[branch_id_col] == user_data['assigned_branch']].iloc[0].to_dict() if not df_branches[df_branches[branch_id_col] == user_data['assigned_branch']].empty else {}
                role_info = df_roles[df_roles[role_id_col] == user_data['role_id']].iloc[0].to_dict() if not df_roles[df_roles[role_id_col] == user_data['role_id']].empty else {}
                
                st.session_state['user_info'] = {
                    'name': user_data['employee_name'],
                    'role': user_data['role_id'],
                    'branch_id': user_data['assigned_branch'],
                    'branch_name': branch_info.get(branch_name_col, 'Unknown'),
                    'branch_type': branch_info.get(branch_type_col, 'Unknown'),
                    'permissions': role_info
                }
                st.session_state['logged_in'] = True
                st.session_state['active_menu'] = "Dashboard Utama"
                st.rerun()
            else:
                st.error("Username atau Password salah!")
        else:
            st.error("Database pengguna kosong!")

# --- FASE 2: APLIKASI UTAMA ---
else:
    info = st.session_state['user_info']
    perms = info['permissions']
    
    menu_options = ["Dashboard Utama"]
    menu_icons = ["speedometer2"]
    
    if perms.get('allow_wms_inventory') in [True, 'TRUE', 1]:
        menu_options.append("WMS & Gudang")
        menu_icons.append("box-seam")
    if perms.get('allow_production_hub') in [True, 'TRUE', 1]:
        menu_options.append("Pusat Produksi (WIP)")
        menu_icons.append("tools")
    if perms.get('allow_finance') in [True, 'TRUE', 1]:
        menu_options.append("Keuangan & Konsolidasi")
        menu_icons.append("wallet2")
    if info['role'] in ["CASHIER", "OWNER"]:
        menu_options.append("Mesin Kasir (POS)")
        menu_icons.append("calculator")
    if info['role'] == "OWNER":
        menu_options.append("⚙️ Master Data")
        menu_icons.append("database-gear")

    with st.sidebar:
        st.subheader("🏬 ERPOS Control Panel")
        st.caption(f"User: **{info['name']}** ({info['role']})")
        
        # PERBAIKAN RESPONSIVITAS: Ikat navigasi langsung tanpa key statis bermasalah
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

    # --- ROUTER HALAMAN ---
    if st.session_state['active_menu'] == "Dashboard Utama":
        st.title("📊 Ringkasan Eksekutif Bisnis")
        st.write(f"Sistem Kendali aktif pada cabang: **{info['branch_name']}**")
        
    elif st.session_state['active_menu'] == "WMS & Gudang":
        st.title("📦 Warehouse Management System (WMS)")
        df_items = load_data("mst_items")
        st.dataframe(df_items, use_container_width=True, hide_index=True)
        
    elif st.session_state['active_menu'] == "⚙️ Master Data":
        st.title("⚙️ Pusat Pengaturan Master Data Terpusat")
        
        tab_core, tab_field, tab_import, tab_permission = st.tabs([
            "📁 Master Data Core (CRUD)", "➕ Kustomisasi Field Modul", "📥 Bulk Import Data", "🔒 Permission Matrix"
        ])
        
        with tab_core:
            pilih_tabel_core = st.selectbox("Pilih Tabel Core untuk Dikelola", ["mst_branches (Daftar Cabang)", "mst_units (Satuan Ukur)", "mst_suppliers (Daftar Vendor)", "mst_items (Katalog Barang)"], key="sel_core")
            tabel_target = pilih_tabel_core.split(" ")[0]
            df_core = load_data(tabel_target)
            
            st.subheader(f"Data Live Tabel `{tabel_target}`")
            col_exp1, col_exp2 = st.columns([4, 1])
            with col_exp1:
                st.dataframe(df_core, use_container_width=True, hide_index=True)
            with col_exp2:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as excel_writer:
                    df_core.to_excel(excel_writer, index=False, sheet_name=tabel_target)
                st.download_button(label="📥 Export ke Excel", data=buffer.getvalue(), file_name=f"export_{tabel_target}.xlsx", mime="application/vnd.ms-excel", use_container_width=True, key=f"dl_{tabel_target}")
            
            st.markdown("---")
            action_mode = st.radio("Pilih Tindakan Operasional", ["➕ Submit (Tambah Data)", "✏️ Edit Baris Data", "❌ Delete (Hapus Data)"], horizontal=True, key="action_core")
            pk_col = df_core.columns[0]
            
            if action_mode == "➕ Submit (Tambah Data)":
                with st.form("form_core_submit"):
                    inputs = {}
                    for col in df_core.columns:
                        inputs[col] = st.text_input(f"Isi {col}", key=f"add_{tabel_target}_{col}")
                    if st.form_submit_button("Submit Data"):
                        if inputs[pk_col].strip() == "":
                            st.error(f"Kolom utama `{pk_col}` wajib diisi.")
                        elif inputs[pk_col] in df_core[pk_col].astype(str).tolist():
                            st.error("Data dengan ID tersebut sudah terdaftar!")
                        else:
                            new_row = pd.DataFrame([[inputs[c] for c in df_core.columns]], columns=df_core.columns)
                            df_core = pd.concat([df_core, new_row], ignore_index=True)
                            save_data(df_core, tabel_target)
                            st.success("Data berhasil disubmit!")
                            st.rerun()
                            
            elif action_mode == "✏️ Edit Baris Data":
                if not df_core.empty:
                    id_pilih_edit = st.selectbox("Pilih ID Data yang Akan Diubah", df_core[pk_col].tolist(), key="sb_edit")
                    baris_edit = df_core[df_core[pk_col] == id_pilih_edit].iloc[0]
                    
                    with st.form("form_core_edit"):
                        edit_inputs = {}
                        for col in df_core.columns:
                            if col == pk_col:
                                st.text(f"Mengubah Kunci Data: {id_pilih_edit}")
                                edit_inputs[col] = id_pilih_edit
                            else:
                                edit_inputs[col] = st.text_input(f"Ubah {col}", value=str(baris_edit[col]), key=f"ed_{tabel_target}_{col}")
                                
                        if st.form_submit_button("Simpan Perubahan Data"):
                            for col in df_core.columns:
                                df_core.loc[df_core[pk_col] == id_pilih_edit, col] = edit_inputs[col]
                            save_data(df_core, tabel_target)
                            st.success("Perubahan data tersimpan!")
                            st.rerun()
                else:
                    st.info("Tidak ada data untuk diedit.")
                    
            elif action_mode == "❌ Delete (Hapus Data)":
                if not df_core.empty:
                    id_pilih_hapus = st.selectbox("Pilih ID Data yang Akan Dihapus", df_core[pk_col].tolist(), key="sb_del")
                    if st.button("Konfirmasi Hapus Data Secara Permanen", type="primary", key="btn_confirm_del"):
                        df_core = df_core[df_core[pk_col] != id_pilih_hapus]
                        save_data(df_core, tabel_target)
                        st.success(f"Data dengan ID '{id_pilih_hapus}' telah dihapus!")
                        st.rerun()
                else:
                    st.info("Tidak ada data untuk dihapus.")

        with tab_field:
            st.subheader("➕ Suntik Kolom Global (Universal Field Injection)")
            import openpyxl
            wb = openpyxl.load_workbook(DB_PATH)
            daftar_sheet_global = wb.sheetnames
            wb.close()
            
            pilih_sheet_universal = st.selectbox("Pilih Target Sheet Utama / Turunan", daftar_sheet_global, key="sel_sheet_univ")
            nama_kolom_global = st.text_input("Nama Kolom Baru", key="input_col_univ").strip()
            
            if st.button("Eksekusi Suntik Kolom Global", type="primary", key="btn_univ_col"):
                if not nama_kolom_global:
                    st.error("Nama kolom tidak boleh kosong!")
                else:
                    df_univ = load_data(pilih_sheet_universal)
                    if nama_kolom_global in df_univ.columns:
                        st.error("Kolom tersebut sudah ada di sheet.")
                    else:
                        df_univ[nama_kolom_global] = ""
                        save_data(df_univ, pilih_sheet_universal)
                        st.success(f"Kolom `{nama_kolom_global}` resmi disuntikkan!")
                        st.rerun()

        with tab_import:
            st.subheader("📥 Bulk Import System Terproteksi")
            pilih_target_bulk = st.selectbox("Pilih Modul Tujuan Upload Massal", ["mst_items", "mst_branches", "mst_suppliers", "mst_users"], key="sel_bulk")
            df_meta = load_data(pilih_target_bulk)
            
            template_buffer = io.BytesIO()
            with pd.ExcelWriter(template_buffer, engine='openpyxl') as tmpl_writer:
                pd.DataFrame(columns=df_meta.columns).to_excel(tmpl_writer, index=False, sheet_name="Template")
            st.download_button(label="📥 Download Template Excel Resmi", data=template_buffer.getvalue(), file_name=f"template_import_{pilih_target_bulk}.xlsx", mime="application/vnd.ms-excel", key="btn_dl_tmpl")
            
            file_unggah = st.file_uploader("Pilih File Excel Hasil Pengisian", type=["xlsx"], key="file_bulk_uploader")
            
            if file_unggah is not None:
                try:
                    df_upload_baru = pd.read_excel(file_unggah)
                    st.write("Pratinjau Data Unggahan Anda:")
                    st.dataframe(df_upload_baru.head(), use_container_width=True, hide_index=True)
                    
                    if st.button("Eksekusi Gabungkan Data Ke Sistem", type="primary", key="btn_commit_bulk"):
                        if list(df_upload_baru.columns) == list(df_meta.columns):
                            df_gabung_final = pd.concat([df_meta, df_upload_baru], ignore_index=True).drop_duplicates()
                            save_data(df_gabung_final, pilih_target_bulk)
                            st.success("Bulk Import Berhasil!")
                            st.rerun()
                        else:
                            st.error("Susunan kolom file yang diupload berbeda dengan template resmi!")
                except Exception as err:
                    st.error(f"Gagal memproses berkas! Error: {err}")

        with tab_permission:
            st.subheader("🔒 Checklist Atur Hak Akses Menu Jabatan")
            df_r = load_data("mst_roles_permission")
            role_col = df_r.columns[0]
            pilih_role_akses = st.selectbox("Pilih Jabatan Pengaturan", df_r[role_col].tolist(), key="sel_perm_role")
            row_p = df_r[df_r[role_col] == pilih_role_akses].iloc[0]
            
            c_dash = st.checkbox("Akses Dashboard Utama", value=bool(row_p.get('allow_dashboard', False)), key="chk_p1")
            c_wms = st.checkbox("Akses WMS & Gudang Inventory", value=bool(row_p.get('allow_wms_inventory', False)), key="chk_p2")
            c_prod = st.checkbox("Akses Pusat Produksi (WIP)", value=bool(row_p.get('allow_production_hub', False)), key="chk_p3")
            c_fin = st.checkbox("Akses Keuangan & Konsolidasi", value=bool(row_p.get('allow_finance', False)), key="chk_p4")
            
            if st.button("Simpan Otentikasi Hak Akses", type="primary", key="btn_save_perm"):
                df_r.loc[df_r[role_col] == pilih_role_akses, 'allow_dashboard'] = c_dash
                df_r.loc[df_r[role_col] == pilih_role_akses, 'allow_wms_inventory'] = c_wms
                df_r.loc[df_r[role_col] == pilih_role_akses, 'allow_production_hub'] = c_prod
                df_r.loc[df_r[role_col] == pilih_role_akses, 'allow_finance'] = c_fin
                save_data(df_r, "mst_roles_permission")
                st.success("Otentikasi matrix diperbarui!")
                st.rerun()
