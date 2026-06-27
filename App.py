import streamlit as st
import pandas as pd
import os

# 1. KONFIGURASI UTAMA
st.set_page_config(page_title="ERPOS System", page_icon="🏬", layout="wide")
DB_PATH = "data/erpos_database.xlsx"

# --- PANEL DIAGNOSIS BROWSER (KIRI) ---
st.sidebar.subheader("🔍 Pengecekan Berkas Database")
if not os.path.exists(DB_PATH):
    st.sidebar.error(f"❌ File TIDAK ADA di jalur: `{DB_PATH}`")
else:
    st.sidebar.success("✅ File `erpos_database.xlsx` Ditemukan!")
    try:
        import openpyxl
        wb = openpyxl.load_workbook(DB_PATH, read_only=True)
        sheets = wb.sheetnames
        st.sidebar.write("📂 **Daftar Sheet Terdeteksi:**")
        st.sidebar.json(sheets)
        
        if "mst_users" in sheets:
            df_test = pd.read_excel(DB_PATH, sheet_name="mst_users")
            st.sidebar.info(f"📊 Sheet `mst_users` berisi {len(df_test)} baris data.")
        else:
            st.sidebar.error("❌ Sheet `mst_users` TIDAK DITEMUKAN!")
    except Exception as e:
        st.sidebar.error(f"❌ Gagal baca Excel: {str(e)}")

# --- FUNGSI LOAD DATA AMAN ---
def load_data(sheet_name):
    if os.path.exists(DB_PATH):
        try:
            return pd.read_excel(DB_PATH, sheet_name=sheet_name)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# 2. INISIALISASI SESSION STATE
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# --- FASE 1: HALAMAN LOGIN ---
if not st.session_state['logged_in']:
    st.title("🔐 ERPOS System - Enterprise Core")
    username_input = st.text_input("Username", key="login_username")
    password_input = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Masuk Ke Sistem", type="primary"):
        df_users = load_data("mst_users")
        df_branches = load_data("mst_branches")
        
        if not df_users.empty:
            user_match = df_users[(df_users['username'].astype(str).str.strip() == username_input.strip()) & 
                                  (df_users['password'].astype(str).str.strip() == str(password_input).strip())]
            
            if not user_match.empty:
                user_data = user_match.iloc[0].to_dict()
                
                # Deteksi Kolom Cabang Dinamis
                branch_id_col = 'branch_id (ID Cabang)' if 'branch_id (ID Cabang)' in df_branches.columns else df_branches.columns[0] if not df_branches.empty else ''
                branch_name_col = 'branch_name (Nama Lokasi)' if 'branch_name (Nama Lokasi)' in df_branches.columns else df_branches.columns[1] if len(df_branches.columns) > 1 else ''
                
                branch_match = df_branches[df_branches[branch_id_col].astype(str).str.strip() == str(user_data['assigned_branch']).strip()] if branch_id_col else pd.DataFrame()
                branch_info = branch_match.iloc[0].to_dict() if not branch_match.empty else {}
                
                st.session_state['user_info'] = {
                    'name': user_data['employee_name'],
                    'role': user_data['role_id'],
                    'branch_name': branch_info.get(branch_name_col, 'Kantor Pusat / Unknown')
                }
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Username atau Password salah!")
        else:
            st.error("Database pengguna tidak terbaca atau kosong!")

# --- FASE 2: HALAMAN UTAMA DASHBOARD ---
else:
    info = st.session_state['user_info']
    
    st.title("📊 Dashboard Utama ERPOS")
    st.success(f"Selamat Datang, **{info['name']}**!")
    
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"👤 **Hak Akses:** {info['role']}")
    with col2:
        st.info(f"🏬 **Lokasi Penugasan:** {info['branch_name']}")
        
    st.markdown("### 🏬 Selamat! Sistem ERPOS Anda berhasil terkoneksi ke database.")
    
    if st.sidebar.button("🚪 Keluar dari Sistem", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
        st.rerun()
