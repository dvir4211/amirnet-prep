import streamlit as st
import google.generativeai as genai
import json
import re
import threading
import time
import sqlite3
from datetime import datetime

# הגדרת תצוגה
st.set_page_config(page_title="Amirnet Prep", layout="wide", initial_sidebar_state="collapsed")

# CSS משודרג
st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden;}
        @media (min-width: 768px) { .block-container { max-width: 800px; margin: 0 auto; direction: rtl; text-align: right; } }
        @media (max-width: 767px) { .block-container { max-width: 100%; padding: 1rem; direction: rtl; text-align: right; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .animated-box { animation: fadeIn 0.4s ease-out forwards; }
        .passage-box { background-color: #f8fafc; padding: 20px; border-radius: 12px; border-right: 4px solid #94a3b8; margin-bottom: 20px; direction: ltr; text-align: left; font-size: 17px; color: #334155; font-family: 'Georgia', serif; line-height: 1.7; }
        .question-box { background-color: #ffffff; padding: 25px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; direction: ltr; text-align: left; font-size: 20px; font-weight: 600; line-height: 1.5; border-top: 5px solid #3b82f6; color: #0f172a; }
        .stButton>button { width: 100%; min-height: 60px; font-size: 18px; margin-top: 10px; border-radius: 12px; border: 2px solid #e2e8f0; background-color: #ffffff; color: #1e293b; font-weight: 500; transition: all 0.2s ease; }
        .stButton>button:hover { border-color: #3b82f6; background-color: #eff6ff; transform: translateY(-2px); }
        .explanation-box { background-color: #f0fdf4; padding: 25px; border-radius: 16px; margin-top: 20px; border: 1px solid #bbf7d0; border-right: 6px solid #22c55e; }
        .exp-section { margin-bottom: 12px; }
        .exp-title { color: #166534; font-weight: 700; font-size: 16px; margin-bottom: 4px; }
        .exp-text { color: #15803d; font-size: 16px; line-height: 1.5; }
        .title-text { text-align: center; color: #0f172a; font-size: 30px; font-weight: 800; margin-bottom: 25px; }
        .stats-text { text-align: center; color: #64748b; font-size: 15px; margin-bottom: 5px; font-weight: 600;}
        .menu-btn-container .stButton>button { height: 80px; font-size: 18px; border-radius: 16px; border: none; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); color: #334155; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .menu-btn-container .stButton>button:hover { background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); color: #1d4ed8; }
        .login-box { background-color: #ffffff; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); text-align: center; max-width: 400px; margin: 50px auto; border-top: 6px solid #3b82f6; }
    </style>
""", unsafe_allow_html=True)

# חיבור למסד נתונים SQLite
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

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.8-flash')

PROMPTS = {
    "השלמת משפטים": "Question type: Sentence Completion. Advanced academic vocabulary (C1/C2).",
    "ניסוח מחדש": "Question type: Restatements. Complex logical structures and pivot words.",
    "הבנת הנקרא (קטע קצר)": "Question type: Reading Comprehension. Provide a short academic paragraph (3-4 sentences) in the 'passage' field. The question should be about inference, main idea, or vocabulary in context.",
    "אוצר מילים ואסוציאציות": "Question type: Vocabulary Practice. Options are Hebrew translations.",
    "מיקוד בטעויות עבר": "Create Sentence Completion or Vocabulary questions specifically testing the following words/concepts the user previously got wrong: {mistakes_list}. Make new sentences for them."
}

def generate_questions(q_type, num_questions=10, retries=2, custom_context=""):
    prompt_instruction = PROMPTS.get(q_type, PROMPTS["השלמת משפטים"])
    if custom_context:
        prompt_instruction = prompt_instruction.replace("{mistakes_list}", custom_context)
        
    prompt = f"""
    Create {num_questions} high-level English questions for the Israeli AMIRNET exam.
    {prompt_instruction}
    Output exactly in this strict JSON FORMAT (an array of objects). Do NOT include trailing commas.
    [
        {{
            "passage": "Reading passage here if applicable, else empty string ''",
            "question": "The English question or sentence",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "The correct option",
            "exp_translation": "תרגום מדויק לעברית",
            "exp_correct": "הסבר בעברית מדוע התשובה הנכונה היא הנכונה",
            "exp_wrong": "הסבר בעברית מדוע המסיחים האחרים שגויים"
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
            if attempt == retries - 1: return []
            time.sleep(1)

def fetch_in_background(q_type, target_list, num_questions, custom_context=""):
    new_qs = generate_questions(q_type, num_questions, custom_context=custom_context)
    if new_qs: target_list.extend(new_qs)

# אתחול משתנים (Session State)
for key in ['current_user', 'question_bank', 'next_batch', 'current_index', 'answered', 'user_choice', 'is_fetching', 'start_time', 'exam_mode', 'correct_count', 'current_mode']:
    if key not in st.session_state:
        st.session_state[key] = None if key == 'current_user' else [] if 'bank' in key or 'batch' in key else 0 if 'count' in key or 'index' in key else False

# --- מסך התחברות (Login) ---
if not st.session_state.current_user:
    st.markdown("<div class='login-box animated-box'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #0f172a; margin-bottom: 20px;'>ברוך הבא לאמירנ\"ט פרו 🚀</h2>", unsafe_allow_html=True)
    username_input = st.text_input("הכנס שם משתמש כדי לשמור את ההתקדמות שלך:", placeholder="למשל: דביר")
    if st.button("כניסה למערכת", type="primary"):
        if username_input.strip():
            st.session_state.current_user = username_input.strip()
            st.rerun()
        else:
            st.error("אנא הזן שם חוקי.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- תפריט צד למשתמש מחובר ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align: center; color: #3b82f6;'>אהלן, {st.session_state.current_user}! 👋</h3>", unsafe_allow_html=True)
    
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM mistakes WHERE username=?", (st.session_state.current_user,))
    mistakes_count = c.fetchone()[0]
    st.markdown(f"<div style='text-align: center; color: #64748b; margin-bottom: 20px;'>מילים לשיפור במאגר: <b>{mistakes_count}</b></div>", unsafe_allow_html=True)
    
    if st.session_state.question_bank:
        if st.button("🚪 חזור למסך הראשי", use_container_width=True):
            st.session_state.question_bank = []
            st.session_state.next_batch = []
            st.rerun()
    if st.button("התנתק משתמש", type="secondary", use_container_width=True):
        st.session_state.current_user = None
        st.session_state.question_bank = []
        st.rerun()

# --- אזור התוכן המרכזי ---
if not st.session_state.question_bank:
    st.markdown("<div class='title-text animated-box'>בחר מסלול אימון</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='menu-btn-container'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    selected_mode = None
    with col1:
        if st.button("השלמת משפטים", use_container_width=True): selected_mode = "השלמת משפטים"
        if st.button("הבנת הנקרא (קטע קצר)", use_container_width=True): selected_mode = "הבנת הנקרא (קטע קצר)"
    with col2:
        if st.button("ניסוח מחדש", use_container_width=True): selected_mode = "ניסוח מחדש"
        if st.button("אוצר מילים ואסוציאציות", use_container_width=True): selected_mode = "אוצר מילים ואסוציאציות"
        
    st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("🎯 מיקוד בטעויות עבר", use_container_width=True, type="primary"):
            if mistakes_count < 3:
                st.warning("אין מספיק טעויות במאגר כדי לייצר מקבץ. תרגל קצת קודם!")
            else:
                selected_mode = "מיקוד בטעויות עבר"
    with col4:
        if st.button("🏆 סימולציה מלאה", use_container_width=True, type="primary"):
            selected_mode = "סימולציה מלאה"
    st.markdown("</div>", unsafe_allow_html=True)
    
    if selected_mode:
        with st.spinner("מייצר מקבץ מותאם אישית..."):
            st.session_state.exam_mode = "סימולציה" in selected_mode
            st.session_state.current_mode = selected_mode
            num_q = 22 if st.session_state.exam_mode else 10
            
            custom_context = ""
            fetch_type = selected_mode
            if selected_mode == "מיקוד בטעויות עבר":
                mistakes_data = get_user_mistakes(st.session_state.current_user)
                custom_context = ", ".join([row[1] for row in mistakes_data]) # שולח ל-API את המילים השגויות
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
                st.error("הייתה בעיה בטעינה. נסה שוב.")

if st.session_state.question_bank:
    total = len(st.session_state.question_bank)
    idx = st.session_state.current_index
    q = st.session_state.question_bank[idx]
    
    # טעינת המשך ברקע
    if not st.session_state.exam_mode and idx == 7 and not st.session_state.is_fetching:
        st.session_state.is_fetching = True
        custom_ctx = ""
        if st.session_state.current_mode == "מיקוד בטעויות עבר":
            mistakes_data = get_user_mistakes(st.session_state.current_user)
            custom_ctx = ", ".join([row[1] for row in mistakes_data])
        threading.Thread(target=fetch_in_background, args=(st.session_state.current_mode, st.session_state.next_batch, 10, custom_ctx)).start()

    # מד התקדמות וסטטוס
    st.progress(idx / total)
    stats_html = f"<div class='stats-text animated-box'>שאלה {idx + 1} מתוך {total}</div>"
    if st.session_state.exam_mode:
        elapsed = int(time.time() - st.session_state.start_time)
        mins, secs = divmod(elapsed, 60)
        stats_html += f"<div class='stats-text' style='color: #ef4444;'>⏱️ {mins:02d}:{secs:02d}</div>"
    st.markdown(stats_html, unsafe_allow_html=True)
    
    if q.get('passage'):
        st.markdown(f"<div class='passage-box animated-box'>{q['passage']}</div>", unsafe_allow_html=True)
        
    st.markdown(f"<div class='question-box animated-box'>{q['question']}</div>", unsafe_allow_html=True)
    
    # בדיקת תשובות ושמירת טעויות במסד הנתונים
    for opt in q['options']:
        if st.button(opt, disabled=st.session_state.answered, key=f"{idx}_{opt}"):
            st.session_state.user_choice = opt
            st.session_state.answered = True
            if opt == q['correct_answer']:
                st.session_state.correct_count += 1
            else:
                # רישום הטעות ב-SQLite
                log_mistake(st.session_state.current_user, st.session_state.current_mode, q['question'], q['correct_answer'], q.get('exp_translation', ''))
            st.rerun()

    # פידבק
    if st.session_state.answered:
        if not st.session_state.exam_mode:
            is_correct = st.session_state.user_choice == q['correct_answer']
            if is_correct: st.success("מעולה! תשובה נכונה 🎉") 
            else: st.error(f"טעות. נרשם במאגר לשיפור. התשובה הנכונה: {q['correct_answer']}")
            
            st.markdown(f"""
            <div class='explanation-box animated-box'>
                <div class='exp-section'>
                    <div class='exp-title'>🌍 תרגום:</div>
                    <div class='exp-text'>{q.get('exp_translation', '')}</div>
                </div>
                <div class='exp-section'>
                    <div class='exp-title'>✅ למה זו התשובה הנכונה?</div>
                    <div class='exp-text'>{q.get('exp_correct', '')}</div>
                </div>
                <div class='exp-section'>
                    <div class='exp-title'>❌ מדוע השאר שגויות?</div>
                    <div class='exp-text'>{q.get('exp_wrong', '')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("") 
        if idx < total - 1:
            if st.button("לשאלה הבאה ➡️", type="primary"):
                st.session_state.current_index += 1
                st.session_state.answered = False
                st.session_state.user_choice = None
                st.rerun()
        else:
            if st.session_state.exam_mode:
                score = int((st.session_state.correct_count / total) * 100)
                st.markdown(f"<div class='title-text animated-box'>סיימת את הסימולציה! 🎓<br>ציון: {score}</div>", unsafe_allow_html=True)
            else:
                if st.session_state.next_batch:
                    if st.button("למקבץ הבא ברצף ⚡", type="primary"):
                        st.session_state.question_bank = st.session_state.next_batch.copy()
                        st.session_state.next_batch = []
                        st.session_state.is_fetching = False
                        st.session_state.current_index = 0
                        st.session_state.answered = False
                        st.session_state.user_choice = None
                        st.rerun()
                else:
                    st.info("טוען עוד שאלות משרתי גוגל...")
                    if st.button("רענן בדיקה"): st.rerun()
