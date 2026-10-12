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
    "positive_moment": "",
    "support_plan": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value

# ---------- CUSTOMISATION & NAVIGATION ----------
PAGES = [
    "🏠 Dashboard",
    "💜 Mood Check-In",
    "🌿 Calm Corner",
    "🎯 Weekly Goals",
    "💬 Support Chatbot",
    "📔 Reflection Journal",
    "🤝 Parent Support",
    "🔒 Privacy & About",
]

if "page" not in st.session_state:
    st.session_state.page = PAGES[0]

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
    theme_names = ["Lavender", "Ocean", "Mint", "Sunset"]
    if st.session_state.theme not in theme_names:
        st.session_state.theme = "Lavender"
    st.session_state.theme = st.selectbox(
        "Choose a theme",
        theme_names,
        index=theme_names.index(st.session_state.theme),
    )
    st.radio("Go to", PAGES, key="page")
    st.caption("Session data may reset when the app session restarts.")

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
# Illustrative synthetic data only; not a validated mental-health assessment.
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
        st.write(
            "🌙 You could reflect on your bedtime routine and whether you are getting enough rest."
        )
    st.caption(
        "Suggestions are based on a Decision Tree trained on illustrative synthetic data. "
        "They are not a validated mental-health assessment or diagnosis."
    )


# ---------- DASHBOARD ----------
page = st.session_state.page

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
        if st.button("💜 Do a mood check-in", use_container_width=True):
            st.session_state.page = "💜 Mood Check-In"
            st.rerun()
        if st.button("🌿 Visit Calm Corner", use_container_width=True):
            st.session_state.page = "🌿 Calm Corner"
            st.rerun()
    with q2:
        if st.button("🎯 Review weekly goals", use_container_width=True):
            st.session_state.page = "🎯 Weekly Goals"
            st.rerun()
        if st.button("💬 Open support chatbot", use_container_width=True):
            st.session_state.page = "💬 Support Chatbot"
            st.rerun()

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
        st.write(
            "Sit comfortably if you can. Keep your breathing natural and easy; "
            "don't force or hold your breath."
        )
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
        st.markdown(
            "- Stretch gently if that feels okay.\n"
            "- Drink some water.\n"
            "- Look away from your screen for a moment.\n"
            "- Tidy one small part of your desk.\n"
            "- Step somewhere quiet or get a little fresh air, if possible."
        )
    else:
        st.subheader("Find one positive moment")
        st.write("Think of one small thing from today that felt pleasant, interesting, or kind.")
        st.text_area(
            "Optional note (not saved unless you choose to write it in your journal)",
            key="positive_moment",
            max_chars=500,
        )
    st.caption(
        "These are general well-being activities, not medical advice. "
        "Skip anything that makes you uncomfortable."
    )

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
        st.success(
            "You checked off every goal. Remember, your well-being matters more than completing a list."
        )
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
    st.write(
        "Writing is optional. Avoid entering passwords, contact details, or other sensitive information."
    )
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

