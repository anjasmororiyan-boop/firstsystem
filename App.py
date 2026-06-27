import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import os

# 1. KONFIGURASI UTAMA
st.set_page_config(page_title="ERPOS System", page_icon="🚀", layout="wide")

DB_PATH = "data/erpos_database.xlsx"

# Fungsi pembantu membaca Excel
def load_data(sheet_name):
    if os.path.exists(DB_PATH):
        return pd.read_excel(DB_PATH, sheet_name=sheet_name)
    return None

# Fungsi pembantu menyimpan Excel secara aman (tidak merusak sheet lain)
def save_data(df, sheet_name):
    with pd.ExcelWriter(DB_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

# Inisialisasi Memori Aplikasi
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# --- FASE 1: HALAMAN LOGIN ---
if not st.session_state['logged_in']:
    st.title("🔐 ERPOS System - Dynamic Core Engine")
    
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    
    if st.button("Masuk Ke Sistem", type="primary"):
        df_users = load_data("mst_users")
        df_roles = load_data("mst_roles_permission")
        df_branches = load_data("mst_branches")
        
        if df_users is not None:
            user_match = df_users[(df_users['username'] == username_input) & (df_users['password'] == str(password_input))]
            
            if not user_match.empty:
                user_data = user_match.iloc[0].to_dict()
                
                # Cari branch dinamis berdasarkan kolom
                b_id_col = [c for c in df_branches.columns if 'branch_id' in c][0]
                branch_match = df_branches[df_branches[b_id_col] == user_data['assigned_branch']]
                branch_info = branch_match.iloc[0].to_dict() if not branch_match.empty else {"branch_name": "Unknown", "branch_type": "Unknown"}
                
                # Cari role dinamis berdasarkan kolom
                r_id_col = [c for c in df_roles.columns if 'role_id' in c][0]
                role_match = df_roles[df_roles[r_id_col] == user_data['role_id']]
                role_info = role_match.iloc[0].to_dict() if not role_match.empty else {}
                
                st.session_state['user_info'] = {
                    'name': user_data['employee_name'],
                    'role': user_data['role_id'],
                    'branch_id': user_data['assigned_branch'],
                    'branch_name': branch_info.get('branch_name (Nama Lokasi)', branch_info.get('branch_name', 'Unknown')),
                    'branch_type': branch_info.get('branch_type (Tipe)', branch_info.get('branch_type', 'Unknown')),
                    'permissions': role_info
                }
                st.session_state['logged_in'] = True
                st.success("Login Berhasil!")
                st.rerun()
            else:
                st.error("Username atau Password salah!")

# --- FASE 2: DASHBOARD (SETELAH LOGIN) ---
else:
    info = st.session_state['user_info']
    perms = info['permissions']
    
    # Navigasi Menu Dinamis pembaca baris kolom Excel
    menu_options = []
    menu_icons = []
    
    if perms.get('allow_dashboard') == True:
        menu_options.append("Dashboard Utama")
        menu_icons.append("speedometer2")
    if perms.get('allow_wms_inventory') == True:
        menu_options.append("WMS & Gudang")
        menu_icons.append("box-seam")
    if perms.get('allow_production_hub') == True:
        menu_options.append("Pusat Produksi (WIP)")
        menu_icons.append("tools")
    if perms.get('allow_finance') == True:
        menu_options.append("Keuangan & Konsolidasi")
        menu_icons.append("wallet2")
    if info['role'] in ["CASHIER", "OWNER"]:
        menu_options.append("Mesin Kasir (POS)")
        menu_icons.append("calculator")
        
    # MENU KHUSUS SUPER USER
    if info['role'] == "OWNER":
        menu_options.append("⚙️ Pengaturan Sistem")
        menu_icons.append("gear")

    # Layout Sidebar
    with st.sidebar:
        st.subheader("🏬 ERPOS Control Panel")
        menu_terpilih = option_menu(
            menu_title="Navigasi Modul",
            options=menu_options,
            icons=menu_icons,
            menu_icon="layers-half",
            default_index=0,
        )
        if st.button("🚪 Keluar Sistem", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.rerun()

    # ROUTER HALAMAN
    if menu_terpilih == "Dashboard Utama":
        st.title("📊 Ringkasan Eksekutif Bisnis")
        st.write(f"Selamat datang kembali, **{info['name']}** di **{info['branch_name']}**")
        
    elif menu_terpilih == "⚙️ Pengaturan Sistem":
        st.title("⚙️ Pusat Kendali Pengaturan Sistem (Super User)")
        st.write("Semua konfigurasi di bawah ini akan langsung memperbarui database Excel secara real-time.")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏬 Manajemen Cabang", 
            "👥 Manajemen Pengguna", 
            "🔒 Atur Hak Akses Menu",
            "📏 Satuan Logistik (UoM)",
            "🤝 Pemasok (Supplier)"
        ])
        
        # TAB 1: MANAJEMEN CABANG
        with tab1:
            st.subheader("Tambah Cabang / Gudang WMS Baru")
            df_b = load_data("mst_branches")
            st.dataframe(df_b, use_container_width=True)
            
            with st.form("form_cabang"):
                new_id = st.text_input("ID Cabang Baru (Contoh: BR-OUT02)")
                new_name = st.text_input("Nama Lokasi / Cabang")
                new_type = st.selectbox("Tipe Lokasi", ["Head Office", "Production Hub", "Outlet"])
                new_addr = st.text_input("Alamat Fisik")
                
                if st.form_submit_button("Simpan Cabang Baru"):
                    if new_id and new_name:
                        new_row = pd.DataFrame([[new_id, new_name, new_type, new_addr]], columns=df_b.columns)
                        df_b = pd.concat([df_b, new_row], ignore_index=True)
                        save_data(df_b, "mst_branches")
                        st.success(f"Cabang {new_name} berhasil didaftarkan!")
                        st.rerun()
                        
        # TAB 2: MANAJEMEN PENGGUNA
        with tab2:
            st.subheader("Manajemen Akun Login Karyawan")
            df_u = load_data("mst_users")
            st.dataframe(df_u, use_container_width=True)
            
            df_branches = load_data("mst_branches")
            df_roles = load_data("mst_roles_permission")
            
            with st.form("form_user"):
                u_id = st.text_input("User ID (Contoh: USR-004)")
                u_name = st.text_input("Username untuk Login")
                u_pass = st.text_input("Password Default")
                u_role = st.selectbox("Pilih Jabatan / Role", df_roles.iloc[:, 0].tolist())
                u_branch = st.selectbox("Penempatan Cabang Kerja", df_branches.iloc[:, 0].tolist())
                u_emp = st.text_input("Nama Lengkap Karyawan")
                
                if st.form_submit_button("Daftarkan Karyawan"):
                    new_user = pd.DataFrame([[u_id, u_name, u_pass, u_role, u_branch, u_emp]], columns=df_u.columns)
                    df_u = pd.concat([df_u, new_user], ignore_index=True)
                    save_data(df_u, "mst_users")
                    st.success(f"Akun {u_emp} berhasil diaktifkan!")
                    st.rerun()

        # TAB 3: HAK AKSES MENU
        with tab3:
            st.subheader("Modifikasi Hak Akses Menu Jabatan")
            df_r = load_data("mst_roles_permission")
            edited_df = st.data_editor(df_r, use_container_width=True)
            if st.button("Simpan Perubahan Hak Akses"):
                save_data(edited_df, "mst_roles_permission")
                st.success("Hak akses seluruh jabatan diperbarui!")
                st.rerun()

        # TAB 4: SATUAN LOGISTIK (UoM)
        with tab4:
            st.subheader("Master Data Satuan Ukuran / UoM")
            df_units = load_data("mst_units")
            st.dataframe(df_units, use_container_width=True)
            
            with st.form("form_unit"):
                unit_id = st.text_input("ID Satuan (Contoh: UOM-BOX)")
                unit_name = st.text_input("Nama Satuan (Contoh: Box/Dus)")
                base_unit = st.text_input("Satuan Dasar Acuan (Contoh: pcs / kg)")
                conv_factor = st.number_input("Faktor Konversi Ke Satuan Dasar", min_value=0.0001, value=1.0000, format="%.4f")
                ket = st.text_input("Keterangan Tambahan")
                
                if st.form_submit_button("Tambah Satuan Baru"):
                    if unit_id and unit_name:
                        new_unit = pd.DataFrame([[unit_id, unit_name, base_unit, conv_factor, ket]], columns=df_units.columns)
                        df_units = pd.concat([df_units, new_unit], ignore_index=True)
                        save_data(df_units, "mst_units")
                        st.success(f"Satuan {unit_name} berhasil ditambahkan!")
                        st.rerun()

        # TAB 5: PEMASOK (SUPPLIER)
        with tab5:
            st.subheader("Master Data Supplier & Vendor")
            df_suppliers = load_data("mst_suppliers")
            st.dataframe(df_suppliers, use_container_width=True)
            
            with st.form("form_supplier"):
                sup_id = st.text_input("ID Supplier (Contoh: SPL-003)")
                sup_name = st.text_input("Nama Perusahaan / Vendor")
                sup_phone = st.text_input("Nomor Telepon / WhatsApp")
                sup_terms = st.selectbox("Termin Pembayaran (Payment Terms)", ["COD / Cash", "TOP 7 Hari", "TOP 14 Hari", "TOP 30 Hari"])
                
                if st.form_submit_button("Tambah Supplier Baru"):
                    if sup_id and sup_name:
                        new_sup = pd.DataFrame([[sup_id, sup_name, sup_phone, sup_terms]], columns=df_suppliers.columns)
                        df_suppliers = pd.concat([df_suppliers, new_sup], ignore_index=True)
                        save_data(df_suppliers, "mst_suppliers")
                        st.success(f"Supplier {sup_name} berhasil diregistrasi!")
                        st.rerun()

    else:
        st.subheader(f"Modul {menu_terpilih}")
        st.write("Konten modul sedang dalam proses blueprint.")

    elif menu_terpilih == "WMS & Gudang":
        st.title("📦 Warehouse Management System (WMS)")
        st.write(f"Lokasi Kontrol Aktif: **{info['branch_name']}** (Tipe: {info['branch_type']})")
        st.markdown("---")
        
        # Ambal Data dari Excel
        df_items = load_data("mst_items")
        df_mutations = load_data("trn_stock_mutations")
        df_branches = load_data("mst_branches")
        
        # JIKA SHEET BARU BELUM ADA DI EXCEL, BUAT BIAR TIDAK CRASH
        if df_items is None or df_items.empty:
            df_items = pd.DataFrame(columns=["item_id", "item_name", "item_type", "category", "uom_id", "min_stock"])
        if df_mutations is None or df_mutations.empty:
            df_mutations = pd.DataFrame(columns=["mutation_id", "timestamp", "branch_id", "item_id", "qty_change", "type", "reference"])

        # TAMBAHKAN TAB MUTASI ANTAR CABANG
        tab_stok, tab_tambah_barang, tab_stok_masuk, tab_mutasi = st.tabs([
            "📊 Stok Gudang Real-Time", 
            "➕ Tambah Master Barang", 
            "📥 Penerimaan Stok Baru",
            "🔄 Mutasi Antar Cabang"
        ])
        
        # ----------------------------------------------------
        # TAB 1: HITUNG DAN TAMPILKAN STOK SECARA REAL-TIME
        # ----------------------------------------------------
        with tab_stok:
            st.subheader(f"Daftar Persediaan Barang di {info['branch_name']}")
            if not df_items.empty:
                stok_list = []
                for index, row in df_items.iterrows():
                    mutasi_cabang = df_mutations[(df_mutations['branch_id'] == info['branch_id']) & (df_mutations['item_id'] == row['item_id'])]
                    total_stok = mutasi_cabang['qty_change'].sum() if not mutasi_cabang.empty else 0
                    
                    stok_list.append({
                        "ID Barang": row['item_id'],
                        "Nama Barang": row['item_name'],
                        "Tipe": row['item_type'],
                        "Kategori": row['category'],
                        "Stok Fisik": total_stok,
                        "Satuan": row['uom_id'],
                        "Min. Stok": row['min_stock'],
                        "Status": "⚠️ RESTOCK" if total_stok <= row['min_stock'] else "✅ AMAN"
                    })
                df_tampilan_stok = pd.DataFrame(stok_list)
                st.dataframe(df_tampilan_stok, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada barang yang didaftarkan di master data.")

        # ----------------------------------------------------
        # TAB 2: TAMBAH MASTER BARANG
        # ----------------------------------------------------
        with tab_tambah_barang:
            st.subheader("Daftarkan Katalog Barang Baru")
            df_units = load_data("mst_units")
            with st.form("form_master_barang"):
                i_id = st.text_input("ID Barang (Contoh: ITM-001)")
                i_name = st.text_input("Nama Lengkap Barang")
                i_type = st.selectbox("Tipe Barang", ["Bahan Baku", "Barang Setengah Jadi (WIP)", "Barang Jadi"])
                i_cat = st.text_input("Kategori (Contoh: Tepung / Roti / Kemasan)")
                i_uom = st.selectbox("Satuan Ukur (UoM)", df_units['unit_id'].tolist() if df_units is not None else ["UOM-KG"])
                i_min = st.number_input("Batas Minimum Stok (Alarm)", min_value=0, value=10)
                
                if st.form_submit_button("Simpan Katalog Barang"):
                    if i_id and i_name:
                        new_item = pd.DataFrame([[i_id, i_name, i_type, i_cat, i_uom, i_min]], columns=df_items.columns)
                        df_items = pd.concat([df_items, new_item], ignore_index=True)
                        save_data(df_items, "mst_items")
                        st.success(f"Barang '{i_name}' berhasil didaftarkan ke sistem!")
                        st.rerun()

        # ----------------------------------------------------
        # TAB 3: INPUT PENERIMAAN BARANG MASUK (SUPPLIER)
        # ----------------------------------------------------
        with tab_stok_masuk:
            st.subheader("Pencatatan Barang Masuk / Pembelian")
            df_sups = load_data("mst_suppliers")
            if not df_items.empty:
                with st.form("form_stok_masuk"):
                    import datetime
                    next_mut_id = f"MUT-{len(df_mutations) + 1:03d}"
                    pilih_barang = st.selectbox("Pilih Barang yang Masuk", df_items['item_id'].tolist(), 
                                                format_func=lambda x: f"{x} - {df_items[df_items['item_id']==x]['item_name'].values[0]}")
                    qty_masuk = st.number_input("Jumlah Barang Masuk", min_value=0.01, step=1.0)
                    pilih_supplier = st.selectbox("Asal Supplier", df_sups['supplier_name'].tolist() if df_sups is not None else ["Umum"])
                    no_ref = st.text_input("Nomor Nota / PO / Referensi Pembelian", value=f"PO-{datetime.datetime.now().strftime('%Y%m%d')}")
                    
                    if st.form_submit_button("Konfirmasi Masuk Gudang"):
                        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        new_mut = pd.DataFrame([[next_mut_id, now_str, info['branch_id'], pilih_barang, qty_masuk, "Masuk Supplier", f"{no_ref} ({pilih_supplier})"]], columns=df_mutations.columns)
                        df_mutations = pd.concat([df_mutations, new_mut], ignore_index=True)
                        save_data(df_mutations, "trn_stock_mutations")
                        st.success(f"Stok berhasil dimasukkan ke gudang {info['branch_name']}!")
                        st.rerun()
            else:
                st.warning("Silakan isi katalog barang di Tab 2 terlebih daraulu.")

        # ----------------------------------------------------
        # TAB 4: MUTASI ANTAR CABANG (DINAMIS & REAL-TIME)
        # ----------------------------------------------------
        with tab_mutasi:
            st.subheader("Kirim / Transfer Stok ke Cabang Lain")
            
            # Ambil daftar cabang tujuan (kecuali cabang yang sedang login saat ini)
            daftar_cabang_tujuan = df_branches[df_branches.iloc[:, 0] != info['branch_id']]
            
            if not df_items.empty and not daftar_cabang_tujuan.empty:
                with st.form("form_mutasi_cabang"):
                    import datetime
                    
                    # 1. Pilih barang & hitung dulu stok sisa di cabang asal agar tidak minus
                    pilih_item_mutasi = st.selectbox("Pilih Barang yang Akan Dikirim", df_items['item_id'].tolist(), key="mut_item",
                                                    format_func=lambda x: f"{x} - {df_items[df_items['item_id']==x]['item_name'].values[0]}")
                    
                    stok_asal_saat_ini = df_mutations[(df_mutations['branch_id'] == info['branch_id']) & (df_mutations['item_id'] == pilih_item_mutasi)]['qty_change'].sum()
                    st.warning(f"Sisa Stok Anda saat ini: {stok_asal_saat_ini}")
                    
                    # 2. Input Tujuan & Jumlah
                    pilih_cabang_tujuan = st.selectbox("Pilih Cabang / Outlet Tujuan", daftar_cabang_tujuan.iloc[:, 0].tolist(),
                                                       format_func=lambda x: f"{x} - {df_branches[df_branches.iloc[:, 0]==x].iloc[:, 1].values[0]}")
                    
                    qty_mutasi = st.number_input("Jumlah yang Dikirim", min_value=0.01, max_value=float(max(0.01, stok_asal_saat_ini)), step=1.0)
                    no_trf_ref = st.text_input("Nomor Surat Jalan / Referensi Transfer", value=f"TRF-{datetime.datetime.now().strftime('%Y%m%d%H%M')}")
                    
                    if st.form_submit_button("Kirim Barang"):
                        if stok_asal_saat_ini >= qty_mutasi:
                            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            
                            # ID Mutasi urut otomatis
                            id_mut_1 = f"MUT-{len(df_mutations) + 1:03d}"
                            id_mut_2 = f"MUT-{len(df_mutations) + 2:03d}"
                            
                            # BARIS A: Sisi Cabang Pengirim (Stok berkurang -> NEGATIF)
                            mut_keluar = pd.DataFrame([[id_mut_1, now_str, info['branch_id'], pilih_item_mutasi, -qty_mutasi, "Mutasi Keluar", f"{no_trf_ref} (Ke {pilih_cabang_tujuan})"]], columns=df_mutations.columns)
                            
                            # BARIS B: Sisi Cabang Penerima (Stok bertambah -> POSITIF)
                            mut_masuk = pd.DataFrame([[id_mut_2, now_str, pilih_cabang_tujuan, pilih_item_mutasi, qty_mutasi, "Mutasi Masuk", f"{no_trf_ref} (Dari {info['branch_id']})"]], columns=df_mutations.columns)
                            
                            # Gabungkan kedua data ke log mutasi database utama
                            df_mutations = pd.concat([df_mutations, mut_keluar, mut_masuk], ignore_index=True)
                            save_data(df_mutations, "trn_stock_mutations")
                            
                            st.success(f"Mutasi Berhasil! {qty_mutasi} unit telah dipindahkan dari {info['branch_name']} ke {pilih_cabang_tujuan}.")
                            st.rerun()
                        else:
                            st.error("Gagal! Stok di gudang Anda tidak mencukupi untuk melakukan transfer.")
            else:
                st.info("Pastikan master data barang dan data cabang sudah terisi.")
