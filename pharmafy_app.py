import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import time

st.set_page_config(page_title="SAPC Client Validator", layout="centered")

st.title("🧾 SAPC Client Validator")
st.markdown("Upload your client list (.csv) to validate against the SAPC register.")

# Upload section
uploaded_file = st.file_uploader("Upload CSV File", type="csv")

def search_sapc(pharmacy_name):
    """Scrape SAPC for a given pharmacy name."""
    base_url = "https://www.pharmcouncil.co.za/B_Registers.asp"
    params = {"txtName": pharmacy_name}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        results = []
        for row in soup.select("table tr"):
            cols = row.find_all("td")
            if len(cols) >= 2:
                name = cols[0].get_text(strip=True)
                status = cols[1].get_text(strip=True)
                results.append((name, status))
        return results
    except Exception as e:
        return [("Error", str(e))]

def validate_clients(df):
    output = []
    for _, row in df.iterrows():
        name = str(row['PharmacyName']).strip()
        st.write(f"🔍 Validating: {name}...")
        matches = search_sapc(name)
        best_match = max(matches, key=lambda x: fuzz.ratio(name.lower(), x[0].lower()), default=("None", "No match"))
        score = fuzz.ratio(name.lower(), best_match[0].lower())
        result = {
            "PharmacyName": name,
            "BestMatch": best_match[0],
            "MatchScore": score,
            "Status": best_match[1]
        }
        output.append(result)
        time.sleep(1.5)  # Delay to be respectful to SAPC server
    return pd.DataFrame(output)

# Process and display results
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        if 'PharmacyName' not in df.columns:
            st.error("❌ CSV must contain a column named 'PharmacyName'")
        else:
            with st.spinner("Validating clients, please wait..."):
                validated = validate_clients(df)
            st.success("✅ Validation complete!")
            st.dataframe(validated)

            # Export results
            csv = validated.to_csv(index=False).encode('utf-8')
            st.download_button("⬇ Download Results as CSV", csv, "validated_clients.csv", "text/csv")
    except Exception as e:
        st.error(f"Error processing file: {e}")
