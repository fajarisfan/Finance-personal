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

DATA_FILE       = "data/transactions.json"
SALARY_FILE     = "data/salaries.json"
CUSTOM_CAT_FILE = "data/custom_categories.json"

DEFAULT_EXPENSE_CATEGORIES = [
    "Makanan & Minuman", "Belanja Online", "Transportasi",
    "Tagihan & Utilitas", "Kesehatan", "Hiburan",
    "Pendidikan", "Investasi", "Lainnya"
]
DEFAULT_INCOME_CATEGORIES = [
    "Gaji", "Freelance", "Bonus", "Investasi",
    "Transfer Masuk", "Lainnya"
]

BASE_CAT_COLORS = {
    "Makanan & Minuman": "#E24B4A",
    "Belanja Online":    "#BA7517",
    "Transportasi":      "#3266ad",
    "Tagihan & Utilitas":"#7F77DD",
    "Kesehatan":         "#D4537E",
    "Hiburan":           "#1D9E75",
    "Pendidikan":        "#639922",
    "Investasi":         "#0F6E56",
    "Lainnya":           "#73726c",
    "Gaji":              "#1D9E75",
    "Freelance":         "#3266ad",
    "Bonus":             "#BA7517",
    "Transfer Masuk":    "#7F77DD",
}

# Warna tambahan untuk kategori custom (pool warna yang cukup bervariasi)
EXTRA_COLORS = [
    "#E67E22", "#9B59B6", "#2ECC71", "#E74C3C", "#1ABC9C",
    "#F39C12", "#8E44AD", "#27AE60", "#C0392B", "#16A085",
    "#D35400", "#7D3C98", "#1E8449", "#922B21", "#148F77",
    "#CA6F1E", "#6C3483", "#196F3D", "#7B241C", "#117A65",
]


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

def load_custom_categories():
    ensure_dir()
    if not os.path.exists(CUSTOM_CAT_FILE):
        return {"expense": [], "income": []}
    with open(CUSTOM_CAT_FILE, "r") as f:
        data = json.load(f)
    # pastikan kedua key ada
    data.setdefault("expense", [])
    data.setdefault("income", [])
    return data

def save_custom_categories(cats):
    ensure_dir()
    with open(CUSTOM_CAT_FILE, "w") as f:
        json.dump(cats, f, indent=2)

def get_all_expense_categories(custom):
    return DEFAULT_EXPENSE_CATEGORIES + [c for c in custom["expense"] if c not in DEFAULT_EXPENSE_CATEGORIES]

def get_all_income_categories(custom):
    return DEFAULT_INCOME_CATEGORIES + [c for c in custom["income"] if c not in DEFAULT_INCOME_CATEGORIES]

def get_cat_colors(custom):
    colors = dict(BASE_CAT_COLORS)
    all_custom = custom["expense"] + custom["income"]
    color_idx = 0
    for cat in all_custom:
        if cat not in colors:
            colors[cat] = EXTRA_COLORS[color_idx % len(EXTRA_COLORS)]
            color_idx += 1
    return colors

def month_key(y, m):
    return f"{y}-{str(m).zfill(2)}"


