import streamlit as st
import pandas as pd
import json
import os
from datetime import date, datetime
import calendar
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dompet Digital",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = "data/transactions.json"
SALARY_FILE = "data/salaries.json"

EXPENSE_CATEGORIES = [
    "Makanan & Minuman", "Belanja Online", "Transportasi",
    "Tagihan & Utilitas", "Kesehatan", "Hiburan",
    "Pendidikan", "Investasi", "Lainnya"
]
INCOME_CATEGORIES = [
    "Gaji", "Freelance", "Bonus", "Investasi",
    "Transfer Masuk", "Lainnya"
]

CAT_COLORS = [
    "Makanan & Minuman": "
#E24B4A",
    "Belanja Online":    "
#BA7517",
    "Transportasi":      "
#3266ad",
    "Tagihan & Utilitas":"
#7F77DD",
    "Kesehatan":         "
#D4537E",
    "Hiburan":           "
#1D9E75",
    "Pendidikan":        "
#639922",
    "Investasi":         "
#0F6E56",
    "Lainnya":           "
#73726c",
    "Gaji":              "
#1D9E75",
    "Freelance":         "
#3266ad",
    "Bonus":             "
#BA7517",
    "Transfer Masuk":    "
#7F77DD",
}

# ─── STORAGE ──────────────────────────────────────────────────────────────────
def ensure_dir():
    os.makedirs("data", exist_ok=True)

def load_transactions():
    ensure_dir()
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_transactions(txs):
    ensure_dir()
    with open(DATA_FILE, "w") as f:
        json.dump(txs, f, indent=2, default=str)

def load_salaries():
    ensure_dir()
    if not os.path.exists(SALARY_FILE):
        return {}
    with open(SALARY_FILE, "r") as f:
        return json.load(f)

def save_salaries(sal):
    ensure_dir()
    with open(SALARY_FILE, "w") as f:
        json.dump(sal, f, indent=2)

def month_key(y, m):
    return f"{y}-{str(m).zfill(2)}"

# ─── AUTH ─────────────────────────────────────────────────────────────────────
def check_auth():
    try:
        correct_pin = str(st.secrets["PIN"])
    except Exception:
        correct_pin = "1234"  # fallback dev mode

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown("## 💰 Dompet Digital")
    st.markdown("Masukkan PIN untuk masuk.")
    col1, col2 = st.columns([1, 2])
    with col1:
        pin = st.text_input("PIN", type="password", max_chars=8, key="pin_input")
        if st.button("Masuk", use_container_width=True):
            if pin == correct_pin:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("PIN salah!")
    return False

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def fmt_rp(n):
    return f"Rp {int(n):,}".replace(",", ".")

def get_month_txs(txs, year, month):
    key = month_key(year, month)
    return [t for t in txs if t["date"].startswith(key)]

def to_df(txs):
    if not txs:
        return pd.DataFrame(columns=["id","type","amount","category","date","desc"])
    return pd.DataFrame(txs)

def export_excel(df_exp, df_inc, year, month):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_exp.to_excel(writer, sheet_name="Pengeluaran", index=False)
        df_inc.to_excel(writer, sheet_name="Pemasukan", index=False)
    return buf.getvalue()

