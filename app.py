"""
AI-Powered CV Screener (Groq version)
-----------------------------------------
Upload a CV (PDF) and paste a job description. The app calls the
Groq API (free, no credit card required) with a structured prompt
and returns:
  - a match score (0-100)
  - top missing keywords
  - red flags a human reviewer would notice first

Author: Tilemachos Palikaridis
"""

import json
import os

import pdfplumber
import streamlit as st
from groq import Groq

# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------
MODEL_NAME = "llama-3.3-70b-versatile"  # free on Groq, strong general model

st.set_page_config(page_title="AI CV Screener", page_icon="📄", layout="wide")


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def extract_text_from_pdf(uploaded_file) -> str:
    """Extract raw text from an uploaded PDF file object."""
    text_chunks = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)
    return "\n".join(text_chunks).strip()


def build_prompt(cv_text: str, job_description: str) -> str:
    """Build the prompt sent to the model. Ask for JSON only, so the
    output is easy to parse deterministically."""
    return f"""You are a senior technical recruiter. Compare the CV below
against the job description and evaluate the match.

Respond with ONLY a valid JSON object (no markdown fences, no preamble),
matching exactly this schema:

{{
  "match_score": <integer 0-100>,
  "score_reasoning": "<1-2 sentence explanation of the score>",
  "missing_keywords": ["<keyword 1>", "<keyword 2>", "..."],
  "red_flags": ["<red flag 1>", "<red flag 2>", "..."],
  "strengths": ["<strength 1>", "<strength 2>", "..."]
}}

Rules:
- missing_keywords: up to 5 specific skills/terms present in the job
  description but absent or weak in the CV.
- red_flags: up to 3 things a hiring manager would notice in the first
  10 seconds of skimming (formatting issues, mismatched experience,
  unclear scope, etc). Do not invent flags that aren't supported by the text.
- strengths: up to 3 genuine strengths that match the job description.
- Do not fabricate skills, experience, or metrics that are not present
  in the CV text.

--- JOB DESCRIPTION ---
{job_description}

--- CV TEXT ---
{cv_text}
"""


def call_groq(prompt: str, api_key: str) -> dict:
    """Send the prompt to the Groq API and parse the JSON response."""
    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    raw_text = response.choices[0].message.content.strip()

    # Defensive cleanup in case the model wraps output in ```json fences
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()

    return json.loads(cleaned)


# ---------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------
st.title("📄 AI-Powered CV Screener")
st.caption(
    "Upload a CV and paste a job description to get a match score, "
    "missing keywords, and first-impression red flags — powered by the "
    "free Groq API and structured prompting."
)

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input(
        "Groq API key",
        type="password",
        help="Get a free key at console.groq.com/keys. Never commit this to GitHub.",
    )
    api_key = api_key or os.environ.get("GROQ_API_KEY", "")
    st.caption("Tip: set GROQ_API_KEY as an environment variable instead "
               "of pasting it here, so it's never typed into the UI.")

col1, col2 = st.columns(2)

with col1:
    uploaded_cv = st.file_uploader("Upload CV (PDF)", type=["pdf"])

with col2:
    job_description = st.text_area("Paste job description", height=250)

run_button = st.button("Analyze match", type="primary", use_container_width=True)

if run_button:
    if not api_key:
        st.error("Please provide a Groq API key in the sidebar.")
    elif not uploaded_cv:
        st.error("Please upload a CV PDF.")
    elif not job_description.strip():
        st.error("Please paste a job description.")
    else:
        with st.spinner("Extracting CV text..."):
            cv_text = extract_text_from_pdf(uploaded_cv)

        if not cv_text:
            st.error("Could not extract text from this PDF. Try a different file.")
        else:
            with st.spinner("Calling Groq API..."):
                prompt = build_prompt(cv_text, job_description)
                try:
                    result = call_groq(prompt, api_key)
                except json.JSONDecodeError:
                    st.error("The model did not return valid JSON. Try again.")
                    result = None
                except Exception as e:  # noqa: BLE001
                    st.error(f"API call failed: {e}")
                    result = None

            if result:
                st.divider()

                score = result.get("match_score", 0)
                st.metric("Match Score", f"{score}/100")
                st.write(result.get("score_reasoning", ""))

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    st.subheader("Missing Keywords")
                    for kw in result.get("missing_keywords", []):
                        st.markdown(f"- {kw}")

                with col_b:
                    st.subheader("Red Flags")
                    for flag in result.get("red_flags", []):
                        st.markdown(f"- {flag}")

                with col_c:
                    st.subheader("Strengths")
                    for s in result.get("strengths", []):
                        st.markdown(f"- {s}")

                with st.expander("Raw JSON response"):
                    st.json(result)
