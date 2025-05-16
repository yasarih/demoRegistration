import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# Define scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load credentials from Streamlit secrets
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

spreadsheet_id = "13_ckKpI381EF2rCfVS28sn9cSlhxfsZaIOeUJJo3ngc"
sheet = client.open_by_key(spreadsheet_id)
slots_sheet = sheet.worksheet("DEMO AVAILABLE")
response_sheet = sheet.worksheet("TEACHER'S RESPONSE")
teachers_sheet = sheet.worksheet("Demo accessible teachers")

# Session state init
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = ""
if "teacher_name" not in st.session_state:
    st.session_state.teacher_name = ""

# --- Login UI ---
st.title("🎓 Demo Class Slot Registration")
st.subheader("Teacher Login")

if not st.session_state.logged_in:
    teacher_id_input = st.text_input("Teacher ID")
    password_input = st.text_input("Enter the last 4 digits of your Phone number")

    if st.button("Login"):
        teachers_data = teachers_sheet.get_all_records()
        teachers_df = pd.DataFrame(teachers_data)
        teacher_row = teachers_df[teachers_df['Teacher ID'] == teacher_id_input]

        if not teacher_row.empty:
            full_teacher_name = teacher_row.iloc[0]['Teacher Name']
            correct_password = str(teacher_row.iloc[0]['Password'])

            if password_input == correct_password:
                st.session_state.logged_in = True
                st.session_state.teacher_id = teacher_id_input
                st.session_state.teacher_name = full_teacher_name
                st.success("✅ Login successful!")
            else:
                st.error("❌ Verification failed. Please double-check your Teacher ID and the last part of your phone number. If you've entered the correct details and the issue persists, kindly contact the Teachers Manager, Nihala at 8089381416 for assistance.")
        else:
            st.error("❌ Invalid Teacher ID. Please check your ID.")


# --- Logged in UI ---
if st.session_state.logged_in:
    teacher_id = st.session_state.teacher_id

    # --- Load all slot data ---
    slots = slots_sheet.get_all_records()
    df = pd.DataFrame(slots)

    st.sidebar.header("Filter Slots")
    subjects = sorted(df['Subject'].dropna().unique())
    dates = sorted(df['Date'].dropna().unique())
    selected_subject = st.sidebar.selectbox("Select Subject", ["All"] + subjects)
    selected_date = st.sidebar.selectbox("Select Date", ["All"] + dates)

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
                selected_row = df[df['Demo ID'] == demo_id].iloc[0]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                demo_responses = response_sheet.get_all_records()
                demo_responses_df = pd.DataFrame(demo_responses)
                demo_responses_for_id = demo_responses_df[demo_responses_df['Demo ID'] == demo_id]
                position = len(demo_responses_for_id) + 1

                response_sheet.append_row([
                    timestamp,
                    teacher_id,
                    contact,
                    demo_id
                ])

                if position <= 3:
                    st.success(f"✅ Successfully registered for Demo ID {demo_id}!")
                else:
                    st.warning(f"❗ Request submitted! You are at position {position}, so the probability of getting this demo slot is low.")
            else:
                st.error("❌ Invalid Demo ID. Please check the table above.")