# ─── MAIN APP ─────────────────────────────────────────────────────────────────
def main():
    if not check_auth():
        return

    # ── Sidebar navigation ──
    with st.sidebar:
        st.markdown("## 💰 Dompet Digital")
        st.markdown("---")
        page = st.radio(
            "Menu",
            ["📊 Rekap Bulan Ini", "➕ Catat Transaksi", "📋 Riwayat", "📈 Analisis"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        # Month selector
        st.markdown("**Periode**")
        now = datetime.now()
        sel_year  = st.selectbox("Tahun", list(range(now.year - 2, now.year + 1))[::-1], index=0)
        sel_month = st.selectbox("Bulan", list(range(1, 13)),
                                 index=now.month - 1,
                                 format_func=lambda m: calendar.month_name[m])

        st.markdown("---")
        if st.button("🚪 Keluar", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    txs = load_transactions()
    salaries = load_salaries()
    mk = month_key(sel_year, sel_month)
    month_txs = get_month_txs(txs, sel_year, sel_month)

    salary_val = salaries.get(mk, 0)
    total_income = sum(t["amount"] for t in month_txs if t["type"] == "income") + salary_val
    total_expense = sum(t["amount"] for t in month_txs if t["type"] == "expense")
    saldo = total_income - total_expense

    # ═══════════════════════════════════════════════════
    # PAGE: REKAP
    # ═══════════════════════════════════════════════════
    if page == "📊 Rekap Bulan Ini":
        st.markdown(f"## 📊 Rekap — {calendar.month_name[sel_month]} {sel_year}")

        # Gaji input
        with st.expander("💼 Set Gaji Bulan Ini", expanded=(salary_val == 0)):
            new_salary = st.number_input(
                "Gaji Pokok (Rp)", min_value=0, value=int(salary_val), step=100_000,
                format="%d", key="salary_inp"
            )
            if st.button("Simpan Gaji"):
                salaries[mk] = new_salary
                save_salaries(salaries)
                st.success(f"Gaji disimpan: {fmt_rp(new_salary)}")
                st.rerun()

        st.markdown("---")
        # Metric cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💚 Pemasukan", fmt_rp(total_income))
        c2.metric("❤️ Pengeluaran", fmt_rp(total_expense))
        delta_color = "normal" if saldo >= 0 else "inverse"
        c3.metric("💰 Saldo", fmt_rp(saldo), delta=fmt_rp(saldo - salary_val) if salary_val else None)
        c4.metric("📝 Transaksi", len(month_txs))

        st.markdown("---")
        col_left, col_right = st.columns([1, 1])

        # Pie chart — pengeluaran per kategori
        exp_txs = [t for t in month_txs if t["type"] == "expense"]
        with col_left:
            st.markdown("#### Pengeluaran per Kategori")
            if exp_txs:
                cat_map = {}
                for t in exp_txs:
                    cat_map[t["category"]] = cat_map.get(t["category"], 0) + t["amount"]
                fig = px.pie(
                    names=list(cat_map.keys()),
                    values=list(cat_map.values()),
                    color=list(cat_map.keys()),
                    color_discrete_map=CAT_COLORS,
                    hole=0.4,
                )
                fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300,
                                  showlegend=True, legend=dict(orientation="v", font=dict(size=11)))
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Belum ada pengeluaran bulan ini.")

        # Bar chart — top kategori
        with col_right:
            st.markdown("#### Top Pengeluaran")
            if exp_txs:
                cat_map = {}
                for t in exp_txs:
                    cat_map[t["category"]] = cat_map.get(t["category"], 0) + t["amount"]
                sorted_cats = sorted(cat_map.items(), key=lambda x: x[1], reverse=True)
                df_bar = pd.DataFrame(sorted_cats, columns=["Kategori", "Jumlah"])
                df_bar["Warna"] = df_bar["Kategori"].map(lambda c: CAT_COLORS.get(c, "
#73726c"))
                fig2 = px.bar(df_bar, x="Jumlah", y="Kategori", orientation="h",
                              color="Kategori", color_discrete_map=CAT_COLORS,
                              text=df_bar["Jumlah"].apply(fmt_rp))
                fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300,
                                   showlegend=False, yaxis=dict(categoryorder="total ascending"))
                fig2.update_traces(textposition="outside")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Belum ada data.")

        # Tren 6 bulan
        st.markdown("---")
        st.markdown("#### Tren 6 Bulan Terakhir")
        months_6, inc_6, exp_6, lab_6 = [], [], [], []
        for i in range(5, -1, -1):
            ref = datetime(sel_year, sel_month, 1)
            m_idx = ref.month - i
            y_idx = ref.year
            while m_idx <= 0:
                m_idx += 12; y_idx -= 1
            while m_idx > 12:
                m_idx -= 12; y_idx += 1
            k = month_key(y_idx, m_idx)
            t_month = get_month_txs(txs, y_idx, m_idx)
            inc = sum(t["amount"] for t in t_month if t["type"] == "income") + salaries.get(k, 0)
            exp = sum(t["amount"] for t in t_month if t["type"] == "expense")
            lab_6.append(f"{calendar.month_abbr[m_idx]} {y_idx}")
            inc_6.append(inc); exp_6.append(exp)

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Pemasukan", x=lab_6, y=inc_6, marker_color="
#1D9E75"))
        fig3.add_trace(go.Bar(name="Pengeluaran", x=lab_6, y=exp_6, marker_color="
#E24B4A"))
        fig3.update_layout(barmode="group", height=280, margin=dict(t=10,b=10,l=10,r=10),
                           legend=dict(orientation="h", yanchor="bottom", y=1.02))
        fig3.update_yaxes(tickformat=",")
        st.plotly_chart(fig3, use_container_width=True)

        # Export
        st.markdown("---")
        if month_txs:
            df_exp_dl = to_df([t for t in month_txs if t["type"] == "expense"])
            df_inc_dl = to_df([t for t in month_txs if t["type"] == "income"])
            xlsx_data = export_excel(df_exp_dl, df_inc_dl, sel_year, sel_month)
            st.download_button(
                "⬇️ Export Excel Bulan Ini",
                data=xlsx_data,
                file_name=f"keuangan_{mk}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ═══════════════════════════════════════════════════
    # PAGE: CATAT TRANSAKSI
    # ═══════════════════════════════════════════════════
    elif page == "➕ Catat Transaksi":
        st.markdown("## ➕ Catat Transaksi")

        with st.form("add_tx_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                tx_type = st.selectbox("Jenis", ["Pengeluaran", "Pemasukan"])
                tx_amount = st.number_input("Jumlah (Rp)", min_value=1, step=1000, format="%d")
            with col2:
                cats = EXPENSE_CATEGORIES if tx_type == "Pengeluaran" else INCOME_CATEGORIES
                tx_cat = st.selectbox("Kategori", cats)
                tx_date = st.date_input("Tanggal", value=date.today())

            tx_desc = st.text_input(
                "Keterangan",
                placeholder="Contoh: Belanja Shopee — baju, Makan siang warteg, dll..."
            )
            submitted = st.form_submit_button("✅ Simpan Transaksi", use_container_width=True)

        if submitted:
            new_tx = {
                "id": int(datetime.now().timestamp() * 1000),
                "type": "expense" if tx_type == "Pengeluaran" else "income",
                "amount": int(tx_amount),
                "category": tx_cat,
                "date": str(tx_date),
                "desc": tx_desc or tx_cat,
            }
            txs.append(new_tx)
            save_transactions(txs)
            st.success(f"✅ Transaksi disimpan! {tx_type} {fmt_rp(tx_amount)} — {tx_cat}")
            st.balloons()

        # Quick summary bulan ini
        st.markdown("---")
        st.markdown(f"#### Ringkasan {calendar.month_name[sel_month]} {sel_year}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Pemasukan", fmt_rp(total_income))
        c2.metric("Pengeluaran", fmt_rp(total_expense))
        c3.metric("Saldo", fmt_rp(saldo))

    # ═══════════════════════════════════════════════════
    # PAGE: RIWAYAT
    # ═══════════════════════════════════════════════════
    elif page == "📋 Riwayat":
        st.markdown(f"## 📋 Riwayat — {calendar.month_name[sel_month]} {sel_year}")

        if not month_txs:
            st.info("Belum ada transaksi bulan ini.")
        else:
            # Filter
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_type = st.selectbox("Filter Jenis", ["Semua", "Pengeluaran", "Pemasukan"])
            with col_f2:
                all_cats = list({t["category"] for t in month_txs})
                filter_cat = st.selectbox("Filter Kategori", ["Semua"] + sorted(all_cats))

            filtered = month_txs
            if filter_type == "Pengeluaran":
                filtered = [t for t in filtered if t["type"] == "expense"]
            elif filter_type == "Pemasukan":
                filtered = [t for t in filtered if t["type"] == "income"]
            if filter_cat != "Semua":
                filtered = [t for t in filtered if t["category"] == filter_cat]

            filtered_sorted = sorted(filtered, key=lambda x: x["date"], reverse=True)

            # Delete UI
            to_delete = None
            for t in filtered_sorted:
                col_a, col_b, col_c, col_d, col_e = st.columns([2, 1.5, 1.5, 1, 0.4])
                col_a.markdown(f"**{t['desc']}**  \n<small style='color:gray'>{t['category']} · {t['date']}</small>", unsafe_allow_html=True)
                col_b.write("")
                col_c.markdown(
                    f"<span style='color:{'
#E24B4A' if t['type']=='expense' else '
#1D9E75'};font-weight:600'>"
                    f"{'−' if t['type']=='expense' else '+'} {fmt_rp(t['amount'])}</span>",
                    unsafe_allow_html=True
                )
                col_d.write("")
                if col_e.button("🗑️", key=f"del_{t['id']}"):
                    to_delete = t["id"]
                st.divider()

            if to_delete:
                txs = [t for t in txs if t["id"] != to_delete]
                save_transactions(txs)
                st.success("Transaksi dihapus.")
                st.rerun()

            # Export
            df_all = to_df(filtered_sorted)
            csv = df_all.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Export CSV", data=csv,
                               file_name=f"riwayat_{mk}.csv", mime="text/csv")

    # ═══════════════════════════════════════════════════
    # PAGE: ANALISIS
    # ═══════════════════════════════════════════════════
    elif page == "📈 Analisis":
        st.markdown("## 📈 Analisis Keuangan")

        if not txs:
            st.info("Belum ada data transaksi.")
            return

        df = to_df(txs)
        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.to_period("M").astype(str)
        df["month_label"] = df["date"].dt.strftime("%b %Y")

        # Total per bulan semua waktu
        st.markdown("#### Pengeluaran per Kategori (Semua Waktu)")
        exp_all = df[df["type"] == "expense"]
        if not exp_all.empty:
            cat_total = exp_all.groupby("category")["amount"].sum().reset_index()
            cat_total.columns = ["Kategori", "Total"]
            cat_total = cat_total.sort_values("Total", ascending=False)
            fig = px.bar(cat_total, x="Kategori", y="Total",
                         color="Kategori", color_discrete_map=CAT_COLORS,
                         text=cat_total["Total"].apply(fmt_rp))
            fig.update_layout(showlegend=False, height=320, margin=dict(t=10,b=10))
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        # Tren bulanan semua kategori
        st.markdown("#### Tren Pengeluaran per Kategori per Bulan")
        if not exp_all.empty:
            pivot = exp_all.groupby(["month", "category"])["amount"].sum().reset_index()
            fig2 = px.line(pivot, x="month", y="amount", color="category",
                           color_discrete_map=CAT_COLORS, markers=True)
            fig2.update_layout(height=320, margin=dict(t=10,b=10),
                               legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=10)),
                               xaxis_title="", yaxis_title="Jumlah (Rp)")
            st.plotly_chart(fig2, use_container_width=True)

        # Rata-rata pengeluaran per kategori per bulan
        st.markdown("#### Rata-rata Pengeluaran per Bulan")
        if not exp_all.empty:
            n_months = df["month"].nunique() or 1
            avg_cat = exp_all.groupby("category")["amount"].sum().div(n_months).reset_index()
            avg_cat.columns = ["Kategori", "Rata-rata/Bulan"]
            avg_cat = avg_cat.sort_values("Rata-rata/Bulan", ascending=False)
            avg_cat["Rata-rata/Bulan (fmt)"] = avg_cat["Rata-rata/Bulan"].apply(fmt_rp)
            st.dataframe(avg_cat[["Kategori", "Rata-rata/Bulan (fmt)"]].rename(
                columns={"Rata-rata/Bulan (fmt)": "Rata-rata per Bulan"}),
                use_container_width=True, hide_index=True
            )

if __name__ == "__main__":
    main() kurang lengkap harusnya bisa tambah kategori sendiri,terus di grafik gada tulisan kategorinya

Show more
3 Jun
Oke gua rewrite sekalian — tambah fitur custom kategori + fix grafik. Langsung gua buatin file baru yang tinggal lo paste ke GitHub.


Write new app_v2.py without plotly
Write new app_v2.py without plotly

design-md-finance-management-system-fms-DESIGN.md
69 lines

md

Gua mau pake design MD ini gimana buat di aplikasi finance gua

21.50
Bagus, ini design system yang solid! Gua akan implement token-tokennya ke app lo — warna navy/teal, typography Inter, spacing system, card components, semua sesuai DESIGN.md.


Ran 2 commands, viewed a file
Ran 2 commands, viewed a file

Verify app_v2 syntax before modifying

Script

Read current app_v2 to understand structure

Write full redesigned app
bash

cat > /home/claude/keuangan/app_v2.py << 'PYEOF'
import streamlit as st
import pandas as pd
import json
import os
from datetime import date, datetime
import calendar
from io import BytesIO
import math

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dompet Digital",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── DESIGN SYSTEM (from DESIGN.md) ──────────────────────────────────────────
# Colors
C_PRIMARY    = "#1A365D"   # Deep Navy
C_SECONDARY  = "#319795"   # Teal
C_ACCENT     = "#4FD1C5"   # Light Teal
C_SUCCESS    = "#38A169"   # Green  — income / positive
C_DANGER     = "#E53E3E"   # Red    — expense / negative
C_BG         = "#F7FAFC"   # Off-White background
C_SURFACE    = "#FFFFFF"   # Card / panel surface
C_BORDER     = "#E2E8F0"
C_TEXT       = "#1A202C"
C_CAPTION    = "#A0AEC0"

PALETTE = [
    "#319795","#E53E3E","#38A169","#1A365D","#ED8936",
    "#9F7AEA","#F56565","#4FD1C5","#667EEA","#48BB78",
    "#FC8181","#63B3ED","#68D391","#F6AD55","#B794F4",
]

# ─── INJECT CSS ───────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
    font-size: 16px;
    color: {C_TEXT};
  }}

  /* ── Main background ── */
  .stApp {{ background: {C_BG}; }}

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {{
    background: {C_PRIMARY} !important;
  }}
  [data-testid="stSidebar"] * {{
    color: #EBF8FF !important;
  }}
  [data-testid="stSidebar"] .stRadio label {{
    color: #EBF8FF !important;
    font-size: 14px;
  }}
  [data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,0.15) !important;
  }}

  /* ── Metric cards ── */
  [data-testid="metric-container"] {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }}
  [data-testid="metric-container"] label {{
    font-size: 12.8px !important;
    color: {C_CAPTION} !important;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  [data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 22px !important;
    font-weight: 700 !important;
    color: {C_TEXT} !important;
  }}

  /* ── Buttons ── */
  .stButton > button {{
    background: {C_SECONDARY} !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    transition: background .2s;
  }}
  .stButton > button:hover {{
    background: {C_ACCENT} !important;
    color: {C_PRIMARY} !important;
  }}

  /* ── Download button ── */
  .stDownloadButton > button {{
    background: {C_PRIMARY} !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
  }}

  /* ── Inputs & selects ── */
  .stTextInput input, .stNumberInput input, .stSelectbox select,
  [data-testid="stDateInput"] input {{
    border: 1px solid {C_BORDER} !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    background: {C_SURFACE} !important;
  }}
  .stTextInput input:focus, .stNumberInput input:focus {{
    border-color: {C_SECONDARY} !important;
    box-shadow: 0 0 0 3px rgba(79,209,197,0.2) !important;
  }}

  /* ── Expander ── */
  .streamlit-expanderHeader {{
    background: {C_SURFACE} !important;
    border: 1px solid {C_BORDER} !important;
    border-radius: 8px !important;
    font-weight: 500;
  }}

  /* ── Divider ── */
  hr {{ border-color: {C_BORDER} !important; }}

  /* ── Section headings ── */
  h2 {{ font-size: 30.52px !important; font-weight: 600 !important; color: {C_PRIMARY} !important; }}
  h3, h4 {{ font-size: 20px !important; font-weight: 600 !important; color: {C_PRIMARY} !important; }}

  /* ── KPI card strip ── */
  .kpi-card {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }}
  .kpi-label {{
    font-size: 12.8px;
    color: {C_CAPTION};
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: .05em;
    margin-bottom: 6px;
  }}
  .kpi-value {{
    font-size: 24px;
    font-weight: 700;
    color: {C_TEXT};
  }}

  /* ── Transaction table ── */
  .tx-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: {C_SURFACE};
    border-bottom: 1px solid {C_BORDER};
    font-size: 14px;
  }}
  .tx-row:last-child {{ border-bottom: none; border-radius: 0 0 10px 10px; }}
  .tx-row:first-child {{ border-radius: 10px 10px 0 0; }}
  .tx-desc {{ flex: 3; }}
  .tx-cat  {{ flex: 2; text-align: center; color: {C_CAPTION}; font-size: 12.8px; }}
  .tx-date {{ flex: 1.5; color: {C_CAPTION}; font-size: 12.8px; }}
  .tx-amt  {{ flex: 1.5; text-align: right; font-weight: 600; }}
  .income  {{ color: {C_SUCCESS}; }}
  .expense {{ color: {C_DANGER};  }}
  .badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 500;
    background: {C_BG};
    border: 1px solid {C_BORDER};
    color: {C_TEXT};
  }}

  /* ── Info box ── */
  .stAlert {{ border-radius: 8px !important; font-size: 14px !important; }}

  /* ── Dataframe ── */
  .stDataFrame {{ border-radius: 10px; overflow: hidden; }}
