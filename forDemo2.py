import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)
sheet = client.open("DemoSchedule")

# --- Cached Reads ---
@st.cache_data(ttl=120)
def get_slots_data():
    return pd.DataFrame(sheet.worksheet("DEMO AVAILABLE").get_all_records())

@st.cache_data(ttl=120)
def get_teacher_responses():
    return pd.DataFrame(sheet.worksheet("TEACHER'S RESPONSE").get_all_records())

@st.cache_data(ttl=600)
def get_teachers_data():
    return pd.DataFrame(sheet.worksheet("Demo accessible teachers").get_all_records())

# --- UI ---
st.title("🎓 Demo Class Slot Registration")

st.subheader("Teacher Login")
teacher_id = st.text_input("Teacher ID")
teacher_name_part = st.text_input("Enter the first 4 letters of your name")
login_button = st.button("🔐 Login")

login_success = False
teacher_row = None

if login_button and teacher_id and teacher_name_part:
    teachers_df = get_teachers_data()
    teacher_row = teachers_df[teachers_df['Teacher ID'] == teacher_id]

    if not teacher_row.empty:
        full_teacher_name = teacher_row.iloc[0]['Teacher Name']
        if full_teacher_name[:4].lower() == teacher_name_part.lower():
            login_success = True
            st.success("✅ Login successful!")
        else:
            st.error("❌ Incorrect name entered.")
    else:
        st.error("❌ Invalid Teacher ID.")

if st.button("🔄 Force Refresh"):
    st.cache_data.clear()
    st.rerun()

if login_success:
    df = get_slots_data()

    st.sidebar.header("Filter Slots")
    subjects = sorted(df['Subject'].dropna().unique())
    date = sorted(df['Date'].dropna().unique())

    selected_subject = st.sidebar.selectbox("Select Subject", ["All"] + subjects)
    selected_date = st.sidebar.selectbox("Select Date", ["All"] + date)

    filtered_df = df.copy()
    if selected_subject != "All":
        filtered_df = filtered_df[filtered_df['Subject'] == selected_subject]
    if selected_date != "All":
        filtered_df = filtered_df[filtered_df['Date'] == selected_date]

    st.subheader("📋 Available Demo Slots")
    st.dataframe(filtered_df, use_container_width=True)

    st.subheader("✍️ Apply for a Demo Class")
    with st.form("apply_form"):
        available_demo_ids = filtered_df['Demo ID'].tolist()
        demo_id = st.selectbox("Select a Demo ID to take", available_demo_ids)
        contact = st.text_input("Contact Number")
        submit = st.form_submit_button("Ready to Take")

        if submit:
            if demo_id in df['Demo ID'].values:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # LIVE read to get accurate position
                live_response_sheet = sheet.worksheet("TEACHER'S RESPONSE")
                demo_responses = live_response_sheet.get_all_records()
                demo_responses_df = pd.DataFrame(demo_responses)
                demo_responses_for_id = demo_responses_df[demo_responses_df['Demo ID'] == demo_id]
                position = len(demo_responses_for_id) + 1

                # Write response
                live_response_sheet.append_row([
                    timestamp,
                    teacher_id,
                    contact,
                    demo_id
                ])

                st.cache_data.clear()

                if position <= 3:
                    st.success(f"✅ Successfully registered for Demo ID {demo_id}! You are at position {position}.")
                else:
                    st.warning(f"📌 Registered. You are at position {position}. The chance is lower.")
            else:
                st.error("❌ Invalid Demo ID.")
