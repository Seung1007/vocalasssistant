# vocalasssistant

A Streamlit app that uses Google Gemini to analyze lyrics in German, French, Russian, Italian, English, and Spanish for Korean translation and diction guidance.

## Run locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the app:
   ```bash
   streamlit run app.py
   ```

## Notes

- Set `GEMINI_API_KEY` in Streamlit Secrets before running the app.
- The analysis output is generated in real time by Gemini model `gemini-2.5-flash`.
