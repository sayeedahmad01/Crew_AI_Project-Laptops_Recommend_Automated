# 🎯 Laptops Recommend - AI-Powered Laptop Recommendation System

A web-based application that uses **CrewAI** and **FastAPI** to recommend laptops based on student profile, budget, and technical requirements. The system scrapes data from Amazon and provides intelligent recommendations powered by multiple LLM providers.

---

## 📋 Features

- ✅ **AI-Powered Recommendations** - Uses CrewAI agents to analyze and recommend laptops
- ✅ **Multi-LLM Support** - Works with OpenAI, Google Gemini, and Kimi (via LiteLLM)
- ✅ **Dataset Management** - Data cleaning and statistical analysis tools
- ✅ **Interactive Dashboard** - Beautiful frontend for browsing and filtering laptops
- ✅ **Real-time Processing** - Fast API responses with streaming support
- ✅ **CORS Enabled** - Ready for external integrations

---

## 🛠️ Requirements

### System Requirements
- **Python** 3.8 or higher
- **Node.js** (optional, for frontend development)

### Python Dependencies

All dependencies are listed in `backend/requirements.txt`:

```
fastapi>=0.110.0           # Web framework
uvicorn>=0.28.0            # ASGI server
pandas>=2.0.0              # Data processing
crewai>=1.14.1             # AI agents framework
python-dotenv>=1.0.0       # Environment variable management
langchain-google-genai>=1.0.0  # Google Gemini integration
litellm==1.61.15           # Compatible LiteLLM release for CrewAI provider fallback
```

---

## 🚀 Installation & Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/sumitsartale4952/Crew_AI_Project-Web_scrap_data_from_amazon_and_laptops_Recommend.git
cd Laptop_Recomandation
```

### Step 2: Create a Virtual Environment (Recommended)
```bash
# Using venv
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the root directory with your API keys.

You can copy the sample template from [.env.example](.env.example):

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini Configuration
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Kimi/NVIDIA Configuration (Optional)
NVIDIA_API_KEY=your_nvidia_api_key_here
```

### Quick Start Scripts

For Windows users, the project includes ready-to-run launchers:

- [start_backend.bat](start_backend.bat) — double-click to start the backend server
- [start_backend.ps1](start_backend.ps1) — PowerShell version of the launcher
- [.env.example](.env.example) — sample environment file for API keys

---

## 📦 Project Structure

```
Laptop_Recomandation/
├── backend/
│   ├── main.py              # FastAPI main application
│   ├── crew.py              # CrewAI configuration
│   ├── data_manager.py      # Data processing utilities
│   ├── tools.py             # Custom tools for agents
│   ├── requirements.txt      # Python dependencies
│   └── test_backend.py       # Backend tests
├── frontend/
│   ├── index.html           # Main HTML page
│   ├── app.js               # Frontend JavaScript
│   └── style.css            # Styling
├── Datasets/
│   ├── amazon_laptops.csv   # Raw laptop data
│   └── Clean Dataset.csv    # Cleaned data
├── Scraping_Data_From_Amazon.ipynb  # Data scraping notebook
└── README.md                # This file
```

---

## ▶️ Running the Application

### Start the Backend & Frontend Server

The frontend is served from the backend, so you only need to start the FastAPI app from the project root:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

If you are using the workspace virtual environment from this project, you can also run:

```bash
.\crewai\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Then open your browser and navigate to:
```
http://127.0.0.1:8000
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve frontend dashboard |
| `/api/stats` | GET | Get dataset statistics |
| `/api/laptops` | GET | Get all cleaned laptops |
| `/api/clean` | POST | Trigger data cleaning |
| `/api/recommend` | POST | Get AI recommendations |

---

## 💡 Usage Example

### Sending a Recommendation Request

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "provider": "openai",
    "major": "Computer Science",
    "budget": 1500,
    "ram": 16,
    "brand": "Dell",
    "os_name": "Windows",
    "details": "Need a laptop for programming and machine learning"
  }'
```

---

## 🔑 Supported LLM Providers

| Provider | Configuration |
|----------|---|
| **OpenAI** | Set `OPENAI_API_KEY` environment variable |
| **Google Gemini** | Set `GOOGLE_API_KEY` or `GEMINI_API_KEY` |
| **Kimi (via LiteLLM)** | Set `NVIDIA_API_KEY` or use header |

---

## 📊 Data Cleaning

The application includes data cleaning tools. Run:

```bash
curl -X POST http://localhost:8000/api/clean
```

This will:
- Clean raw Amazon laptop data
- Remove duplicates
- Standardize formats
- Generate statistics

---

## 🔧 Troubleshooting

### Issue: "LiteLLM not installed" or provider initialization fails
**Solution:** Install the compatible version used by this project:
```bash
pip install litellm==1.61.15
```

### Issue: "API Key not found" or "API key not valid"
**Solution:** Ensure your `.env` file is configured with the correct API keys and that the selected provider matches the key you entered in the UI.

For example:
```env
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
NVIDIA_API_KEY=your_nvidia_api_key_here
```

### Issue: FastAPI not starting from `backend/main.py`
**Solution:** Run Uvicorn from the project root with the proper app path:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### Issue: Frontend not loading
**Solution:** Make sure the `frontend` folder exists in the project root with `index.html`, `app.js`, and `style.css`.

### Issue: Port 8000 already in use
**Solution:** Use a different port:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

---

## 📝 Development Notes

### Adding New LLM Providers
Edit `backend/crew.py` to add support for additional LLM providers.

### Customizing Agents
Modify agent configurations in `backend/crew.py` to change behavior.

### Frontend Customization
Edit HTML/CSS/JS in the `frontend/` directory. Changes will hot-reload thanks to uvicorn's `--reload` flag.

---

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

---

## 👤 Author

**sayeed ahmad

GitHub: [@sayeedahmad01](https://github.com/sayeedahmad01)

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Reques