</style>
""", unsafe_allow_html=True)

# ─── FILE PATHS ───────────────────────────────────────────────────────────────
DATA_FILE       = "data/transactions.json"
SALARY_FILE     = "data/salaries.json"
CATEGORIES_FILE = "data/categories.json"

DEFAULT_EXPENSE_CATS = [
    "Makanan & Minuman","Belanja Online","Transportasi",
    "Tagihan & Utilitas","Kesehatan","Hiburan",
    "Pendidikan","Investasi","Lainnya"
]
DEFAULT_INCOME_CATS = [
    "Gaji","Freelance","Bonus","Investasi","Transfer Masuk","Lainnya"
]

# ─── STORAGE ──────────────────────────────────────────────────────────────────
def ensure_dir(): os.makedirs("data", exist_ok=True)

def load_json(path, default):
    ensure_dir()
    if not os.path.exists(path): return default
    with open(path) as f: return json.load(f)

def save_json(path, obj):
    ensure_dir()
    with open(path,"w") as f: json.dump(obj, f, indent=2, default=str)

def load_transactions():  return load_json(DATA_FILE, [])
def save_transactions(v): save_json(DATA_FILE, v)
def load_salaries():      return load_json(SALARY_FILE, {})
def save_salaries(v):     save_json(SALARY_FILE, v)

def load_categories():
    cats = load_json(CATEGORIES_FILE, {"expense": list(DEFAULT_EXPENSE_CATS), "income": list(DEFAULT_INCOME_CATS)})
    for c in DEFAULT_EXPENSE_CATS:
        if c not in cats["expense"]: cats["expense"].append(c)
    for c in DEFAULT_INCOME_CATS:
        if c not in cats["income"]: cats["income"].append(c)
    return cats

def save_categories(v): save_json(CATEGORIES_FILE, v)
def month_key(y,m): return f"{y}-{str(m).zfill(2)}"

# ─── AUTH ─────────────────────────────────────────────────────────────────────
def check_auth():
    try:    correct_pin = str(st.secrets["PIN"])
    except: correct_pin = "1234"

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated: return True

    st.markdown(f"""
    <div style="max-width:400px;margin:60px auto;background:{C_SURFACE};
         border:1px solid {C_BORDER};border-radius:16px;padding:40px 36px;
         box-shadow:0 4px 24px rgba(26,54,93,.10)">
      <div style="font-size:36px;text-align:center;margin-bottom:8px">💰</div>
      <h2 style="text-align:center;font-size:24px!important;color:{C_PRIMARY}!important;
          margin-bottom:4px">Dompet Digital</h2>
      <p style="text-align:center;color:{C_CAPTION};font-size:14px;margin-bottom:24px">
        Masukkan PIN untuk masuk</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pin = st.text_input("PIN", type="password", max_chars=8, key="pin_input", label_visibility="collapsed", placeholder="Masukkan PIN...")
        if st.button("Masuk", use_container_width=True):
            if pin == correct_pin:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("PIN salah!")
    return False

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def fmt_rp(n): return f"Rp {int(n):,}".replace(",",".")

