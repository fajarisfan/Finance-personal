# 💰 Dompet Digital — Aplikasi Keuangan Pribadi

Streamlit app buat catat pemasukan, pengeluaran, dan rekap bulanan dengan breakdown per kategori.

## Fitur
- 🔐 Login PIN (via `st.secrets`)
- 💼 Input gaji per bulan
- ➕ Catat pengeluaran & pemasukan dengan kategori
- 📊 Rekap bulanan (pie chart, bar chart, tren 6 bulan)
- 📋 Riwayat transaksi dengan filter & delete
- 📈 Analisis semua waktu per kategori
- ⬇️ Export Excel & CSV

## Cara Jalankan Lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```


> ⚠️ **Penting:** Jangan push `secrets.toml` ke GitHub (sudah ada di `.gitignore`).  
> Data transaksi tersimpan di folder `data/` — di Streamlit Cloud akan reset kalau app di-restart.  
> Untuk data permanen, bisa upgrade ke Google Sheets integration.

## Struktur
```
├── app.py
├── requirements.txt
├── .gitignore
├── .streamlit/
│   ├── config.toml      # tema gelap hijau
│   └── secrets.toml     # PIN (jangan di-commit!)
└── data/                # auto-created, disimpan lokal
    ├── transactions.json
    └── salaries.json
```
