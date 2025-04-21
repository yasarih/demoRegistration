import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# Define scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load credentials from Streamlit secrets
creds_dict = st.secrets["gcp_service_account"]

# Convert the dictionary to a JSON string and use it for credentials
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)

# Authorize client
client = gspread.authorize(creds)

sheet = client.open("DemoSchedule")  # Your sheet name
slots_sheet = sheet.worksheet("DEMO AVAILABLE")  # Available slots
response_sheet = sheet.worksheet("TEACHER'S RESPONSE")  # Submissions

# --- Load all slot data ---
slots = slots_sheet.get_all_records()
df = pd.DataFrame(slots)

# Add unique Demo ID (optional: from sheet or auto-generated here)
 # You can adjust this to match your own column if needed

st.title("🎓 Demo Class Slot Registration")

# --- Sidebar Filters ---
st.sidebar.header("Filter Slots")
subjects = sorted(df['Subject'].dropna().unique())
date = sorted(df['Date'].dropna().unique())

selected_subject = st.sidebar.selectbox("Select Subject", ["All"] + subjects)
selected_date = st.sidebar.selectbox("Select Date", ["All"] + date)

# --- Apply filters ---
filtered_df = df.copy()
if selected_subject != "All":
    filtered_df = filtered_df[filtered_df['Subject'] == selected_subject]
if selected_date != "All":
    filtered_df = filtered_df[filtered_df['Date'] == selected_date]

# --- Show Table ---
st.subheader("📋 Available Demo Slots")
st.dataframe(filtered_df, use_container_width=True)

# --- Booking Section ---
st.subheader("✍️ Apply for a Demo Class")

with st.form("apply_form"):
    available_demo_ids = filtered_df['Demo ID'].tolist()
    demo_id = st.selectbox("Select a Demo ID to take", available_demo_ids)
    name = st.text_input("Teacher ID")
    contact = st.text_input("Contact Number")
    submit = st.form_submit_button("Ready to Take")

    if submit:
        # Check if demo ID is valid
        if demo_id in df['Demo ID'].values:
            selected_row = df[df['Demo ID'] == demo_id].iloc[0]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            response_sheet.append_row([
                timestamp,
                name,
                contact,   
                demo_id
            ])
            st.success(f"✅ Successfully registered for Demo ID {demo_id}!")
        else:
            st.error("❌ Invalid Demo ID. Please check the table above.")