def get_month_txs(txs, year, month):
    key = month_key(year, month)
    return [t for t in txs if t["date"].startswith(key)]

def to_df(txs):
    if not txs: return pd.DataFrame(columns=["id","type","amount","category","date","desc"])
    return pd.DataFrame(txs)

def cat_color(cat, cat_list):
    try: return PALETTE[cat_list.index(cat) % len(PALETTE)]
    except: return C_CAPTION

def export_excel(df_exp, df_inc):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df_exp.to_excel(w, sheet_name="Pengeluaran", index=False)
        df_inc.to_excel(w, sheet_name="Pemasukan", index=False)
    return buf.getvalue()

# ─── CHART: HORIZONTAL BAR ────────────────────────────────────────────────────
def bar_chart_kategori(cat_map, cat_list):
    if not cat_map: st.info("Belum ada data."); return
    items = sorted(cat_map.items(), key=lambda x: x[1], reverse=True)
    max_v = items[0][1] if items else 1
    rows = ""
    for cat, val in items:
        color = cat_color(cat, cat_list)
        pct   = round(val / max_v * 100)
        rows += f"""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
          <div style="width:140px;font-size:13px;color:{C_TEXT};white-space:nowrap;
               overflow:hidden;text-overflow:ellipsis;font-weight:500">{cat}</div>
          <div style="flex:1;background:{C_BG};border-radius:6px;height:10px;border:1px solid {C_BORDER}">
            <div style="width:{pct}%;background:{color};height:10px;border-radius:6px;
                 transition:width .4s"></div>
          </div>
          <div style="width:110px;font-size:13px;color:{C_TEXT};text-align:right;font-weight:600">
            {fmt_rp(val)}</div>
        </div>"""
    st.markdown(
        f'<div style="background:{C_SURFACE};border:1px solid {C_BORDER};border-radius:12px;'
        f'padding:20px 24px;box-shadow:0 1px 3px rgba(0,0,0,.06)">{rows}</div>',
        unsafe_allow_html=True)

