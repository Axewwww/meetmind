import os
import re
import json
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MeetMind | Action Item Extractor",
    page_icon="🧠",
    layout="wide",
)

st.markdown("""
<style>
    .main { background: #f6f8fc; }
    .block-container { padding-top: 2rem; max-width: 1200px; }
    .hero { padding: 1.5rem; border-radius: 18px; background: linear-gradient(120deg,#14213d,#2457a7); color: white; margin-bottom: 1rem; }
    .hero h1 { color: white; margin-bottom: .25rem; }
    .hero p { color: #e7efff; margin-bottom: 0; }
    div[data-testid="stMetric"] { background: white; padding: 1rem; border-radius: 12px; border: 1px solid #e5eaf3; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🧠 MeetMind</h1>
  <p>AI Meeting Action-Item Extractor · Turn meeting notes into clear, trackable tasks.</p>
</div>
""", unsafe_allow_html=True)

st.write("Paste a transcript, extract likely action items, review uncertain fields, and export the result.")

SAMPLE = """Meeting: Website Launch Planning
Aisha will prepare the presentation slides by Friday.
Rahul will test the login and signup flow tomorrow.
The team discussed the project budget and launch risks.
Assigned to Priya: send the final project report by October 15.
Owner: Omar - schedule the next review meeting next week.
We need to fix the signup bug by 10/12/2026.
Aisha will prepare the presentation slides by Friday.
"""

ACTION_VERBS = [
    "prepare", "send", "create", "finish", "complete", "review", "check", "update",
    "call", "contact", "email", "schedule", "organize", "design", "build", "develop",
    "submit", "share", "fix", "test", "research", "collect", "analyze", "discuss",
    "confirm", "arrange", "upload", "download", "present", "write", "make", "deliver",
    "follow up", "ensure", "book", "plan", "implement", "deploy", "coordinate",
    "document", "approve", "finalize", "verify", "investigate", "review"
]

def split_sentences(text):
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [re.sub(r"^[\s\-•*]+", "", x).strip() for x in chunks if x.strip()]

