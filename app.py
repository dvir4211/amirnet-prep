import streamlit as st
import google.generativeai as genai
import json
import re

# הגדרות תצוגה
st.set_page_config(page_title="Amirnet Prep", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
        .block-container { direction: rtl; text-align: right; padding-top: 2rem; }
        .stButton>button { width: 100%; height: 55px; font-size: 18px; margin-top: 10px; border-radius: 10px; }
        .explanation-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-top: 20px; color: black;}
    </style>
""", unsafe_allow_html=True)

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("לא נמצא מפתח API. ודא שהגדרת אותו ב-Advanced Settings.")

model = genai.GenerativeModel('gemini-3.8-flash')

def generate_question(q_type):
    prompt = f"""
    Create a high-level English question for the Israeli AMIRNET exam.
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
        
        # ניקוי חכם ששולף רק את התוכן של ה-JSON, גם אם המודל הוסיף שטויות מסביב
        match = re.search(r'```(?:json)?(.*?)```', raw_text, re.DOTALL)
        if match:
            raw_text = match.group(1).strip()
            
        return json.loads(raw_text)
    except Exception as e:
        st.error(f"שגיאה בניתוח התשובה. נסה ללחוץ שוב.")
        with st.expander("פרטי השגיאה למפתחים"):
            st.write(e)
            st.write("פלט גולמי:", response.text if 'response' in locals() else "אין פלט")
        return None

if 'current_q' not in st.session_state:
    st.session_state.current_q = None
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'user_choice' not in st.session_state:
    st.session_state.user_choice = None

st.title("🎓 הכנה לאמירנ\"ט")

mode = st.selectbox("בחר סוג תרגול:", ["השלמת משפטים (Sentence Completion)", "ניסוח מחדש (Restatements)"])

if st.button("ייצר שאלה חדשה"):
    with st.spinner("מחולל שאלה ברמת פטור... (זה יכול לקחת כמה שניות)"):
        st.session_state.current_q = generate_question(mode)
        st.session_state.answered = False
        st.session_state.user_choice = None

if st.session_state.current_q:
    q = st.session_state.current_q
    st.markdown(f"### {q['question']}")
    
    st.write("בחר את התשובה הנכונה:")
    for opt in q['options']:
        if st.button(opt, disabled=st.session_state.answered):
            st.session_state.user_choice = opt
            st.session_state.answered = True
            st.rerun()

    if st.session_state.answered:
        if st.session_state.user_choice == q['correct_answer']:
            st.success("מעולה! תשובה נכונה. 🎉")
        else:
            st.error(f"טעות. התשובה הנכונה היא: {q['correct_answer']}")
            
        st.markdown(f"<div class='explanation-box'><b>ניתוח והסבר:</b><br>{q['explanation']}</div>", unsafe_allow_html=True)
