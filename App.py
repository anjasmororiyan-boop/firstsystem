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
        # Jalur Darurat Tetap Aktif sebagai Pengaman Backdoor
        if username_input.strip() == "riyan_owner" and password_input.strip() == "admin123":
            st.session_state['user_info'] = {
                'name': "Riyan Anjasmoro",
                'role': "OWNER",
                'branch_id': "SR-SOF0001-JS-01",
                'branch_name': "Supporting Office",
                'permissions': {'allow_dashboard': True, 'allow_wms_inventory': True, 'allow_production_hub': True, 'allow_finance': True}
            }
            st.session_state['logged_in'] = True
            st.session_state['active_menu'] = "Dashboard Utama"
            st.rerun()
        else:
            df_users = load_data("mst_users")
            df_roles = load_data("mst_roles_permission")
            df_branches = load_data("mst_branches")
            
            if not df_users.empty:
                user_match = df_users[(df_users['username'].astype(str).str.strip() == username_input.strip()) & 
                                      (df_users['password'].astype(str).str.strip() == str(password_input).strip())]
                
                if not user_match.empty:
                    user_data = user_match.iloc[0].to_dict()
                    
                    # Deteksi nama kolom secara fleksibel sesuai dengan database baru kamu
                    branch_id_col = 'branch_id' if 'branch_id' in df_branches.columns else df_branches.columns[0] if not df_branches.empty else ''
                    branch_name_col = 'branch_name' if 'branch_name' in df_branches.columns else df_branches.columns[1] if len(df_branches.columns) > 1 else ''
                    branch_type_col = 'branch_type' if 'branch_type' in df_branches.columns else df_branches.columns[2] if len(df_branches.columns) > 2 else ''
                    
                    role_id_col = 'role_id' if 'role_id' in df_roles.columns else df_roles.columns[0] if not df_roles.empty else ''
                    
                    branch_match = df_branches[df_branches[branch_id_col].astype(str).str.strip() == str(user_data['assigned_branch']).strip()] if branch_id_col else pd.DataFrame()
                    branch_info = branch_match.iloc[0].to_dict() if not branch_match.empty else {}
                    
                    role_match = df_roles[df_roles[role_id_col].astype(str).str.strip() == str(user_data['role_id']).strip()] if role_id_col else pd.DataFrame()
                    role_info = role_match.iloc[0].to_dict() if not role_match.empty else {}
                    
                    st.session_state['user_info'] = {
                        'name': user_data['employee_name'],
                        'role': user_data['role_id'],
                        'branch_id': user_data['assigned_branch'],
                        'branch_name': branch_info.get(branch_name_col, 'Kantor Pusat / Unknown'),
                        'branch_type': branch_info.get(branch_type_col, 'Default'),
                        'permissions': role_info
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
    perms = info.get('permissions', {})
    
    # Membangun Menu Berdasarkan Hak Akses Role Permission Matrix
    menu_options = ["Dashboard Utama"]
    menu_icons = ["speedometer2"]
    
    if perms.get('allow_wms_inventory') in [True, 'TRUE', 1, 'True']:
        menu_options.append("WMS & Gudang")
        menu_icons.append("box-seam")
    if perms.get('allow_production_hub') in [True, 'TRUE', 1, 'True']:
        menu_options.append("Pusat Produksi (WIP)")
        menu_icons.append("tools")
    if perms.get('allow_finance') in [True, 'TRUE', 1, 'True']:
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
            
        st.markdown("
