# Dokumentasi Lengkap Sistem AI Trading (Next.js + Python MT5)

## 1. Pendahuluan
Sistem ini adalah platform **AI Trading Assistant** canggih yang menggabungkan analisis teknikal algoritma dengan kecerdasan buatan (Large Language Models) untuk memberikan sinyal trading berkualitas tinggi di pasar Forex dan Logam (Gold/Silver).

Sistem ini dirancang untuk bekerja berdampingan dengan trader, memberikan:
- Analisis pasar otomatis.
- Validasi sinyal menggunakan AI (LLM seperti Gemini/Zhipu/OpenAI).
- Manajemen risiko yang ketat dan otomatis.
- Eksekusi order langsung ke terminal MetaTrader 5 (MT5).

---

## 2. Fitur Utama

### A. Cerdas & Analitis (`Genius AI Engine`)
- **Multi-Layer Analysis**: Setiap sinyal melalui 4 tahap validasi:
  1. **Indikator Teknikal**: RSI, MACD, EMA Cross, Divergence.
  2. **Price Action**: Deteksi pola candlestick (Hammer, Engulfing, Doji, dll).
  3. **Multi-Timeframe**: Mengecek tren di H1, H4, dan D1 untuk memastikan keselarasan (confluence).
  4. **LLM Validation**: Mengirim data pasar ke AI (LLM) untuk mendapatkan "pendapat kedua" (Second Opinion) mengenai konteks pasar, sentimen, dan level kunci.

### B. Manajemen Risiko Otomatis (`Risk Manager`)
- **Penghitungan Lot Dinamis**: Tidak perlu menghitung lot manual. Sistem menghitung lot berdasarkan % risiko yang Anda tentukan (misal: 1% per trade).
- **Risk/Reward Ratio Proper**: Sistem merekomendasikan TP dan SL dengan rasio minimal 1:1.5 (dapat dikonfigurasi).
- **Proteksi Akun**: Mencegah trading jika margin bebas terlalu rendah atau drawdown harian melampaui batas.

### C. Eksekusi Langsung (`Direct Execution`)
- Terintegrasi langsung dengan **MetaTrader 5 Desktop Terminal**.
- Eksekusi order instan dengan parameter SL/TP yang presisi.
- Mendukung modifikasi order (Trailing Stop - *opsional/future dev*).

### D. Antarmuka Modern (UI/UX)
- Berbasis **Next.js** dengan tampilan responsif.
- Sidebar AI yang interaktif (Scan, Analisa, Order).
- Visualisasi data yang jelas (Grafik Confidence, Indikator Status).
- Tema Gelap/Terang (Dark Mode support).

---

## 3. Arsitektur Sistem

Sistem ini menggunakan arsitektur **Client-Server** yang terpisah namun terintegrasi:

### Frontend (User Interface)
- **Teknologi**: Next.js 14, React, Tailwind CSS, Lucide Icons.
- **Lokasi**: Folder `/src`.
- **Fungsi**: Menampilkan dashboard, sidebar sinyal, grafik performa, dan pengaturan.
- **Komponen Kunci**:
  - `AiSidebar.tsx`: Pusat kontrol utama (Scan Sinyal, Tab Analisis, Tab Order).
  - `SettingsModal.tsx`: Konfigurasi API Key, Risiko, dan Preferensi.
  - `api.ts`: Jembatan komunikasi ke Backend.

### Backend (Logic Core)
- **Teknologi**: Python 3.10+, FastAPI, MetaTrader5 Python API.
- **Lokasi**: Folder `/backend`.
- **Fungsi**: Memproses data pasar, menjalankan algoritma trading, menghubungi API LLM.
- **Komponen Kunci**:
  - `main.py`: Entry point server API.
  - `mt5/connector.py`: Mengelola koneksi ke terminal MT5 (Login, Data Fetching, Order).
  - `ai/genius_ai.py`: Mesin analisis utama (Teknikal + Pattern).
  - `ai/ai_service.py`: Integrasi dengan LLM Provider (ZhipuAI, Gemini, OpenAI).
  - `ai/risk_manager.py`: Logika penghitungan posisi dan risiko.
  - `api/routes/signals.py`: Endpoint API untuk frontend.

---

## 4. Panduan Instalasi & Menjalankan

### Prasyarat
1. **MetaTrader 5 (MT5)** Desktop Terminal terinstal dan login ke akun broker.
2. **Python** (versi 3.10 atau lebih baru).
3. **Node.js** (versi 18 atau lebih baru).

### Langkah 1: Persiapan Backend
1. Buka terminal, masuk ke folder backend: `cd backend`
2. Buat virtual environment (opsional tapi disarankan):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Mac/Linux
   venv\Scripts\activate     # Windows
   ```
3. Instal dependensi:
   ```bash
   pip install -r requirements.txt
   ```
   *(Pastikan `MetaTrader5`, `fastapi`, `uvicorn`, `httpx`, `pandas`, `ta-lib` atau `pandas-ta` terinstal)*.

### Langkah 2: Persiapan Frontend
1. Buka terminal baru, masuk ke root folder project.
2. Instal dependensi Node.js:
   ```bash
   npm install
   ```

### Langkah 3: Menjalankan Sistem
1. **Pastikan MT5 Terbuka**: Buka aplikasi MT5 dan pastikan tombol "Algo Trading" aktif (Hijau).
2. **Jalankan Backend**:
   Di terminal backend:
   ```bash
   python main.py
   ```
   *Server akan berjalan di `http://localhost:8000`*.
   
