# AI-Powered CV Screener

A small Streamlit app that evaluates a CV against a job description using
the Claude API, returning a structured match score, missing keywords, and
first-impression red flags — the kind of quick triage a recruiter does in
the first few seconds of reading a resume.

## Why I built this

Manually checking a CV against a job posting is repetitive and easy to do
inconsistently. This project explores how far prompt engineering and
structured (JSON) outputs can go in automating that first pass — while
being explicit in the prompt that the model must not invent skills or
metrics that aren't actually present in the CV.

## How it works

1. The user uploads a CV (PDF) and pastes a job description.
2. `pdfplumber` extracts raw text from the PDF.
3. A structured prompt asks Claude to return **only** a JSON object with:
   - `match_score` (0-100)
   - `score_reasoning`
   - `missing_keywords`
   - `red_flags`
   - `strengths`
4. Streamlit renders the parsed JSON as score, metrics, and lists.

## Tech stack

- Python
- Streamlit (UI)
- Anthropic API (Claude) — structured prompting, JSON output
- pdfplumber (PDF text extraction)

## Running locally

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"   # or paste it into the sidebar
streamlit run app.py
```

Get an API key at [console.anthropic.com](https://console.anthropic.com).

## Notes / limitations

- This is a reference implementation, not a production tool — no
  authentication, no rate limiting, no persistence.
- PDF text extraction quality depends on how the source PDF was generated
  (scanned/image-based PDFs will need OCR, which is out of scope here).
- The prompt explicitly instructs the model not to fabricate CV content;
  this is a design choice worth discussing in interviews, since
  hallucination control is a real concern in applied GenAI tools.

## Possible extensions

- Support `.docx` CVs in addition to PDF
- Batch mode: screen multiple CVs against one job description
- Cache/compare results across multiple job descriptions for one CV
- Swap in a different model provider via an abstraction layer
