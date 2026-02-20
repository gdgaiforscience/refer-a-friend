import streamlit as st
import requests
import os
import datetime
import calendar

# Configuration
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def get_time_until_end_of_month():
    now = datetime.datetime.now()
    last_day = calendar.monthrange(now.year, now.month)[1]
    end_of_month = datetime.datetime(now.year, now.month, last_day, 23, 59, 59)
    delta = end_of_month - now
    
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return f"{days}d {hours}h {minutes}m"

st.set_page_config(
    page_title="GDG Referral Tracker",
    page_icon="🔗",
    layout="centered"
)

st.title("GDG AI for Science - Refer a friend!")
st.markdown("1. Generate your referral link.")
st.markdown("2. Share it with your friends and colleagues.")
st.markdown("3. Get swag!")

tab1, tab2 = st.tabs(["Generate Link", "Leaderboard"])

# --- Tab 1: Generate Link ---
with tab1:
    st.header("Generate a New Link")
    with st.form("generate_form"):
        member_email = st.text_input("Email Address (used only to keep links unique to you - we do not store this in plain text for your privacy)", placeholder="jane.doe@example.com")
        
        events = {
            "The Adversarial Misuse of AI": "https://gdg.community.dev/events/details/google-gdg-ai-for-science-australia-presents-the-adversarial-misuse-of-ai-and-how-to-defend-against-it/",
            "Gemma in the Lab": "https://gdg.community.dev/events/details/google-gdg-ai-for-science-japan-presents-gemma-in-the-lab/",
            "Applying Deep Learning in Genomics": "https://gdg.community.dev/events/details/google-gdg-ai-for-science-australia-presents-applying-deep-learning-in-genomics/",
            "Building Conversational Genomics": "https://gdg.community.dev/events/details/google-gdg-ai-for-science-australia-presents-building-conversational-genomics-multi-agent-ai-for-variant-interpretation/"
        }
        
        event_name = st.selectbox("Select Event", options=list(events.keys()))
        event_path = events[event_name]
        
        submitted = st.form_submit_button("Generate Link")
        
        if submitted:
            if not member_email or not event_path:
                st.error("Please fill in both fields.")
            else:
                try:
                    response = requests.post(
                        f"{API_URL}/generate",
                        json={"member_email": member_email, "event_path": event_path}
                    )
                    if response.status_code in (200, 201):
                        data = response.json()
                        banner = "Link generated successfully!" if response.status_code == 201 else "Found your existing code!"
                        st.success(banner)

                        st.write("### Your referral link to share:")
                        st.code(data["tracking_url"], language="text")
                        st.info(f"Referral Code: **{data['referral_code']}** (Save this to check your stats later!)")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Failed to connect to the backend API: {e}")


# --- Tab 2: Leaderboard ---
with tab2:
    st.header("Top Referrers Leaderboard")
    
    # Simple Admin Toggle
    admin_mode = st.toggle("Admin - View All Time Stats", value=False)
    
    if not admin_mode:
        # Show countdown for normal view
        countdown = get_time_until_end_of_month()
        st.info(f"⏱️ **Time remaining this month:** {countdown}")
        st.markdown("See who has referred the most clicks **this month** across all events!")
        api_params = {"all_time": "false"}
    else:
        st.warning("📊 **Admin Mode:** Showing all-time stats.")
        api_params = {"all_time": "true"}
    
    if admin_mode:
        st.divider()
        st.subheader("Admin: Check Specific Referral Code")
        with st.form("admin_check"):
            target_code = st.text_input("Enter Referral Code", placeholder="aB3h9K")
            check_all_time = st.checkbox("All Time Stats", value=True)
            check_submitted = st.form_submit_button("Fetch Stats")
            
            if check_submitted and target_code:
                try:
                    params = {"all_time": "true" if check_all_time else "false"}
                    res = requests.get(f"{API_URL}/stats/{target_code}", params=params)
                    if res.status_code == 200:
                        stats = res.json()
                        c1, c2 = st.columns(2)
                        c1.metric("Total Clicks", stats["total_clicks"])
                        c2.info(f"Event: {stats['event_path']}")
                    else:
                        st.error(f"Code not found: {res.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
        st.divider()

    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        if st.button("Refresh 🔄"):
            pass # Just clicking the button triggers a Streamlit script re-run
            
    try:
        response = requests.get(f"{API_URL}/leaderboard", params=api_params)
        if response.status_code == 200:
            data = response.json()
            if data:
                import pandas as pd
                df = pd.DataFrame(data)
                df.columns = ["Referral Code", "Total Clicks"]
                df.index = df.index + 1
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No referral data yet.")
        else:
            st.error(f"Error fetching leaderboard: {response.text}")
    except Exception as e:
        st.error(f"Failed to connect to the backend API: {e}")
