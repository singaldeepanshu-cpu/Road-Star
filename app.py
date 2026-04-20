import streamlit as st
import json
import os
from datetime import datetime
from statistics import mean
from io import StringIO
import csv

# =========================================================
# CONFIGURATION (edit only this section)
# =========================================================
APP_TITLE = "🏆 Road-Star for Quarter-1"
APP_ICON = "🏆"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "votes.json")

# Put this in Streamlit secrets when deployed:
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
# For local testing, fallback is used if secrets are not available.
#try:
#    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
#except Exception:
#    ADMIN_PASSWORD = "admin123"

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

EMPLOYEES = [
    "Varun Arora",
    "Rajendra Singh Bisht",
    "Heena Gupta",
    "Rakesh Kumar Jalandra",
    "Anant Kesarwani",
    "Rupa Kumari",
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
    except Exception:
        return []

def save_votes(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_voted_users(votes):
    voters = set()
    for row in votes:
        if isinstance(row, dict) and row.get("voter"):
            voters.add(row["voter"])
    return sorted(voters)

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

def build_raw_vote_rows(votes):
    rows = []
    for row in votes:
        if not isinstance(row, dict):
            continue

        ratings = row.get("ratings", {})
        avg_rating = round(sum(ratings.values()) / len(ratings), 2) if ratings else 0

        rows.append({
            "Voter": row.get("voter", ""),
            "Nominee": row.get("nominee", ""),
            "Work Quality": ratings.get("Work Quality", ""),
            "Ownership": ratings.get("Ownership", ""),
            "Team Support": ratings.get("Team Support", ""),
            "Reliability": ratings.get("Reliability", ""),
            "Average Rating": avg_rating,
            "Timestamp": row.get("timestamp", ""),
        })
    return rows

def to_csv_text(rows):
    if not rows:
        return ""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()

# =========================================================
# PAGE SETUP
# =========================================================
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
st.title(APP_TITLE)

if "just_submitted" not in st.session_state:
    st.session_state.just_submitted = False

# =========================================================
# LOAD DATA
# =========================================================
votes_data = load_votes()
voted_users = get_voted_users(votes_data)
available_voters = [emp for emp in EMPLOYEES if emp not in voted_users]

# =========================================================
# VOTING SECTION
# =========================================================
st.subheader("🗳️ Vote for 2 employees")

if st.session_state.just_submitted:
    st.success("✅ Vote submitted successfully!")
    st.caption("Your vote is recorded. Thank you.")
else:
    if not available_voters:
        st.warning("All employees have already voted.")
    else:
        voter = st.selectbox("Select your name", available_voters)

        st.caption("Select exactly 2 employees. You cannot vote for yourself.")

        nominee_options = [emp for emp in EMPLOYEES if emp != voter]

        nominees = st.multiselect(
            "Select 2 nominees",
            nominee_options,
            max_selections=VOTES_REQUIRED
        )

        ratings = {}

        if len(nominees) > 0:
            st.markdown("### Rate the selected nominees")

            for nominee in nominees:
                st.markdown(f"#### {nominee}")
                ratings[nominee] = {}

                for category in RATING_CATEGORIES:
                    ratings[nominee][category] = st.slider(
                        f"{nominee} - {category}",
                        min_value=1,
                        max_value=5,
                        value=3,
                        key=f"{voter}_{nominee}_{category}"
                    )

        if st.button("Submit Vote"):
            if voter in voted_users:
                st.error("This person has already voted.")
            elif len(nominees) != VOTES_REQUIRED:
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
                st.session_state.just_submitted = True
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

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Show Results"):
                latest_votes = load_votes()
                final_results = calculate_results(latest_votes)
                raw_rows = build_raw_vote_rows(latest_votes)

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

                st.markdown("### 🧾 Raw Vote Details")
                st.dataframe(raw_rows, use_container_width=True)

                if final_results:
                    winner = final_results[0]
                    st.success(f"🏆 Winner: {winner['Employee']} | Score: {winner['Final Score']}")

                st.markdown("### ⬇️ Download Data")
                st.download_button(
                    "Download Raw Votes CSV",
                    data=to_csv_text(raw_rows),
                    file_name="raw_votes.csv",
                    mime="text/csv"
                )
                st.download_button(
                    "Download Rankings CSV",
                    data=to_csv_text(final_results),
                    file_name="rankings.csv",
                    mime="text/csv"
                )

        with col2:
            st.markdown("### ♻️ Reset Voting")
            st.caption("This clears all saved votes and starts fresh.")
            reset_text = st.text_input("Type RESET to confirm", key="reset_confirm")

            if st.button("Clear All Votes"):
                if reset_text == "RESET":
                    save_votes([])
                    st.success("All votes cleared. You can start fresh now.")
                    st.rerun()
                else:
                    st.error("Type RESET exactly to confirm clearing all votes.")

    elif admin_password != "":
        st.error("❌ Incorrect password")