# ─── CHART: DONUT ─────────────────────────────────────────────────────────────
def donut_chart(cat_map, cat_list):
    if not cat_map: return
    items = sorted(cat_map.items(), key=lambda x: x[1], reverse=True)
    total = sum(v for _,v in items)
    if total == 0: return
    cx=cy=110; ro=88; ri=52; angle=-90.0
    paths=""; legend=""
    for cat, val in items:
        color = cat_color(cat, cat_list)
        sweep = val/total*360
        ea = angle + sweep
        la = 1 if sweep > 180 else 0
        def pt(a,r): return cx+r*math.cos(math.radians(a)), cy+r*math.sin(math.radians(a))
        x1,y1=pt(angle,ro); x2,y2=pt(ea,ro)
        x3,y3=pt(ea,ri);    x4,y4=pt(angle,ri)
        paths += (f'<path d="M{x1:.1f},{y1:.1f} A{ro},{ro} 0 {la},1 {x2:.1f},{y2:.1f} '
                  f'L{x3:.1f},{y3:.1f} A{ri},{ri} 0 {la},0 {x4:.1f},{y4:.1f}Z" '
                  f'fill="{color}" stroke="{C_SURFACE}" stroke-width="2.5"/>')
        pct = round(val/total*100)
        legend += (f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
                   f'<div style="width:10px;height:10px;border-radius:3px;background:{color};flex-shrink:0"></div>'
                   f'<div style="font-size:12.8px;color:{C_TEXT}">{cat}</div>'
                   f'<div style="font-size:12.8px;color:{C_CAPTION};margin-left:auto"><b style="color:{C_TEXT}">{pct}%</b></div>'
                   f'</div>')
        angle = ea

    svg = (f'<svg viewBox="0 0 220 220" width="190" xmlns="http://www.w3.org/2000/svg">'
           f'{paths}'
           f'<text x="{cx}" y="{cy-6}" text-anchor="middle" fill="{C_CAPTION}" font-size="10" font-family="Inter">Total</text>'
           f'<text x="{cx}" y="{cy+12}" text-anchor="middle" fill="{C_TEXT}" font-size="11" font-weight="600" font-family="Inter">{fmt_rp(total)}</text>'
           f'</svg>')

    c1,c2 = st.columns([1,1.2])
    with c1: st.markdown(svg, unsafe_allow_html=True)
    with c2: st.markdown(
        f'<div style="padding:12px 0;background:{C_SURFACE};border:1px solid {C_BORDER};'
        f'border-radius:12px;padding:16px 20px">{legend}</div>', unsafe_allow_html=True)

