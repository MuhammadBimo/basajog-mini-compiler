# BasaJog Mini Compiler

Mini compiler untuk **bahasa pemrograman sederhana berbasis Bahasa Jawa** (Ngayogyakarta).
Seluruh kata kunci bahasanya memakai Bahasa Jawa — misalnya `tulis` (print), `yen` (if),
dan `baleni` (while). Dibangun dengan Python sebagai tugas mata kuliah **Teknik Kompilasi**.

```
Nama   : Muhammad Bimo Krisyono
NIM    : 231011400622
Kelas  : 06TPLP014
```

## Alur Kompilasi (6 Tahap)

| # | Tahap | File | Fungsi |
|---|-------|------|--------|
| 1 | **Lexer** | `lexer.py` | Memecah source code menjadi token |
| 2 | **Parser** | `parser.py`, `ast_nodes.py` | Menyusun token menjadi AST (pohon sintaks) |
| 3 | **Semantic** | `semantic.py`, `symbol_table.py` | Memeriksa makna: variabel, fungsi, tipe, scope |
| 4 | **Optimizer** | `optimizer.py` | Constant folding & dead code elimination |
| 5 | **Code Generator** | `code_generator.py` | Menerjemahkan AST ke pseudo-assembly |
| 6 | **Visual AST** | `visual_ast.py` | Menggambar pohon sintaks (matplotlib + networkx) |

File pendukung:
- `main.py` — menjalankan seluruh pipeline 6 tahap
- `evaluator.py` — interpreter (menjalankan program & menampilkan output asli)
- `test_compiler.py` — 15 kasus uji (program valid, error sintaks, error makna)
- `program.bj` — contoh program BasaJog

## Kata Kunci BasaJog

| BasaJog | Arti | | BasaJog | Arti |
|---------|------|---|---------|------|
| `tulis` | print | | `bali` | return |
| `takon` | input | | `bener` | true |
| `yen` | if | | `salah` | false |
| `liyane` | else | | `fungsi` | function |
| `baleni` | while | | | |

## Cara Menjalankan

Ada **2 cara**. Cara A paling cepat (tanpa install apa pun).

### Cara A — Pakai File EXE (TANPA install Python) ⭐

File `basajog.exe` sudah tersedia di repo ini (juga bisa diunduh di bagian
[**Releases**](../../releases)). Tidak perlu Python, matplotlib, atau apa pun.

1. Download / siapkan file `basajog.exe` dan `program.bj` dalam satu folder.
2. Buka terminal (CMD/PowerShell) di folder itu, lalu ketik:
   ```bat
   basajog.exe program.bj
   ```
   Atau cukup **dobel-klik** `basajog.exe` untuk mode interaktif (mengetik program langsung).

> Catatan: di akhir akan muncul jendela gambar pohon AST. Tutup jendelanya untuk mengakhiri program.

### Cara B — Dari Source Code Python

**1. Instalasi** — dobel-klik `install.bat`, atau lewat terminal:
```bat
install.bat
```
Otomatis membuat virtual environment `COM_venv` dan memasang `matplotlib` & `networkx`.

**2. Aktifkan virtual environment:**
```bat
COM_venv\Scripts\activate
```

**3. Perintah utama:**
```bat
python main.py program.bj      :: jalankan compiler penuh (6 tahap)
python evaluator.py program.bj :: jalankan interpreter (lihat output asli)
python test_compiler.py        :: jalankan 15 kasus uji
```

### Membuat ulang file EXE sendiri (opsional)
```bat
pip install pyinstaller
pyinstaller --onefile --name basajog main.py
:: hasilnya ada di folder dist\basajog.exe
```

## Contoh Program

```
dawa   = 10
amba   = 5
jembar = dawa * amba
tulis("Jembare pesagi:")
tulis(jembar)

biji = 80
yen (biji >= 75) {
    tulis("Lulus")
} liyane {
    tulis("Ngambali")
}

fungsi wuwuh(a, b) {
    bali a + b
}
tulis(wuwuh(15, 25))
```

## Kebutuhan

- Python 3.10+
- matplotlib, networkx (lihat `requirements.txt`)
