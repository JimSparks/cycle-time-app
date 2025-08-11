# ⏱️ Cycle Time & Work Item Age (Streamlit)

Upload a Jira issue-history export (CSV/Excel) and get **cycle time** and **work item age** per issue.

- **Cycle Time** = first **Done** date − first **In Progress** date + 1 day  
- **Work Item Age** (no Done) = today − first **In Progress** date + 1 day

Expected columns (case-insensitive): `Key`, `Date of change`, `Status`, `Status [new]`

---

## 🚀 Quick Start (Local)

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Open the printed URL (usually http://localhost:8501).

---

## ☁️ Deploy on Streamlit Community Cloud (Free)

1. Push this folder to a GitHub repo (e.g., `cycle-time-app`).
2. Go to https://streamlit.io → **Sign in** with GitHub.
3. **New app** → pick your repo/branch, set `app.py` as the entrypoint.
4. **Deploy**. Done.

---

## 🐳 Run with Docker

```bash
docker build -t cycle-time-app .
docker run -p 8501:8501 cycle-time-app
```

Open http://localhost:8501

---

## 🔧 Customization

- Change timezone and status aliases in the left sidebar.
- Add more “Done” or “In Progress” terms as needed.
- The results table is downloadable as Excel.

---

## 📄 Notes

- We use **Status [new]** to detect transitions.
- Rows missing `Key` or `Date of change` are skipped.
- If your export headers differ, adjust `app.py`'s column mapping.
