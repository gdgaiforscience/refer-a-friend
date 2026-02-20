import streamlit as st
import requests
import os

# Configuration
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="GDG Referral Tracker",
    page_icon="🔗",
    layout="centered"
)

st.title("GDG AI for Science - Refer a friend!")
st.markdown("1. Generate your referral link.")
st.markdown("2. Share it with your friends and colleagues.")
st.markdown("3. Get swag!")

tab1, tab2, tab3 = st.tabs(["Generate Link", "View Stats", "Leaderboard"])

# --- Tab 1: Generate Link ---
with tab1:
    st.header("Generate a New Link")
    with st.form("generate_form"):
        member_email = st.text_input("Email Address (used only for contacting about swag and keeping links unique to you)", placeholder="jane.doe@example.com")
        
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
                    if response.status_code == 201:
                        data = response.json()
                        st.success("Link generated successfully!")
                        
                        st.write("### Your Shareable Links:")
                        
                        # st.info("💡 **Which one should I share?**")
                        # st.markdown("""
                        # - **Tracking Link (Recommended):** Use this to appear on the **Leaderboard** and track your click count! It will redirect visitors to the event page.
                        # - **Direct Link:** A direct link to the Bevy event with your UTM parameters. *Note: Clicks on this link are NOT tracked in our local leaderboard.*
                        # """)

                        st.write("**Your referral link to share:**")
                        st.code(data["tracking_url"], language="text")

                        # col1, col2 = st.columns(2)
                        # with col1:
                        #     st.write("**Tracking Link (Share this!)**")
                        #     st.code(data["tracking_url"], language="text")
                        # with col2:
                        #     st.write("**Direct Link**")
                        #     st.code(data["referral_url"], language="text")
                        
                        st.info(f"Referral Code: **{data['referral_code']}** (Save this to check your stats later!)")
                    elif response.status_code == 200:
                        data = response.json()
                        st.info("Found your exisitng code!")
                        
                        st.write("### Your Shareable Links:")
                        
                        st.write("**Your referral link to share:**")
                        st.code(data["tracking_url"], language="text")
                        # col1, col2 = st.columns(2)
                        # with col1:
                        #     st.write("**Tracking Link (Share this!)**")
                        #     st.code(data["tracking_url"], language="text")
                        # with col2:
                        #     st.write("**Direct Link**")
                        #     st.code(data["referral_url"], language="text")
                        
                        st.info(f"Referral Code: **{data['referral_code']}**")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Failed to connect to the backend API: {e}")

# --- Tab 2: View Stats ---
with tab2:
    st.header("Check Link Performance")
    with st.form("stats_form"):
        referral_code = st.text_input("Enter your Referral Code", placeholder="aB3h9K")
        
        checked = st.form_submit_button("Get Stats")
        
        if checked:
            if not referral_code:
                st.error("Please enter a referral code.")
            else:
                try:
                    response = requests.get(f"{API_URL}/stats/{referral_code}")
                    if response.status_code == 200:
                        data = response.json()
                        
                        st.write(f"### Stats for `{referral_code}`")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Clicks", data["total_clicks"])
                        with col2:
                            st.write("**Referrer:**", data["member_email"])
                            
                        st.write("**Target Event:**", data["event_path"])
                        
                    elif response.status_code == 404:
                        st.warning("Referral code not found.")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Failed to connect to the backend API: {e}")

# --- Tab 3: Leaderboard ---
with tab3:
    st.header("Top Referrers Leaderboard")
    st.markdown("See who has referred the most clicks across all events!")
    
    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        if st.button("Refresh 🔄"):
            pass # Just clicking the button triggers a Streamlit script re-run
            
    try:
        response = requests.get(f"{API_URL}/leaderboard")
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
