
import streamlit as st
import pandas as pd
from datetime import datetime
from sklearn.tree import DecisionTreeClassifier

st.set_page_config(
    page_title="Solune AI",
    page_icon="🌙",
    layout="centered"
)

# ---------- SESSION STORAGE ----------
if "mood_history" not in st.session_state:
    st.session_state.mood_history = []

if "journal_entries" not in st.session_state:
    st.session_state.journal_entries = []

# ---------- DESIGN ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #f8f5ff, #ffffff);
}
h1, h2, h3 {
    color: #66518f;
}
div.stButton > button {
    background-color: #7965a8;
    color: white;
    border-radius: 12px;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# ---------- DEMONSTRATION DATA ----------
# Illustrative synthetic data, not real student records.
data = pd.DataFrame({
    "mood": [0, 0, 1, 1, 2, 2, 3, 3, 4, 4,
             0, 1, 2, 3, 4, 1, 2, 3, 0, 4],
    "stress": [5, 4, 5, 4, 3, 3, 2, 2, 1, 1,
               5, 4, 3, 2, 1, 5, 4, 3, 3, 2],
    "sleep": [4, 6, 5, 6, 6, 7, 7, 8, 8, 9,
              5, 5, 7, 6, 8, 4, 6, 7, 7, 8],
    "pressure": [5, 5, 4, 4, 3, 4, 2, 2, 1, 1,
                 4, 5, 3, 2, 1, 5, 4, 3, 4, 2],
    "support": [
        "Extra support", "Extra support",
        "Extra support", "Extra support",
        "Gentle check-in", "Gentle check-in",
        "Self-care", "Self-care", "Self-care", "Self-care",
        "Extra support", "Extra support",
        "Gentle check-in", "Self-care", "Self-care",
        "Extra support", "Gentle check-in",
        "Gentle check-in", "Gentle check-in", "Self-care"
    ]
})

X = data[["mood", "stress", "sleep", "pressure"]]
y = data["support"]

model = DecisionTreeClassifier(max_depth=4, random_state=42)
model.fit(X, y)

# ---------- HOME ----------
st.title("🌙 Solune AI")
st.subheader("A little space to check in with yourself")

st.write(
    "Notice how you're feeling, reflect on your day, "
    "and explore gentle suggestions for your well-being."
)

st.info(
    "Student project prototype. Check-ins and journal notes "
    "are kept in this active session and are not sent to parents."
)

# ---------- MOOD CHECK-IN ----------
st.header("💜 Mood Check-In")

mood_options = {
    "Very low": 0,
    "Low": 1,
    "Okay": 2,
    "Good": 3,
    "Very good": 4
}

mood = st.select_slider(
    "How are you feeling today?",
    options=list(mood_options.keys()),
    value="Okay"
)

stress = st.slider("How stressed do you feel?", 1, 5, 3)
sleep = st.slider("Approximately how many hours did you sleep?", 0, 12, 7)
pressure = st.slider("How much academic pressure do you feel?", 1, 5, 3)

if st.button("Get my suggestions", use_container_width=True):
    now = datetime.now()

    answers = pd.DataFrame([{
        "mood": mood_options[mood],
        "stress": stress,
        "sleep": sleep,
        "pressure": pressure
    }])

    # Record the check-in in the current session.
    st.session_state.mood_history.append({
        "Time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "Mood": mood,
        "Mood score": mood_options[mood],
        "Stress level": stress,
        "Sleep hours": sleep,
        "Academic pressure": pressure
    })

    prediction = model.predict(answers)[0]

    st.session_state.latest_suggestion = prediction

    st.header("✨ Your supportive suggestions")

    if prediction == "Extra support":
        st.write(
            "You may benefit from some extra support. "
            "Consider talking with a trusted adult or school counsellor."
        )
    elif prediction == "Gentle check-in":
        st.write(
            "Take things one step at a time. Try a short break, "
            "a calming activity, or smaller study tasks."
        )
    else:
        st.write(
            "Keep making space for yourself. Relaxing activities, "
            "regular sleep, and breaks can support your well-being."
        )

    if sleep < 7:
        st.write(
            "🌙 You could reflect on your bedtime routine "
            "and whether you are getting enough rest."
        )

    st.caption(
        "Suggestions use a Decision Tree trained on illustrative "
        "synthetic data. They are not a validated mental-health assessment."
    )

# ---------- MOOD HISTORY ----------
st.divider()
st.header("📈 My Mood History")

st.write(
    "Review the check-ins you've recorded during this active session."
)

if st.session_state.mood_history:
    history_df = pd.DataFrame(st.session_state.mood_history)

    st.line_chart(
        history_df.set_index("Time")[["Mood score", "Stress level"]]
    )

    st.dataframe(
        history_df[[
            "Time", "Mood", "Stress level",
            "Sleep hours", "Academic pressure"
        ]],
        use_container_width=True,
        hide_index=True
    )

    if st.button("Clear mood history"):
        st.session_state.mood_history = []
        st.rerun()
else:
    st.info(
        "Your chart will appear after you complete your first mood check-in. "
        "Try recording check-ins at different times to compare them."
    )

# ---------- DAILY JOURNAL ----------
st.divider()
st.header("📔 Daily Reflection Journal")

st.write(
    "Take a moment to reflect. Writing is optional, "
    "and you can leave this section blank."
)

with st.form("journal_form"):
    journal_note = st.text_area(
        "How was your day? What went well, and what felt challenging?",
        placeholder="Write your reflection here...",
        max_chars=2000
    )

    save_journal = st.form_submit_button("Save reflection")

    if save_journal:
        if journal_note.strip():
            st.session_state.journal_entries.append({
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Reflection": journal_note.strip()
            })
            st.success("Your reflection has been added to this session.")
        else:
            st.warning("Write a reflection first, or leave the journal blank.")

if st.session_state.journal_entries:
    st.subheader("My saved reflections")

    for index, entry in enumerate(
        reversed(st.session_state.journal_entries)
    ):
        with st.expander(f"Reflection — {entry['Time']}"):
            st.write(entry["Reflection"])

            if st.button(
                "Delete this reflection",
                key=f"delete_journal_{index}"
            ):
                original_index = len(st.session_state.journal_entries) - 1 - index
                st.session_state.journal_entries.pop(original_index)
                st.rerun()

    if st.button("Clear all reflections"):
        st.session_state.journal_entries = []
        st.rerun()

# ---------- PARENT SUPPORT ----------
st.divider()
st.header("👨‍👩‍👧 Parent Support")

st.write(
    "Parents and trusted adults can help by listening patiently, "
    "asking open questions, and offering support without judgement."
)

consent = st.checkbox(
    "I'd like a conversation starter to ask a trusted adult for support."
)

if consent:
    st.success(
        "I have been feeling under pressure lately. "
        "Could we talk about it? I would appreciate your support."
    )
    st.caption(
        "This displays a message for you. It does not contact "
        "a parent or share your check-in."
    )

# ---------- PRIVACY ----------
st.divider()
st.header("🔒 Privacy and About")

st.write(
    "This prototype keeps mood check-ins and journal entries in "
    "Streamlit session state. They are not saved to a permanent "
    "database by this app, and they are not automatically shared "
    "with parents. Session data may disappear when the session resets."
)

st.caption(
    "Solune AI | Student project prototype | "
    "For learning and demonstration purposes"
)
