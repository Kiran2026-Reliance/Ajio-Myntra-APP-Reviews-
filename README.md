# Ajio vs Myntra — Review Dashboard

> Self-refreshing dashboard that scrapes Play Store + App Store reviews daily and deploys automatically to a shareable URL.

---

## 🚀 Setup (5 minutes)

### Step 1 — Push to GitHub

Create a new repository on GitHub, then push:

```bash
unzip dashboard-repo.zip
cd dashboard-repo
git init
git add .
git commit -m "initial setup"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

### Step 2 — Enable GitHub Pages (via GitHub Actions)

1. Go to your repo → **Settings** → **Pages**
2. Under **Source**, select **"GitHub Actions"** *(not "Deploy from a branch")*
3. Click **Save** — that's it, no branch selection needed

> ⚠️ This is the key difference from "Deploy from branch" — you won't see a branch dropdown, just select "GitHub Actions" as the source.

---

### Step 3 — Run the workflow for the first time

1. Go to the **Actions** tab in your repo
2. Click **"Daily Dashboard Refresh"** in the left sidebar
3. Click **"Run workflow"** → **"Run workflow"** (green button)

Wait ~15 minutes. The workflow will:
1. Scrape all reviews since March 2025
2. Process and categorise them
3. Build `index.html`
4. Deploy to GitHub Pages automatically

---

### Step 4 — Get your shareable link

After the workflow completes, your dashboard is live at:

```
https://YOUR_USERNAME.github.io/YOUR_REPO/
```

Share this URL with your internal team. Password: **AjioMyntra@2025**

---

## 🔄 How daily refresh works

The workflow runs every day at **6:00 AM IST** automatically:

```
Scrape → Process → Build → Deploy  (same URL, fresh data)
```

The "Last Refresh" timestamp in the dashboard header updates on every run.

---

## 🔑 Change the password

Open `scripts/template.html`, search for `AjioMyntra@2025` and replace with your password.

---

## 📁 File Structure

```
├── .github/workflows/daily-refresh.yml   ← Cron + deploy automation
├── scripts/
│   ├── scrape.py       ← Fetches Play Store + App Store reviews
│   ├── process.py      ← Categories, sentiment, aggregation
│   ├── build.py        ← Builds index.html from template
│   └── template.html   ← Dashboard UI
├── data/               ← Generated data (committed to repo)
├── index.html          ← Built dashboard (served by Pages)
└── requirements.txt
```
