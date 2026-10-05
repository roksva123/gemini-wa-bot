# Demo & Development Scripts

Berikut adalah script untuk testing dan development.

## Setup & Installation

- **run.sh** - Setup script untuk Linux/Mac
- **run.ps1** - Setup script untuk Windows PowerShell
- **quickstart.py** - Interactive Python setup

Jalankan salah satu dari script di atas untuk:
1. Create virtual environment
2. Install dependencies
3. Validate database connection
4. Configure .env file

## Testing & Demo

- **quick_demo.sh** - Interactive demo untuk Linux/Mac (dengan template selection)
- **quick_demo.bat** - Interactive demo untuk Windows

Script ini akan memandu untuk:
1. Memilih template bisnis (Phone Repair, E-Commerce, atau Custom)
2. Edit test case dengan data Anda
3. Jalankan tests terhadap bot
4. Generate dan buka HTML report

## Files

- **requirements_demo.txt** - Demo-specific dependencies (PyYAML, httpx)

Semua script ini adalah untuk development/demo saja. Untuk production, gunakan:
- Docker (Dockerfile ada di root)
- Render deployment (render.yaml)
- Manual: `python main.py` atau `uvicorn main:app`
