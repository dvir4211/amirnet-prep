import streamlit as st
import google.generativeai as genai
import json
import re
import threading
import random
import time

# הגדרות תצוגה לעיצוב מודרני, ממורכז וצבעוני
st.set_page_config(page_title="Amirnet Prep", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden;}
        
        /* עיצוב רקע ומרווחים */
        .block-container { 
            direction: rtl; 
            text-align: right; 
            padding-top: 1rem; 
            max-width: 500px;
        }
        
        /* כרטיסיית השאלה - עיצוב נקי וברור */
        .question-box {
            background-color: #ffffff;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            margin-bottom: 20px;
            direction: ltr;
            text-align: left;
            font-size: 19px;
            line-height: 1.6;
            border-top: 6px solid #4A90E2;
        }
        
        /* כפתורי תשובות - צבעים חיים יותר */
        .stButton>button { 
            width: 100%; 
            min-height: 60px; 
            font-size: 17px; 
            margin-top: 10px; 
            border-radius: 15px; 
            border: 2px solid #e1e4e8;
            background-color: #ffffff;
            color: #24292e;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .stButton>button:hover {
            border-color: #4A90E2;
            background-color: #f1f8ff;
            transform: translateY(-2px);
        }
        
        /* קופסת הסבר מודגשת */
        .explanation-box { 
            background-color: #f0f7ff; 
            padding: 20px; 
            border-radius: 15px; 
            margin-top: 25px; 
            color: #0366d6;
            font-size: 16px;
            border-right: 5px solid #4A90E2;
            line-height: 1.5;
        }
        
        .title-text { text-align: center; color: #24292e; font-size: 28px; font-weight: 800; margin-bottom: 20px; }
        .stats-text { text-align: center; color: #6a737d; font-size: 15px; margin-bottom: 15px; font-weight: 600;}
    </style>
""", unsafe_allow_html=True)

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

model = genai.GenerativeModel('gemini-3.8-flash')

# מאגר הפרומפטים לפי סוג התרגול
PROMPTS = {
    "השלמת משפטים": "Question type: Sentence Completion. Advanced academic vocabulary (C1/C2).",
    "ניסוח מחדש": "Question type: Restatements. Complex logical structures and pivot words.",
    "פירוק מורפולוגי (תחיליות וסופיות)": "Question type: Morphological Breakdown. Provide an advanced academic word. Ask for its meaning. The explanation MUST break down its prefixes, suffixes, and root to show how to deduce the meaning.",
    "אלימינציה עיוורת (דקדוק והקשר)": "Question type: Grammar & Context Elimination. Provide a sentence with a BLANK. The correct word should be extremely rare or made-up. The options must be grammatically different (noun, verb, prep) or logically impossible except for one. The explanation must teach how to eliminate options using grammar/context clues without knowing the word.",
    "אוצר מילים ואסוציאציות": "Question type: Vocabulary Practice. Provide a high-level English word. Options: 4 Hebrew translations. The explanation must include: the correct translation, an English example sentence, and a highly creative, memorable Hebrew mnemonic/association (אסוציאציה זיכרונית) to remember it."
}

def generate_questions(q_type, num_questions=10):
    prompt_instruction = PROMPTS.get(q_type, PROMPTS["השלמת משפטים"])
    prompt = f"""
    Create {num_questions} high-level English questions for the Israeli AMIRNET exam.
    {prompt_instruction}
    Output exactly in this JSON FORMAT (an array of objects), in Hebrew (except for English text). Do not use Markdown formatting in keys.
    [
        {{
            "question": "The English text or sentence",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "The correct option",
            "explanation": "הסבר מפורט בעברית לפי ההנחיות."
        }}
    ]
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        match = re.search(r'```(?:json)?(.*?)```', raw_text, re.DOTALL)
        if match:
            raw_text = match.group(1).strip()
        return json.loads(raw_text)
    except Exception as e:
        return []

# פונקציה שרצה ברקע לטעינת המקבץ הבא
def fetch_in_background(q_type, target_list, num_questions):
    new_qs = generate_questions(q_type, num_questions)
    target_list.extend(new_qs)

# אתחול זיכרון
if 'question_bank' not in st.session_state:
    st.session_state.question_bank = []
if 'next_batch' not in st.session_state:
    st.session_state.next_batch = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'user_choice' not in st.session_state:
    st.session_state.user_choice = None
if 'is_fetching' not in st.session_state:
    st.session_state.is_fetching = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'exam_mode' not in st.session_state:
    st.session_state.exam_mode = False
if 'correct_count' not in st.session_state:
    st.session_state.correct_count = 0

st.markdown("<div class='title-text'>🚀 אימון אמירנ\"ט</div>", unsafe_allow_html=True)

# תפריט ראשי מוצג רק אם אין שאלות פעילות
if not st.session_state.question_bank:
    mode = st.selectbox("בחר מצב למידה:", 
                       ["השלמת משפטים", "ניסוח מחדש", "פירוק מורפולוגי (תחיליות וסופיות)", "אלימינציה עיוורת (דקדוק והקשר)", "אוצר מילים ואסוציאציות", "סימולציה מלאה (פרק מעורב 22 שאלות)"])
    
    if st.button("התחל תרגול", type="primary"):
        with st.spinner("בונה מקבץ חכם..."):
            st.session_state.exam_mode = "סימולציה מלאה" in mode
            num_q = 22 if st.session_state.exam_mode else 10
            # בסימולציה נבחר סוג שאלות מעורב, לצורך הפשטות הקוד ישלח פרומפט משולב או יבחר ברירת מחדל
            fetch_type = "השלמת משפטים" if st.session_state.exam_mode else mode
            
            bank = generate_questions(fetch_type, num_q)
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
                st.error("שגיאה בטעינת הנתונים מהמודל. נסה שוב.")

# ניהול רצף השאלות
if st.session_state.question_bank:
    total = len(st.session_state.question_bank)
    idx = st.session_state.current_index
    q = st.session_state.question_bank[idx]
    
    # טעינת רקע (Threading) כשמגיעים לשאלה השמינית (במוד תרגול רגיל)
    if not st.session_state.exam_mode and idx == 7 and not st.session_state.is_fetching:
        st.session_state.is_fetching = True
        threading.Thread(target=fetch_in_background, args=("השלמת משפטים", st.session_state.next_batch, 10)).start()

    # תצוגת סטטוס וטיימר בסימולציה
    stats_html = f"<div class='stats-text'>שאלה {idx + 1} מתוך {total}</div>"
    if st.session_state.exam_mode:
        elapsed = int(time.time() - st.session_state.start_time)
        mins, secs = divmod(elapsed, 60)
        stats_html += f"<div class='stats-text' style='color: #d73a49;'>⏱️ זמן רץ: {mins:02d}:{secs:02d}</div>"
    st.markdown(stats_html, unsafe_allow_html=True)
    
    # תצוגת השאלה
    st.markdown(f"<div class='question-box'>{q['question']}</div>", unsafe_allow_html=True)
    
    # תצוגת כפתורי התשובות
    for opt in q['options']:
        if st.button(opt, disabled=st.session_state.answered, key=f"{idx}_{opt}"):
            st.session_state.user_choice = opt
            st.session_state.answered = True
            if opt == q['correct_answer']:
                st.session_state.correct_count += 1
            st.rerun()

    # פידבק והסבר לאחר לחיצה (בסימולציה ההסבר מוסתר עד הסוף)
    if st.session_state.answered:
        if not st.session_state.exam_mode:
            if st.session_state.user_choice == q['correct_answer']:
                st.success("מעולה! 🎯")
            else:
                st.error(f"טעות. התשובה הנכונה: {q['correct_answer']}")
            st.markdown(f"<div class='explanation-box'><b>פיצוח השאלה:</b><br>{q['explanation']}</div>", unsafe_allow_html=True)
        
        # כפתור מעבר לשאלה הבאה
        if idx < total - 1:
            if st.button("המשך לשאלה הבאה ➡️", type="primary"):
                st.session_state.current_index += 1
                st.session_state.answered = False
                st.session_state.user_choice = None
                st.rerun()
        else:
            # סיום המקבץ
            if st.session_state.exam_mode:
                score = int((st.session_state.correct_count / total) * 100)
                st.markdown(f"<div class='title-text'>סיימת את הסימולציה! 🎓<br>ציון: {score}/100</div>", unsafe_allow_html=True)
                if st.button("חזור לתפריט הראשי"):
                    st.session_state.question_bank = []
                    st.rerun()
            else:
                # משיכת שאלות מחדר ההמתנה (Threading) במצב רגיל
                if st.session_state.next_batch:
                    if st.button("המשך ברצף (המקבץ הבא מוכן) ⚡", type="primary"):
                        st.session_state.question_bank = st.session_state.next_batch.copy()
                        st.session_state.next_batch = []
                        st.session_state.is_fetching = False
                        st.session_state.current_index = 0
                        st.session_state.answered = False
                        st.session_state.user_choice = None
                        st.rerun()
                else:
                    st.info("טוען עוד שאלות משרתי גוגל...")
                    if st.button("בדוק אם מוכן"):
                        st.rerun()
