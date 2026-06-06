import streamlit as st
import pandas as pd
import json
import os
from datetime import date, datetime
import calendar
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import math

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dompet Digital",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── DESIGN SYSTEM (DESIGN.md tokens) ────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  /* ── Base typography ── */
  html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', Roboto, sans-serif !important;
    font-size: 16px;
    color: #1A202C;
    background: #F7FAFC;
  }

  /* ── App background ── */
  .stApp { background: #F7FAFC !important; }

  /* ── Sidebar — Deep Navy ── */
  [data-testid="stSidebar"] {
    background: #1A365D !important;
  }
  [data-testid="stSidebar"] * { color: #EBF8FF !important; }
  [data-testid="stSidebar"] .stRadio label {
    font-size: 14px !important;
    padding: 6px 0 !important;
  }
  [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }

  /* ── Headings ── */
  h1 { font-size: 38.15px !important; font-weight: 700 !important; color: #1A365D !important; }
  h2 { font-size: 30.52px !important; font-weight: 600 !important; color: #1A365D !important; }
  h3 { font-size: 24.41px !important; font-weight: 600 !important; color: #1A365D !important; }
  h4 { font-size: 20px   !important; font-weight: 600 !important; color: #1A365D !important; }

  /* ── Metric cards ── */
  [data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }
  [data-testid="metric-container"] label {
    font-size: 12.80px !important;
    color: #A0AEC0 !important;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #1A202C !important;
  }

  /* ── Buttons — Teal CTA ── */
  .stButton > button {
    background: #319795 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 8px 16px !important;
    transition: background .2s, box-shadow .2s;
  }
  .stButton > button:hover {
    background: #4FD1C5 !important;
    color: #1A365D !important;
    box-shadow: 0 0 0 3px rgba(79,209,197,0.25) !important;
  }
  .stButton > button:focus {
    outline: 2px solid #4FD1C5 !important;
    outline-offset: 2px !important;
  }

  /* ── Download button ── */
  .stDownloadButton > button {
    background: #1A365D !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
  }
  .stDownloadButton > button:hover { background: #319795 !important; }

  /* ── Inputs ── */
  .stTextInput input, .stNumberInput input,
  [data-testid="stDateInput"] input {
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    background: #FFFFFF !important;
    padding: 8px 12px !important;
  }
  .stTextInput input:focus, .stNumberInput input:focus {
    border-color: #319795 !important;
    box-shadow: 0 0 0 3px rgba(79,209,197,0.20) !important;
  }

  /* ── Select ── */
  [data-testid="stSelectbox"] > div > div {
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
    font-size: 14px !important;
  }

  /* ── Expander ── */
  .streamlit-expanderHeader {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 2px solid #E2E8F0;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0 !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    color: #A0AEC0 !important;
    padding: 8px 16px !important;
  }
  .stTabs [aria-selected="true"] {
    background: #EBF8FF !important;
    color: #1A365D !important;
    border-bottom: 2px solid #319795 !important;
  }

  /* ── Form ── */
  [data-testid="stForm"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 24px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }

  /* ── Dataframe ── */
  .stDataFrame {
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    overflow: hidden;
  }
  .stDataFrame td {
    font-size: 14px !important;
    border-bottom: 1px solid #E2E8F0 !important;
  }
  .stDataFrame th {
    background: #F7FAFC !important;
    font-size: 12.80px !important;
    color: #A0AEC0 !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  /* ── Alert / info ── */
  .stAlert { border-radius: 8px !important; font-size: 14px !important; }

  /* ── Divider ── */
  hr { border-color: #E2E8F0 !important; }

  /* ── Caption ── */
  small, .caption { font-size: 12.80px !important; color: #A0AEC0 !important; }

  /* ── Progress bar ── */
  .stProgress > div > div { background: #319795 !important; border-radius: 99px; }
  .stProgress > div { background: #E2E8F0 !important; border-radius: 99px; }

  /* ── Slider ── */
  [data-testid="stSlider"] [role="slider"] { background: #319795 !important; }

  /* ── Spacing helpers ── */
  .block-container { padding-top: 32px !important; padding-bottom: 48px !important; }
</style>
""", unsafe_allow_html=True)

# ─── FILES ────────────────────────────────────────────────────────────────────
DATA_FILE       = "data/transactions.json"
SALARY_FILE     = "data/salaries.json"
CATEGORIES_FILE = "data/categories.json"
NOTES_FILE      = "data/notes.json"

# ─── DEFAULT CATEGORIES ───────────────────────────────────────────────────────
DEFAULT_EXPENSE_CATS = [
    "Makanan & Minuman", "Belanja Online", "Transportasi",
    "Tagihan & Utilitas", "Kesehatan", "Hiburan",
    "Pendidikan", "Investasi", "Lainnya"
]
DEFAULT_INCOME_CATS = [
    "Gaji", "Freelance", "Bonus", "Investasi", "Transfer Masuk", "Lainnya"
]

CAT_COLORS = {
    "Makanan & Minuman":  "#E24B4A",
    "Belanja Online":     "#BA7517",
    "Transportasi":       "#3266ad",
    "Tagihan & Utilitas": "#7F77DD",
    "Kesehatan":          "#D4537E",
    "Hiburan":            "#1D9E75",
    "Pendidikan":         "#639922",
    "Investasi":          "#0F6E56",
    "Lainnya":            "#73726c",
    "Gaji":               "#1D9E75",
    "Freelance":          "#3266ad",
    "Bonus":              "#BA7517",
    "Transfer Masuk":     "#7F77DD",
}

EXTRA_PALETTE = [
    "#E53E3E","#319795","#38A169","#1A365D","#ED8936",
    "#9F7AEA","#4FD1C5","#667EEA","#FC8181","#63B3ED",
]

def get_cat_color(cat, idx=0):
    return CAT_COLORS.get(cat, EXTRA_PALETTE[idx % len(EXTRA_PALETTE)])

# ─── STORAGE ──────────────────────────────────────────────────────────────────
def ensure_dir():
    os.makedirs("data", exist_ok=True)

def load_json(path, default):
    ensure_dir()
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)

def save_json(path, obj):
    ensure_dir()
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)

def load_transactions():  return load_json(DATA_FILE, [])
def save_transactions(v): save_json(DATA_FILE, v)
def load_salaries():      return load_json(SALARY_FILE, {})
def save_salaries(v):     save_json(SALARY_FILE, v)
def load_notes():         return load_json(NOTES_FILE, [])
def save_notes(v):        save_json(NOTES_FILE, v)

def load_categories():
    cats = load_json(CATEGORIES_FILE, {
        "expense": list(DEFAULT_EXPENSE_CATS),
        "income":  list(DEFAULT_INCOME_CATS)
    })
    for c in DEFAULT_EXPENSE_CATS:
        if c not in cats["expense"]: cats["expense"].append(c)
    for c in DEFAULT_INCOME_CATS:
        if c not in cats["income"]: cats["income"].append(c)
    return cats

def save_categories(v): save_json(CATEGORIES_FILE, v)
def month_key(y, m):    return f"{y}-{str(m).zfill(2)}"

# ─── AUTH ─────────────────────────────────────────────────────────────────────
def check_auth():
    try:    correct_pin = str(st.secrets["PIN"])
    except: correct_pin = "1234"

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("## 💰 Dompet Digital")
        st.markdown("Masukkan PIN untuk masuk.")
        pin = st.text_input("PIN", type="password", max_chars=8, key="pin_input")
        if st.button("Masuk", use_container_width=True):
            if pin == correct_pin:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("PIN salah!")
    return False

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def fmt_rp(n):
    return f"Rp {int(n):,}".replace(",", ".")

def get_month_txs(txs, year, month):
    key = month_key(year, month)
    return [t for t in txs if t["date"].startswith(key)]

def to_df(txs):
    if not txs:
        return pd.DataFrame(columns=["id","type","amount","category","date","desc"])
    return pd.DataFrame(txs)

def export_excel(df_exp, df_inc):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df_exp.to_excel(w, sheet_name="Pengeluaran", index=False)
        df_inc.to_excel(w, sheet_name="Pemasukan",   index=False)
    return buf.getvalue()

def build_color_map(cat_list):
    return {cat: get_cat_color(cat, i) for i, cat in enumerate(cat_list)}

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    if not check_auth():
        return

    cats = load_categories()

    with st.sidebar:
        st.markdown("## 💰 Dompet Digital")
        st.markdown("---")
        page = st.radio("Menu", [
            "📊 Rekap Bulan Ini",
            "➕ Catat Transaksi",
            "📋 Riwayat",
            "📈 Analisis",
            "📉 Saldo Berjalan",
            "🧮 Kalkulator Nabung",
            "📝 Catatan & Reminder",
            "🏷️ Kelola Kategori",
        ], label_visibility="collapsed")

        st.markdown("---")
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

    txs       = load_transactions()
    salaries  = load_salaries()
    mk        = month_key(sel_year, sel_month)
    month_txs = get_month_txs(txs, sel_year, sel_month)

    salary_val    = salaries.get(mk, 0)
    total_income  = sum(t["amount"] for t in month_txs if t["type"] == "income") + salary_val
    total_expense = sum(t["amount"] for t in month_txs if t["type"] == "expense")
    saldo         = total_income - total_expense

    # ══ REKAP ═════════════════════════════════════════════════════════════════
    if page == "📊 Rekap Bulan Ini":
        st.markdown(f"## 📊 Rekap — {calendar.month_name[sel_month]} {sel_year}")

        with st.expander("💼 Set Gaji Bulan Ini", expanded=(salary_val == 0)):
            new_sal = st.number_input("Gaji Pokok (Rp)", min_value=0,
                value=int(salary_val), step=100_000, format="%d", key="salary_inp")
            if st.button("Simpan Gaji"):
                salaries[mk] = new_sal
                save_salaries(salaries)
                st.success(f"✅ Gaji disimpan: {fmt_rp(new_sal)}")
                st.rerun()

        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💚 Total Pemasukan",   fmt_rp(total_income))
        c2.metric("❤️ Total Pengeluaran", fmt_rp(total_expense))
        c3.metric("💰 Saldo Bersih",      fmt_rp(saldo))
        c4.metric("📝 Jumlah Transaksi",  len(month_txs))

        st.markdown("---")
        exp_txs = [t for t in month_txs if t["type"] == "expense"]
        cat_map = {}
        for t in exp_txs:
            cat_map[t["category"]] = cat_map.get(t["category"], 0) + t["amount"]

        color_map = build_color_map(cats["expense"])
        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown("#### 🍩 Komposisi Pengeluaran")
            if cat_map:
                fig = px.pie(
                    names=list(cat_map.keys()),
                    values=list(cat_map.values()),
                    color=list(cat_map.keys()),
                    color_discrete_map=color_map,
                    hole=0.4,
                )
                fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=320,
                                  showlegend=True,
                                  legend=dict(orientation="v", font=dict(size=11)))
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Belum ada pengeluaran bulan ini.")

        with col_r:
            st.markdown("#### 📊 Top Pengeluaran per Kategori")
            if cat_map:
                sorted_cats = sorted(cat_map.items(), key=lambda x: x[1], reverse=True)
                df_bar = pd.DataFrame(sorted_cats, columns=["Kategori", "Jumlah"])
                df_bar["color"] = df_bar["Kategori"].map(lambda c: color_map.get(c, "#73726c"))
                fig2 = px.bar(df_bar, x="Jumlah", y="Kategori", orientation="h",
                              color="Kategori", color_discrete_map=color_map,
                              text=df_bar["Jumlah"].apply(fmt_rp))
                fig2.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=320,
                                   showlegend=False,
                                   yaxis=dict(categoryorder="total ascending"))
                fig2.update_traces(textposition="outside")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Belum ada data.")

        # Tren 6 bulan
        st.markdown("---")
        st.markdown("#### 📅 Tren 6 Bulan Terakhir")
        lab_6, inc_6, exp_6 = [], [], []
        for i in range(5, -1, -1):
            mi = sel_month - i; yi = sel_year
            while mi <= 0: mi += 12; yi -= 1
            k = month_key(yi, mi); tm = get_month_txs(txs, yi, mi)
            lab_6.append(f"{calendar.month_abbr[mi]} {yi}")
            inc_6.append(sum(t["amount"] for t in tm if t["type"]=="income") + salaries.get(k, 0))
            exp_6.append(sum(t["amount"] for t in tm if t["type"]=="expense"))

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Pemasukan",   x=lab_6, y=inc_6, marker_color="#1D9E75"))
        fig3.add_trace(go.Bar(name="Pengeluaran", x=lab_6, y=exp_6, marker_color="#E24B4A"))
        fig3.update_layout(barmode="group", height=300,
                           margin=dict(t=10,b=10,l=10,r=10),
                           legend=dict(orientation="h", yanchor="bottom", y=1.02))
        fig3.update_yaxes(tickformat=",")
        st.plotly_chart(fig3, use_container_width=True)

        # Export
        st.markdown("---")
        if month_txs:
            df_e = to_df([t for t in month_txs if t["type"]=="expense"])
            df_i = to_df([t for t in month_txs if t["type"]=="income"])
            st.download_button("⬇️ Export Excel Bulan Ini",
                data=export_excel(df_e, df_i),
                file_name=f"keuangan_{mk}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ══ CATAT TRANSAKSI ═══════════════════════════════════════════════════════
    elif page == "➕ Catat Transaksi":
        st.markdown("## ➕ Catat Transaksi")

        with st.form("add_tx", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                tx_type   = st.selectbox("Jenis Transaksi", ["Pengeluaran", "Pemasukan"])
                tx_amount = st.number_input("Jumlah (Rp)", min_value=1, step=1000, format="%d")
            with c2:
                cat_list = cats["expense"] if tx_type == "Pengeluaran" else cats["income"]
                tx_cat   = st.selectbox("Kategori", cat_list)
                tx_date  = st.date_input("Tanggal", value=date.today())
            tx_desc = st.text_input("Keterangan",
                placeholder="Contoh: Makan siang warteg, Gojek ke kantor, Shopee baju...")
            ok = st.form_submit_button("✅ Simpan Transaksi", use_container_width=True)

        if ok:
            txs.append({
                "id":       int(datetime.now().timestamp() * 1000),
                "type":     "expense" if tx_type == "Pengeluaran" else "income",
                "amount":   int(tx_amount),
                "category": tx_cat,
                "date":     str(tx_date),
                "desc":     tx_desc or tx_cat,
            })
            save_transactions(txs)
            st.success(f"✅ {tx_type} **{fmt_rp(tx_amount)}** — {tx_cat} berhasil disimpan!")
            st.balloons()

        st.markdown("---")
        st.markdown(f"#### Ringkasan {calendar.month_name[sel_month]} {sel_year}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Pemasukan",   fmt_rp(total_income))
        c2.metric("Pengeluaran", fmt_rp(total_expense))
        c3.metric("Saldo",       fmt_rp(saldo))

    # ══ RIWAYAT ═══════════════════════════════════════════════════════════════
    elif page == "📋 Riwayat":
        st.markdown(f"## 📋 Riwayat — {calendar.month_name[sel_month]} {sel_year}")

        if not month_txs:
            st.info("Belum ada transaksi bulan ini.")
        else:
            cf1, cf2, cf3 = st.columns(3)
            with cf1:
                ft = st.selectbox("Filter Jenis", ["Semua", "Pengeluaran", "Pemasukan"])
            with cf2:
                all_c = ["Semua"] + sorted({t["category"] for t in month_txs})
                fc = st.selectbox("Filter Kategori", all_c)
            with cf3:
                sort_by = st.selectbox("Urutkan", ["Terbaru", "Terlama", "Terbesar", "Terkecil"])

            filtered = list(month_txs)
            if ft == "Pengeluaran": filtered = [t for t in filtered if t["type"]=="expense"]
            elif ft == "Pemasukan": filtered = [t for t in filtered if t["type"]=="income"]
            if fc != "Semua":       filtered = [t for t in filtered if t["category"]==fc]

            key_map = {"Terbaru":"date","Terlama":"date","Terbesar":"amount","Terkecil":"amount"}
            rev_map = {"Terbaru":True,"Terlama":False,"Terbesar":True,"Terkecil":False}
            filtered = sorted(filtered, key=lambda x: x[key_map[sort_by]], reverse=rev_map[sort_by])

            to_del = None
            for t in filtered:
                color = "#E24B4A" if t["type"]=="expense" else "#1D9E75"
                sign  = "−" if t["type"]=="expense" else "+"
                ca, cb, cc, cd, ce = st.columns([3, 2, 1.5, 1.5, 0.4])
                ca.markdown(f"**{t['desc']}**")
                cb.markdown(f"`{t['category']}`")
                cc.markdown(f"<small style='color:gray'>{t['date']}</small>", unsafe_allow_html=True)
                cd.markdown(
                    f"<div style='text-align:right;font-weight:600;color:{color}'>"
                    f"{sign} {fmt_rp(t['amount'])}</div>",
                    unsafe_allow_html=True)
                if ce.button("🗑️", key=f"d{t['id']}"):
                    to_del = t["id"]
                st.divider()

            if to_del:
                save_transactions([t for t in txs if t["id"] != to_del])
                st.success("Transaksi dihapus.")
                st.rerun()

            st.markdown("---")
            total_shown = sum(t["amount"] for t in filtered)
            st.markdown(f"**Total: {fmt_rp(total_shown)}** dari {len(filtered)} transaksi")

            csv = to_df(filtered).to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Export CSV", data=csv,
                file_name=f"riwayat_{mk}.csv", mime="text/csv")

    # ══ ANALISIS ══════════════════════════════════════════════════════════════
    elif page == "📈 Analisis":
        st.markdown("## 📈 Analisis Keuangan")

        if not txs:
            st.info("Belum ada data transaksi.")
            return

        df = to_df(txs)
        df["date"]        = pd.to_datetime(df["date"])
        df["month"]       = df["date"].dt.to_period("M").astype(str)
        df["month_label"] = df["date"].dt.strftime("%b %Y")
        exp_all = df[df["type"] == "expense"]
        color_map = build_color_map(cats["expense"])

        st.markdown("#### Pengeluaran per Kategori — Semua Waktu")
        if not exp_all.empty:
            cat_total = exp_all.groupby("category")["amount"].sum().reset_index()
            cat_total.columns = ["Kategori", "Total"]
            cat_total = cat_total.sort_values("Total", ascending=False)
            fig = px.bar(cat_total, x="Kategori", y="Total",
                         color="Kategori", color_discrete_map=color_map,
                         text=cat_total["Total"].apply(fmt_rp))
            fig.update_layout(showlegend=False, height=340, margin=dict(t=10,b=10))
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Tren Pengeluaran per Kategori per Bulan")
        if not exp_all.empty:
            pivot = exp_all.groupby(["month","category"])["amount"].sum().reset_index()
            fig2 = px.line(pivot, x="month", y="amount", color="category",
                           color_discrete_map=color_map, markers=True)
            fig2.update_layout(height=340, margin=dict(t=10,b=10),
                               legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                           font=dict(size=10)),
                               xaxis_title="", yaxis_title="Jumlah (Rp)")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Rata-rata Pengeluaran per Bulan")
        if not exp_all.empty:
            n_months = df["month"].nunique() or 1
            avg_cat  = exp_all.groupby("category")["amount"].sum().div(n_months).reset_index()
            avg_cat.columns = ["Kategori", "Rata-rata/Bulan"]
            avg_cat = avg_cat.sort_values("Rata-rata/Bulan", ascending=False)
            avg_cat["Rata-rata per Bulan"] = avg_cat["Rata-rata/Bulan"].apply(fmt_rp)
            st.dataframe(avg_cat[["Kategori","Rata-rata per Bulan"]],
                         use_container_width=True, hide_index=True)

    # ══ SALDO BERJALAN ════════════════════════════════════════════════════════
    elif page == "📉 Saldo Berjalan":
        st.markdown("## 📉 Grafik Saldo Berjalan")
        st.caption("Visualisasi saldo kumulatif dari waktu ke waktu berdasarkan semua transaksi.")

        if not txs:
            st.info("Belum ada data transaksi.")
            return

        df = to_df(txs).copy()
        df["date"]   = pd.to_datetime(df["date"])
        df["signed"] = df.apply(
            lambda r: r["amount"] if r["type"]=="income" else -r["amount"], axis=1)
        df = df.sort_values("date")

        # Tambahkan gaji ke timeline
        sal_rows = []
        for key_str, val in salaries.items():
            if val > 0:
                try:
                    y, m = map(int, key_str.split("-"))
                    sal_rows.append({
                        "date":     pd.Timestamp(y, m, 1),
                        "signed":   val,
                        "type":     "income",
                        "category": "Gaji",
                        "desc":     "Gaji",
                        "amount":   val,
                    })
                except Exception:
                    pass
        if sal_rows:
            df = pd.concat([df, pd.DataFrame(sal_rows)], ignore_index=True)
            df = df.sort_values("date")

        df["saldo_kumulatif"] = df["signed"].cumsum()

        # Filter rentang
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            range_opt = st.selectbox("Rentang Waktu", ["3 Bulan", "6 Bulan", "1 Tahun", "Semua"])
        range_map = {"3 Bulan": 3, "6 Bulan": 6, "1 Tahun": 12}
        if range_opt != "Semua":
            cutoff = pd.Timestamp.now() - pd.DateOffset(months=range_map[range_opt])
            df_plot = df[df["date"] >= cutoff]
        else:
            df_plot = df

        if df_plot.empty:
            st.info("Tidak ada data di rentang waktu ini.")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_plot["date"],
                y=df_plot["saldo_kumulatif"],
                mode="lines+markers",
                line=dict(color="#319795", width=2.5),
                marker=dict(size=5),
                fill="tozeroy",
                fillcolor="rgba(49,151,149,0.12)",
                hovertemplate="<b>%{x|%d %b %Y}</b><br>Saldo: Rp %{y:,.0f}<extra></extra>",
            ))
            # Garis nol
            fig.add_hline(y=0, line_dash="dash", line_color="#E24B4A", line_width=1.2)
            fig.update_layout(
                height=380,
                margin=dict(t=10,b=10,l=10,r=10),
                xaxis_title="",
                yaxis_title="Saldo (Rp)",
                yaxis=dict(tickformat=","),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Summary
            last_saldo = df_plot["saldo_kumulatif"].iloc[-1]
            min_saldo  = df_plot["saldo_kumulatif"].min()
            max_saldo  = df_plot["saldo_kumulatif"].max()
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Saldo Saat Ini", fmt_rp(last_saldo))
            c2.metric("📈 Saldo Tertinggi", fmt_rp(max_saldo))
            c3.metric("📉 Saldo Terendah",  fmt_rp(min_saldo))

    # ══ KALKULATOR NABUNG ═════════════════════════════════════════════════════
    elif page == "🧮 Kalkulator Nabung":
        st.markdown("## 🧮 Kalkulator Target Nabung")
        st.caption("Hitung berapa yang harus disisihkan tiap bulan untuk mencapai target-mu.")

        tab1, tab2 = st.tabs(["🎯 Target → Cicilan", "💸 Cicilan → Hasil"])

        with tab1:
            st.markdown("#### Dari Target ke Cicilan Bulanan")
            c1, c2, c3 = st.columns(3)
            with c1:
                target    = st.number_input("🎯 Target (Rp)", min_value=0, step=100_000,
                                            format="%d", key="t1_target")
            with c2:
                sudah     = st.number_input("💼 Sudah punya (Rp)", min_value=0, step=100_000,
                                            format="%d", key="t1_sudah")
            with c3:
                bulan     = st.number_input("📅 Dalam berapa bulan?", min_value=1,
                                            max_value=360, value=12, key="t1_bulan")
            bunga_pct = st.slider("📈 Bunga/return per tahun (%)", 0.0, 20.0, 0.0,
                                  step=0.5, key="t1_bunga")

            if target > 0 and bulan > 0:
                sisa = max(target - sudah, 0)
                if bunga_pct == 0:
                    cicilan = sisa / bulan
                else:
                    r = bunga_pct / 100 / 12
                    cicilan = sisa * r / ((1 + r)**bulan - 1)

                st.markdown("---")
                ca, cb, cc = st.columns(3)
                ca.metric("💰 Sisa Target",     fmt_rp(sisa))
                cb.metric("📆 Cicilan per Bulan", fmt_rp(cicilan))
                cc.metric("📊 Total Setoran",    fmt_rp(cicilan * bulan))

                # Progress bar vs saldo bulan ini
                if saldo > 0 and cicilan > 0:
                    pct = min(saldo / cicilan * 100, 100)
                    st.markdown(f"**Saldo bulan ini** {fmt_rp(saldo)} "
                                f"{'✅' if saldo >= cicilan else '⚠️'} "
                                f"{'Cukup untuk cicilan!' if saldo >= cicilan else f'Kurang {fmt_rp(cicilan - saldo)}'}")
                    st.progress(int(pct))

        with tab2:
            st.markdown("#### Dari Cicilan ke Hasil Akhir")
            c1, c2, c3 = st.columns(3)
            with c1:
                cicilan2  = st.number_input("💸 Cicilan per bulan (Rp)", min_value=0,
                                            step=100_000, format="%d", key="t2_cicilan")
            with c2:
                modal2    = st.number_input("💼 Modal awal (Rp)", min_value=0,
                                            step=100_000, format="%d", key="t2_modal")
            with c3:
                bulan2    = st.number_input("📅 Berapa bulan?", min_value=1,
                                            max_value=360, value=12, key="t2_bulan")
            bunga2_pct = st.slider("📈 Bunga/return per tahun (%)", 0.0, 20.0, 0.0,
                                   step=0.5, key="t2_bunga")

            if cicilan2 > 0 and bulan2 > 0:
                if bunga2_pct == 0:
                    hasil = modal2 + cicilan2 * bulan2
                else:
                    r     = bunga2_pct / 100 / 12
                    fv_modal  = modal2 * (1 + r)**bulan2
                    fv_cicilan = cicilan2 * ((1 + r)**bulan2 - 1) / r
                    hasil = fv_modal + fv_cicilan

                total_setor = modal2 + cicilan2 * bulan2
                bunga_earned = hasil - total_setor

                st.markdown("---")
                ca, cb, cc = st.columns(3)
                ca.metric("🏦 Hasil Akhir",      fmt_rp(hasil))
                cb.metric("💵 Total Disetorkan", fmt_rp(total_setor))
                cc.metric("📈 Bunga Didapat",    fmt_rp(bunga_earned))

                # Proyeksi per bulan
                with st.expander("📋 Lihat Proyeksi per Bulan"):
                    rows = []
                    saldo_proj = float(modal2)
                    r = bunga2_pct / 100 / 12
                    for i in range(1, int(bulan2) + 1):
                        bunga_bln = saldo_proj * r
                        saldo_proj = saldo_proj * (1 + r) + cicilan2
                        rows.append({
                            "Bulan": i,
                            "Setoran": fmt_rp(cicilan2),
                            "Bunga":   fmt_rp(bunga_bln),
                            "Saldo":   fmt_rp(saldo_proj),
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ══ CATATAN & REMINDER ════════════════════════════════════════════════════
    elif page == "📝 Catatan & Reminder":
        st.markdown("## 📝 Catatan & Reminder")
        notes = load_notes()

        with st.form("add_note", clear_on_submit=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                note_text = st.text_input("Catatan / reminder baru",
                    placeholder="Contoh: Bayar listrik tgl 20, Cicilan motor jatuh tempo...")
            with c2:
                note_type = st.selectbox("Tipe", ["📌 Catatan", "⚠️ Penting", "✅ Selesai"])
            note_date = st.date_input("Tanggal reminder (opsional)", value=None, key="note_date")
            add_note  = st.form_submit_button("➕ Tambah Catatan", use_container_width=True)

        if add_note and note_text:
            notes.append({
                "id":    int(datetime.now().timestamp() * 1000),
                "text":  note_text,
                "type":  note_type,
                "date":  str(note_date) if note_date else "",
                "done":  False,
            })
            save_notes(notes)
            st.success("✅ Catatan ditambahkan!")
            st.rerun()

        st.markdown("---")
        if not notes:
            st.info("Belum ada catatan. Tambahkan reminder tagihan, target, atau catatan penting.")
        else:
            # Pisah: belum selesai & selesai
            active = [n for n in notes if not n.get("done")]
            done   = [n for n in notes if n.get("done")]

            if active:
                st.markdown(f"**Aktif ({len(active)})**")
                to_done = None; to_del_n = None
                for n in active:
                    c1, c2, c3 = st.columns([5, 1, 0.6])
                    date_str = f" · 📅 {n['date']}" if n.get("date") else ""
                    c1.markdown(f"{n['type']} **{n['text']}**"
                                f"<small style='color:gray'>{date_str}</small>",
                                unsafe_allow_html=True)
                    if c2.button("✅ Done", key=f"dn{n['id']}"):
                        to_done  = n["id"]
                    if c3.button("🗑️", key=f"dn2{n['id']}"):
                        to_del_n = n["id"]

                if to_done:
                    for n in notes:
                        if n["id"] == to_done: n["done"] = True
                    save_notes(notes); st.rerun()
                if to_del_n:
                    save_notes([n for n in notes if n["id"] != to_del_n])
                    st.rerun()

            if done:
                with st.expander(f"✅ Selesai ({len(done)})"):
                    to_del_done = None
                    for n in done:
                        c1, c2 = st.columns([6, 0.6])
                        c1.markdown(f"~~{n['text']}~~")
                        if c2.button("🗑️", key=f"dd{n['id']}"): to_del_done = n["id"]
                    if to_del_done:
                        save_notes([n for n in notes if n["id"] != to_del_done])
                        st.rerun()

    # ══ KELOLA KATEGORI ═══════════════════════════════════════════════════════
    elif page == "🏷️ Kelola Kategori":
        st.markdown("## 🏷️ Kelola Kategori")
        st.info("Tambah kategori custom sesuai kebutuhanmu. Kategori default 🔒 tidak bisa dihapus.")

        for kind, label in [("expense","Pengeluaran"), ("income","Pemasukan")]:
            st.markdown(f"#### {label}")
            ca, cb = st.columns([3, 1])
            with ca:
                new_cat = st.text_input(f"Nama kategori baru ({label})",
                    key=f"nc_{kind}", placeholder="Contoh: BPJS, Cicilan, Arisan...")
            with cb:
                st.write(""); st.write("")
                if st.button("➕ Tambah", key=f"add_{kind}"):
                    if new_cat and new_cat not in cats[kind]:
                        cats[kind].append(new_cat)
                        save_categories(cats)
                        st.success(f"✅ '{new_cat}' ditambahkan!")
                        st.rerun()
                    elif new_cat in cats[kind]:
                        st.warning("Kategori sudah ada.")

            defaults = DEFAULT_EXPENSE_CATS if kind=="expense" else DEFAULT_INCOME_CATS
            for cat in list(cats[kind]):
                c1, c2 = st.columns([4, 1])
                is_def = cat in defaults
                c1.markdown(f"{'🔒' if is_def else '🏷️'} **{cat}**")
                if not is_def:
                    if c2.button("Hapus", key=f"del_{kind}_{cat}"):
                        cats[kind].remove(cat)
                        save_categories(cats)
                        st.rerun()
                else:
                    c2.markdown(f"<small style='color:gray'>default</small>",
                                unsafe_allow_html=True)
            st.markdown("---")


if __name__ == "__main__":
    main()