# ─── CHART: TREND BARS ────────────────────────────────────────────────────────
def trend_chart(labels, inc_list, exp_list):
    W,H,pl,pb,pt2 = 580,230,68,44,24
    cw = W-pl-16; ch = H-pb-pt2
    max_v = max(max(inc_list,default=0), max(exp_list,default=0)) or 1
    n = len(labels)
    gw = cw/n; bw = gw*0.30
    bars=x_labels=y_lines=""

    for step in [0,.25,.5,.75,1.0]:
        y  = pt2 + ch*(1-step)
        v  = max_v*step
        lbl = (f"Rp{int(v/1_000_000)}jt" if v>=1_000_000
               else f"Rp{int(v/1_000)}rb" if v>=1000 else str(int(v)))
        y_lines += (f'<line x1="{pl}" y1="{y:.1f}" x2="{W-10}" y2="{y:.1f}" '
                    f'stroke="{C_BORDER}" stroke-width="1"/>'
                    f'<text x="{pl-5}" y="{y+4:.1f}" text-anchor="end" '
                    f'fill="{C_CAPTION}" font-size="9" font-family="Inter">{lbl}</text>')

    for i,(lbl,inc,exp) in enumerate(zip(labels,inc_list,exp_list)):
        gx = pl + i*gw + gw*0.1
        hi = inc/max_v*ch
        bars += (f'<rect x="{gx:.1f}" y="{pt2+ch-hi:.1f}" width="{bw:.1f}" height="{hi:.1f}" '
                 f'fill="{C_SUCCESS}" rx="3"/>')
        he = exp/max_v*ch
        bars += (f'<rect x="{gx+bw+3:.1f}" y="{pt2+ch-he:.1f}" width="{bw:.1f}" height="{he:.1f}" '
                 f'fill="{C_DANGER}" rx="3"/>')
        x_labels += (f'<text x="{gx+bw+1.5:.1f}" y="{H-10}" text-anchor="middle" '
                     f'fill="{C_CAPTION}" font-size="10" font-family="Inter">{lbl}</text>')

    legend = (f'<rect x="{pl}" y="5" width="10" height="10" fill="{C_SUCCESS}" rx="2"/>'
              f'<text x="{pl+14}" y="14" fill="{C_TEXT}" font-size="10" font-family="Inter">Pemasukan</text>'
              f'<rect x="{pl+95}" y="5" width="10" height="10" fill="{C_DANGER}" rx="2"/>'
              f'<text x="{pl+109}" y="14" fill="{C_TEXT}" font-size="10" font-family="Inter">Pengeluaran</text>')

    svg = (f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" '
           f'style="background:{C_SURFACE};border:1px solid {C_BORDER};border-radius:12px;padding:8px">'
           f'{y_lines}{bars}{x_labels}{legend}</svg>')
    st.markdown(svg, unsafe_allow_html=True)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    if not check_auth(): return

    cats = load_categories()

    with st.sidebar:
        st.markdown(f'<div style="font-size:22px;font-weight:700;color:#EBF8FF;margin-bottom:4px">💰 Dompet Digital</div>', unsafe_allow_html=True)
        st.markdown("---")
        page = st.radio("Menu",[
            "📊 Rekap Bulan Ini",
            "➕ Catat Transaksi",
            "📋 Riwayat",
            "📈 Analisis",
            "🏷️ Kelola Kategori",
        ], label_visibility="collapsed")
        st.markdown("---")
        st.markdown('<div style="font-size:12px;color:#90CDF4;font-weight:600;letter-spacing:.06em">PERIODE</div>', unsafe_allow_html=True)
        now = datetime.now()
        sel_year  = st.selectbox("Tahun", list(range(now.year-2,now.year+1))[::-1], index=0)
        sel_month = st.selectbox("Bulan", list(range(1,13)), index=now.month-1,
                                 format_func=lambda m: calendar.month_name[m])
        st.markdown("---")
        if st.button("🚪 Keluar", use_container_width=True):
            st.session_state.authenticated = False; st.rerun()

    txs      = load_transactions()
    salaries = load_salaries()
    mk       = month_key(sel_year, sel_month)
    month_txs = get_month_txs(txs, sel_year, sel_month)
    salary_val   = salaries.get(mk, 0)
    total_income = sum(t["amount"] for t in month_txs if t["type"]=="income") + salary_val
    total_expense= sum(t["amount"] for t in month_txs if t["type"]=="expense")
    saldo        = total_income - total_expense

    # ══ REKAP ══════════════════════════════════════════════════════════════════
    if page == "📊 Rekap Bulan Ini":
        st.markdown(f"## 📊 Rekap — {calendar.month_name[sel_month]} {sel_year}")

        with st.expander("💼 Set Gaji Bulan Ini", expanded=(salary_val==0)):
            new_sal = st.number_input("Gaji Pokok (Rp)", min_value=0,
                value=int(salary_val), step=100_000, format="%d", key="salary_inp")
            if st.button("Simpan Gaji"):
                salaries[mk]=new_sal; save_salaries(salaries)
                st.success(f"✅ Gaji disimpan: {fmt_rp(new_sal)}"); st.rerun()

        st.markdown("---")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("💚 Total Pemasukan",  fmt_rp(total_income))
        c2.metric("❤️ Total Pengeluaran", fmt_rp(total_expense))
        c3.metric("💰 Saldo Bersih",      fmt_rp(saldo))
        c4.metric("📝 Jumlah Transaksi",  len(month_txs))

        st.markdown("---")
        exp_txs = [t for t in month_txs if t["type"]=="expense"]
        cat_map = {}
        for t in exp_txs: cat_map[t["category"]] = cat_map.get(t["category"],0)+t["amount"]

        col_l,col_r = st.columns(2)
        with col_l:
            st.markdown("#### 🍩 Komposisi Pengeluaran")
            if cat_map: donut_chart(cat_map, cats["expense"])
            else: st.info("Belum ada pengeluaran bulan ini.")
        with col_r:
            st.markdown("#### 📊 Rincian per Kategori")
            bar_chart_kategori(cat_map, cats["expense"])

        st.markdown("---")
        st.markdown("#### 📅 Tren 6 Bulan Terakhir")
        lab_6=[]; inc_6=[]; exp_6=[]
        for i in range(5,-1,-1):
            mi=sel_month-i; yi=sel_year
            while mi<=0: mi+=12; yi-=1
            k=month_key(yi,mi); tm=get_month_txs(txs,yi,mi)
            lab_6.append(calendar.month_abbr[mi])
            inc_6.append(sum(t["amount"] for t in tm if t["type"]=="income")+salaries.get(k,0))
            exp_6.append(sum(t["amount"] for t in tm if t["type"]=="expense"))
        trend_chart(lab_6,inc_6,exp_6)

        st.markdown("---")
        if month_txs:
            df_e = to_df([t for t in month_txs if t["type"]=="expense"])
            df_i = to_df([t for t in month_txs if t["type"]=="income"])
            st.download_button("⬇️ Export Excel Bulan Ini", data=export_excel(df_e,df_i),
                file_name=f"keuangan_{mk}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ══ CATAT ══════════════════════════════════════════════════════════════════
    elif page == "➕ Catat Transaksi":
        st.markdown("## ➕ Catat Transaksi")

        st.markdown(f"""
        <div style="background:{C_SURFACE};border:1px solid {C_BORDER};border-radius:12px;
             padding:24px 24px 8px;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:16px">
          <p style="color:{C_CAPTION};font-size:12.8px;margin:0 0 16px">
            Isi form di bawah untuk mencatat pengeluaran atau pemasukan baru.</p>
        </div>""", unsafe_allow_html=True)

        with st.form("add_tx", clear_on_submit=True):
            c1,c2 = st.columns(2)
            with c1:
                tx_type  = st.selectbox("Jenis Transaksi", ["Pengeluaran","Pemasukan"])
                tx_amount= st.number_input("Jumlah (Rp)", min_value=1, step=1000, format="%d")
            with c2:
                cat_list = cats["expense"] if tx_type=="Pengeluaran" else cats["income"]
                tx_cat   = st.selectbox("Kategori", cat_list)
                tx_date  = st.date_input("Tanggal", value=date.today())
            tx_desc = st.text_input("Keterangan",
                placeholder="Contoh: Belanja Shopee baju, Makan siang warteg, Gojek ke kantor...")
            ok = st.form_submit_button("✅ Simpan Transaksi", use_container_width=True)

        if ok:
            txs.append({
                "id": int(datetime.now().timestamp()*1000),
                "type": "expense" if tx_type=="Pengeluaran" else "income",
                "amount": int(tx_amount),
                "category": tx_cat,
                "date": str(tx_date),
                "desc": tx_desc or tx_cat,
            })
            save_transactions(txs)
            st.success(f"✅ {tx_type} sebesar **{fmt_rp(tx_amount)}** pada kategori **{tx_cat}** berhasil disimpan!")
            st.balloons()

        st.markdown("---")
        st.markdown(f"#### Ringkasan {calendar.month_name[sel_month]} {sel_year}")
        c1,c2,c3 = st.columns(3)
        c1.metric("Pemasukan",  fmt_rp(total_income))
        c2.metric("Pengeluaran",fmt_rp(total_expense))
        c3.metric("Saldo",      fmt_rp(saldo))

    # ══ RIWAYAT ════════════════════════════════════════════════════════════════
    elif page == "📋 Riwayat":
        st.markdown(f"## 📋 Riwayat — {calendar.month_name[sel_month]} {sel_year}")

        if not month_txs:
            st.info("Belum ada transaksi bulan ini.")
        else:
            cf1,cf2,cf3 = st.columns(3)
            with cf1:
                ft = st.selectbox("Filter Jenis", ["Semua","Pengeluaran","Pemasukan"])
            with cf2:
                all_c = ["Semua"]+sorted({t["category"] for t in month_txs})
                fc = st.selectbox("Filter Kategori", all_c)
            with cf3:
                sort_by = st.selectbox("Urutkan", ["Terbaru","Terlama","Terbesar","Terkecil"])

            filtered = list(month_txs)
            if ft=="Pengeluaran": filtered=[t for t in filtered if t["type"]=="expense"]
            elif ft=="Pemasukan": filtered=[t for t in filtered if t["type"]=="income"]
            if fc!="Semua":       filtered=[t for t in filtered if t["category"]==fc]

            if sort_by=="Terbaru":  filtered=sorted(filtered,key=lambda x:x["date"],reverse=True)
            elif sort_by=="Terlama": filtered=sorted(filtered,key=lambda x:x["date"])
            elif sort_by=="Terbesar": filtered=sorted(filtered,key=lambda x:x["amount"],reverse=True)
            elif sort_by=="Terkecil": filtered=sorted(filtered,key=lambda x:x["amount"])

            # Table header
            st.markdown(f"""
            <div style="display:flex;gap:12px;padding:10px 16px;background:{C_BG};
                 border:1px solid {C_BORDER};border-radius:10px 10px 0 0;
                 font-size:12.8px;font-weight:600;color:{C_CAPTION};
                 text-transform:uppercase;letter-spacing:.05em">
              <div style="flex:3">Deskripsi</div>
              <div style="flex:2;text-align:center">Kategori</div>
              <div style="flex:1.5">Tanggal</div>
              <div style="flex:1.5;text-align:right">Jumlah</div>
              <div style="flex:0.4"></div>
            </div>""", unsafe_allow_html=True)

            to_del = None
            for t in filtered:
                color = C_DANGER if t["type"]=="expense" else C_SUCCESS
                sign  = "−" if t["type"]=="expense" else "+"
                ca,cb,cc,cd,ce = st.columns([3,2,1.5,1.5,0.4])
                ca.markdown(f"**{t['desc']}**")
                cb.markdown(f'<div style="text-align:center"><span class="badge">{t["category"]}</span></div>', unsafe_allow_html=True)
                cc.markdown(f'<span style="color:{C_CAPTION};font-size:12.8px">{t["date"]}</span>', unsafe_allow_html=True)
                cd.markdown(f'<div style="text-align:right;font-weight:600;color:{color}">{sign} {fmt_rp(t["amount"])}</div>', unsafe_allow_html=True)
                if ce.button("🗑️", key=f"d{t['id']}"):
                    to_del = t["id"]
                st.markdown(f'<hr style="margin:4px 0;border-color:{C_BORDER}">', unsafe_allow_html=True)

            if to_del:
                save_transactions([t for t in txs if t["id"]!=to_del])
                st.rerun()

            st.markdown("---")
            total_shown = sum(t["amount"] for t in filtered)
            st.markdown(f'<div style="text-align:right;font-size:14px;color:{C_CAPTION}">Total: <b style="color:{C_TEXT}">{fmt_rp(total_shown)}</b> dari {len(filtered)} transaksi</div>', unsafe_allow_html=True)
            st.markdown("")

            csv = to_df(filtered).to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Export CSV", data=csv,
                file_name=f"riwayat_{mk}.csv", mime="text/csv")

    # ══ ANALISIS ═══════════════════════════════════════════════════════════════
    elif page == "📈 Analisis":
        st.markdown("## 📈 Analisis Keuangan")
        if not txs: st.info("Belum ada data transaksi."); return

        df = to_df(txs)
        df["date"]  = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.strftime("%Y-%m")
        exp_all = df[df["type"]=="expense"]

        st.markdown("#### Pengeluaran per Kategori — Semua Waktu")
        if not exp_all.empty:
            bar_chart_kategori(exp_all.groupby("category")["amount"].sum().to_dict(), cats["expense"])

        st.markdown("---")
        st.markdown("#### Tren Pengeluaran per Kategori per Bulan")
        if not exp_all.empty:
            pivot = exp_all.groupby(["month","category"])["amount"].sum().unstack(fill_value=0)
            pivot.index.name="Bulan"; pivot.columns.name=None
            st.line_chart(pivot)

        st.markdown("---")
        st.markdown("#### Rata-rata Pengeluaran per Bulan")
        if not exp_all.empty:
            n = df["month"].nunique() or 1
            avg = exp_all.groupby("category")["amount"].sum().div(n).sort_values(ascending=False)
            df_avg = avg.reset_index()
            df_avg.columns = ["Kategori","Rata-rata per Bulan (Rp)"]
            df_avg["Rata-rata per Bulan (Rp)"] = df_avg["Rata-rata per Bulan (Rp)"].apply(fmt_rp)
            st.dataframe(df_avg, use_container_width=True, hide_index=True)

    # ══ KELOLA KATEGORI ════════════════════════════════════════════════════════
    elif page == "🏷️ Kelola Kategori":
        st.markdown("## 🏷️ Kelola Kategori")
        st.info("Tambah kategori custom sesuai kebutuhanmu. Kategori default 🔒 tidak bisa dihapus.")

        for kind, label in [("expense","Pengeluaran"),("income","Pemasukan")]:
            st.markdown(f"#### {label}")
            ca,cb = st.columns([3,1])
            with ca:
                new_cat = st.text_input(f"Nama kategori baru ({label})",
                    key=f"nc_{kind}", placeholder="Contoh: BPJS, Cicilan, Jajan...")
            with cb:
                st.write(""); st.write("")
                if st.button("➕ Tambah", key=f"add_{kind}"):
                    if new_cat and new_cat not in cats[kind]:
                        cats[kind].append(new_cat); save_categories(cats)
                        st.success(f"✅ '{new_cat}' ditambahkan!"); st.rerun()
                    elif new_cat in cats[kind]:
                        st.warning("Kategori sudah ada.")

            defaults = DEFAULT_EXPENSE_CATS if kind=="expense" else DEFAULT_INCOME_CATS
            for cat in list(cats[kind]):
                c1,c2 = st.columns([4,1])
                is_default = cat in defaults
                c1.markdown(f"{'🔒' if is_default else '🏷️'} **{cat}**")
                if not is_default:
                    if c2.button("Hapus", key=f"del_{kind}_{cat}"):
                        cats[kind].remove(cat); save_categories(cats); st.rerun()
                else:
                    c2.markdown(f'<span style="color:{C_CAPTION};font-size:12px">default</span>', unsafe_allow_html=True)
            st.markdown("---")

if __name__ == "__main__":
    main()





