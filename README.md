# WANDATA — AI-Powered ATS Resume Checker

## 🚀 Quick Start

### Method 1: One Command
```bash
chmod +x start.sh
./start.sh
```

### Method 2: Manual
```bash
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000** in your browser.

---

## 📁 File Structure

```
wandata-ats/
├── app.py              ← Flask backend server
├── ats_engine.py       ← AI scoring engine
├── index.html          ← Main website
├── style.css           ← Styles
├── script.js           ← Frontend logic
├── static/
│   └── logo.png        ← WANDATA logo
├── requirements.txt
└── start.sh            ← Quick start
```

---

## 🧠 How the ATS Engine Works

**General ATS Score (no job description):**
| Factor | Weight |
|---|---|
| Resume Sections | 25% |
| Action Verbs | 15% |
| Keyword Optimization | 15% |
| Quantifiable Impact | 15% |
| Contact Info | 10% |
| Length & Readability | 10% |
| Education Details | 5% |
| ATS Formatting | 5% |

**Job-Specific Match Score:**
| Factor | Weight |
|---|---|
| Keyword Match (TF-IDF) | 30% |
| Skills Alignment | 25% |
| Content Similarity | 20% |
| General ATS | 15% |
| Job Title Relevance | 10% |

---

## 📄 Supported Resume Formats
- **PDF** (recommended)
- **DOCX / DOC**
- **TXT**

---

## ⚙️ Requirements
- Python 3.8+
- Flask
- pdfplumber
- python-docx
- scikit-learn

No external API needed — 100% local processing.
