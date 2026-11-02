import streamlit as st
import google.generativeai as genai
import json
import re
import threading
import time
import sqlite3

# הגדרת עמוד
st.set_page_config(page_title="Amirnet Pro", layout="wide", initial_sidebar_state="collapsed")

# --- CSS מתקדם: רקע חי, צבעים לכל כפתור, אנימציות תנועה ועיצוב Glassmorphism ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700;800&display=swap');
        
        #MainMenu, header, footer {visibility: hidden;}
        
        html, body, [class*="css"] {
            font-family: 'Rubik', sans-serif;
        }

        /* רקע דינמי זז וחי לכל האפליקציה */
        .stApp {
            background: linear-gradient(-45deg, #e0c3fc, #8ec5fc, #c2e9fb, #f3e7e9, #d4fc79);
            background-size: 400% 400%;
            animation: gradientBG 18s ease infinite;
        }
        
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* התאמה רספונסיבית למחשב ולנייד */
        @media (min-width: 768px) {
            .block-container { max-width: 820px; margin: 0 auto; padding-top: 1.5rem; direction: rtl; text-align: right; }
        }
        @media (max-width: 767px) {
            .block-container { max-width: 100%; padding: 0.8rem; direction: rtl; text-align: right; }
        }

        /* אנימציות כניסה ותנועה חיה */
        @keyframes popIn {
            0% { opacity: 0; transform: scale(0.94) translateY(15px); }
            100% { opacity: 1; transform: scale(1) translateY(0); }
        }
        
        @keyframes floatBadge {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
            100% { transform: translateY(0px); }
        }

        .animated-pop { animation: popIn 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        
        .floating-badge {
            display: inline-block;
            animation: floatBadge 3s ease-in-out infinite;
            background: rgba(255, 255, 255, 0.9);
            padding: 6px 18px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 14px;
            color: #4f46e5;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
            margin-bottom: 12px;
        }

        /* סרגל עליון (HUD) */
        .hud-bar {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(12px);
            padding: 14px 22px;
            border-radius: 20px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06);
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.7);
        }
        .hud-user { font-weight: 800; font-size: 18px; color: #1e293b; }
        .hud-mistakes {
            background: linear-gradient(135deg, #ff416c, #ff4b2b);
            color: white;
            padding: 5px 14px;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 700;
            box-shadow: 0 4px 10px rgba(255, 65, 108, 0.3);
        }

        /* כרטיסיית קטע קריאה */
        .passage-box {
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(10px);
            padding: 24px;
            border-radius: 20px;
            border-left: 6px solid #8b5cf6;
            margin-bottom: 20px;
            direction: ltr;
            text-align: left;
            font-size: 17px;
            color: #1e293b;
            line-height: 1.75;
            box-shadow: 0 10px 25px rgba(0,0,0,0.06);
        }

        /* כרטיסיית השאלה המרכזית */
        .question-box {
            background: rgba(255, 255, 255, 0.96);
            padding: 30px;
            border-radius: 24px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.08);
            margin-bottom: 22px;
            direction: ltr;
            text-align: left;
            font-size: 21px;
            font-weight: 700;
            line-height: 1.55;
            border-top: 6px solid #6366f1;
            color: #0f172a;
        }

        /* עיצוב בסיסי לכל הכפתורים */
        .stButton > button {
            width: 100%;
            min-height: 64px;
            font-size: 18px;
            font-weight: 600;
            border-radius: 16px;
            transition: all 0.28s cubic-bezier(0.25, 0.8, 0.25, 1);
            border: 2px solid rgba(255,255,255,0.8);
            background: rgba(255, 255, 255, 0.92);
            color: #1e293b;
            box-shadow: 0 6px 15px rgba(0,0,0,0.05);
            margin-top: 6px;
        }
        .stButton > button:hover {
            transform: translateY(-4px) scale(1.01);
            box-shadow: 0 12px 24px rgba(99, 102, 241, 0.2);
            border-color: #6366f1;
            background: #ffffff;
            color: #4f46e5;
        }

        /* --- צבעים ייחודיים לכל כפתור/טאב בדשבורד הראשי --- */
        div.st-key-mode_sc button {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
            color: white !important; height: 95px; font-size: 20px; border: none !important;
            box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3) !important;
        }
        div.st-key-mode_rest button {
            background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%) !important;
            color: white !important; height: 95px; font-size: 20px; border: none !important;
            box-shadow: 0 10px 20px rgba(139, 92, 246, 0.3) !important;
        }
        div.st-key-mode_rc button {
            background: linear-gradient(135deg, #10b981 0%, #047857 100%) !important;
            color: white !important; height: 95px; font-size: 20px; border: none !important;
            box-shadow: 0 10px 20px rgba(16, 185, 129, 0.3) !important;
        }
        div.st-key-mode_voc button {
            background: linear-gradient(135deg, #f59e0b 0%, #b45309 100%) !important;
            color: white !important; height: 95px; font-size: 20px; border: none !important;
            box-shadow: 0 10px 20px rgba(245, 158, 11, 0.3) !important;
        }
        div.st-key-mode_elim button {
            background: linear-gradient(135deg, #ec4899 0%, #be185d 100%) !important;
            color: white !important; height: 95px; font-size: 20px; border: none !important;
            box-shadow: 0 10px 20px rgba(236, 72, 153, 0.3) !important;
        }
        div.st-key-mode_morph button {
            background: linear-gradient(135deg, #06b6d4 0%, #0e7490 100%) !important;
            color: white !important; height: 95px; font-size: 20px; border: none !important;
            box-shadow: 0 10px 20px rgba(6, 182, 212, 0.3) !important;
        }
        div.st-key-mode_mistakes button {
            background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
            color: white !important; height: 85px; font-size: 19px; border: none !important;
            box-shadow: 0 10px 20px rgba(239, 68, 68, 0.3) !important;
        }
        div.st-key-mode_sim button {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            color: #fbbf24 !important; height: 85px; font-size: 20px; border: 2px solid #fbbf24 !important;
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.4) !important;
        }
        div[class*="st-key-mode_"] button:hover {
            transform: translateY(-6px) scale(1.02) !important;
            filter: brightness(1.08);
        }

        /* כפתור יציאה בסרגל עליון */
        div.st-key-exit_top_btn button {
            min-height: 44px !important;
            height: 44px !important;
            font-size: 15px !important;
            background: #fee2e2 !important;
            color: #dc2626 !important;
            border: 1px solid #fca5a5 !important;
            border-radius: 12px !important;
            margin-top: 0 !important;
        }

        /* חיווי תשובות לאחר מענה */
        .ans-option-correct {
            background: linear-gradient(135deg, #dcfce7, #bbf7d0);
            border: 2px solid #22c55e;
            color: #14532d;
            padding: 16px 20px;
            border-radius: 16px;
            font-size: 18px;
            font-weight: 700;
            margin-top: 10px;
            direction: ltr;
            text-align: left;
            box-shadow: 0 6px 15px rgba(34, 197, 94, 0.15);
        }
        .ans-option-wrong {
            background: linear-gradient(135deg, #fee2e2, #fecaca);
            border: 2px solid #ef4444;
            color: #7f1d1d;
            padding: 16px 20px;
            border-radius: 16px;
            font-size: 18px;
            font-weight: 700;
            margin-top: 10px;
            direction: ltr;
            text-align: left;
        }
        .ans-option-neutral {
            background: rgba(255, 255, 255, 0.6);
            border: 1px solid #cbd5e1;
            color: #64748b;
            padding: 16px 20px;
            border-radius: 16px;
            font-size: 18px;
            margin-top: 10px;
            direction: ltr;
            text-align: left;
        }

        /* קופסת הסבר מעוצבת */
        .explanation-box {
            background: rgba(255, 255, 255, 0.95);
            padding: 26px;
            border-radius: 22px;
            margin-top: 22px;
            border-right: 7px solid #10b981;
            box-shadow: 0 15px 30px rgba(0,0,0,0.07);
        }
        .exp-card {
            background: #f8fafc;
            padding: 14px 18px;
            border-radius: 14px;
            margin-bottom: 12px;
            border: 1px solid #e2e8f0;
        }
        .exp-title { color: #0f172a; font-weight: 800; font-size: 16px; margin-bottom: 4px; }
        .exp-text { color: #334155; font-size: 16px; line-height: 1.55; }

        .main-hero-title {
            text-align: center;
            background: linear-gradient(135deg, #1e1b4b, #4338ca, #0ea5e9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 36px;
            font-weight: 900;
            margin-bottom: 8px;
        }
        .sub-hero-title {
            text-align: center;
            color: #334155;
            font-size: 17px;
            font-weight: 500;
            margin-bottom: 25px;
        }
        
        .login-card {
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(16px);
            padding: 40px 30px;
            border-radius: 28px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.1);
            max-width: 440px;
            margin: 60px auto 20px auto;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.8);
        }
    </style>
""", unsafe_allow_html=True)

# --- מסד נתונים SQLite ---
@st.cache_resource
def init_db():
    conn = sqlite3.connect('amirnet_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mistakes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  q_type TEXT,
                  question TEXT,
                  correct_answer TEXT,
                  translation TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    return conn

conn = init_db()

def log_mistake(username, q_type, question, correct_answer, translation):
    c = conn.cursor()
    c.execute("INSERT INTO mistakes (username, q_type, question, correct_answer, translation) VALUES (?, ?, ?, ?, ?)",
              (username, q_type, question, correct_answer, translation))
    conn.commit()

def get_user_mistakes(username, limit=10):
    c = conn.cursor()
    c.execute("SELECT question, correct_answer, translation FROM mistakes WHERE username=? ORDER BY RANDOM() LIMIT ?", (username, limit))
    return c.fetchall()

def count_user_mistakes(username):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM mistakes WHERE username=?", (username,))
    return c.fetchone()[0]

# --- הגדרת מודל AI ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.8-flash')

PROMPTS = {
    "השלמת משפטים": "Question type: Sentence Completion. Advanced academic vocabulary (C1/C2).",
    "ניסוח מחדש": "Question type: Restatements. Complex logical structures and pivot words.",
    "הבנת הנקרא (קטע קצר)": "Question type: Reading Comprehension. Provide a short academic paragraph (3-4 sentences) in the 'passage' field. The question should test inference, main idea, or vocabulary in context.",
    "אוצר מילים ואסוציאציות": "Question type: Vocabulary Practice. Question is an English academic word, options are 4 Hebrew translations. In 'exp_correct', include a creative Hebrew memory association (אסוציאציה זיכרונית).",
    "אלימינציה עיוורת (דקדוק והקשר)": "Question type: Grammar & Context Elimination. Sentence with a blank where the target word is very rare, but 3 options can be eliminated via grammar (noun/verb/adj) or logical connectors.",
    "פירוק מורפולוגי (תחיליות וסופיות)": "Question type: Morphological Breakdown. Provide a complex English word with prefixes/suffixes. In 'exp_correct', break down the prefix, root, and suffix.",
    "מיקוד בטעויות עבר": "Create new high-level Sentence Completion or Vocabulary questions testing these exact concepts/words the user previously missed: {mistakes_list}."
}

def generate_questions(q_type, num_questions=10, retries=2, custom_context=""):
    prompt_instruction = PROMPTS.get(q_type, PROMPTS["השלמת משפטים"])
    if custom_context:
        prompt_instruction = prompt_instruction.replace("{mistakes_list}", custom_context)
        
    prompt = f"""
    Create {num_questions} high-level English questions for the Israeli AMIRNET exam.
    {prompt_instruction}
    Output ONLY a strict JSON array of objects. No markdown outside JSON, no trailing commas.
    [
        {{
            "passage": "Academic paragraph ONLY if Reading Comprehension, otherwise ''",
            "question": "The English sentence, word, or question",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Exact match to one of the options",
            "exp_translation": "תרגום מדויק וברור לעברית של המשפט או המילה",
            "exp_correct": "הסבר חד בעברית למה התשובה הנכונה מתאימה (כולל טיפ פסיכומטרי או אסוציאציה)",
            "exp_wrong": "פירוט תמציתי בעברית של תרגום המסיחים האחרים ומדוע כל אחד מהם נפסל"
        }}
    ]
    """
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            match = re.search(r'```(?:json)?(.*?)```', raw_text, re.DOTALL)
            if match:
                raw_text = match.group(1).strip()
            return json.loads(raw_text)
        except Exception:
            if attempt == retries - 1:
                return []
            time.sleep(1)

def fetch_in_background(q_type, target_list, num_questions, custom_context=""):
    new_qs = generate_questions(q_type, num_questions, custom_context=custom_context)
    if new_qs:
        target_list.extend(new_qs)

# --- אתחול Session State ---
defaults = {
    'current_user': None,
    'question_bank': [],
    'next_batch': [],
    'current_index': 0,
    'answered': False,
    'user_choice': None,
    'is_fetching': False,
    'start_time': None,
    'exam_mode': False,
    'correct_count': 0,
    'current_mode': None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==========================================
# 1. מסך כניסת משתמש (Login)
# ==========================================
if not st.session_state.current_user:
    st.markdown("""
        <div class='login-card animated-pop'>
            <div style='font-size: 52px; margin-bottom: 10px;'>🚀</div>
            <div class='main-hero-title'>Amirnet Pro</div>
            <div class='sub-hero-title'>מערכת אימון אדפטיבית חכמה ברמת פטור</div>
        </div>
    """, unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        username_input = st.text_input("איך קוראים לך?", placeholder="הזן שם משתמש לשמירת הנתונים...")
        if st.button("כניסה לאזור האישי ⚡", use_container_width=True):
            if username_input.strip():
                st.session_state.current_user = username_input.strip()
                st.rerun()
            else:
                st.error("אנא הזן שם משתמש כדי להתחיל.")
    st.stop()

# ספירת טעויות של המשתמש הנוכחי
mistakes_count = count_user_mistakes(st.session_state.current_user)

# ==========================================
# 2. סרגל עליון קבוע (HUD) עם כפתור יציאה מיידי
# ==========================================
hud_col1, hud_col2 = st.columns([3, 1])
with hud_col1:
    st.markdown(f"""
        <div class='hud-bar animated-pop'>
            <div class='hud-user'>👋 היי, {st.session_state.current_user}</div>
            <div class='hud-mistakes'>🔥 {mistakes_count} מילים לחיזוק</div>
        </div>
    """, unsafe_allow_html=True)
with hud_col2:
    if st.session_state.question_bank:
        if st.button("🏠 יציאה לראשי", key="exit_top_btn", use_container_width=True):
            st.session_state.question_bank = []
            st.session_state.next_batch = []
            st.rerun()
    else:
        if st.button("🚪 התנתק", key="exit_top_btn", use_container_width=True):
            st.session_state.current_user = None
            st.rerun()

# ==========================================
# 3. דשבורד ראשי צבעוני (כשלא בתוך תרגול)
# ==========================================
if not st.session_state.question_bank:
    st.markdown("<div class='main-hero-title animated-pop'>בחר את זירת האימון שלך</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-hero-title animated-pop'>כל מסלול מתמקד במיומנות פסיכומטרית אחרת לפיצוח הבחינה</div>", unsafe_allow_html=True)
    
    selected_mode = None
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧩 השלמת משפטים\n(Sentence Completion)", key="mode_sc", use_container_width=True):
            selected_mode = "השלמת משפטים"
        if st.button("📖 הבנת הנקרא\n(Reading Passages)", key="mode_rc", use_container_width=True):
            selected_mode = "הבנת הנקרא (קטע קצר)"
        if st.button("🕵️‍♂️ אלימינציה עיוורת\n(טכניקות פסילה ודקדוק)", key="mode_elim", use_container_width=True):
            selected_mode = "אלימינציה עיוורת (דקדוק והקשר)"
            
    with c2:
        if st.button("🔄 ניסוח מחדש\n(Restatements)", key="mode_rest", use_container_width=True):
            selected_mode = "ניסוח מחדש"
        if st.button("🧠 אוצר מילים ואסוציאציות\n(שינון חכם)", key="mode_voc", use_container_width=True):
            selected_mode = "אוצר מילים ואסוציאציות"
        if st.button("🔬 פירוק מורפולוגי\n(תחיליות, שורשים וסופיות)", key="mode_morph", use_container_width=True):
            selected_mode = "פירוק מורפולוגי (תחיליות וסופיות)"

    st.write("")
    c3, c4 = st.columns(2)
    with c3:
        if st.button(f"🎯 מיקוד בטעויות עבר ({mistakes_count})", key="mode_mistakes", use_container_width=True):
            if mistakes_count < 3:
                st.warning("צבור לפחות 3 טעויות בתרגולים השונים כדי לפתוח אימון ממוקד אישית!")
            else:
                selected_mode = "מיקוד בטעויות עבר"
    with c4:
        if st.button("🏆 סימולציה מלאה (22 שאלות עם טיימר)", key="mode_sim", use_container_width=True):
            selected_mode = "סימולציה מלאה"

    if selected_mode:
        with st.spinner("🚀 מייצר לך מקבץ שאלות חכם בזמן אמת..."):
            st.session_state.exam_mode = "סימולציה" in selected_mode
            st.session_state.current_mode = selected_mode
            num_q = 22 if st.session_state.exam_mode else 10
            
            custom_context = ""
            fetch_type = selected_mode
            if selected_mode == "מיקוד בטעויות עבר":
                mistakes_data = get_user_mistakes(st.session_state.current_user)
                custom_context = ", ".join([row[1] for row in mistakes_data])
            elif st.session_state.exam_mode:
                fetch_type = "השלמת משפטים"
            
            bank = generate_questions(fetch_type, num_q, custom_context=custom_context)
            if bank:
                st.session_state.question_bank = bank
                st.session_state.current_index = 0
                st.session_state.answered = False
                st.session_state.user_choice = None
                st.session_state.correct_count = 0
                st.session_state.start_time = time.time()
                st.session_state.next_batch = []
                st.session_state.is_fetching = False
                st.rerun()
            else:
                st.error("תקלה רגעית ביצירת השאלות מול השרת. לחץ שוב!")

# ==========================================
# 4. מסך תרגול פעיל (Active Practice)
# ==========================================
if st.session_state.question_bank:
    total = len(st.session_state.question_bank)
    idx = st.session_state.current_index
    q = st.session_state.question_bank[idx]
    
    # טעינת רקע אוטומטית בשאלה השמינית
    if not st.session_state.exam_mode and idx == 7 and not st.session_state.is_fetching:
        st.session_state.is_fetching = True
        custom_ctx = ""
        if st.session_state.current_mode == "מיקוד בטעויות עבר":
            mistakes_data = get_user_mistakes(st.session_state.current_user)
            custom_ctx = ", ".join([row[1] for row in mistakes_data])
        threading.Thread(target=fetch_in_background, args=(st.session_state.current_mode, st.session_state.next_batch, 10, custom_ctx)).start()

    # תגית נושא מרחפת ומד התקדמות
    st.markdown(f"<div style='text-align: center;'><span class='floating-badge'>✨ {st.session_state.current_mode} • שאלה {idx + 1} מתוך {total}</span></div>", unsafe_allow_html=True)
    st.progress((idx + 1) / total)
    
    if st.session_state.exam_mode:
        elapsed = int(time.time() - st.session_state.start_time)
        mins, secs = divmod(elapsed, 60)
        st.markdown(f"<div style='text-align: center; color: #dc2626; font-weight: 800; font-size: 18px; margin-bottom: 10px;'>⏱️ זמן: {mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

    # קטע קריאה (אם רלוונטי)
    if q.get('passage') and len(q['passage'].strip()) > 5:
        st.markdown(f"<div class='passage-box animated-pop'>{q['passage']}</div>", unsafe_allow_html=True)
        
    # כרטיסיית השאלה
    st.markdown(f"<div class='question-box animated-pop'>{q['question']}</div>", unsafe_allow_html=True)
    
    # הצגת האפשרויות: לפני לחיצה כפתורים חיים, אחרי לחיצה כרטיסיות צבעוניות (ירוק/אדום)
    if not st.session_state.answered:
        for opt_i, opt in enumerate(q['options']):
            if st.button(opt, key=f"q_{idx}_opt_{opt_i}", use_container_width=True):
                st.session_state.user_choice = opt
                st.session_state.answered = True
                if opt == q['correct_answer']:
                    st.session_state.correct_count += 1
                else:
                    log_mistake(st.session_state.current_user, st.session_state.current_mode, q['question'], q['correct_answer'], q.get('exp_translation', ''))
                st.rerun()
    else:
        for opt in q['options']:
            if opt == q['correct_answer']:
                st.markdown(f"<div class='ans-option-correct animated-pop'>✅ {opt}</div>", unsafe_allow_html=True)
            elif opt == st.session_state.user_choice:
                st.markdown(f"<div class='ans-option-wrong animated-pop'>❌ {opt}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='ans-option-neutral'>{opt}</div>", unsafe_allow_html=True)

    # פידבק מפורט לאחר בחירת תשובה
    if st.session_state.answered:
        if not st.session_state.exam_mode:
            is_correct = st.session_state.user_choice == q['correct_answer']
            if is_correct:
                st.balloons()
            
            st.markdown(f"""
            <div class='explanation-box animated-pop'>
                <div class='exp-card'>
                    <div class='exp-title'>🌍 תרגום המשפט / המילה:</div>
                    <div class='exp-text'>{q.get('exp_translation', '')}</div>
                </div>
                <div class='exp-card'>
                    <div class='exp-title'>✅ פיצוח התשובה הנכונה:</div>
                    <div class='exp-text'>{q.get('exp_correct', '')}</div>
                </div>
                <div class='exp-card'>
                    <div class='exp-title'>❌ ניתוח ופסילת המסיחים האחרים:</div>
                    <div class='exp-text'>{q.get('exp_wrong', '')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        if idx < total - 1:
            if st.button("המשך לשאלה הבאה ⬅️", use_container_width=True):
                st.session_state.current_index += 1
                st.session_state.answered = False
                st.session_state.user_choice = None
                st.rerun()
        else:
            if st.session_state.exam_mode:
                score = int(50 + (st.session_state.correct_count / total) * 100)
                st.balloons()
                st.markdown(f"""
                    <div class='question-box animated-pop' style='text-align: center; direction: rtl;'>
                        <h2>🎉 סיימת את הסימולציה!</h2>
                        <h1 style='color: #4f46e5; font-size: 48px;'>ציון מוערך: {score}</h1>
                        <p>ענית נכון על {st.session_state.correct_count} מתוך {total} שאלות.</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("חזור לדשבורד הראשי 🏠", use_container_width=True):
                    st.session_state.question_bank = []
                    st.rerun()
            else:
                if st.session_state.next_batch:
                    if st.button("⚡ המשך מיד למקבץ הבא (מוכן בזיכרון!)", use_container_width=True):
                        st.session_state.question_bank = st.session_state.next_batch.copy()
                        st.session_state.next_batch = []
                        st.session_state.is_fetching = False
                        st.session_state.current_index = 0
                        st.session_state.answered = False
                        st.session_state.user_choice = None
                        st.rerun()
                else:
                    st.info("טוען את המקבץ הבא ברקע...")
                    if st.button("רענן להמשך 🔄", use_container_width=True):
                        st.rerun()