3. **Jalankan Frontend**:
   Di terminal root:
   ```bash
   npm run dev
   ```
   *Web akan berjalan di `http://localhost:3000`*.

---

## 5. Panduan Penggunaan (User Manual)

### A. Konfigurasi Awal
1. Buka web di browser.
2. Klik ikon **Settings** (Gerigi) di pojok Sidebar.
3. **Trading Settings**:
   - **Lot Size**: Base lot (default 0.01).
   - **Risk Percent**: Persentase risiko per trade (saran: 1% atau 2%).
   - **Risk Reward**: Target minimal (saran: 1.5 atau 2).
4. **AI Settings**:
   - **AI Provider**: Pilih provider (misal: ZAI / ZhipuAI).
   - **API Key**: Masukkan API Key dari provider tersebut.
   - Klik "Save".

### B. Mencari Sinyal (Scanning)
1. Di Sidebar, pilih tab **"Sinyal"**.
2. Klik tombol **"Scan Sinyal"**.
3. Sistem akan memindai pair aktif di Market Watch MT5 Anda.
4. Daftar sinyal potensial akan muncul, diurutkan berdasarkan skor kepercayaan (Confidence %).

### C. Analisis Mendalam
1. Klik salah satu kartu sinyal di daftar.
2. Sistem akan pindah ke tab **"Analis"**.
3. Periksa panel-panel informasi:
   - **Technical**: Lihat status RSI, MACD, dan EMA. Pastikan tren mendukung arah sinyal.
   - **Patterns**: Lihat apakah ada pola candlestick yang terdeteksi.
   - **AI Insight**: Baca pendapat AI. Apakah AI setuju dengan sinyal teknikal? Perhatikan peringatan risiko (Risk Warning) jika ada.
   - **Support/Resistance**: Level - level kunci yang terdeteksi.

### D. Eksekusi Trade
1. Jika Anda yakin, pindah ke tab **"Order"**.
2. Sistem menampilkan kalkulasi detil:
   - **Entry Price**.
   - **Stop Loss (SL)**: Dihitung otomatis berdasarkan Support/Resistance.
   - **Take Profit (TP)**: Dihitung otomatis berdasarkan Risk:Reward ratio.
   - **Lot Size**: Dihitung otomatis agar risiko loss sesuai settingan (misal 1%).
3. Klik tombol **"Place Order"**.
4. Order akan terkirim ke MT5 dalam hitungan milidetik. Tiket order akan muncul sebagai konfirmasi.

---

## 6. Troubleshooting (Pemecahan Masalah)

### Masalah: "MT5 Not Connected"
- **Penyebab**: Aplikasi MT5 tertutup, atau library Python tidak bisa menemukannya.
- **Solusi**: 
  1. Buka aplikasi MT5.
  2. Pastikan file `backend/.env` (jika ada) menunjuk ke path `terminal64.exe` yang benar jika tidak terdeteksi otomatis.
  3. Cek log di terminal backend.

### Masalah: "AI Error / Tidak Ada Hasil"
- **Penyebab**: API Key salah, saldo API habis, atau koneksi internet bermasalah.
- **Solusi**:
  1. Cek kembali API Key di menu Settings.
  2. Pastikan Anda memiliki kuota/kredit di provider AI (OpenAI/Zhipu/dll).
  3. Cek log backend untuk melihat pesan error spesifik (misal: "401 Unauthorized").

### Masalah: "Risk Calculation Salah / Lot Size Aneh"
- **Penyebab**: Saldo akun terlalu kecil untuk risiko 1% (terbentur minimal lot 0.01).
- **Solusi**:
  - Jika saldo < $100, lot 0.01 mungkin merepresentasikan risiko > 1%. Ini normal karena batasan broker.
  - Tambah modal atau terima risiko minimal tersebut.

### Masalah: "Tidak Ada Sinyal Ditemukan"
- **Penyebab**: Pasar sedang sepi (konsolidasi) atau Market Watch di MT5 hanya menampilkan sedikit simbol.
- **Solusi**:
  1. Tambahkan lebih banyak simbol (Forex Majors, Gold) ke Market Watch di MT5.
  2. Coba scan lagi di jam pasar sibuk (Sesi London/New York).

---

## 7. Pengembangan Lanjutan (Developer Notes)

Jika Anda ingin mengembangkan sistem ini lebih lanjut:
- **Menambah AI Provider**: Edit `backend/ai/ai_service.py` dan tambahkan kelas provider baru.
- **Mengubah Indikator Teknikal**: Edit `backend/ai/genius_ai.py` di method `_technical_analysis`.
- **Menambah Pair Khusus**: Edit `backend/mt5/connector.py` untuk normalisasi simbol broker (misal: penanganan suffix `.pro` atau `.m`).

---

**Dibuat oleh Tim Pengembang AI Trading Assistant**
*Versi Dokumen: 1.0 - Februari 2026*
