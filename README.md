# TrendTrace AI 📈

**Track trending topics. Explore news activity. Understand how trends evolve over time.**

TrendTrace AI is a web-based trend intelligence application that helps users explore topics through news coverage and available public social activity over a selected date range.

🌐 **Live Website:** https://trendtrace-ai.onrender.com

## ✨ Features

- 🔎 **Topic Search** — Search for a topic you want to explore.
- 📅 **Custom Date Range** — Select a time period for trend analysis.
- 📰 **News Coverage** — Retrieve relevant news articles using NewsAPI.
- 📊 **Activity Visualization** — View retrieved activity in a daily chart.
- 🚀 **Trend Insights** — Display first observed activity, peak activity, last observed activity, and the number of retrieved items when data is available.
- 📱 **Responsive Interface** — A dark-themed interface designed for desktop and mobile screens.

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Charts:** Chart.js
- **Data Retrieval:** NewsAPI and available public social-source integrations
- **Deployment:** Render
- **Version Control:** Git and GitHub

## ⚙️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/PulapaigariKesava/TrendTrace-AI.git
cd TrendTrace-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install flask requests python-dotenv gunicorn
```

### 4. Configure your API key

Create a `.env` file in the project root:

```env
NEWS_API_KEY=your_newsapi_key_here
```

Replace the example value with your own NewsAPI key.

**Security:** Never commit your `.env` file or publish API keys.

### 5. Start the application

```bash
python app.py
```

Open the local address displayed by Flask in your browser.

## 📌 Important Notes

- Results depend on the availability and limitations of the configured data sources.
- Social-source integrations may occasionally be unavailable.
- Trend insights are based on retrieved data and should not be interpreted as a complete measure of internet-wide popularity.
- The free hosting instance may take extra time to respond after periods of inactivity.

## 🔮 Future Improvements

- Add more reliable social-source integrations.
- Improve trend lifecycle analysis.
- Add topic comparison and richer analytics.
- Improve data collection and error handling.

## 👨‍💻 Author

**Pulapaigari Kesava**

Built as a project exploring web development, news intelligence, data visualization, and trend analysis.

---

⭐ If you find this project interesting, explore the live demo and repository!
## 📸 Project Screenshots

### Home Page
![TrendTrace AI Home Page](screenshots/home.png)

### Analytics Dashboard
![TrendTrace AI Analytics](screenshots/analytics.png)