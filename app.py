import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO

# --------------- STREAMLIT INTERFACE -------------------
st.set_page_config(page_title="Travel PDF to Google Sheet", layout="centered")
st.title("✈ PDF to Google Sheets Converter (for Travel Businesses)")
st.write("Upload your travel-related PDF (invoice, itinerary, etc.), and it will be automatically extracted and added to Google Sheets.")

# ------------------ FILE UPLOAD ------------------------
uploaded_file = st.file_uploader("📄 Upload a PDF file", type="pdf")

if uploaded_file:
    st.success("✅ PDF uploaded successfully!")

    # Read PDF using fitz (PyMuPDF)
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    st.subheader("📝 Extracted Text Preview")
    st.text(text[:1000] + "..." if len(text) > 1000 else text)

    # Example: extract table-like data (dummy logic - can be replaced)
    lines = text.split('\n')
    data = []
    for line in lines:
        parts = re.split(r'\s{2,}', line.strip())  # split on 2+ spaces
        if len(parts) > 1:
            data.append(parts)

    if data:
        df = pd.DataFrame(data)
        st.subheader("📊 Table Extracted from PDF")
        st.dataframe(df)

        # ---------------- GOOGLE SHEET -------------------
        st.subheader("☁ Upload to Google Sheets")

        sheet_name = st.text_input("Enter Google Sheet name")
        sheet_tab = st.text_input("Enter worksheet/tab name (default: Sheet1)", value="Sheet1")
        if st.button("📤 Send to Google Sheets"):
            try:
                # Auth
                scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                creds = Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"], scopes=scope
                )
                client = gspread.authorize(creds)

                # Create or open sheet
                try:
                    sheet = client.open(sheet_name)
                except gspread.exceptions.SpreadsheetNotFound:
                    sheet = client.create(sheet_name)
                    sheet.share(None, perm_type='anyone', role='writer')

                worksheet = sheet.worksheet(sheet_tab) if sheet_tab in [ws.title for ws in sheet.worksheets()] else sheet.add_worksheet(title=sheet_tab, rows="100", cols="20")

                worksheet.update([df.columns.values.tolist()] + df.values.tolist())
                st.success("✅ Data uploaded to Google Sheets!")

            except Exception as e:
                st.error(f"❌ Error uploading to Google Sheets: {e}")
    else:
        st.warning("⚠ Could not extract structured data. Try with another PDF.")
