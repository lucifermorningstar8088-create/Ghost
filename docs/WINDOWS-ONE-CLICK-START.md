# Ghost Windows one-click launch

## Prerequisites
- Windows 10/11
- Python 3.12 (or compatible Python 3)
- Node.js LTS with npm
- Internet access for the first dependency install

## Start
1. Extract the complete repository ZIP.
2. Double-click `setup.bat` once. It installs API and web dependencies and checks the frontend build.
3. Double-click `run.bat`. It launches the local API and React/Vite UI in separate minimized terminal windows.
4. Open `http://127.0.0.1:5173`. Swagger remains available for developers at `http://127.0.0.1:8000/docs`.

## Safety and limitations
- The launcher uses local SQLite for development migrations.
- It does not enable the LLM task worker, paid providers, social publishing, or OAuth automatically.
- A credential form is not proof that an integration is implemented. Only show Connected after a real server-side test or OAuth callback succeeds.
- Do not put provider secrets in frontend `VITE_*` variables or commit them to Git.
- These scripts have not been executed on Windows by repository automation; run setup on Windows and review any terminal error before using the system.
