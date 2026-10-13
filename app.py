import base64
import hashlib
import json
import os
import sqlite3
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.tree import DecisionTreeClassifier
from cryptography.fernet import Fernet, InvalidToken

# Solune AI 2.0 — local, single-user prototype
# Run locally. Do not deploy publicly without adding user separation and a reviewed security design.

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "solune_data.db"
CATEGORIES = {
    "mood": "Mood check-ins",
    "goals": "Weekly goals",
    "calm": "Calm Corner preferences",
    "reflections": "Personal reflections",
    "insights": "AI insights history",
}
DEFAULT_GOALS = [
    "Take a short break",
    "Make time for a relaxing activity",
    "Reflect on my day",
    "Follow a calming bedtime routine",
]
MOOD_GUIDE = {
    1: "Very low — I'm having a really difficult day",
    2: "Low — I'm feeling a little down",
    3: "Normal / okay — I'm feeling average or just okay",
    4: "Good — I'm feeling good overall",
    5: "Very good — I'm feeling really positive",
}
STRESS_GUIDE = {
    1: "Very low", 2: "Low", 3: "Moderate / normal", 4: "High", 5: "Very high"
}
QUALITY_GUIDE = {1: "Very poor", 2: "Poor", 3: "Average", 4: "Good", 5: "Excellent"}

# Small illustrative Decision Tree trained on synthetic examples for the school project.
# This is a demonstration classifier, not a validated mental-health assessment.
TRAINING_DATA = pd.DataFrame({
    "mood": [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 2, 3, 4, 1, 5, 3],
    "stress": [5, 4, 5, 4, 3, 4, 2, 3, 1, 2, 3, 2, 4, 5, 3, 3],
    "sleep": [1, 2, 4, 5, 6, 7, 7, 6, 8, 9, 6, 8, 5, 4, 7, 7],
    "pressure": [5, 5, 4, 5, 3, 4, 2, 2, 1, 2, 4, 2, 4, 5, 1, 3],
    "suggestion_type": ["Extra support", "Extra support", "Extra support", "Extra support", "Gentle check-in", "Gentle check-in", "Self-care", "Self-care", "Self-care", "Self-care", "Gentle check-in", "Self-care", "Gentle check-in", "Extra support", "Self-care", "Gentle check-in"],
})
DECISION_TREE = DecisionTreeClassifier(max_depth=4, random_state=42)
DECISION_TREE.fit(TRAINING_DATA[["mood", "stress", "sleep", "pressure"]], TRAINING_DATA["suggestion_type"])

st.set_page_config(page_title="Solune AI 2.0", page_icon="🌙", layout="wide")


def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.commit()
    return conn


def get_setting(key, default=None):
    with db_connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row[0])
    except (TypeError, json.JSONDecodeError):
        return default


def set_setting(key, value):
    with db_connect() as conn:
        conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value, ensure_ascii=False)))
        conn.commit()


def read_records(category):
    with db_connect() as conn:
        rows = conn.execute("SELECT id, created_at, payload FROM records WHERE category=? ORDER BY id", (category,)).fetchall()
    result = []
    for record_id, created_at, payload in rows:
        try:
            item = json.loads(payload)
            item["_id"] = record_id
            item.setdefault("Time", created_at)
            result.append(item)
        except (TypeError, json.JSONDecodeError):
            continue
    return result


def save_record(category, item):
    timestamp = item.get("Time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_connect() as conn:
        conn.execute("INSERT INTO records(category,created_at,payload) VALUES(?,?,?)", (category, timestamp, json.dumps(item, ensure_ascii=False)))
        conn.commit()


def delete_record(record_id):
    with db_connect() as conn:
        conn.execute("DELETE FROM records WHERE id=?", (int(record_id),))
        conn.commit()


def clear_category(category):
    with db_connect() as conn:
        conn.execute("DELETE FROM records WHERE category=?", (category,))
        conn.commit()


def clear_all():
    with db_connect() as conn:
        conn.execute("DELETE FROM records")
        conn.execute("DELETE FROM settings WHERE key IN ('display_name','theme','welcome_seen','save_mood','save_goals','save_calm','save_reflections','save_insights')")
        conn.commit()


def get_save_pref(category):
    return bool(get_setting("save_" + category, True))


def persist_if_enabled(category, item):
    if get_save_pref(category):
        save_record(category, item)
        return True
    return False


def make_key(password: str, salt: bytes) -> bytes:
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000, dklen=32)
    return base64.urlsafe_b64encode(key)


def make_encrypted_backup(password: str) -> bytes:
    with db_connect() as conn:
        records = conn.execute("SELECT category,created_at,payload FROM records ORDER BY id").fetchall()
        settings = conn.execute("SELECT key,value FROM settings").fetchall()
    data = {"format": "Solune AI encrypted backup", "version": 1,
            "records": [{"category": c, "created_at": t, "payload": p} for c, t, p in records],
            "settings": {k: v for k, v in settings}}
    salt = os.urandom(16)
    token = Fernet(make_key(password, salt)).encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    return b"SOLUNE2\n" + base64.b64encode(salt) + b"\n" + token