# ---------- IMPROVED PARENT & TRUSTED ADULT SUPPORT ----------
elif page == "🤝 Parent Support":
    st.title("🤝 Parent & Trusted Adult Support")
    st.write(
        "A supportive space for students and parents to communicate, "
        "understand one another, and take small steps together."
    )

    student_tab, parent_tab = st.tabs(["💜 Student Support", "🌷 Parent Guidance"])

    with student_tab:
        st.subheader("💬 Conversation Starter Generator")
        st.write(
            "Choose what you would like to talk about. You can use the suggested message "
            "as it is or change it to sound like you."
        )
        topic = st.selectbox(
            "What would you like support with?",
            [
                "Academic pressure or exams",
                "Feeling overwhelmed",
                "Needing someone to listen",
                "Asking for help with schoolwork",
                "Balancing study and rest",
                "Something difficult I don't know how to explain",
            ],
            key="support_conversation_topic",
        )
        recipient = st.selectbox(
            "Who would you prefer to talk to?",
            [
                "Parent or guardian",
                "Teacher or school counsellor",
                "Another trusted adult",
            ],
            key="support_recipient",
        )
        student_messages = {
            "Academic pressure or exams": (
                "I've been feeling pressure about my studies lately. Could we talk about what's worrying me "
                "and work out one manageable next step together?"
            ),
            "Feeling overwhelmed": (
                "I've had a lot on my mind, and things feel overwhelming right now. Could you listen to me "
                "for a little while? It would help to talk it through."
            ),
            "Needing someone to listen": (
                "I'd like to share something that's been on my mind. I don't need you to solve everything "
                "straight away. I'd really appreciate it if you could listen."
            ),
            "Asking for help with schoolwork": (
                "I'm finding some of my schoolwork difficult at the moment. Could you help me work out "
                "where to start or who I could ask?"
            ),
            "Balancing study and rest": (
                "I'd like to find a better balance between studying and taking breaks. Could we discuss "
                "a routine that feels manageable?"
            ),
            "Something difficult I don't know how to explain": (
                "Something has been bothering me, and I'm finding it difficult to explain. Could we talk "
                "somewhere comfortable, at a time when we won't feel rushed?"
            ),
        }
        student_message = student_messages[topic]
        st.markdown(f"**Suggested message for your {recipient.lower()}**")
        st.code(student_message, language=None)
        st.caption("Use the copy icon on the message above, or personalise it before sharing.")

        st.divider()
        st.subheader("🌱 My Personal Support Plan")
        st.write(
            "Make a small plan for reaching out. You do not need to enter anyone's name, "
            "phone number, or other personal details."
        )
        trusted_person = st.selectbox(
            "What kind of person could you approach?",
            [
                "Parent or guardian",
                "Teacher",
                "School counsellor",
                "Relative",
                "Another adult I trust",
                "I'm not sure yet",
            ],
            key="support_plan_person",
        )
        approach = st.radio(
            "How would you prefer to start?",
            [
                "Talk in person",
                "Write a message",
                "Ask someone to help me start the conversation",
            ],
            key="support_plan_approach",
        )
        next_step = st.selectbox(
            "Choose one small next step",
            [
                "Find a comfortable time to talk",
                "Use one of the conversation starters above",
                "Write down what I want to say",
                "Ask a trusted person to help me arrange a conversation",
                "Take time to think about what support I need",
            ],
            key="support_plan_next_step",
        )
        if st.button("Create my support plan", use_container_width=True):
            st.session_state.support_plan = {
                "Trusted person": trusted_person,
                "Preferred approach": approach,
                "Next step": next_step,
            }
        if st.session_state.support_plan:
            plan = st.session_state.support_plan
            st.success("Your support plan is ready.")
            st.markdown(f"**Person to approach:** {plan['Trusted person']}")
            st.markdown(f"**How to start:** {plan['Preferred approach']}")
            st.markdown(f"**My next step:** {plan['Next step']}")
            plan_message = (
                "MY SOLUNE AI SUPPORT PLAN\n\n"
                f"Person to approach: {plan['Trusted person']}\n"
                f"How to start: {plan['Preferred approach']}\n"
                f"My next step: {plan['Next step']}"
            )
            st.code(plan_message, language=None)
            st.caption(
                "Your plan is kept in this active app session. It is not automatically sent to anyone."
            )

    with parent_tab:
        st.subheader("🌷 Supporting a Student")
        st.write(
            "A calm, patient response can make it easier for a student to talk about what they need."
        )
        with st.expander("💗 Listen before offering solutions"):
            st.write(
                "Give the student time to speak without interrupting. Try asking: "
                "“Would you like me to listen, or would you like help thinking through a solution?”"
            )
        with st.expander("🌿 Avoid comparisons and judgement"):
            st.write(
                "Avoid comparing marks, behaviour, or progress with other students. "
                "Recognise effort and ask what kind of help would be useful."
            )
        with st.expander("📚 Talk about academic pressure together"):
            st.write(
                "Ask which tasks feel most difficult. Help break work into smaller steps and make "
                "reasonable space for rest, activities, and family time."
            )
        with st.expander("🛡️ Respect privacy while keeping them safe"):
            st.write(
                "Treat personal conversations respectfully. If there is a serious safety concern, "
                "involve an appropriate trusted adult or professional who can help keep the student safe."
            )

        st.subheader("💬 Conversation Starter for Parents")
        parent_topic = st.selectbox(
            "What would you like to discuss with the student?",
            [
                "How they have been feeling",
                "Schoolwork and exams",
                "Rest and daily routine",
                "How I can support them better",
            ],
            key="parent_conversation_topic",
        )
        parent_messages = {
            "How they have been feeling": (
                "I've noticed you may have a lot on your mind. How have things been feeling for you lately? "
                "I'm here to listen, and you don't have to explain everything at once."
            ),
            "Schoolwork and exams": (
                "How are you feeling about your schoolwork at the moment? Let's talk about what feels "
                "difficult and decide together what might make it more manageable."
            ),
            "Rest and daily routine": (
                "How has your daily routine been working for you? Would it help to look at how we can make "
                "time for studying, rest, and the things you enjoy?"
            ),
            "How I can support them better": (
                "I want to understand how I can support you better. Is there something you wish I would "
                "listen to more carefully or something we could approach differently?"
            ),
        }
        st.code(parent_messages[parent_topic], language=None)
        st.caption("Use the copy icon on the message above or adapt it to sound natural.")

        st.subheader("✨ A Gentle Reminder")
        st.info(
            "You do not have to solve everything in one conversation. Listening, showing patience, "
            "and agreeing on one small next step can be a helpful beginning."
        )

    st.divider()
    st.caption(
        "Solune AI provides general supportive guidance. It is a student project prototype, not a "
        "counselling or emergency service. Messages and support plans are not automatically sent to anyone. "
        "If a student feels unsafe or needs urgent help, they should reach out to a trusted adult or "
        "appropriate local emergency service."
    )

# ---------- PRIVACY & ABOUT ----------
elif page == "🔒 Privacy & About":
    st.title("🔒 Privacy & About")
    st.write(
        "Solune AI is a student project prototype. Mood check-ins, goals, journal entries, and support plans "
        "are kept in Streamlit session state. They are not saved to a permanent database by this app and "
        "are not automatically shared with parents. Session data may disappear when the session resets."
    )
    st.write(
        "The support suggestions use a small Decision Tree trained on illustrative synthetic data. "
        "The guided chatbot uses prepared responses rather than a live AI model. Neither is a validated "
        "mental-health assessment."
    )
    st.caption("Solune AI | Student project prototype | For learning and demonstration purposes")