# ─── AUTH ─────────────────────────────────────────────────────────────────────
def check_auth():
    try:
        correct_pin = str(st.secrets["PIN"])
    except Exception:
        correct_pin = "1234"

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

    custom = load_custom_categories()
    CAT_COLORS = get_cat_colors(custom)
    EXPENSE_CATEGORIES = get_all_expense_categories(custom)
    INCOME_CATEGORIES  = get_all_income_categories(custom)
    
    BULAN_INDO = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni", 7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}

    # ── Sidebar navigation ──
    with st.sidebar:
        st.markdown("## 💰 Dompet Digital")
        st.markdown("---")
        page = st.radio(
            "Menu",
            ["📊 Rekap Bulan Ini", "➕ Catat Transaksi", "📋 Riwayat", "📈 Analisis", "🏷️ Kelola Kategori"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("**Periode**")
        now = datetime.now()
        sel_year  = st.selectbox("Tahun", list(range(now.year - 2, now.year + 1))[::-1], index=0)
        sel_month = st.selectbox("Bulan", list(range(1, 13)),
                                 index=now.month - 1,
                                 format_func=lambda m: BULAN_INDO[m])
        st.markdown("---")
        if st.button("🚪 Keluar", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    txs = load_transactions()
    salaries = load_salaries()
    mk = month_key(sel_year, sel_month)
    month_txs = get_month_txs(txs, sel_year, sel_month)

    salary_val    = salaries.get(mk, 0)
    total_income  = sum(t["amount"] for t in month_txs if t["type"] == "income") + salary_val
    total_expense = sum(t["amount"] for t in month_txs if t["type"] == "expense")
    saldo         = total_income - total_expense

    # ═══════════════════════════════════════════════════
    # PAGE: REKAP
    # ═══════════════════════════════════════════════════
    if page == "📊 Rekap Bulan Ini":
        st.markdown(f"## 📊 Rekap — {BULAN_INDO[sel_month]} {sel_year}")

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
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💚 Pemasukan",  fmt_rp(total_income))
        c2.metric("❤️ Pengeluaran", fmt_rp(total_expense))
        c3.metric("💰 Saldo",      fmt_rp(saldo), delta=fmt_rp(saldo - salary_val) if salary_val else None)
        c4.metric("📝 Transaksi",  len(month_txs))

        st.markdown("---")
        col_left, col_right = st.columns([1, 1])

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
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=300,
                    showlegend=True,
                    legend=dict(orientation="v", font=dict(size=11)),
                )
                # Tampilkan nama kategori + persen di dalam slice
                fig.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                    hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Belum ada pengeluaran bulan ini.")

        with col_right:
            st.markdown("#### Top Pengeluaran")
            if exp_txs:
                cat_map = {}
                for t in exp_txs:
                    cat_map[t["category"]] = cat_map.get(t["category"], 0) + t["amount"]
                sorted_cats = sorted(cat_map.items(), key=lambda x: x[1], reverse=True)
                df_bar = pd.DataFrame(sorted_cats, columns=["Kategori", "Jumlah"])

                fig2 = px.bar(
                    df_bar, x="Jumlah", y="Kategori", orientation="h",
                    color="Kategori", color_discrete_map=CAT_COLORS,
                    text=df_bar["Jumlah"].apply(fmt_rp),
                )
                fig2.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=300,
                    showlegend=False,
                    yaxis=dict(
                        categoryorder="total ascending",
                        title="",           # hilangkan judul sumbu Y
                        tickfont=dict(size=11),
                    ),
                    xaxis=dict(
                        title="",
                        tickformat=",",
                    ),
                )
                fig2.update_traces(
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>%{x:,.0f}<extra></extra>",
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Belum ada data.")

        # Tren 6 bulan
        st.markdown("---")
        st.markdown("#### Tren 6 Bulan Terakhir")
        months_6, inc_6, exp_6, lab_6 = [], [], [], []
        for i in range(5, -1, -1):
            ref   = datetime(sel_year, sel_month, 1)
            m_idx = ref.month - i
            y_idx = ref.year
            while m_idx <= 0:
                m_idx += 12; y_idx -= 1
            while m_idx > 12:
                m_idx -= 12; y_idx += 1
            k       = month_key(y_idx, m_idx)
            t_month = get_month_txs(txs, y_idx, m_idx)
            inc     = sum(t["amount"] for t in t_month if t["type"] == "income") + salaries.get(k, 0)
            exp     = sum(t["amount"] for t in t_month if t["type"] == "expense")
            lab_6.append(f"{BULAN_INDO[m_idx][:3]} {y_idx}")
            inc_6.append(inc); exp_6.append(exp)

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Pemasukan",   x=lab_6, y=inc_6, marker_color="#1D9E75",
                              hovertemplate="<b>%{x}</b><br>Pemasukan: Rp %{y:,.0f}<extra></extra>"))
        fig3.add_trace(go.Bar(name="Pengeluaran", x=lab_6, y=exp_6, marker_color="#E24B4A",
                              hovertemplate="<b>%{x}</b><br>Pengeluaran: Rp %{y:,.0f}<extra></extra>"))
        fig3.update_layout(
            barmode="group", height=280,
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis=dict(title=""),
            yaxis=dict(title="", tickformat=","),
        )
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

        # Load custom fresh supaya kategori baru langsung muncul
        custom_fresh   = load_custom_categories()
        exp_cats_fresh = get_all_expense_categories(custom_fresh)
        inc_cats_fresh = get_all_income_categories(custom_fresh)

        # tx_type di luar form agar selectbox Kategori bisa update dinamis.
        # Di dalam st.form nilai widget lain tidak terbaca sebelum submit,
        # akibatnya cats selalu fallback ke EXPENSE_CATEGORIES.
        tx_type = st.selectbox("Jenis Transaksi", ["Pengeluaran", "Pemasukan"])
        cats    = exp_cats_fresh if tx_type == "Pengeluaran" else inc_cats_fresh

        with st.form("add_tx_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                tx_amount = st.number_input("Jumlah (Rp)", min_value=1, step=1000, format="%d")
                tx_date   = st.date_input("Tanggal", value=date.today())
            with col2:
                tx_cat  = st.selectbox("Kategori", cats)
                tx_desc = st.text_input(
                    "Keterangan",
                    placeholder="Contoh: Makan siang warteg, Gaji Mei, ..."
                )
            submitted = st.form_submit_button("✅ Simpan Transaksi", use_container_width=True)

        if submitted:
            new_tx = {
                "id":       int((datetime.now().timestamp() + 25200) * 1000),
                "type":     "expense" if tx_type == "Pengeluaran" else "income",
                "amount":   int(tx_amount),
                "category": tx_cat,
                "date":     str(tx_date),
                "desc":     tx_desc or tx_cat,
            }
            txs.append(new_tx)
            save_transactions(txs)
            st.success(f"✅ Transaksi disimpan! {tx_type} {fmt_rp(tx_amount)} — {tx_cat}")
            st.balloons()

        st.markdown("---")
        st.markdown(f"#### Ringkasan {BULAN_INDO[sel_month]} {sel_year}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Pemasukan",  fmt_rp(total_income))
        c2.metric("Pengeluaran",fmt_rp(total_expense))
        c3.metric("Saldo",      fmt_rp(saldo))

    # ═══════════════════════════════════════════════════
    # PAGE: RIWAYAT
    # ═══════════════════════════════════════════════════
    elif page == "📋 Riwayat":
        st.markdown(f"## 📋 Riwayat — {BULAN_INDO[sel_month]} {sel_year}")

        if not month_txs:
            st.info("Belum ada transaksi bulan ini.")
        else:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_type = st.selectbox("Filter Jenis", ["Semua", "Pengeluaran", "Pemasukan"])
            with col_f2:
                all_cats   = list({t["category"] for t in month_txs})
                filter_cat = st.selectbox("Filter Kategori", ["Semua"] + sorted(all_cats))

            filtered = month_txs
            if filter_type == "Pengeluaran":
                filtered = [t for t in filtered if t["type"] == "expense"]
            elif filter_type == "Pemasukan":
                filtered = [t for t in filtered if t["type"] == "income"]
            if filter_cat != "Semua":
                filtered = [t for t in filtered if t["category"] == filter_cat]

            filtered_sorted = sorted(filtered, key=lambda x: x["date"], reverse=True)

            to_delete = None
            for t in filtered_sorted:
                col_a, col_b, col_c, col_d, col_e = st.columns([2, 1.5, 1.5, 1, 0.4])
                col_a.markdown(
                    f"**{t['desc']}**  \n<small style='color:gray'>{t['category']} · {t['date']}</small>",
                    unsafe_allow_html=True
                )
                col_b.write("")
                col_c.markdown(
                    f"<span style='color:{'#E24B4A' if t['type']=='expense' else '#1D9E75'};font-weight:600'>"
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

            df_all = to_df(filtered_sorted)
            csv    = df_all.to_csv(index=False).encode("utf-8")
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
        df["date"]        = pd.to_datetime(df["date"])
        df["month"]       = df["date"].dt.to_period("M").astype(str)
        df["month_label"] = df["date"].dt.strftime("%b %Y")

        st.markdown("#### Pengeluaran per Kategori (Semua Waktu)")
        exp_all = df[df["type"] == "expense"]
        if not exp_all.empty:
            cat_total = exp_all.groupby("category")["amount"].sum().reset_index()
            cat_total.columns = ["Kategori", "Total"]
            cat_total = cat_total.sort_values("Total", ascending=False)

            fig = px.bar(
                cat_total, x="Kategori", y="Total",
                color="Kategori", color_discrete_map=CAT_COLORS,
                text=cat_total["Total"].apply(fmt_rp),
            )
            fig.update_layout(
                showlegend=False, height=320,
                margin=dict(t=10, b=10),
                xaxis=dict(title="", tickfont=dict(size=11)),
                yaxis=dict(title="", tickformat=","),
            )
            fig.update_traces(
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>%{y:,.0f}<extra></extra>",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Tren Pengeluaran per Kategori per Bulan")
        if not exp_all.empty:
            pivot = exp_all.groupby(["month", "category"])["amount"].sum().reset_index()
            # Pastikan semua kategori mendapat warna — fallback ke abu-abu jika tidak ada di map
            all_cats_in_pivot = pivot["category"].unique().tolist()
            color_map_safe    = {c: CAT_COLORS.get(c, "#73726c") for c in all_cats_in_pivot}

            fig2 = px.line(
                pivot, x="month", y="amount", color="category",
                color_discrete_map=color_map_safe,
                markers=True,
                labels={"month": "", "amount": "Jumlah (Rp)", "category": "Kategori"},
            )
            fig2.update_layout(
                height=320,
                margin=dict(t=10, b=10),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02,
                    font=dict(size=10),
                    title_text="",
                ),
                xaxis=dict(title="", tickfont=dict(size=11)),
                yaxis=dict(title="Jumlah (Rp)", tickformat=","),
            )
            fig2.update_traces(
                hovertemplate="<b>%{fullData.name}</b><br>%{x}<br>Rp %{y:,.0f}<extra></extra>",
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### Rata-rata Pengeluaran per Bulan")
        if not exp_all.empty:
            n_months = df["month"].nunique() or 1
            avg_cat  = exp_all.groupby("category")["amount"].sum().div(n_months).reset_index()
            avg_cat.columns = ["Kategori", "Rata-rata/Bulan"]
            avg_cat = avg_cat.sort_values("Rata-rata/Bulan", ascending=False)
            avg_cat["Rata-rata per Bulan"] = avg_cat["Rata-rata/Bulan"].apply(fmt_rp)
            st.dataframe(
                avg_cat[["Kategori", "Rata-rata per Bulan"]],
                use_container_width=True,
                hide_index=True,
            )

    # ═══════════════════════════════════════════════════
    # PAGE: KELOLA KATEGORI
    # ═══════════════════════════════════════════════════
    elif page == "🏷️ Kelola Kategori":
        st.markdown("## 🏷️ Kelola Kategori")
        st.caption("Kategori bawaan tidak bisa dihapus. Kamu bisa tambah atau hapus kategori custom di sini.")

        # Selalu load fresh dari file di sini
        custom = load_custom_categories()
        CAT_COLORS_fresh = get_cat_colors(custom)

        # Pakai selectbox bukan st.tabs — st.tabs + st.form ada known bug di Streamlit
        # di mana form di tab non-aktif tidak ter-submit dengan benar
        jenis_kat = st.radio(
            "Pilih jenis kategori",
            ["💸 Pengeluaran", "💵 Pemasukan"],
            horizontal=True,
            label_visibility="collapsed",
        )

        st.markdown("---")

        if jenis_kat == "💸 Pengeluaran":
            st.markdown("**Kategori bawaan**")
            cols = st.columns(3)
            for i, cat in enumerate(DEFAULT_EXPENSE_CATEGORIES):
                color = CAT_COLORS_fresh.get(cat, "#73726c")
                cols[i % 3].markdown(
                    f"<span style='background:{color}22;color:{color};"
                    f"padding:4px 10px;border-radius:6px;font-size:13px;"
                    f"border:1px solid {color}55'>{cat}</span>",
                    unsafe_allow_html=True
                )

            st.markdown("---")
            st.markdown("**Kategori custom**")
            if not custom["expense"]:
                st.info("Belum ada kategori custom untuk Pengeluaran.")
            else:
                to_del_exp = None
                for cat in custom["expense"]:
                    color = CAT_COLORS_fresh.get(cat, "#73726c")
                    c1, c2 = st.columns([5, 1])
                    c1.markdown(
                        f"<span style='background:{color}22;color:{color};"
                        f"padding:4px 10px;border-radius:6px;font-size:13px;"
                        f"border:1px solid {color}55'>{cat}</span>",
                        unsafe_allow_html=True
                    )
                    if c2.button("Hapus", key=f"del_exp_{cat}"):
                        to_del_exp = cat
                if to_del_exp:
                    custom["expense"].remove(to_del_exp)
                    save_custom_categories(custom)
                    st.success(f"Kategori '{to_del_exp}' dihapus.")
                    st.rerun()

            st.markdown("---")
            with st.form("add_exp_cat_form", clear_on_submit=True):
                new_cat_exp = st.text_input("Nama kategori baru", placeholder="Contoh: Olahraga, Hobi, ...")
                if st.form_submit_button("➕ Tambah Kategori Pengeluaran"):
                    new_cat_exp = new_cat_exp.strip()
                    all_exp = get_all_expense_categories(custom)
                    if not new_cat_exp:
                        st.error("Nama kategori tidak boleh kosong.")
                    elif new_cat_exp in all_exp:
                        st.warning(f"Kategori '{new_cat_exp}' sudah ada.")
                    else:
                        custom["expense"].append(new_cat_exp)
                        save_custom_categories(custom)
                        st.success(f"Kategori '{new_cat_exp}' ditambahkan!")
                        st.rerun()

        else:  # Pemasukan
            st.markdown("**Kategori bawaan**")
            cols = st.columns(3)
            for i, cat in enumerate(DEFAULT_INCOME_CATEGORIES):
                color = CAT_COLORS_fresh.get(cat, "#73726c")
                cols[i % 3].markdown(
                    f"<span style='background:{color}22;color:{color};"
                    f"padding:4px 10px;border-radius:6px;font-size:13px;"
                    f"border:1px solid {color}55'>{cat}</span>",
                    unsafe_allow_html=True
                )

            st.markdown("---")
            st.markdown("**Kategori custom**")
            if not custom["income"]:
                st.info("Belum ada kategori custom untuk Pemasukan.")
            else:
                to_del_inc = None
                for cat in custom["income"]:
                    color = CAT_COLORS_fresh.get(cat, "#73726c")
                    c1, c2 = st.columns([5, 1])
                    c1.markdown(
                        f"<span style='background:{color}22;color:{color};"
                        f"padding:4px 10px;border-radius:6px;font-size:13px;"
                        f"border:1px solid {color}55'>{cat}</span>",
                        unsafe_allow_html=True
                    )
                    if c2.button("Hapus", key=f"del_inc_{cat}"):
                        to_del_inc = cat
                if to_del_inc:
                    custom["income"].remove(to_del_inc)
                    save_custom_categories(custom)
                    st.success(f"Kategori '{to_del_inc}' dihapus.")
                    st.rerun()

            st.markdown("---")
            with st.form("add_inc_cat_form", clear_on_submit=True):
                new_cat_inc = st.text_input("Nama kategori baru", placeholder="Contoh: Dividen, Sewa, Tabungan ...")
                if st.form_submit_button("➕ Tambah Kategori Pemasukan"):
                    new_cat_inc = new_cat_inc.strip()
                    all_inc = get_all_income_categories(custom)
                    if not new_cat_inc:
                        st.error("Nama kategori tidak boleh kosong.")
                    elif new_cat_inc in all_inc:
                        st.warning(f"Kategori '{new_cat_inc}' sudah ada.")
                    else:
                        custom["income"].append(new_cat_inc)
                        save_custom_categories(custom)
                        st.success(f"Kategori '{new_cat_inc}' ditambahkan!")
                        st.rerun()


if __name__ == "__main__":
    main()