def restore_encrypted_backup(upload_bytes: bytes, password: str):
    try:
        header, salt_text, token = upload_bytes.split(b"\n", 2)
        if header != b"SOLUNE2":
            return False, "That file doesn't look like a Solune 2.0 encrypted backup."
        salt = base64.b64decode(salt_text)
        decoded = Fernet(make_key(password, salt)).decrypt(token)
        data = json.loads(decoded.decode("utf-8"))
        if data.get("format") != "Solune AI encrypted backup" or data.get("version") != 1:
            return False, "This backup version is not supported."
        with db_connect() as conn:
            conn.execute("DELETE FROM records")
            conn.execute("DELETE FROM settings")
            for record in data.get("records", []):
                conn.execute("INSERT INTO records(category,created_at,payload) VALUES(?,?,?)", (record["category"], record["created_at"], record["payload"]))
            for key, value in data.get("settings", {}).items():
                conn.execute("INSERT INTO settings(key,value) VALUES(?,?)", (key, value))
            conn.commit()
        return True, "Backup restored. The app will reload using the restored information."
    except (InvalidToken, ValueError, KeyError, json.JSONDecodeError, UnicodeDecodeError):
        return False, "The password may be incorrect, or the backup file may be damaged."


def go_to(page):
    st.session_state.page = page


def show_scale(title, guide, key, default=3, help_text=None):
    value = st.slider(title, min_value=1, max_value=5, value=default, step=1, key=key, help=help_text)
    st.caption(f"**{value} = {guide[value]}**")
    return value


def supportive_insight(entry):
    mood = entry["Mood score"]
    stress = entry["Stress level"]
    sleep_quality = entry["Sleep quality"]
    energy = entry["Energy level"]
    pressure = entry["Academic pressure"]
    motivation = entry["Motivation"]
    ideas = []
    if stress >= 4 or pressure >= 4:
        ideas.append("Choose one small task for now, and break it into a few manageable steps. You don't have to solve everything at once.")
        ideas.append("If school pressure keeps feeling heavy, consider talking with a teacher or trusted adult about what could be made more manageable.")
    if sleep_quality <= 2:
        ideas.append("You might gently review your evening routine and make room for a little more rest where possible.")
    if energy <= 2:
        ideas.append("Try a small reset that feels comfortable, such as drinking water, stretching gently, or taking a screen break.")
    if motivation <= 2:
        ideas.append("Start with a two-minute version of a task. Beginning small can be enough for today.")
    if mood <= 2:
        ideas.append("Be kind to yourself today. You could write down what has been weighing on you or reach out to someone you trust.")
    if mood >= 4 and stress <= 3:
        ideas.append("Notice what helped today feel a little better. You may want to make space for that again when you can.")
    if not ideas:
        ideas.extend([
            "Pause for a moment and check what you need next: a break, a little movement, some focus time, or a conversation.",
            "Try choosing one realistic intention for the rest of the day. Small steps count, even when progress is quiet.",
        ])
    if entry.get("reflection"):
        reflection = entry["reflection"].lower()
        if any(word in reflection for word in ["exam", "test", "homework", "marks", "study"]):
            ideas.append("Your reflection mentions schoolwork. Consider writing down the very next step, rather than the whole to-do list.")
        elif any(word in reflection for word in ["friend", "family", "alone", "talk"]):
            ideas.append("Your reflection touches on connection. If it feels right, think of one person who usually listens kindly.")
    return list(dict.fromkeys(ideas))[:3]


# Load basic preferences. Each category's records persist locally only when saving is enabled.
if "page" not in st.session_state:
    st.session_state.page = "🌙 Welcome"
if "display_name" not in st.session_state:
    st.session_state.display_name = get_setting("display_name", "")
if "theme" not in st.session_state:
    st.session_state.theme = get_setting("theme", "Lavender")
if "welcome_seen" not in st.session_state:
    st.session_state.welcome_seen = get_setting("welcome_seen", False)

PAGES = ["🏠 Dashboard", "💜 Mood Check-In", "🌿 Calm Corner", "🎯 Weekly Goals", "✨ AI Insights", "📔 Personal Reflections", "🤝 Adult Support", "🔒 Privacy & Data"]

# Theme and custom styling
THEMES = {
    "Lavender": {"bg": "#f7f3ff", "panel": "#ffffff", "ink": "#46365f", "accent": "#8066b3", "soft": "#eee6fb", "line": "#e0d5f2"},
    "Midnight Lavender": {"bg": "#211a35", "panel": "#302545", "ink": "#f6efff", "accent": "#c0a8f0", "soft": "#423458", "line": "#57456d"},
    "Soft Rose": {"bg": "#fff5f8", "panel": "#ffffff", "ink": "#69475c", "accent": "#bd7798", "soft": "#f8e5ee", "line": "#efd0df"},
    "Misty Blue": {"bg": "#f1f7ff", "panel": "#ffffff", "ink": "#35516e", "accent": "#638ab5", "soft": "#e1edfb", "line": "#ccdef2"},
}
if st.session_state.theme not in THEMES:
    st.session_state.theme = "Lavender"
