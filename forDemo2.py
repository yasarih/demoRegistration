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
teachers_sheet = sheet.worksheet("Demo accessible teachers")  # Teachers data for login

# --- Load teachers' data for authentication ---
teachers_data = teachers_sheet.get_all_records()
teachers_df = pd.DataFrame(teachers_data)

# --- Initial Login Section ---
st.title("🎓 Demo Class Slot Registration")

# Teacher Login
st.subheader("Teacher Login")
teacher_id = st.text_input("Teacher ID")
teacher_name_part = st.text_input("Enter the first 4 letters of your name")

login_success = False

# Verify credentials
if teacher_id and teacher_name_part:
    # Check if Teacher ID exists in the teachers' data
    teacher_row = teachers_df[teachers_df['Teacher ID'] == teacher_id]
    
    if not teacher_row.empty:
        # Check if the first 4 letters of the teacher's name match
        full_teacher_name = teacher_row.iloc[0]['Teacher Name']
        if full_teacher_name[:4].lower() == teacher_name_part.lower():
            login_success = True
            st.success("✅ Login successful!")
        else:
            st.error("❌ Incorrect name entered. Please check the first 4 letters.")
    else:
        st.error("❌ Invalid Teacher ID. Please check your ID.")

# Proceed only if login is successful
if login_success:
    # --- Load all slot data ---
    slots = slots_sheet.get_all_records()
    df = pd.DataFrame(slots)

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
        name = teacher_id
        contact = st.text_input("Contact Number")
        submit = st.form_submit_button("Ready to Take")

        if submit:
            # Check if demo ID is valid
            if demo_id in df['Demo ID'].values:
                selected_row = df[df['Demo ID'] == demo_id].iloc[0]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # --- Count number of responses for this Demo ID ---
                demo_responses = response_sheet.get_all_records()
                demo_responses_df = pd.DataFrame(demo_responses)
                demo_responses_for_id = demo_responses_df[demo_responses_df['Demo ID'] == demo_id]
                
                # --- Get the position of this teacher ---
                position = len(demo_responses_for_id) + 1  # Position is based on the number of existing responses
                
                response_sheet.append_row([
                    timestamp,
                    name,
                    contact,   
                    demo_id
                ])
                
                # Notify the user of their position
                if position <= 3:
                    st.success(f"✅ Successfully registered for Demo ID {demo_id}!.")
                else:
                    st.warning(f"❗ Request submitted! You are at position {position}, so the probability of getting this demo slot is low.")
            else:
                st.error("❌ Invalid Demo ID. Please check the table above.")
