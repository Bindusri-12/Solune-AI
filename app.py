import streamlit as st
import pandas as pd
from datetime import datetime, date
from sklearn.tree import DecisionTreeClassifier

st.set_page_config(
    page_title="Solune AI",
    page_icon="🌙",
    layout="wide",
)

# ---------- SESSION STORAGE ----------
DEFAULTS = {
    "mood_history": [],
    "journal_entries": [],
    "weekly_goals": {
        "Take a short break": False,
        "Make time for a relaxing activity": False,
        "Reflect on my day": False,
        "Follow a calming bedtime routine": False,
    },
    "latest_suggestion": None,
    "latest_checkin_date": None,
    "display_name": "",
    "theme": "Lavender",
    "chat_messages": [],
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        # Copy mutable defaults so each session gets its own objects.
        st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value

# ---------- CUSTOMISATION ----------
with st.sidebar:
    st.title("🌙 Solune AI")
    st.caption("Your personal well-being space")
    st.subheader("🎨 Customise your space")
    st.session_state.display_name = st.text_input(
        "What should we call you?",
        value=st.session_state.display_name,
        placeholder="Enter a nickname (optional)",
        max_chars=30,
    )
    selected_theme = st.selectbox(
        "Choose a theme",
        ["Lavender", "Ocean", "Mint", "Sunset"],
        index=["Lavender", "Ocean", "Mint", "Sunset"].index(st.session_state.theme),
    )
    st.session_state.theme = selected_theme
    page = st.radio(
        "Go to",
        [
            "🏠 Dashboard",
            "💜 Mood Check-In",
            "🌿 Calm Corner",
            "🎯 Weekly Goals",
            "💬 Support Chatbot",
            "📔 Reflection Journal",
            "🤝 Parent Support",
            "🔒 Privacy & About",
        ],
        key="page_selection",
    )
    st.caption("Your session data may reset when the app session restarts.")

themes = {
    "Lavender": ("#f8f5ff", "#66518f", "#7965a8", "#eee7fb"),
    "Ocean": ("#f0f8ff", "#285d78", "#367fa0", "#dceff8"),
    "Mint": ("#f1fbf6", "#28654f", "#3a9270", "#ddf4e8"),
    "Sunset": ("#fff6f0", "#8b4c38", "#c87857", "#fbe7dc"),
}
bg, heading, accent, soft = themes[st.session_state.theme]
st.markdown(
    f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {bg}, #ffffff 72%); }}
    h1, h2, h3 {{ color: {heading}; }}
    div.stButton > button {{
        background-color: {accent}; color: white; border-radius: 12px;
        border: none; padding: 0.45rem 0.9rem;
    }}
    div[data-testid="stMetric"] {{
        background-color: {soft}; padding: 12px; border-radius: 12px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- DEMONSTRATION MODEL ----------
# Illustrative synthetic data only; this is not a validated assessment.
data = pd.DataFrame({
    "mood": [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 1, 2, 3, 4, 1, 2, 3, 0, 4],
    "stress": [5, 4, 5, 4, 3, 3, 2, 2, 1, 1, 5, 4, 3, 2, 1, 5, 4, 3, 3, 2],
    "sleep": [4, 6, 5, 6, 6, 7, 7, 8, 8, 9, 5, 5, 7, 6, 8, 4, 6, 7, 7, 8],
    "pressure": [5, 5, 4, 4, 3, 4, 2, 2, 1, 1, 4, 5, 3, 2, 1, 5, 4, 3, 4, 2],
    "support": [
        "Extra support", "Extra support", "Extra support", "Extra support",
        "Gentle check-in", "Gentle check-in", "Self-care", "Self-care",
        "Self-care", "Self-care", "Extra support", "Extra support",
        "Gentle check-in", "Self-care", "Self-care", "Extra support",
        "Gentle check-in", "Gentle check-in", "Gentle check-in", "Self-care",
    ],
})
model = DecisionTreeClassifier(max_depth=4, random_state=42)
model.fit(data[["mood", "stress", "sleep", "pressure"]], data["support"])

mood_options = {"Very low": 0, "Low": 1, "Okay": 2, "Good": 3, "Very good": 4}

def navigate_to(target):
    st.session_state.page_selection = target

def greeting():
    name = st.session_state.display_name.strip()
    return f"Hello, {name} 🌙" if name else "Hello 🌙"

def latest_checkin_today():
    today = date.today().isoformat()
    return any(item.get("Date") == today for item in st.session_state.mood_history)

def show_suggestion(prediction, sleep_hours=None):
    if prediction == "Extra support":
        st.info(
            "You may benefit from extra support. Consider talking with a trusted "
            "adult or school counsellor about how things have been feeling."
        )
    elif prediction == "Gentle check-in":
        st.info(
            "Take things one step at a time. A short break, a calming activity, "
            "or splitting study into smaller tasks may help."
        )
    else:
        st.info(
            "Keep making space for yourself. Breaks, relaxing activities, and "
            "a steady rest routine can support your well-being."
        )
    if sleep_hours is not None and sleep_hours < 7:
        st.write("🌙 You could reflect on your bedtime routine and whether you are getting enough rest.")
    st.caption(
        "Suggestions are based on a Decision Tree trained on illustrative synthetic data. "
        "They are not a validated mental-health assessment or diagnosis."
    )

# ---------- DASHBOARD ----------
if page == "🏠 Dashboard":
    st.title("🌙 Solune AI")
    st.subheader(greeting())
    st.write("A little space to check in with yourself, pause, and reflect.")
    st.info(
        "Student project prototype. Check-ins, goals, and journal notes are held "
        "in this active session and are not automatically sent to parents."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Today's check-in", "Completed" if latest_checkin_today() else "Not yet")
    with col2:
        done = sum(st.session_state.weekly_goals.values())
        st.metric("Weekly goals", f"{done}/{len(st.session_state.weekly_goals)}")
    with col3:
        st.metric("Saved reflections", len(st.session_state.journal_entries))

    st.subheader("✨ Quick shortcuts")
    q1, q2 = st.columns(2)
    with q1:
        st.button(
            "💜 Do a mood check-in", use_container_width=True,
            on_click=navigate_to, args=("💜 Mood Check-In",)
        )
        st.button(
            "🌿 Visit Calm Corner", use_container_width=True,
            on_click=navigate_to, args=("🌿 Calm Corner",)
        )
    with q2:
        st.button(
            "🎯 Review weekly goals", use_container_width=True,
            on_click=navigate_to, args=("🎯 Weekly Goals",)
        )
        st.button(
            "💬 Open support chatbot", use_container_width=True,
            on_click=navigate_to, args=("💬 Support Chatbot",)
        )

    if st.session_state.mood_history:
        st.subheader("📈 Your recent check-ins")
        recent_df = pd.DataFrame(st.session_state.mood_history[-7:])
        st.line_chart(recent_df.set_index("Time")[["Mood score", "Stress level"]])
    else:
        st.caption("Your recent check-in chart will appear here after you record a mood check-in.")


# ---------- MOOD CHECK-IN ----------
elif page == "💜 Mood Check-In":
    st.title("💜 Mood Check-In")
    st.write("There is no right or wrong answer. Choose what feels closest to your day.")
    mood = st.select_slider(
        "How are you feeling today?",
        options=list(mood_options.keys()),
        value="Okay",
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
            "pressure": pressure,
        }])
        prediction = model.predict(answers)[0]
        st.session_state.mood_history.append({
            "Time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "Date": now.date().isoformat(),
            "Mood": mood,
            "Mood score": mood_options[mood],
            "Stress level": stress,
            "Sleep hours": sleep,
            "Academic pressure": pressure,
        })
        st.session_state.latest_suggestion = prediction
        st.session_state.latest_checkin_date = now.date().isoformat()
        st.subheader("✨ Your supportive suggestions")
        show_suggestion(prediction, sleep)

    if st.session_state.latest_suggestion:
        st.divider()
        st.subheader("Most recent suggestion")
        show_suggestion(st.session_state.latest_suggestion)

    st.divider()
    st.subheader("📈 My Mood History")
    if st.session_state.mood_history:
        history_df = pd.DataFrame(st.session_state.mood_history)
        st.line_chart(history_df.set_index("Time")[["Mood score", "Stress level"]])
        st.dataframe(
            history_df[["Time", "Mood", "Stress level", "Sleep hours", "Academic pressure"]],
            use_container_width=True,
            hide_index=True,
        )
        if st.button("Clear mood history"):
            st.session_state.mood_history = []
            st.session_state.latest_suggestion = None
            st.rerun()
    else:
        st.info("Your chart will appear after your first mood check-in.")

# ---------- CALM CORNER ----------
elif page == "🌿 Calm Corner":
    st.title("🌿 Calm Corner")
    st.write("Choose a small activity. You can stop or skip any exercise whenever you like.")
    activity = st.selectbox(
        "Choose an activity",
        ["Gentle breathing", "5-4-3-2-1 grounding", "Tiny reset break", "Positive moment"],
    )
    if activity == "Gentle breathing":
        st.subheader("A gentle breathing pause")
        st.write("Sit comfortably if you can. Keep your breathing natural and easy; don't force or hold your breath.")
        st.markdown(
            f"""
            <div style="background:{soft}; padding:22px; border-radius:16px; text-align:center;">
                <div style="font-size:42px;">🌬️</div>
                <div style="font-size:22px; color:{heading}; font-weight:600;">Breathe in gently</div>
                <div>Then breathe out slowly, at a comfortable pace.</div>
                <div style="margin-top:10px;">Repeat for a few comfortable breaths, or stop whenever you want.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif activity == "5-4-3-2-1 grounding":
        st.subheader("Notice your surroundings")
        st.write("Take your time. You can do only the steps that feel comfortable.")
        for prompt in [
            "5 things you can see",
            "4 things you can feel (such as your feet on the floor)",
            "3 things you can hear",
            "2 things you can smell, or two scents you like",
            "1 thing you appreciate about this moment",
        ]:
            st.markdown(f"- {prompt}")
    elif activity == "Tiny reset break":
        st.subheader("A tiny reset")
        st.write("Try one small, comfortable option:")
        st.markdown("- Stretch gently if that feels okay.\n- Drink some water.\n- Look away from your screen for a moment.\n- Tidy one small part of your desk.\n- Step somewhere quiet or get a little fresh air, if possible.")
    else:
        st.subheader("Find one positive moment")
        st.write("Think of one small thing from today that felt pleasant, interesting, or kind.")
        st.text_area("Optional note (kept only in this active session if you save it nowhere)", key="positive_moment", max_chars=500)
    st.caption("These are general well-being activities, not medical advice. Skip anything that makes you uncomfortable.")

# ---------- WEEKLY GOALS ----------
elif page == "🎯 Weekly Goals":
    st.title("🎯 Weekly Well-being Goals")
    st.write("Choose gentle, realistic goals for this week. These are invitations, not rules.")
    st.caption("Goal progress is stored only for this active session.")
    for goal in list(st.session_state.weekly_goals.keys()):
        st.session_state.weekly_goals[goal] = st.checkbox(
            goal,
            value=st.session_state.weekly_goals[goal],
            key=f"goal_{goal}",
        )
    done = sum(st.session_state.weekly_goals.values())
    total = len(st.session_state.weekly_goals)
    st.progress(done / total if total else 0)
    st.write(f"**Progress:** {done} of {total} goals checked off.")
    if done == total:
        st.success("You checked off every goal. Remember, your well-being matters more than completing a list.")
    if st.button("Reset weekly goals"):
        st.session_state.weekly_goals = {goal: False for goal in st.session_state.weekly_goals}
        for goal in list(st.session_state.weekly_goals.keys()):
            st.session_state.pop(f"goal_{goal}", None)
        st.rerun()

# ---------- GUIDED SUPPORT CHATBOT ----------
elif page == "💬 Support Chatbot":
    st.title("💬 Solune Support Guide")
    st.write(
        "This is a guided, rule-based helper with prepared suggestions. "
        "It does not use a live AI service and cannot diagnose or replace a trusted person or professional."
    )
    choice = st.selectbox(
        "What would you like help with today?",
        [
            "Choose a topic",
            "I feel stressed about studies",
            "I feel worried or overwhelmed",
            "I want to calm down",
            "I feel lonely or need someone to talk to",
            "I want help asking an adult for support",
            "I am not sure what I need",
        ],
    )
    responses = {
        "I feel stressed about studies": (
            "Try choosing one small task and working on it for a short, manageable period. "
            "Take a break between tasks, and consider telling a teacher or trusted adult if the workload feels too much."
        ),
        "I feel worried or overwhelmed": (
            "Pause and name one thing you can do next—not everything at once. You could try a grounding activity "
            "in Calm Corner or talk with someone who listens without judging."
        ),
        "I want to calm down": (
            "Visit Calm Corner and choose gentle breathing or grounding. Keep it comfortable and stop if it doesn't help."
        ),
        "I feel lonely or need someone to talk to": (
            "You deserve to be heard. Consider reaching out to a friend, family member, teacher, school counsellor, "
            "or another trusted adult. You can start with: “Could you listen to me for a few minutes?”"
        ),
        "I want help asking an adult for support": (
            "You could say: “I've had a lot on my mind lately. Could we talk? I don't need you to fix everything; "
            "I'd appreciate it if you listened.”"
        ),
        "I am not sure what I need": (
            "That's okay. You might start with a drink of water, a short pause, writing down one thought, "
            "or talking with someone you trust. You don't have to figure everything out at once."
        ),
    }
    if choice != "Choose a topic":
        st.subheader("A gentle suggestion")
        st.info(responses[choice])
    st.divider()
    st.warning(
        "If you feel unsafe or a problem feels too big to manage alone, please tell a trusted adult or school counsellor. "
        "If there is immediate danger, seek help from a nearby trusted adult or local emergency service."
    )

# ---------- REFLECTION JOURNAL ----------
elif page == "📔 Reflection Journal":
    st.title("📔 Daily Reflection Journal")
    st.write("Writing is optional. Avoid entering passwords, contact details, or other sensitive information.")
    with st.form("journal_form"):
        journal_note = st.text_area(
            "How was your day? What went well, and what felt challenging?",
            placeholder="Write your reflection here...",
            max_chars=2000,
        )
        save_journal = st.form_submit_button("Save reflection")
    if save_journal:
        if journal_note.strip():
            st.session_state.journal_entries.append({
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Reflection": journal_note.strip(),
            })
            st.success("Your reflection has been added to this session.")
        else:
            st.warning("Write a reflection first, or leave the journal blank.")
    if st.session_state.journal_entries:
        st.subheader("My saved reflections")
        for index, entry in enumerate(reversed(st.session_state.journal_entries)):
            with st.expander(f"Reflection — {entry['Time']}"):
                st.write(entry["Reflection"])
                if st.button("Delete this reflection", key=f"delete_journal_{index}"):
                    original_index = len(st.session_state.journal_entries) - 1 - index
                    st.session_state.journal_entries.pop(original_index)
                    st.rerun()
        if st.button("Clear all reflections"):
            st.session_state.journal_entries = []
            st.rerun()
    else:
        st.caption("Your saved reflections will appear here.")

# ---------- PARENT SUPPORT ----------
elif page == "🤝 Parent Support":
    st.title("🤝 Parent & Trusted Adult Support")
    st.write(
        "Parents, guardians, teachers, and trusted adults can help by listening patiently, "
        "asking open questions, and offering support without judgement."
    )
    consent = st.checkbox("I'd like a conversation starter to ask a trusted adult for support.")
    if consent:
        st.success(
            "I've been feeling under pressure lately. Could we talk about it? "
            "I would appreciate your support."
        )
        st.caption("This displays a message for you. It does not contact a parent or share your check-in.")

# ---------- PRIVACY & ABOUT ----------
elif page == "🔒 Privacy & About":
    st.title("🔒 Privacy & About")
    st.write(
        "Solune AI is a student project prototype. Mood check-ins, goals, and journal entries are kept in "
        "Streamlit session state. They are not saved to a permanent database by this app and are not "
        "automatically shared with parents. Session data may disappear when the session resets."
    )
    st.write(
        "The support suggestions use a small Decision Tree trained on illustrative synthetic data. "
        "The guided chatbot uses prepared responses rather than a live AI model. Neither is a validated "
        "mental-health assessment."
    )
    st.caption("Solune AI | Student project prototype | For learning and demonstration purposes")