t = THEMES[st.session_state.theme]
st.markdown(f"""
<style>
:root {{ color-scheme: light; }}
.stApp {{ background: radial-gradient(circle at 10% 0%, {t['soft']} 0, {t['bg']} 40%, {t['bg']} 100%); color: {t['ink']}; }}
[data-testid="stHeader"] {{ background: transparent; }}
h1, h2, h3, p, label, [data-testid="stMarkdownContainer"] {{ color: {t['ink']}; }}
div.stButton > button {{ border-radius: 14px; border: 1px solid {t['line']}; background: {t['accent']}; color: {'#332344' if st.session_state.theme == 'Midnight Lavender' else '#ffffff'}; padding: .58rem .9rem; font-weight: 600; transition: all .15s ease; }}
div.stButton > button:hover {{ filter: brightness(1.04); border-color: {t['accent']}; transform: translateY(-1px); }}
div[data-testid="stMetric"] {{ background: {t['panel']}; border: 1px solid {t['line']}; border-radius: 18px; padding: 14px; }}
div[data-testid="stExpander"] {{ border: 1px solid {t['line']}; border-radius: 14px; background: {t['panel']}; }}
.solune-hero {{ background: linear-gradient(135deg, {t['soft']}, {t['panel']}); border: 1px solid {t['line']}; border-radius: 26px; padding: 30px; margin: 8px 0 20px 0; }}
.solune-card {{ background: {t['panel']}; border: 1px solid {t['line']}; border-radius: 20px; padding: 20px; min-height: 158px; box-shadow: 0 5px 18px rgba(72, 52, 103, .05); }}
.solune-icon {{ font-size: 2rem; margin-bottom: 8px; }}
.solune-card-art {{
    display: flex;
    align-items: center;
    justify-content: center;
    height: 112px;
    border-radius: 18px;
    background: linear-gradient(135deg, #eee5ff, #fceafa, #e5efff);
    font-size: 3.4rem;
    margin-bottom: 16px;
}}
.small-muted {{ opacity: .82; font-size: .92rem; }}
</style>
""", unsafe_allow_html=True)

# Sidebar navigation is hidden on the first-time welcome screen.
if st.session_state.page != "🌙 Welcome":
    with st.sidebar:
        st.markdown("# 🌙 Solune")
        st.caption("A gentle space to check in with yourself")
        new_name = st.text_input("What should we call you?", value=st.session_state.display_name, max_chars=30, placeholder="Your name or nickname")
        if new_name != st.session_state.display_name:
            st.session_state.display_name = new_name
            set_setting("display_name", new_name)
        new_theme = st.selectbox("Choose your theme", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme))
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            set_setting("theme", new_theme)
            st.rerun()
        st.divider()
        selected_page = st.radio("Explore Solune", PAGES, index=PAGES.index(st.session_state.page) if st.session_state.page in PAGES else 0)
        if selected_page != st.session_state.page:
            st.session_state.page = selected_page
            st.rerun()
        st.caption("No account or reminders. Your local data stays on this device unless you export a backup.")

# WELCOME
if st.session_state.page == "🌙 Welcome":
    st.markdown("<div class='solune-hero'>", unsafe_allow_html=True)
    st.markdown("# 🌙 Welcome to Solune")
    st.markdown("### A little space to pause, reflect, and grow")
    st.write("Solune is a student wellbeing companion for mood check-ins, small goals, calming activities, and personal reflection. You can explore at your own pace—there are no scores to pass and no perfect way to feel.")
    st.markdown("</div>", unsafe_allow_html=True)
    name = st.text_input("What would you like Solune to call you?", value=st.session_state.display_name, max_chars=30, placeholder="Your name or nickname (optional)")
    if st.button("Enter my space ✨", type="primary", use_container_width=True):
        st.session_state.display_name = name.strip()
        st.session_state.welcome_seen = True
        set_setting("display_name", st.session_state.display_name)
        set_setting("welcome_seen", True)
        st.session_state.page = "🏠 Dashboard"
        st.rerun()
    st.caption("Your entries are private by default. Solune does not automatically send them to parents or teachers.")