def find_owner(sentence):
    patterns = [
        r"\bassigned to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"\bowner\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"^\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+will\b",
        r"\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\)\s*$",
    ]
    for pattern in patterns:
        m = re.search(pattern, sentence, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "Unassigned"

def find_deadline(sentence):
    patterns = [
        r"\b(?:today|tomorrow|tonight|next week|next month|by end of day|eod|asap)\b",
        r"\b(?:by\s+)?(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)(?:\s+(?:morning|afternoon|evening))?\b",
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[ ]+\d{1,2}(?:,?[ ]+\d{4})?\b",
        r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, sentence, re.IGNORECASE)
        if m:
            return m.group(0)
    return "Not specified"

def looks_like_action(sentence):
    low = sentence.lower()
    verb_found = any(re.search(r"\b" + re.escape(v) + r"\b", low) for v in ACTION_VERBS)
    commitment = re.search(r"\b(will|should|must|need to|needs to|has to|have to|action item|responsible for)\b", low)
    imperative = low.startswith(tuple(ACTION_VERBS))
    assigned = ":" in sentence and verb_found
    return bool(verb_found and (commitment or imperative or assigned))

def remove_owner_prefix(sentence):
    s = sentence.strip()
    s = re.sub(r"^\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+will\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^\s*assigned to\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*:\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^\s*owner\s*:\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*[-:]\s*", "", s, flags=re.IGNORECASE)
    return s.strip()

def extract_rule_based(text):
    rows, seen = [], set()
    for sentence in split_sentences(text):
        if not looks_like_action(sentence):
            continue
        normalized = re.sub(r"[^a-z0-9 ]", "", sentence.lower())
        if normalized in seen:
            continue
        seen.add(normalized)
        owner = find_owner(sentence)
        deadline = find_deadline(sentence)
        confidence = "High" if owner != "Unassigned" and deadline != "Not specified" else (
            "Medium" if owner != "Unassigned" or deadline != "Not specified" else "Low"
        )
        rows.append({
            "Task": remove_owner_prefix(sentence),
            "Owner": owner,
            "Deadline": deadline,
            "Status": "Pending",
            "Confidence": confidence,
            "Needs review": "Yes" if owner == "Unassigned" or deadline == "Not specified" else "No",
        })
    return rows

def extract_with_openai(text, api_key, model):
    # Optional API mode. Uses the OpenAI chat completions endpoint.
    import requests
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    schema_instructions = """Extract only explicit or strongly implied action items from the transcript.
Return valid JSON only as an array of objects with keys: task, owner, deadline, status, confidence.
Use 'Unassigned' when no owner is clear, 'Not specified' when no deadline is clear,
'Pending' as status, and confidence High/Medium/Low. Do not invent information."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": schema_instructions},
            {"role": "user", "content": text}
        ],
        "temperature": 0
    }
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE)
    data = json.loads(content)
    rows = []
    for item in data:
        owner = str(item.get("owner") or "Unassigned")
        deadline = str(item.get("deadline") or "Not specified")
        rows.append({
            "Task": str(item.get("task") or "").strip(),
            "Owner": owner,
            "Deadline": deadline,
            "Status": str(item.get("status") or "Pending"),
            "Confidence": str(item.get("confidence") or "Medium"),
            "Needs review": "Yes" if owner == "Unassigned" or deadline == "Not specified" else "No",
        })
    return [r for r in rows if r["Task"]]

with st.sidebar:
    st.header("Extraction settings")
    mode = st.radio("Mode", ["Offline smart rules", "AI model via API"], help="Offline mode runs without an API key. API mode requires an OpenAI API key and a model available to your account.")
    api_key = ""
    model = "gpt-4o-mini"
    if mode == "AI model via API":
        api_key = st.text_input("OpenAI API key", type="password", help="Used for this session only; do not share your key.")
        model = st.text_input("Model name", value="gpt-4o-mini")
    st.divider()
    st.caption("Always review the extracted tasks. This prototype may miss context or interpret dates incorrectly.")

with st.expander("Example transcript", expanded=False):
    st.code(SAMPLE, language="text")

transcript = st.text_area("Meeting transcript / notes", value=SAMPLE, height=260, placeholder="Paste meeting transcript here...")

if st.button("✨ Extract action items", type="primary", use_container_width=True):
    if not transcript.strip():
        st.warning("Paste some meeting notes first.")
    else:
        try:
            if mode == "AI model via API":
                if not api_key.strip():
                    st.error("Enter your API key in the sidebar, or choose Offline smart rules.")
                    st.stop()
                with st.spinner("Extracting action items with the AI model..."):
                    rows = extract_with_openai(transcript, api_key.strip(), model.strip())
            else:
                rows = extract_rule_based(transcript)
            if not rows:
                st.warning("No likely action items found. Try explicit wording such as 'Aisha will send the report by Friday.'")
            else:
                df = pd.DataFrame(rows)
                st.session_state["results"] = df
                st.session_state["mode_used"] = mode
        except Exception as e:
            st.error(f"Extraction failed: {e}")
            st.info("Try Offline smart rules, check your internet/API settings, and run again.")

if "results" in st.session_state:
    df = st.session_state["results"]
    st.subheader("Extraction results")
    c1, c2, c3 = st.columns(3)
    c1.metric("Action items", len(df))
    c2.metric("Need review", int((df["Needs review"] == "Yes").sum()))
    c3.metric("Mode", "AI API" if st.session_state.get("mode_used") == "AI model via API" else "Offline")
    st.caption("Review and edit the table before exporting. The original text is not changed.")
    edited = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic")
    csv = edited.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, file_name="meeting_action_items.csv", mime="text/csv")
    st.download_button("⬇️ Download JSON", edited.to_json(orient="records", indent=2).encode("utf-8"),
                       file_name="meeting_action_items.json", mime="application/json")
    st.success("Extraction complete. Verify owners and deadlines before using the tasks.")
else:
    st.info("Paste or use the example transcript, then click **Extract action items**.")
