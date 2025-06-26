# BugHunterPro - Advanced Bug Hunting Toolkit

BugHunterPro adalah toolkit powerful untuk para bug bounty hunter dan penetration tester pemula hingga lanjutan. Tool ini mampu mendeteksi berbagai macam kerentanan umum pada aplikasi web secara otomatis atau semi-otomatis.

## ✨ Fitur

* [x] XSS Scanner
* [x] SQL Injection Scanner
* [x] Local File Inclusion Scanner
* [x] IDOR Tester
* [x] Port & Service Scanner
* [x] Recon Tools (Subdomain, Directory Brute, etc)
* [x] SSTI (Server-Side Template Injection) Scanner
* [x] RCE (Remote Command Execution) Scanner
* [x] CSRF (Cross-Site Request Forgery) Detector
* [x] CORS Misconfiguration Detector
* [x] Open Redirect Detector
* [x] Output laporan ke JSON, TXT, CSV
* [x] Parameter discovery & URL crawler
* [x] Custom User-Agent, Cookies, and Proxy support

## 📁 Struktur Folder

```
BugHunterPro/
├── main.py
├── scanners/
│   ├── xss.py
│   ├── sqli.py
│   ├── lfi.py
│   ├── idor.py
│   ├── portscan.py
│   ├── ssti.py
│   ├── rce.py
│   ├── csrf.py
│   ├── cors.py
│   ├── open_redirect.py
│   └── ...
├── recon/
│   ├── subdomains.py
│   ├── dirbrute.py
│   └── ...
├── utils/
│   ├── crawler.py
│   ├── reporter.py
│   └── config.py
├── payloads/
│   └── *.txt
└── README.md
```

## ⚙️ Cara Penggunaan

### Install dependencies:

```bash
pip install -r requirements.txt
```

### Menjalankan Scanner:

* Jalankan semua scanner:

```bash
python main.py --url https://target.com --all
```

* Jalankan hanya XSS dan LFI:

```bash
python main.py --url https://target.com --xss --lfi
```

* Scan subdomain dan port:

```bash
python main.py --recon --target_host target.com
```

* Jalankan dengan opsi kustom (User-Agent, Cookies, Proxy):

```bash
python main.py --url https://target.com --xss --user_agent "MyCustomAgent" --cookies "{\"sessionid\":\"abc\"}" --proxy "http://127.0.0.1:8080"
```

* Output ke format JSON:

```bash
python main.py --url https://target.com --all --output json --output_file my_scan_report
```

### Output:

* Hasil pemindaian disimpan di folder `reports/` dalam format `.json`, `.txt`, atau `.csv`

## 🔐 Disclaimer

Tool ini dibuat hanya untuk edukasi dan legal penetration testing. Jangan gunakan tanpa izin eksplisit dari pemilik sistem.


