import streamlit as st
import google.generativeai as genai
import json

# הגדרות תצוגה למובייל ויישור לימין
st.set_page_config(page_title="Amirnet Prep", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
        .block-container { direction: rtl; text-align: right; padding-top: 2rem; }
        .stButton>button { width: 100%; height: 55px; font-size: 18px; margin-top: 10px; border-radius: 10px; }
        .explanation-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-top: 20px; color: black;}
    </style>
""", unsafe_allow_html=True)

# הגדרת ה-API של המודל
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("יש להגדיר מפתח API בהגדרות השרת (Secrets).")

model = genai.GenerativeModel('gemini-2.5-flash')

# פונקציה לייצור שאלה
def generate_question(q_type):
    prompt = f"""
    Create a high-level English question for the Israeli AMIRNET (university exemption) exam.
    Question type: {q_type}.
    Level: Advanced academic vocabulary and complex logical structures (C1/C2 level).
    Output exactly in this JSON format, in Hebrew (except for the English text):
    {{
        "question": "The English sentence with a blank or the original sentence",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "The correct option",
        "explanation": "הסבר מפורט בעברית: מדוע התשובה נכונה, תרגום המשפט, ומדוע כל אחד מהמסיחים האחרים שגוי מבחינה לוגית או תחבירית."
    }}
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        # ניקוי פורמט Markdown אם קיים
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3]
        return json.loads(raw_text)
    except Exception as e:
        return None

# ניהול מצב (State)
if 'current_q' not in st.session_state:
    st.session_state.current_q = None
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'user_choice' not in st.session_state:
    st.session_state.user_choice = None

# ממשק המשתמש
st.title("🎓 הכנה לאמירנ\"ט")

mode = st.selectbox("בחר סוג תרגול:", ["השלמת משפטים (Sentence Completion)", "ניסוח מחדש (Restatements)"])

if st.button("ייצר שאלה חדשה"):
    with st.spinner("מחולל שאלה ברמת פטור..."):
        st.session_state.current_q = generate_question(mode)
        st.session_state.answered = False
        st.session_state.user_choice = None

# תצוגת השאלה
if st.session_state.current_q:
    q = st.session_state.current_q
    st.markdown(f"### {q['question']}")
    
    st.write("בחר את התשובה הנכונה:")
    for opt in q['options']:
        if st.button(opt, disabled=st.session_state.answered):
            st.session_state.user_choice = opt
            st.session_state.answered = True
            st.rerun()

    # תצוגת פידבק לאחר מענה
    if st.session_state.answered:
        if st.session_state.user_choice == q['correct_answer']:
            st.success("מעולה! תשובה נכונה. 🎉")
        else:
            st.error(f"טעות. התשובה הנכונה היא: {q['correct_answer']}")
            
        st.markdown(f"<div class='explanation-box'><b>ניתוח והסבר:</b><br>{q['explanation']}</div>", unsafe_allow_html=True)
