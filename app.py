import streamlit as st
import json
import os
from datetime import datetime
from statistics import mean

# =========================================================
# CONFIGURATION (edit only this section)
# =========================================================
APP_TITLE = "🏆 Road-Star for January"
APP_ICON = "🏆"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "votes.json")

ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
VOTES_REQUIRED = 2

# Scoring formula:
# Final Score = (Nominations × NOMINATION_WEIGHT) + (Avg Rating × RATING_WEIGHT × RATING_SCALE)
NOMINATION_WEIGHT = 0.4
RATING_WEIGHT = 0.6
RATING_SCALE = 2

RATING_CATEGORIES = [
    "Work Quality",
    "Ownership",
    "Team Support",
    "Reliability",
]

# Names converted to First Last order from your image
EMPLOYEES = [
    "Varun Arora",
    "Rajendra Singh Bisht",
    "Heena Gupta",
    "Rakesh Kumar Jalandra",
    "Anant Kesarwani",
    "Rura Kumari",
    "Aman Shardawadh Mewara",
    "Garvit Nokhwal",
    "Khatibur Rahman",
    "Kaushiki Sharma",
    "Himanshu Sharma",
    "Manu Sharma",
    "Mohit Soni",
    "Ankit Kumar Vardhan",
]

# =========================================================
# HELPERS
# =========================================================
def load_votes():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def save_votes(votes):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(votes, f, indent=4)

def get_voted_users(votes):
    return sorted({
        row.get("voter")
        for row in votes
        if isinstance(row, dict) and row.get("voter")
    })

def calculate_results(votes):
    summary = {
        emp: {
            "nominations": 0,
            "rating_sum": 0.0,
            "rating_count": 0,
        }
        for emp in EMPLOYEES
    }

    for row in votes:
        if not isinstance(row, dict):
            continue

        nominee = row.get("nominee")
        ratings = row.get("ratings", {})

        if nominee not in summary:
            continue

        if isinstance(ratings, dict) and ratings:
            avg_rating = sum(ratings.values()) / len(ratings)
        else:
            avg_rating = 0

        summary[nominee]["nominations"] += 1
        summary[nominee]["rating_sum"] += avg_rating
        summary[nominee]["rating_count"] += 1

    final_results = []
    for emp, data in summary.items():
        avg_rating = data["rating_sum"] / data["rating_count"] if data["rating_count"] else 0
        final_score = (
            data["nominations"] * NOMINATION_WEIGHT
            + avg_rating * RATING_WEIGHT * RATING_SCALE
        )

        final_results.append({
            "Employee": emp,
            "Nominations": data["nominations"],
            "Avg Rating": round(avg_rating, 2),
            "Final Score": round(final_score, 2),
        })

    final_results.sort(key=lambda x: x["Final Score"], reverse=True)
    return final_results

# =========================================================
# PAGE SETUP
# =========================================================
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
st.title(APP_TITLE)

# Load current data
votes_data = load_votes()
voted_users = get_voted_users(votes_data)

# Session state
if "recent_submission_voter" not in st.session_state:
    st.session_state.recent_submission_voter = None

# =========================================================
# VOTING SECTION
# =========================================================
st.subheader("🗳️ Vote for 2 employees")

voter = st.selectbox("Select your name", EMPLOYEES, key="voter_select")

# Show success once after a fresh submit
if st.session_state.recent_submission_voter == voter:
    st.success("✅ Vote submitted successfully!")
    st.session_state.recent_submission_voter = None
    st.stop()

already_voted = voter in voted_users

if already_voted:
    st.warning("⚠️ You have already submitted your vote.")

if not already_voted:
    st.caption("Select exactly 2 employees. You cannot vote for yourself.")

    nominee_options = [emp for emp in EMPLOYEES if emp != voter]

    nominees = st.multiselect(
        "Select 2 nominees",
        nominee_options,
        max_selections=VOTES_REQUIRED,
        key="nominee_select"
    )

    ratings = {}

    if len(nominees) > 0:
        st.markdown("### Rate the selected nominees")

        for idx, nominee in enumerate(nominees):
            st.markdown(f"#### {nominee}")
            ratings[nominee] = {}

            for cat_idx, category in enumerate(RATING_CATEGORIES):
                ratings[nominee][category] = st.slider(
                    f"{nominee} - {category}",
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"rate_{idx}_{cat_idx}_{nominee}_{category}"
                )

    if st.button("Submit Vote"):
        if len(nominees) != VOTES_REQUIRED:
            st.error("Please select exactly 2 nominees.")
        else:
            latest_votes = load_votes()

            for nominee in nominees:
                latest_votes.append({
                    "voter": voter,
                    "nominee": nominee,
                    "ratings": ratings[nominee],
                    "timestamp": datetime.now().isoformat(timespec="seconds")
                })

            save_votes(latest_votes)

            st.session_state.recent_submission_voter = voter
            st.rerun()

# =========================================================
# ADMIN SECTION
# =========================================================
st.markdown("---")
st.subheader("🔐 Admin Access")

show_admin = st.checkbox("Enable admin panel")

if show_admin:
    admin_password = st.text_input("Enter Admin Password", type="password")

    if admin_password == ADMIN_PASSWORD:
        st.success("Admin access granted.")

        if st.button("Show Results"):
            latest_votes = load_votes()
            final_results = calculate_results(latest_votes)

            st.markdown("### 🏆 Top 3")

            for i, row in enumerate(final_results[:3]):
                if i == 0:
                    st.success(f"🥇 {row['Employee']} — Final Score: {row['Final Score']}")
                elif i == 1:
                    st.info(f"🥈 {row['Employee']} — Final Score: {row['Final Score']}")
                else:
                    st.warning(f"🥉 {row['Employee']} — Final Score: {row['Final Score']}")

            st.markdown("### 📋 Full Rankings")
            st.dataframe(final_results, use_container_width=True)

            if final_results:
                winner = final_results[0]
                st.success(f"🏆 Winner: {winner['Employee']} | Score: {winner['Final Score']}")

    elif admin_password != "":
        st.error("❌ Incorrect password")
