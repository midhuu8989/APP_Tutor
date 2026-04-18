import streamlit as st
import pandas as pd
from openai import OpenAI
from datetime import datetime

# ---------------- CONFIG ----------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
st.set_page_config(page_title="AI Banking LMS", layout="wide")

# ---------------- UI ----------------
st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(135deg,#fff3e0,#ffe0b2,#ffd699);
    color:#333;
    font-family: 'Segoe UI', sans-serif;
}

/* Header */
.header {
    display:flex;
    align-items:center;
    gap:20px;
    background: linear-gradient(90deg,#ff8c00,#ffb347);
    padding:15px;
    border-radius:12px;
    margin-bottom:20px;
}

/* Logo */
.header img {
    height:50px;
}

/* Title */
.header-title {
    font-size:26px;
    font-weight:bold;
    color:black;
}

/* Cards */
.card {
    background:white;
    padding:15px;
    border-radius:12px;
    margin-bottom:15px;
    border-left:6px solid #ff8c00;
}

/* Buttons */
.stButton>button {
    background:linear-gradient(90deg,#ff8c00,#ffcc66);
    color:black;
    border:none;
    border-radius:10px;
    font-weight:bold;
}

/* Inputs */
.stTextInput input, .stSelectbox div {
    background:#fffaf5 !important;
    color:black !important;
}

/* Radio fix */
.stRadio > div {
    padding: 5px;
}

/* Feedback */
.correct { color:green; font-weight:bold; }
.wrong { color:red; font-weight:bold; }

</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<div class="header">
    <img src="logo.png">
    <div class="header-title">🏦 AI Banking LMS</div>
</div>
""", unsafe_allow_html=True)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    activity_df = pd.read_csv("activity.csv")
    quiz_df = pd.read_csv("quiz.csv")

    activity_df.columns = activity_df.columns.str.strip()
    quiz_df.columns = quiz_df.columns.str.strip()

    return activity_df, quiz_df

activity_df, quiz_df = load_data()

# ---------------- USER ----------------
name = st.text_input("👤 Enter your name")

# ---------------- TOPICS ----------------
topics = sorted(list(set(activity_df["Topic"]).union(set(quiz_df["Topic"]))))

if not topics:
    st.error("No topics found")
    st.stop()

selected_topic = st.selectbox("📚 Select Topic", topics)

# ---------------- FILTER ----------------
filtered_activities = activity_df[activity_df["Topic"] == selected_topic]
filtered_quiz = quiz_df[quiz_df["Topic"] == selected_topic]

# ---------------- ACTIVITIES ----------------
st.subheader("🛠️ Learning Activities")

for _, row in filtered_activities.iterrows():

    # ✅ NEW FIX: Dataset display (only addition)
    dataset_display = ""
    if "Dataset" in activity_df.columns and pd.notna(row.get("Dataset", "")):
        dataset_display = f"<br><br><b>📊 Sample Dataset:</b><br><pre>{row['Dataset']}</pre>"

    st.markdown(f"""
    <div class="card">
    <b>📌 Scenario:</b> {row['Scenario']}<br><br>
    <b>🧪 Task:</b> {row['Task']}<br><br>
    <b>🎯 Output:</b> {row['Output']}
    {dataset_display}
    </div>
    """, unsafe_allow_html=True)

# ================= QUIZ =================
st.subheader("🧠 Quiz")

if "attempts" not in st.session_state:
    st.session_state.attempts = {}

if "correct" not in st.session_state:
    st.session_state.correct = {}

for idx, (_, row) in enumerate(filtered_quiz.iterrows(), start=1):

    q_key = f"q_{idx}"

    if q_key not in st.session_state.attempts:
        st.session_state.attempts[q_key] = 0
        st.session_state.correct[q_key] = False

    options = [
        row["Option1"],
        row["Option2"],
        row["Option3"],
        row["Option4"]
    ]

    st.markdown(f"""
    <div class="card">
    <b>Q{idx}: {row['Question']}</b>
    </div>
    """, unsafe_allow_html=True)

    selected = st.radio("", options, key=f"radio_{idx}")

    if st.button(f"Submit Q{idx}", key=f"btn_{idx}"):

        if not st.session_state.correct[q_key]:

            st.session_state.attempts[q_key] += 1

            if selected == row["Correct Answer"]:
                st.session_state.correct[q_key] = True
                st.success("✅ Correct!")
            else:
                st.error("❌ Wrong!")

    if st.session_state.correct[q_key]:
        st.markdown(f"<div class='correct'>✔ Correct Answer: {row['Correct Answer']}</div>", unsafe_allow_html=True)
    elif st.session_state.attempts[q_key] > 0:
        st.markdown("<div class='wrong'>❌ Wrong Answer</div>", unsafe_allow_html=True)

    if st.session_state.attempts[q_key] >= 2 and not st.session_state.correct[q_key]:
        st.warning(f"🔒 Correct Answer: {row['Correct Answer']}")

# ---------------- FINAL SCORE ----------------
if st.button("🎯 Final Score"):

    score = sum(st.session_state.correct.values())

    st.success(f"🎯 Score: {score}/{len(filtered_quiz)}")

    new_entry = pd.DataFrame({
        "Name": [name],
        "Topic": [selected_topic],
        "Score": [score],
        "Time": [datetime.now()]
    })

    try:
        leaderboard = pd.read_csv("leaderboard.csv")
        leaderboard = pd.concat([leaderboard, new_entry], ignore_index=True)
    except:
        leaderboard = new_entry

    leaderboard.to_csv("leaderboard.csv", index=False)

    # ================= UPDATED LEADERBOARD =================
    st.subheader("🏆 Leaderboard")

    leaderboard["Time"] = pd.to_datetime(leaderboard["Time"])

    # 🔥 Recent 10
    st.markdown("### 🔥 Recent 10 Attempts")
    recent_10 = leaderboard.sort_values(by="Time", ascending=False).head(10)
    st.dataframe(recent_10)

    # 📥 Filters
    st.markdown("### 📥 Download Reports")

    filter_option = st.selectbox(
        "Select Time Range",
        ["Today", "Last 7 Days", "Last 30 Days"]
    )

    now = pd.Timestamp.now()

    if filter_option == "Today":
        filtered = leaderboard[leaderboard["Time"].dt.date == now.date()]
    elif filter_option == "Last 7 Days":
        filtered = leaderboard[leaderboard["Time"] >= now - pd.Timedelta(days=7)]
    else:
        filtered = leaderboard[leaderboard["Time"] >= now - pd.Timedelta(days=30)]

    st.dataframe(filtered)

    csv = filtered.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name=f"leaderboard_{filter_option.replace(' ','_')}.csv",
        mime="text/csv"
    )

# ================= CHAT =================
st.divider()
st.subheader("💬 AI Tutor")

if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = {}

if selected_topic not in st.session_state.chat_memory:
    st.session_state.chat_memory[selected_topic] = []

messages = st.session_state.chat_memory[selected_topic]

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask your doubt...")

if user_input:
    messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Explain {user_input} in simple banking example under topic {selected_topic}"
            }]
        )

        reply = response.choices[0].message.content
        st.markdown(reply)

    messages.append({"role": "assistant", "content": reply})
