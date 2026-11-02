import streamlit as st
import google.generativeai as genai
import json
import re
import threading
import time

# הגדרת תצוגה שמתפרסת היטב גם במחשב וגם בנייד
st.set_page_config(page_title="Amirnet Prep", layout="wide", initial_sidebar_state="expanded")

# CSS מתקדם: אנימציות, צבעים חיים (בסגנון זינוק), רספונסיביות למחשב/נייד
st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden;}
        
        /* התאמה רספונסיבית */
        @media (min-width: 768px) {
            .block-container { max-width: 750px; margin: 0 auto; direction: rtl; text-align: right; }
        }
        @media (max-width: 767px) {
            .block-container { max-width: 100%; padding: 1rem; direction: rtl; text-align: right; }
        }
        
        /* אנימציות */
        @keyframes slideUpFade {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .animated-box { animation: slideUpFade 0.4s ease-out forwards; }
        
        /* כרטיסיית שאלה */
        .question-box {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            margin-bottom: 25px;
            direction: ltr;
            text-align: left;
            font-size: 20px;
            line-height: 1.6;
            border-top: 6px solid #00d2ff;
            color: #2b2b2b;
        }
        
        /* כפתורי תשובות */
        .stButton>button { 
            width: 100%; 
            min-height: 65px; 
            font-size: 18px; 
            margin-top: 12px; 
            border-radius: 12px; 
            border: 2px solid #edf2f7;
            background-color: #ffffff;
            color: #2d3748;
            font-weight: 500;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }
        .stButton>button:hover {
            border-color: #00d2ff;
            background-color: #f0faff;
            transform: translateY(-3px);
            box-shadow: 0 6px 15px rgba(0, 210, 255, 0.15);
        }
        
        /* קופסת הסבר מובנית וצבעונית */
        .explanation-box { 
            background-color: #fafcff; 
            padding: 25px; 
            border-radius: 16px; 
            margin-top: 25px; 
            border: 1px solid #e2e8f0;
            border-right: 6px solid #48bb78;
        }
        .exp-section { margin-bottom: 15px; }
        .exp-title { color: #2c5282; font-weight: bold; font-size: 17px; margin-bottom: 5px; }
        .exp-text { color: #4a5568; font-size: 16px; line-height: 1.5; }
        
        .title-text { text-align: center; color: #1a202c; font-size: 32px; font-weight: 900; margin-bottom: 30px; letter-spacing: -0.5px;}
        .stats-text { text-align: center; color: #718096; font-size: 16px; margin-bottom: 15px; font-weight: 600;}
    </style>
""", unsafe_allow_html=True)

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

model = genai.GenerativeModel('gemini-3.8-flash')

PROMPTS = {
    "השלמת משפטים": "Question type: Sentence Completion. Advanced academic vocabulary (C1/C2).",
    "ניסוח מחדש": "Question type: Restatements. Complex logical structures and pivot words.",
    "פירוק מורפולוגי (תחיליות וסופיות)": "Question type: Morphological Breakdown. Target an advanced academic word.",
    "אלימינציה עיוורת (דקדוק והקשר)": "Question type: Grammar & Context Elimination. Correct word must be obscure, options grammatically different.",
    "אוצר מילים ואסוציאציות": "Question type: Vocabulary Practice. Options are Hebrew translations."
}

def generate_questions(q_type, num_questions=10):
    prompt_instruction = PROMPTS.get(q_type, PROMPTS["השלמת משפטים"])
    prompt = f"""
    Create {num_questions} high-level English questions for the Israeli AMIRNET exam.
    {prompt_instruction}
    Output exactly in this JSON FORMAT (an array of objects).
    [
        {{
            "question": "The English text or sentence",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "The correct option",
            "exp_translation": "תרגום מדויק של המשפט המקורי / המילה לעברית",
            "exp_correct": "הסבר מדוע התשובה הנכונה היא הנכונה",
            "exp_wrong": "תרגום המסיחים האחרים והסבר מדוע כל אחד מהם שגוי לוגית/תחבירית"
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

def fetch_in_background(q_type, target_list, num_questions):
    new_qs = generate_questions(q_type, num_questions)
    target_list.extend(new_qs)

for key in ['question_bank', 'next_batch', 'current_index', 'answered', 'user_choice', 'is_fetching', 'start_time', 'exam_mode', 'correct_count']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'bank' in key or 'batch' in key else 0 if 'count' in key or 'index' in key else False if 'mode' in key or 'fetching' in key or 'answered' in key else None

# --- תפריט צד (Sidebar) לניווט ויציאה ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00d2ff;'>🎯 תפריט ניווט</h2>", unsafe_allow_html=True)
    
    if st.session_state.question_bank:
        st.success("תרגול פעיל כעת")
        if st.button("🚪 יציאה למסך הראשי", use_container_width=True):
            st.session_state.question_bank = []
            st.session_state.next_batch = []
            st.rerun()
    else:
        st.info("בחר מסלול כדי להתחיל")

# --- אזור התוכן המרכזי ---
if not st.session_state.question_bank:
    st.markdown("<div class='title-text animated-box'>בחר את מסלול האימון שלך</div>", unsafe_allow_html=True)
    mode = st.radio("סוג התרגול:", 
                    ["השלמת משפטים", "ניסוח מחדש", "פירוק מורפולוגי (תחיליות וסופיות)", "אלימינציה עיוורת (דקדוק והקשר)", "אוצר מילים ואסוציאציות", "סימולציה מלאה (פרק מעורב)"],
                    horizontal=False)
    
    if st.button("התחל תרגול 🚀", type="primary"):
        with st.spinner("בונה מסלול אימון חכם..."):
            st.session_state.exam_mode = "סימולציה" in mode
            num_q = 22 if st.session_state.exam_mode else 10
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

if st.session_state.question_bank:
    total = len(st.session_state.question_bank)
    idx = st.session_state.current_index
    q = st.session_state.question_bank[idx]
    
    if not st.session_state.exam_mode and idx == 7 and not st.session_state.is_fetching:
        st.session_state.is_fetching = True
        threading.Thread(target=fetch_in_background, args=("השלמת משפטים", st.session_state.next_batch, 10)).start()

    # סטטוס עליון
    stats_html = f"<div class='stats-text animated-box'>שאלה {idx + 1} מתוך {total}</div>"
    if st.session_state.exam_mode:
        elapsed = int(time.time() - st.session_state.start_time)
        mins, secs = divmod(elapsed, 60)
        stats_html += f"<div class='stats-text' style='color: #e53e3e;'>⏱️ {mins:02d}:{secs:02d}</div>"
    st.markdown(stats_html, unsafe_allow_html=True)
    
    # שאלה
    st.markdown(f"<div class='question-box animated-box'>{q['question']}</div>", unsafe_allow_html=True)
    
    # אפשרויות
    for opt in q['options']:
        if st.button(opt, disabled=st.session_state.answered, key=f"{idx}_{opt}"):
            st.session_state.user_choice = opt
            st.session_state.answered = True
            if opt == q['correct_answer']:
                st.session_state.correct_count += 1
            st.rerun()

    # הסבר מדורג לאחר מענה
    if st.session_state.answered:
        if not st.session_state.exam_mode:
            is_correct = st.session_state.user_choice == q['correct_answer']
            msg = "מעולה! תשובה נכונה 🎉" if is_correct else f"טעות. התשובה הנכונה: {q['correct_answer']}"
            if is_correct: st.success(msg) 
            else: st.error(msg)
            
            # מבנה הסבר חדש ומסודר
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
                    <div class='exp-title'>❌ למה השאר שגויות?</div>
                    <div class='exp-text'>{q.get('exp_wrong', '')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # כפתורי המשך
        st.write("") # מרווח
        if idx < total - 1:
            if st.button("המשך לשאלה הבאה ➡️", type="primary"):
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
                    if st.button("המשך ברצף ⚡", type="primary"):
                        st.session_state.question_bank = st.session_state.next_batch.copy()
                        st.session_state.next_batch = []
                        st.session_state.is_fetching = False
                        st.session_state.current_index = 0
                        st.session_state.answered = False
                        st.session_state.user_choice = None
                        st.rerun()
                else:
                    st.info("טוען עוד שאלות...")
                    if st.button("בדוק שוב"): st.rerun()
