# MeetMind — AI Meeting Action-Item Extractor

## Project overview
MeetMind converts meeting notes or transcript text into structured action items with task, owner, deadline, status, confidence, and a review flag. Results can be edited and exported to CSV or JSON.

## Two extraction modes
1. **Offline smart rules** — works without an API key or internet after packages are installed. Uses rule-based natural-language patterns. This is useful for a reliable demo but is not a trained machine-learning model.
2. **AI model via API** — optionally sends the transcript to the OpenAI Chat Completions API and asks the model to return structured JSON. Requires internet, a valid API key, and access to the chosen model. API usage may incur charges. Never share the key.

## Windows setup
1. Install Python 3.10+ from https://www.python.org/downloads/ and enable **Add Python to PATH**.
2. Extract the ZIP folder.
3. Open the extracted folder in File Explorer.
4. Click the address bar, type `cmd`, and press Enter.
5. Run:
   `python -m pip install -r requirements.txt`
6. Run:
   `python -m streamlit run app.py`
7. Open the local URL printed in the terminal (usually http://localhost:8501).

## Demo steps
1. Keep the default sample transcript.
2. Choose Offline smart rules.
3. Click Extract action items.
4. Edit a row if needed.
5. Download CSV or JSON.
6. For the optional AI demo, choose AI model via API and enter a valid API key in the sidebar.

## Project files
- `app.py` — Streamlit application and extraction logic.
- `requirements.txt` — dependencies.
- `sample_transcript.txt` — sample test data.
- `Project_Report.pdf` — formatted report.
- `Project_Report.md` — editable report source.
- `TEST_CASES.md` — suggested manual tests.

## Limitations
The offline mode relies on patterns and may miss implied tasks, names, and complex dates. The API mode depends on model output and connectivity. Always review the extracted information. Do not paste confidential meeting content into an external AI API unless you have permission.