# DASHBOARD
elif st.session_state.page == "🏠 Dashboard":
    name = st.session_state.display_name.strip()
    greeting = f"Hello, {name} 🌙" if name else "Hello there 🌙"
    st.markdown(f"<div class='solune-hero'><div style='font-size:2.2rem'>🌙 ✨ ☁️</div><h1 style='margin-bottom:4px'>{greeting}</h1><p style='font-size:1.08rem'>You don't have to do everything today. Start wherever you are.</p><p class='small-muted'>A gentle space for your thoughts, goals, and wellbeing.</p></div>", unsafe_allow_html=True)
    mood_history = read_records("mood")
    goal_history = read_records("goals")
    reflections = read_records("reflections")
    col1, col2, col3 = st.columns(3)
    with col1:
        done_today = any(x.get("Date") == date.today().isoformat() for x in mood_history)
        st.metric("Today's check-in", "Complete" if done_today else "Whenever you're ready")
    with col2:
        latest_goal = goal_history[-1].get("completed", []) if goal_history else []
        st.metric("Weekly goals", f"{len(latest_goal)}/{len(DEFAULT_GOALS)}")
    with col3:
        st.metric("Reflections", len(reflections))
    st.subheader("A little space for every part of you")
    cards = [
        ("💜", "Mood Check-In", "Notice how you're feeling, with clear guides for every rating.", "💜 Mood Check-In"),
        ("🌿", "Calm Corner", "Find a quiet moment with gentle, optional activities.", "🌿 Calm Corner"),
        ("🎯", "Weekly Goals", "Choose small, realistic steps that feel right for you.", "🎯 Weekly Goals"),
        ("✨", "AI Insights", "Explore supportive ideas based on the information you allow Solune to save.", "✨ AI Insights"),
        ("📔", "Personal Reflections", "Keep a private space for thoughts and daily moments.", "📔 Personal Reflections"),
        ("🤝", "Adult Support", "Prepare a conversation with an adult you trust—only when you choose.", "🤝 Adult Support"),
    ]
    for row_start in range(0, len(cards), 3):
        cols = st.columns(3)
        for col, card in zip(cols, cards[row_start:row_start + 3]):
            icon, title, description, target = card
            with col:
                
                 st.markdown(
    f"""
    <div class="solune-card">
        <div class="solune-card-art">{icon}</div>
        <h3>{title}</h3>
        <p>{description}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

                if st.button(f"Open {title} →", key=f"card_{title}", use_container_width=True):
                    go_to(target)
                    st.rerun()
    st.caption("Illustrations can be added as local image assets in a later visual-polish pass; this version keeps the interface self-contained and reliable.")

# MOOD CHECK-IN
elif st.session_state.page == "💜 Mood Check-In":
    st.title("💜 Mood Check-In")
    st.write("There are no right or wrong answers. Choose what feels closest to your experience. You can skip optional questions.")
    with st.form("mood_form", clear_on_submit=False):
        st.subheader("🌷 Feelings")
        mood = show_scale("How are you feeling right now?", MOOD_GUIDE, "mood_rating", 3)
        emotions = st.multiselect("Which feelings have shown up today? (Optional)", ["Happy", "Calm", "Hopeful", "Okay", "Worried", "Frustrated", "Sad", "Lonely", "Tired", "Overwhelmed", "Other"])
        intensity = show_scale("How strong have your feelings felt today?", {1:"Very gentle",2:"A little",3:"Moderate",4:"Strong",5:"Very strong"}, "emotion_intensity", 3)
        st.subheader("🌙 Rest and energy")
        sleep_hours = st.select_slider("About how many hours did you sleep? (Optional)", options=list(range(0, 13)), value=7, format_func=lambda x: f"{x} hours")
        sleep_quality = show_scale("How restful was your sleep?", QUALITY_GUIDE, "sleep_quality", 3)
        energy = show_scale("How is your energy today?", {1:"Very low",2:"Low",3:"Normal",4:"Good",5:"Very high"}, "energy_rating", 3)
        st.subheader("📚 School and focus")
        stress = show_scale("How stressed do you feel?", STRESS_GUIDE, "stress_rating", 3)
        pressure = show_scale("How much academic pressure do you feel?", STRESS_GUIDE, "pressure_rating", 3)
        motivation = show_scale("How is your motivation today?", {1:"Very low",2:"Low",3:"Normal",4:"Good",5:"Very high"}, "motivation_rating", 3)
        focus = show_scale("How manageable does schoolwork feel?", {1:"Not manageable",2:"Difficult",3:"Manageable enough",4:"Mostly manageable",5:"Very manageable"}, "schoolwork_rating", 3)
        st.subheader("💗 Connection and reflection")
        support = st.radio("Do you feel you have someone you could talk to if you wanted? (Optional)", ["Yes", "Maybe", "Not right now", "Prefer not to say"], horizontal=True)
        positive_moment = st.text_input("One thing that influenced your mood today (Optional)", max_chars=300)
        reflection = st.text_area("Anything else you'd like to note? (Optional)", max_chars=700, placeholder="You can leave this blank.")
        submitted = st.form_submit_button("Save check-in & show suggestions ✨", use_container_width=True)
    if submitted:
        now = datetime.now()
        entry = {
            "Time": now.strftime("%Y-%m-%d %H:%M:%S"), "Date": now.date().isoformat(),
            "Mood score": mood, "Mood": MOOD_GUIDE[mood].split(" — ")[0], "Emotions": emotions,
            "Emotion intensity": intensity, "Sleep hours": sleep_hours, "Sleep quality": sleep_quality,
            "Energy level": energy, "Stress level": stress, "Academic pressure": pressure,
            "Motivation": motivation, "Schoolwork manageability": focus, "Support feeling": support,
            "Positive moment": positive_moment.strip(), "reflection": reflection.strip(),
        }
        prediction = DECISION_TREE.predict(pd.DataFrame([{
            "mood": mood, "stress": stress, "sleep": sleep_hours, "pressure": pressure,
        }]))[0]
        entry["model suggestion type"] = prediction
        st.session_state.latest_entry = entry
        insights = supportive_insight(entry)
        st.session_state.latest_insights = insights
        saved = persist_if_enabled("mood", entry)
        if saved:
            st.success("Your check-in was saved on this device.")
        else:
            st.info("Saving for Mood check-ins is off. Your suggestions are shown for this visit, but this check-in was not saved.")
        if get_save_pref("insights"):
            persist_if_enabled("insights", {"Time": entry["Time"], "Date": entry["Date"], "source": "Mood check-in", "suggestions": insights, "mood": entry["Mood score"]})
        st.subheader("✨ A few gentle ideas")
        model_messages = {
            "Extra support": "Your answers suggest that reaching out to a trusted adult or school counsellor could be worth considering if things feel difficult.",
            "Gentle check-in": "A gentle check-in may help: pause, notice what you need, and choose one manageable next step.",
            "Self-care": "You could keep making room for small routines and activities that help you feel supported.",
        }
        st.info(model_messages.get(prediction, "Take things one step at a time."))
        for idea in insights:
            st.info(idea)
        st.caption("The Decision Tree uses illustrative synthetic training examples. Its output is not a diagnosis or a validated mental-health assessment.")
    if "latest_entry" in st.session_state and st.session_state.page == "💜 Mood Check-In":
        if st.session_state.get("latest_insights"):
            st.divider()
            st.subheader("Your latest suggestions")
            for idea in st.session_state.latest_insights:
                st.info(idea)
    with st.expander("📈 Review or delete saved mood history"):
        history = read_records("mood")
        if history:
            view = pd.DataFrame([{k:v for k,v in item.items() if not k.startswith("_") and k != "reflection"} for item in history])
            st.dataframe(view, use_container_width=True, hide_index=True)
            selected = st.selectbox("Choose an entry to delete", [x["_id"] for x in history], format_func=lambda rid: next((f"{x.get('Time','Check-in')} — {x.get('Mood','Mood')}" for x in history if x["_id"] == rid), str(rid)))
            if st.button("Delete selected check-in"):
                delete_record(selected)
                st.rerun()
            if st.button("Clear all mood check-ins"):
                clear_category("mood")
                st.rerun()
        else:
            st.caption("No saved check-ins yet. Saving must be enabled in Privacy & Data.")

# CALM CORNER
elif st.session_state.page == "🌿 Calm Corner":
    st.title("🌿 Calm Corner")
    st.write("Choose something gentle. Skip or stop any activity whenever you like.")
    activity = st.selectbox("What would feel helpful?", ["Gentle breathing", "5–4–3–2–1 grounding", "Tiny reset break", "Positive affirmations", "Peaceful sounds and imagery", "Positive moment journal"])
    if activity == "Gentle breathing":
        st.markdown(f"<div class='solune-hero' style='text-align:center'><div style='font-size:3rem'>☁️ 🌬️ ☁️</div><h2>A soft breathing pause</h2><p>Let your breathing stay natural and comfortable. Breathe in gently, then breathe out at your own pace. Repeat only for as long as it feels okay.</p></div>", unsafe_allow_html=True)
    elif activity == "5–4–3–2–1 grounding":
        st.subheader("Notice the moment around you")
        for item in ["5 things you can see", "4 things you can feel", "3 things you can hear", "2 things you can smell or scents you enjoy", "1 thing you appreciate about this moment"]:
            st.markdown(f"- {item}")
    elif activity == "Tiny reset break":
        st.subheader("Pick just one tiny reset")
        st.markdown("- Sip some water.\n- Stretch gently if comfortable.\n- Look away from your screen for a moment.\n- Tidy one small part of your desk.\n- Find a quieter spot if one is available.")
    elif activity == "Positive affirmations":
        affirmations = ["I can take this one step at a time.", "My feelings deserve kindness.", "I don't have to be perfect to make progress.", "Rest is a reasonable thing to need.", "It's okay to ask for help.", "Small steps still count."]
        st.markdown("<div class='solune-hero'>" + "<br><br>".join(f"✨ **{x}**" for x in affirmations) + "</div>", unsafe_allow_html=True)
    elif activity == "Peaceful sounds and imagery":
        st.markdown("<div class='solune-hero' style='text-align:center'><div style='font-size:3rem'>🌙 ✨ ☁️</div><h3>Imagine a peaceful place</h3><p>Picture a quiet sky, soft clouds drifting by, or rain tapping gently on a window. You can also play a favourite calming sound from your own device if you wish.</p></div>", unsafe_allow_html=True)
    else:
        note = st.text_area("Write one small thing that felt pleasant, interesting, or kind (optional)", max_chars=500, key="calm_positive_note")
        if st.button("Save this Calm Corner note"):
            item = {"Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "activity": activity, "note": note.strip()}
            if persist_if_enabled("calm", item):
                st.success("Saved on this device.")
            else:
                st.info("Calm Corner saving is off, so this note wasn't saved.")
    if st.button("Save this activity as a favourite"):
        favourites = get_setting("calm_favourites", [])
        if activity not in favourites:
            favourites.append(activity)
        set_setting("calm_favourites", favourites)
        st.success("Added to your Calm Corner favourites.")
    favs = get_setting("calm_favourites", [])
    if favs:
        st.caption("Your favourites: " + " · ".join(favs))
    st.caption("These activities are optional general wellbeing tools, not medical advice.")

# WEEKLY GOALS
elif st.session_state.page == "🎯 Weekly Goals":
    st.title("🎯 Weekly Goals")
    st.write("Choose realistic intentions for this week. These are invitations, not rules.")
    saved_goals = read_records("goals")
    current = saved_goals[-1].get("completed", []) if saved_goals else []
    custom = st.text_input("Add your own small goal (optional)", max_chars=100)
    goal_list = list(dict.fromkeys(DEFAULT_GOALS + ([custom.strip()] if custom.strip() else [])))
    completed = []
    for goal in goal_list:
        if st.checkbox(goal, value=goal in current, key="goal_" + hashlib.md5(goal.encode()).hexdigest()[:10]):
            completed.append(goal)
    total = len(goal_list)
    st.progress(len(completed) / total if total else 0)
    st.write(f"**Progress:** {len(completed)} of {total} goals checked off.")
    if st.button("Save my weekly goals", use_container_width=True):
        item = {"Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "completed": completed, "all_goals": goal_list}
        if persist_if_enabled("goals", item):
            st.success("Your goal progress was saved on this device.")
        else:
            st.info("Weekly goal saving is off. Your changes are only shown for this visit.")
    if completed and len(completed) == total:
        st.success("You made space for every goal you chose. Remember, your wellbeing matters more than a checklist.")
    with st.expander("Review or clear saved goal history"):
        history = read_records("goals")
        if history:
            for item in reversed(history):
                st.write(f"**{item.get('Time','')}** — {len(item.get('completed', []))} goals checked off")
            if st.button("Clear saved goal history"):
                clear_category("goals")
                st.rerun()
        else:
            st.caption("No saved goal progress yet.")

# AI INSIGHTS
elif st.session_state.page == "✨ AI Insights":
    st.title("✨ AI Insights")
    st.write("A thoughtful summary of patterns you choose to record—not a label, diagnosis, or judgement.")
    st.info("This prototype creates rule-based suggestions from your latest check-in and reflection. It does not send your private writing to an external AI service.")
    moods = read_records("mood") if get_save_pref("mood") else []
    reflection_records = read_records("reflections") if get_save_pref("reflections") else []
    if moods:
        latest = moods[-1]
        st.subheader("A gentle reflection on your latest check-in")
        st.write(f"Your latest mood rating was **{latest.get('Mood score','—')} / 5**. Mood can shift, and one check-in never tells the whole story.")
        for idea in supportive_insight(latest):
            st.info(idea)
        if len(moods) >= 3:
            recent = moods[-7:]
            avg_stress = sum(x.get("Stress level", 3) for x in recent) / len(recent)
            avg_mood = sum(x.get("Mood score", 3) for x in recent) / len(recent)
            st.subheader("Patterns in recent saved check-ins")
            st.write(f"Across the latest {len(recent)} saved check-ins, your average mood rating was **{avg_mood:.1f}/5** and average stress rating was **{avg_stress:.1f}/5**. These are simple summaries, not a diagnosis.")
            if avg_stress >= 4:
                st.write("You have recorded higher stress in this set of check-ins. Consider whether a small workload change or a conversation with someone you trust might help.")
            elif avg_mood >= 4:
                st.write("Your recent ratings have included some positive moments. If you want, notice which routines or activities seemed to support you.")
    else:
        st.info("To see personalised insights, turn on saving for Mood check-ins and record a few check-ins. You can still use the other Solune features without saving.")
    if reflection_records:
        st.subheader("Reflection themes (on-device, simple keyword matching)")
        st.caption("Only a few broad themes are checked; Solune does not interpret your writing as a diagnosis.")
        texts = " ".join(x.get("Reflection", "").lower() for x in reflection_records[-5:])
        theme_counts = {"Schoolwork": sum(texts.count(w) for w in ["study", "exam", "homework", "test"]), "Connection": sum(texts.count(w) for w in ["friend", "family", "lonely", "talk"]), "Rest": sum(texts.count(w) for w in ["sleep", "tired", "rest", "break"])}
        theme_counts = {k:v for k,v in theme_counts.items() if v}
        if theme_counts:
            st.write("Words that appeared in recent reflections: " + ", ".join(f"{k} ({v})" for k,v in theme_counts.items()))
        else:
            st.write("No recurring keywords stood out in your recent saved reflections. That is completely okay.")
    else:
        st.caption("Reflection themes appear only if Personal Reflections saving is enabled and you have saved entries.")
    goal_records = read_records("goals") if get_save_pref("goals") else []
    if goal_records:
        latest_goals = goal_records[-1].get("completed", [])
        st.subheader("Your chosen routines and goals")
        if latest_goals:
            st.write("You most recently chose: " + ", ".join(latest_goals) + ". You can keep, change, or pause any goal as your week changes.")
        else:
            st.write("Your latest saved goal list has no completed items yet. That's okay—goals are invitations, not obligations.")
    calm_favourites = get_setting("calm_favourites", [])
    if calm_favourites:
        st.subheader("Calm Corner favourites")
        st.write("Activities you chose as favourites: " + ", ".join(calm_favourites) + ". You could revisit one when it feels useful.")
    history = read_records("insights")
    if history:
        with st.expander("Saved AI insights history"):
            for item in reversed(history[-20:]):
                st.markdown(f"**{item.get('Time','')}**")
                for idea in item.get("suggestions", []):
                    st.write("- " + idea)
                if st.button("Delete this insight", key=f"del_insight_{item['_id']}"):
                    delete_record(item["_id"])
                    st.rerun()

# PERSONAL REFLECTIONS
elif st.session_state.page == "📔 Personal Reflections":
    st.title("📔 Personal Reflections")
    st.write("A private-by-default space to write, pause, and notice what matters to you.")
    st.warning("Entries are stored in a local database on this computer when saving is enabled. Avoid adding passwords or contact details.")
    with st.form("reflection_form", clear_on_submit=True):
        note = st.text_area("How was your day? What felt good, difficult, or important?", max_chars=2000, placeholder="Write only what you feel comfortable keeping…")
        submitted = st.form_submit_button("Save reflection ✨", use_container_width=True)
    if submitted:
        if note.strip():
            item = {"Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Reflection": note.strip()}
            if persist_if_enabled("reflections", item):
                st.success("Your reflection was saved on this device.")
            else:
                st.info("Personal Reflections saving is off, so this entry was not saved.")
        else:
            st.warning("Write something first, or leave the journal blank.")
    entries = read_records("reflections")
    if entries:
        st.subheader("Your saved reflections")
        for item in reversed(entries):
            with st.expander(f"Reflection — {item.get('Time','')}"):
                st.write(item.get("Reflection", ""))
                if st.button("Delete this reflection", key=f"del_ref_{item['_id']}"):
                    delete_record(item["_id"])
                    st.rerun()
        if st.button("Clear all reflections"):
            clear_category("reflections")
            st.rerun()

# ADULT SUPPORT
elif st.session_state.page == "🤝 Adult Support":
    st.title("🤝 Adult Support")
    st.write("Prepare for a conversation with someone you trust. Nothing is automatically sent or shared.")
    topic = st.selectbox("What would you like to talk about?", ["Academic pressure or exams", "Feeling overwhelmed", "Needing someone to listen", "Balancing study and rest", "Something difficult to explain"])
    recipient = st.selectbox("Who might you talk to?", ["Parent or guardian", "Teacher or school counsellor", "Another trusted adult"])
    messages = {
        "Academic pressure or exams": "I've been feeling pressure about school lately. Could we talk about what's worrying me and find one manageable next step together?",
        "Feeling overwhelmed": "I've had a lot on my mind, and things feel overwhelming right now. Could you listen for a little while?",
        "Needing someone to listen": "I'd like to share something that's been on my mind. I don't need you to solve everything straight away; I'd appreciate it if you listened.",
        "Balancing study and rest": "I'd like to find a better balance between studying and taking breaks. Could we discuss a routine that feels manageable?",
        "Something difficult to explain": "Something has been bothering me, and I'm finding it difficult to explain. Could we talk somewhere comfortable when we have time?",
    }
    st.subheader(f"A message you can adapt for your {recipient.lower()}")
    st.code(messages[topic], language=None)
    st.caption("This only prepares text for you. It does not contact anyone.")
    st.divider()
    st.subheader("Optional: prepare a small support summary")
    include_mood = st.checkbox("Include my latest saved mood check-in", value=False)
    include_goal = st.checkbox("Include my latest saved weekly goals", value=False)
    include_reflection = st.checkbox("Include my latest saved reflection", value=False)
    if st.button("Preview selected information"):
        summary = ["SOLUNE — STUDENT-CHOSEN SUPPORT SUMMARY", "Only share this if you feel comfortable and it is safe to do so."]
        if include_mood:
            mood_data = read_records("mood")
            if mood_data:
                m = mood_data[-1]
                summary.append(f"Latest mood: {m.get('Mood','Not available')} ({m.get('Mood score','—')}/5); stress {m.get('Stress level','—')}/5; school pressure {m.get('Academic pressure','—')}/5.")
        if include_goal:
            goals = read_records("goals")
            if goals:
                summary.append("Latest completed goals: " + (", ".join(goals[-1].get("completed", [])) or "No goals marked complete."))
        if include_reflection:
            reflections = read_records("reflections")
            if reflections:
                summary.append("Latest reflection: " + reflections[-1].get("Reflection", ""))
        st.session_state.support_preview = "\n\n".join(summary)
    if st.session_state.get("support_preview"):
        st.text_area("Review the exact text before sharing", value=st.session_state.support_preview, height=180)
        st.download_button("Download my selected summary", st.session_state.support_preview, file_name="solune_support_summary.txt", mime="text/plain")
        st.caption("Downloaded summaries are not encrypted. Store and share them carefully.")
    st.info("If you feel unsafe or need urgent help, tell a trusted adult or school counsellor who can help you in person.")

# PRIVACY AND DATA
elif st.session_state.page == "🔒 Privacy & Data":
    st.title("🔒 Privacy & Data")
    st.write("You control which categories Solune saves. Turning saving off stops new records for that category; it does not delete records already saved. Use the clear controls below to delete existing information.")
    st.subheader("Choose what Solune may save")
    for key, label in CATEGORIES.items():
        enabled = get_save_pref(key)
        chosen = st.toggle(f"Save {label}", value=enabled, key=f"pref_{key}")
        if chosen != enabled:
            set_setting("save_" + key, chosen)
            st.rerun()
    st.caption("Saving is local to this computer in this prototype. The database is not encrypted at rest. Keep your computer account protected and do not deploy this version as a public multi-user app.")
    st.divider()
    st.subheader("Clear saved information")
    clear_labels = {"mood":"Mood check-ins", "goals":"Weekly goals", "calm":"Calm Corner preferences", "reflections":"Personal reflections", "insights":"AI insights history"}
    chosen_categories = st.multiselect("Choose categories to clear", list(clear_labels.keys()), format_func=lambda x: clear_labels[x])
    if st.button("Clear selected categories", use_container_width=True):
        for category in chosen_categories:
            clear_category(category)
            if category == "calm":
                set_setting("calm_favourites", [])
        st.success("Selected saved categories were cleared.")
        st.rerun()
    if st.button("Clear ALL saved information", type="primary", use_container_width=True):
        st.session_state.confirm_clear_all = True
    if st.session_state.get("confirm_clear_all"):
        st.warning("This permanently deletes all saved records and saved preferences in this local Solune database.")
        confirm = st.checkbox("I understand and want to clear everything", key="confirm_clear_box")
        if st.button("Confirm Clear All", disabled=not confirm):
            clear_all()
            for key in ["latest_entry", "latest_insights", "support_preview"]:
                st.session_state.pop(key, None)
            st.session_state.confirm_clear_all = False
            st.success("All saved Solune information has been cleared.")
            st.rerun()
    st.divider()
    st.subheader("Encrypted backup and restore")
    st.write("Create a password-protected encrypted backup to move your saved information to another device. Your password is not stored by Solune. If you lose it, the backup cannot be restored.")
    with st.form("backup_form"):
        backup_password = st.text_input("Backup password", type="password", help="Use a strong password you can safely remember.")
        backup_confirm = st.text_input("Confirm backup password", type="password")
        make_backup = st.form_submit_button("Create encrypted backup")
    if make_backup:
        if len(backup_password) < 10:
            st.error("Please use a backup password with at least 10 characters.")
        elif backup_password != backup_confirm:
            st.error("The passwords don't match.")
        else:
            encrypted = make_encrypted_backup(backup_password)
            st.download_button("Download encrypted backup", encrypted, file_name="solune_encrypted_backup.solune", mime="application/octet-stream")
    st.markdown("**Restore a backup**")
    uploaded = st.file_uploader("Choose a Solune encrypted backup file", type=None)
    restore_password = st.text_input("Backup password for restore", type="password", key="restore_password")
    if st.button("Restore backup", disabled=(uploaded is None or not restore_password)):
        success, message = restore_encrypted_backup(uploaded.getvalue(), restore_password)
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)
    st.divider()
    st.subheader("About Solune AI")
    st.write("Solune is a student wellbeing project prototype. Its suggestions are simple on-device rules, not a live AI service, clinical tool, or mental-health diagnosis. Your private entries are not automatically sent to a trusted adult.")
    st.caption("Solune AI 2.0 · No login · No reminders · Student-controlled saving")

