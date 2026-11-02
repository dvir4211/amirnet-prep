import streamlit as st
import google.generativeai as genai
import json
import re
import threading
import time
import sqlite3
import random

# הגדרת עמוד
st.set_page_config(page_title="Amirnet Executive", layout="wide", initial_sidebar_state="collapsed")

# --- CSS מקצועי ובוגר (Executive Clean Design) עם פונטים Heebo ו-Inter ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
        
        #MainMenu, header, footer {visibility: hidden;}
        
        html, body, [class*="css"] {
            font-family: 'Heebo', 'Inter', sans-serif !important;
            color: #0f172a;
        }

        /* רקע נקי, סולידי ויוקרתי */
        .stApp {
            background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        }

        /* התאמה רספונסיבית */
        @media (min-width: 768px) {
            .block-container { max-width: 840px; margin: 0 auto; padding-top: 2rem; direction: rtl; text-align: right; }
        }
        @media (max-width: 767px) {
            .block-container { max-width: 100%; padding: 1rem; direction: rtl; text-align: right; }
        }

        @keyframes subtleSlide {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in { animation: subtleSlide 0.25s ease-out forwards; }

        /* סרגל עליון (Header Bar) */
        .top-nav {
            background: #ffffff;
            padding: 14px 24px;
            border-radius: 14px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }
        .nav-user { font-weight: 700; font-size: 16px; color: #0f172a; }
        .nav-badge {
            background: #f1f5f9;
            color: #475569;
            border: 1px solid #cbd5e1;
            padding: 4px 12px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
        }
        .ai-status-badge {
            display: inline-block;
            background: #eef2ff;
            color: #4338ca;
            border: 1px solid #c7d2fe;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 10px;
        }

        /* כותרות דשבורד */
        .hero-title {
            text-align: right;
            color: #0f172a;
            font-size: 30px;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin-bottom: 4px;
        }
        .hero-subtitle {
            text-align: right;
            color: #64748b;
            font-size: 16px;
            font-weight: 400;
            margin-bottom: 28px;
        }

        /* עיצוב כפתורי דשבורד - נקי, בוגר עם פס הדגשה צבעוני בצד */
        .stButton > button {
            width: 100%;
            min-height: 62px;
            font-family: 'Heebo', 'Inter', sans-serif !important;
            font-size: 17px;
            font-weight: 600;
            border-radius: 12px;
            transition: all 0.18s ease;
            border: 1px solid #cbd5e1;
            background: #ffffff;
            color: #1e293b;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            margin-top: 6px;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(15, 23, 42, 0.06);
            border-color: #64748b;
            background: #f8fafc;
            color: #0f172a;
        }

        /* צבעי אקסנט יוקרתיים לכפתורי המסלולים בדשבורד */
        div.st-key-mode_sc button { border-right: 5px solid #2563eb !important; height: 84px; text-align: right; }
        div.st-key-mode_rest button { border-right: 5px solid #4f46e5 !important; height: 84px; text-align: right; }
        div.st-key-mode_rc button { border-right: 5px solid #0d9488 !important; height: 84px; text-align: right; }
        div.st-key-mode_voc button { border-right: 5px solid #d97706 !important; height: 84px; text-align: right; }
        div.st-key-mode_elim button { border-right: 5px solid #db2777 !important; height: 84px; text-align: right; }
        div.st-key-mode_morph button { border-right: 5px solid #0284c7 !important; height: 84px; text-align: right; }
        
        div.st-key-mode_mistakes button {
            background: #fff1f2 !important;
            border: 1px solid #fecdd3 !important;
            border-right: 5px solid #e11d48 !important;
            color: #9f1239 !important;
            height: 76px;
        }
        div.st-key-mode_sim button {
            background: #0f172a !important;
            color: #f8fafc !important;
            border: 1px solid #0f172a !important;
            height: 76px;
        }
        div.st-key-mode_sim button:hover {
            background: #1e293b !important;
            color: #ffffff !important;
        }
        div.st-key-exit_top_btn button {
            min-height: 44px !important;
            height: 44px !important;
            font-size: 14px !important;
            background: #ffffff !important;
            color: #475569 !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 10px !important;
            margin-top: 0 !important;
        }

        /* כרטיסיית קטע קריאה */
        .passage-box {
            background: #ffffff;
            padding: 24px 28px;
            border-radius: 14px;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #0d9488;
            margin-bottom: 18px;
            direction: ltr;
            text-align: left;
            font-family: 'Inter', sans-serif !important;
            font-size: 16.5px;
            color: #334155;
            line-height: 1.75;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03);
        }

        /* כרטיסיית השאלה */
        .question-box {
            background: #ffffff;
            padding: 28px 30px;
            border-radius: 16px;
            border: 1px solid #cbd5e1;
            border-top: 4px solid #2563eb;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
            margin-bottom: 20px;
            direction: ltr;
            text-align: left;
            font-family: 'Inter', sans-serif !important;
            font-size: 20px;
            font-weight: 600;
            line-height: 1.55;
            color: #0f172a;
        }

        /* מצבי תשובות לאחר לחיצה */
        .ans-correct {
            background: #f0fdf4; border: 1.5px solid #16a34a; color: #14532d;
            padding: 15px 20px; border-radius: 12px; font-family: 'Inter', 'Heebo', sans-serif;
            font-size: 17px; font-weight: 600; margin-top: 8px; direction: ltr; text-align: left;
        }
        .ans-wrong {
            background: #fef2f2; border: 1.5px solid #dc2626; color: #7f1d1d;
            padding: 15px 20px; border-radius: 12px; font-family: 'Inter', 'Heebo', sans-serif;
            font-size: 17px; font-weight: 600; margin-top: 8px; direction: ltr; text-align: left;
        }
        .ans-neutral {
            background: #f8fafc; border: 1px solid #e2e8f0; color: #64748b;
            padding: 15px 20px; border-radius: 12px; font-family: 'Inter', 'Heebo', sans-serif;
            font-size: 17px; margin-top: 8px; direction: ltr; text-align: left;
        }

        /* קופסת הסבר מקצועית */
        .explanation-container {
            background: #ffffff;
            padding: 24px;
            border-radius: 16px;
            margin-top: 20px;
            border: 1px solid #e2e8f0;
            border-right: 4px solid #2563eb;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
        }
        .exp-block { margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid #f1f5f9; }
        .exp-block:last-child { margin-bottom: 0; padding-bottom: 0; border-bottom: none; }
        .exp-label { color: #0f172a; font-weight: 700; font-size: 15px; margin-bottom: 4px; }
        .exp-body { color: #334155; font-size: 15.5px; line-height: 1.6; }

        .login-wrapper {
            background: #ffffff; padding: 40px 32px; border-radius: 20px;
            border: 1px solid #e2e8f0; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);
            max-width: 420px; margin: 60px auto 20px auto; text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# מאגר מובנה מיידי (Zero-Latency Local Bank) - 10 שאלות לכל קטגוריה (60 סה"כ)
# ==============================================================================
INSTANT_BANK = {
    "השלמת משפטים": [
        {"passage": "", "question": "Although the initial findings appeared _____, subsequent experiments revealed several critical flaws in the methodology.", "options": ["conclusive", "arbitrary", "redundant", "obsolete"], "correct_answer": "conclusive", "exp_translation": "למרות שהממצאים הראשוניים נראו חד-משמעיים, ניסויים עוקבים חשפו מספר פגמים קריטיים במתודולוגיה.", "exp_correct": "מילת הוויתור Although מחייבת ניגוד בין חלקי המשפט. אם בהמשך התגלו פגמים, בהתחלה הממצאים נראו משכנעים/סופיים (conclusive).", "exp_wrong": "arbitrary = שרירותי | redundant = מיותר | obsolete = מיושן. אף אחד מהם לא יוצר ניגוד חיובי לחשיפת פגמים."},
        {"passage": "", "question": "The diplomat's _____ remarks during the summit inadvertently escalated tensions between the two neighboring nations.", "options": ["provocative", "conciliatory", "benign", "impartial"], "correct_answer": "provocative", "exp_translation": "הערותיו המתגרות של הדיפלומט במהלך הפסגה הסלימו בשוגג את המתיחות בין שתי המדינות השכנות.", "exp_correct": "כדי שהערות יגרמו להסלמת מתיחות (escalated tensions), עליהן להיות מתגרות או מעוררות מחלוקת (provocative).", "exp_wrong": "conciliatory = מפייס | benign = עדין/לא מזיק | impartial = ניטרלי."},
        {"passage": "", "question": "Because the ancient manuscript had _____ over centuries of exposure to humidity, historians could barely decipher its text.", "options": ["deteriorated", "proliferated", "flourished", "stabilized"], "correct_answer": "deteriorated", "exp_translation": "מכיוון שכתב היד העתיק הידרדר לאורך מאות שנים של חשיפה ללחות, היסטוריונים בקושי הצליחו לפענח את הטקסט שלו.", "exp_correct": "חשיפה ללחות וקושי בפענוח מעידים על התבלות או הידרדרות במצב החומר (deteriorated).", "exp_wrong": "proliferated = התרבה | flourished = שגשג | stabilized = התייצב."},
        {"passage": "", "question": "Far from being a _____ summary, the report offers an exhaustive analysis of every financial transaction made by the firm.", "options": ["superficial", "comprehensive", "meticulous", "rigorous"], "correct_answer": "superficial", "exp_translation": "רחוק מלהיות סיכום שטחי, הדוח מציע ניתוח מקיף של כל עסקה פיננסית שביצעה החברה.", "exp_correct": "הביטוי Far from being (רחוק מלהיות) דורש הפך מהמילה exhaustive (מקיף/ממצה). ההפך הוא שטחי (superficial).", "exp_wrong": "comprehensive (מקיף), meticulous (קפדני), ו-rigorous (מחמיר) הן מילים נרדפות ל-exhaustive ולא הפכים."},
        {"passage": "", "question": "While the CEO's strategy was praised for its audacity, the board remained _____ about its long-term financial viability.", "options": ["skeptical", "enthusiastic", "complacent", "indifferent"], "correct_answer": "skeptical", "exp_translation": "בעוד שהאסטרטגיה של המנכ\"ל זכתה לשבחים על תעוזתה, הדירקטוריון נותר ספקן לגבי היתכנותה הכלכלית לטווח ארוך.", "exp_correct": "While יוצר ניגוד בין השבחים (praised) לבין תגובת הדירקטוריון, שלכן חייבת להיות ספקנית/חשדנית (skeptical).", "exp_wrong": "enthusiastic = נלהב | complacent = שאנן | indifferent = אדיש."},
        {"passage": "", "question": "The new regulation is designed to _____ the distribution of counterfeit pharmaceuticals by imposing strict penalties on violators.", "options": ["curtail", "expedite", "foster", "endorse"], "correct_answer": "curtail", "exp_translation": "התקנה החדשה נועדה לצמצם/לבלום את הפצת התרופות המזויפות באמצעות הטלת עונשים מחמירים על מפירי החוק.", "exp_correct": "הטלת עונשים על הפצת תרופות מזויפות נועדה לבלום או לקצץ את התופעה (curtail).", "exp_wrong": "expedite = לזרז | foster = לטפח | endorse = לתמוך פומבית."},
        {"passage": "", "question": "Known for her _____ temperament, the judge rarely allowed emotional appeals to sway her interpretation of the law.", "options": ["impassive", "volatile", "capricious", "fervent"], "correct_answer": "impassive", "exp_translation": "השופטת, הידועה במזגה חסר הפניות/אדיש לרגש, מיעטה לתת לפניות רגשיות להטות את פרשנותה לחוק.", "exp_correct": "מי שלא מושפעת מפניות רגשיות היא בעלת מזג קר רוח ומאופק (impassive).", "exp_wrong": "volatile = הפכפך/נפיץ | capricious = גחמני | fervent = נלהב/לוהט."},
        {"passage": "", "question": "Unless the municipality allocates additional funds to infrastructure, the city's transit system will remain _____.", "options": ["inadequate", "exemplary", "resilient", "viable"], "correct_answer": "inadequate", "exp_translation": "אלא אם העירייה תקצה תקציבים נוספים לתשתיות, מערכת התחבורה של העיר תיוותר לקויה/לא מספקת.", "exp_correct": "Unless מתאר תנאי שללא קיומו המצב יישאר שלילי – כלומר לא מספק (inadequate).", "exp_wrong": "exemplary = למופת | resilient = חסין | viable = בר-קיימא."},
        {"passage": "", "question": "The biographer's account is remarkably _____, presenting both the triumphs and the moral failings of the historical figure.", "options": ["candid", "partisan", "evasive", "eulogistic"], "correct_answer": "candid", "exp_translation": "תיאורו של הביוגרף כן וגלוי לב באופן יוצא דופן, ומציג הן את הניצחונות והן את הכשלים המוסריים של הדמות ההיסטורית.", "exp_correct": "הצגת הצלחות לצד כישלונות מעידה על כנות ויושרה ללא משוא פנים (candid).", "exp_wrong": "partisan = מוטה/מפלגתי | evasive = מתחמק | eulogistic = מהלל/מספיד בשבחים."},
        {"passage": "", "question": "Once considered an _____ theory on the fringes of physics, quantum entanglement is now a cornerstone of modern science.", "options": ["esoteric", "orthodox", "ubiquitous", "axiomatic"], "correct_answer": "esoteric", "exp_translation": "מה שנחשב בעבר לתיאוריה אזוטרית (נחלת מעטים) בשולי הפיזיקה, הוא כיום אבן יסוד של המדע המודרני.", "exp_correct": "תיאוריה בשוליים (on the fringes) שבניגוד להיום הייתה מוכרת רק למעטים היא esoteric.", "exp_wrong": "orthodox = מקובל/שמרני | ubiquitous = נמצא בכל מקום | axiomatic = מובן מאליו."}
    ],
    "ניסוח מחדש": [
        {"passage": "", "question": "Hardly had the new software been deployed when users began reporting severe security vulnerabilities.", "options": ["Users reported security flaws almost immediately after the new software was launched.", "Before the new software could be deployed, severe security issues had to be resolved.", "Hardly any users noticed the security vulnerabilities in the newly deployed software.", "The deployment of the new software was delayed due to user reports of security flaws."], "correct_answer": "Users reported security flaws almost immediately after the new software was launched.", "exp_translation": "בקושי הוטמעה התוכנה החדשה וכבר החלו משתמשים לדווח על פרצות אבטחה חמורות.", "exp_correct": "המבנה Hardly had X happened when Y happened מבטא שני אירועים שקרו זה אחר זה באופן כמעט מיידי.", "exp_wrong": "המסיחים האחרים משנים את סדר הזמנים, טוענים שמעט משתמשים שמו לב (מלכודת המילה Hardly), או ממציאים עיכוב."},
        {"passage": "", "question": "Proponents of renewable energy argue that subsidies for fossil fuels distort market competition.", "options": ["Those in favor of green energy claim that financial support for fossil fuels creates an unfair market.", "Opponents of fossil fuels believe that market competition will eventually eliminate the need for subsidies.", "Renewable energy advocates demand that all market subsidies be abolished immediately.", "Market competition has been distorted by the rapid rise of subsidized renewable energy."], "correct_answer": "Those in favor of green energy claim that financial support for fossil fuels creates an unfair market.", "exp_translation": "תומכי האנרגיה המתחדשת טוענים שסובסידיות לדלקי מאובנים מעוותות את התחרות בשוק.", "exp_correct": "Proponents = Those in favor of | subsidies = financial support | distort market competition = creates an unfair market.", "exp_wrong": "שאר האפשרויות הופכות את המשמעות או מוסיפות דרישות קיצוניות שלא נאמרו (כמו ביטול כל הסובסידיות)."},
        {"passage": "", "question": "Not until the late nineteenth century did surgical procedures become relatively safe due to sterilization techniques.", "options": ["Surgical procedures only became reasonably safe in the late 1800s as a result of sterilization methods.", "Sterilization techniques were not invented until surgical procedures became common in the late 1800s.", "Prior to the late nineteenth century, sterilization techniques made surgery completely safe.", "Even with sterilization methods, surgery remained perilous throughout the late nineteenth century."], "correct_answer": "Surgical procedures only became reasonably safe in the late 1800s as a result of sterilization methods.", "exp_translation": "רק בשלהי המאה ה-19 הפכו הליכים כירורגיים לבטוחים יחסית הודות לטכניקות עיקור.", "exp_correct": "המבנה Not until X did Y happen שווה ערך ל-Y only happened at X.", "exp_wrong": "המסיחים האחרים הופכים סיבה ותוצאה או סותרים את העובדה שהניתוחים אכן הפכו לבטוחים בסוף המאה ה-19."},
        {"passage": "", "question": "The archaeological site yielded artifacts that were no less sophisticated than those found in the capital.", "options": ["The items discovered at the site were just as advanced as the ones from the capital.", "Fewer sophisticated artifacts were found at the archaeological site than in the capital.", "The capital's artifacts were far superior to those uncovered at the archaeological site.", "Neither the site nor the capital contained artifacts of any notable sophistication."], "correct_answer": "The items discovered at the site were just as advanced as the ones from the capital.", "exp_translation": "אתר החפירות הניב ממצאים שלא היו פחות מתוחכמים מאלה שנמצאו בעיר הבירה.", "exp_correct": "הביטוי no less X than Y משמעותו 'באותה מידה של X כמו Y' (just as advanced as).", "exp_wrong": "שאר המסיחים קובעים נחיתות, עליונות או היעדר תחכום מוחלט."},
        {"passage": "", "question": "Had the central bank intervened earlier, the currency depreciation might have been averted.", "options": ["The currency lost value, perhaps because the central bank failed to act in time.", "The central bank intervened early enough to prevent the currency from losing value.", "Regardless of when the central bank acted, the currency depreciation was inevitable.", "Early intervention by the central bank caused the currency to depreciate rapidly."], "correct_answer": "The currency lost value, perhaps because the central bank failed to act in time.", "exp_translation": "אילו הבנק המרכזי היה מתערב מוקדם יותר, ייתכן שפיחות המטבע היה נמנע.", "exp_correct": "משפט תנאי בטל (Conditional Type 3 - Had X happened, Y might have happened) מתאר מצב הפוך למציאות: הבנק לא התערב בזמן, והמטבע אכן איבד מערכו.", "exp_wrong": "מסיחים שטוענים שהפיחות נמנע או שהיה בלתי נמנע לחלוטין סותרים את ה-might have been averted."},
        {"passage": "", "question": "Much as the critic admired the director's visual style, he found the film's narrative disjointed.", "options": ["Although the critic praised the look of the movie, he thought its plot lacked coherence.", "The critic disliked the film's erratic plot just as much as its visual style.", "Because the director focused heavily on visuals, the critic admired the complex narrative.", "The film's coherent narrative compensated for what the critic saw as a weak visual style."], "correct_answer": "Although the critic praised the look of the movie, he thought its plot lacked coherence.", "exp_translation": "עד כמה שהמבקר העריץ את הסגנון הוויזואלי של הבמאי, הוא מצא את עלילת הסרט מקוטעת.", "exp_correct": "Much as בראש משפט משמש כמילת ויתור (למרות ש- / Although). disjointed = lacked coherence.", "exp_wrong": "המסיחים האחרים מפרשים את Much as כהשוואת כמות שגויה או כסיבה ותוצאה."},
        {"passage": "", "question": "Seldom does a scientific paradigm shift occur without considerable resistance from the established community.", "options": ["Established scientists almost always oppose major changes to prevailing scientific theories.", "Scientific paradigms change frequently despite opposition from established researchers.", "The scientific community readily embraces new paradigms whenever evidence is presented.", "Resistance from established scientists prevents any paradigm shifts from ever occurring."], "correct_answer": "Established scientists almost always oppose major changes to prevailing scientific theories.", "exp_translation": "לעיתים נדירות מתרחש שינוי פרדיגמה מדעי ללא התנגדות ניכרת מצד הקהילה המבוססת.", "exp_correct": "Seldom... without (לעיתים נדירות... בלי) היא שלילה כפולה שמשמעותה 'כמעט תמיד עם' (almost always oppose).", "exp_wrong": "המסיח הרביעי קיצוני מדי (prevents... from ever occurring), בעוד המקור אומר שזה קורה לעיתים נדירות בלי התנגדות."},
        {"passage": "", "question": "For all his wealth, the industrialist lived a remarkably austere life.", "options": ["Despite being very rich, the industrialist maintained a simple and modest lifestyle.", "The industrialist used all of his fortune to fund a strictly disciplined lifestyle.", "Because he was wealthy, the industrialist could afford an extravagant way of life.", "Everyone knew about the industrialist's wealth, yet few knew about his private life."], "correct_answer": "Despite being very rich, the industrialist maintained a simple and modest lifestyle.", "exp_translation": "למרות כל עושרו, התעשיין חי חיים סגפניים/צנועים באופן יוצא דופן.", "exp_correct": "הביטוי For all X משמעותו 'למרות X' (Despite). המילה austere פירושה צנוע/סגפני (simple and modest).", "exp_wrong": "המסיחים האחרים מתרגמים מילולית את For all כ'עבור כל' או מחליפים את משמעות המילה austere."},
        {"passage": "", "question": "The committee decided to defer the vote lest hasty legislation lead to unintended consequences.", "options": ["To avoid unexpected outcomes from a rushed law, the committee postponed the vote.", "The committee voted quickly so that the legislation would not be delayed any further.", "Unintended consequences forced the committee to cancel the legislation after the vote.", "Although the legislation was rushed, the committee decided to proceed with the vote."], "correct_answer": "To avoid unexpected outcomes from a rushed law, the committee postponed the vote.", "exp_translation": "הוועדה החליטה לדחות את ההצבעה פן חקיקה נמהרת תוביל להשלכות לא מכוונות.", "exp_correct": "defer = postponed (לדחות) | lest = פן / כדי שלא (To avoid) | hasty = rushed (נמהר).", "exp_wrong": "שאר האפשרויות משנות את משמעות הפועל defer או מתעלמות ממילת התכלית השלילית lest."},
        {"passage": "", "question": "Only when the archives were declassified did the true extent of the espionage operation come to light.", "options": ["The full scale of the spying operation remained unknown until the secret records were made public.", "The archives were declassified only because the espionage operation had already been exposed.", "Even after the records were released, very little was revealed about the spying network.", "Declassifying the archives prevented the espionage operation from expanding any further."], "correct_answer": "The full scale of the spying operation remained unknown until the secret records were made public.", "exp_translation": "רק כאשר הארכיונים הותרו לפרסום התגלה ההיקף האמיתי של מבצע הריגול.", "exp_correct": "Only when X did Y = Y לא קרה עד ש-X קרה. declassified = made public | espionage = spying.", "exp_wrong": "המסיח השני הופך את הסיבה והתוצאה, והשלישי סותר את חשיפת ההיקף המלא."}
    ],
    "הבנת הנקרא (קטע קצר)": [
        {"passage": "Recent studies in urban ecology suggest that fragmented green spaces, such as pocket parks and green roofs, play a far more vital role in supportingavian biodiversity than previously assumed. While vast nature reserves remain indispensable for apex predators, smaller urban patches act as critical stepping stones for migratory songbirds. Consequently, municipal planners are increasingly shifting their focus from single mega-parks to interconnected networks of micro-habitats.", "question": "According to the passage, why are municipal planners changing their approach to urban green spaces?", "options": ["Because connected small green areas effectively support migrating bird populations.", "Because large nature reserves are no longer necessary for protecting apex predators.", "Because pocket parks are significantly cheaper to maintain than single mega-parks.", "Because migratory songbirds prefer urban buildings over natural habitats."], "correct_answer": "Because connected small green areas effectively support migrating bird populations.", "exp_translation": "מחקרים עדכניים באקולוגיה עירונית מצביעים על כך ששטחים ירוקים מקוטעים, כגון גינות כיס וגגות ירוקים, ממלאים תפקיד חיוני בהרבה בתמיכה במגוון הביולוגי של עופות מכפי שהניחו בעבר...", "exp_correct": "הקטע מציין ששטחיים קטנים משמשים כ'אבני מדרך' לציפורי שיר נודדות, ולכן (Consequently) מתכנני ערים עוברים לרשתות של מיקרו-בתי גידול.", "exp_wrong": "הקטע מדגיש ששמורות גדולות עדיין הכרחיות לטורפי-על (פוסל ב'), ולא מזכיר עלויות כלכליות (פוסל ג')."},
        {"passage": "The phenomenon of 'choice overload' occurs when consumers are presented with an excessive array of options, leading to decision paralysis and reduced satisfaction. In a landmark experiment, shoppers exposed to a display of twenty-four gourmet jams were significantly less likely to make a purchase than those shown only six varieties. Paradoxically, while extensive selection initially attracts more browsers, it ultimately inhibits the act of buying.", "question": "What is the 'paradox' referred to in the final sentence of the passage?", "options": ["Having more options draws people in, yet makes them less likely to actually buy anything.", "Consumers claim to prefer fewer choices, but consistently purchase from larger displays.", "Gourmet products attract many browsers, even though most shoppers prefer standard brands.", "Decision paralysis affects shoppers only when they are buying inexpensive food items."], "correct_answer": "Having more options draws people in, yet makes them less likely to actually buy anything.", "exp_translation": "תופעת 'עומס הבחירה' מתרחשת כאשר מוצג לצרכנים מגוון מופרז של אפשרויות, מה שמוביל לשיתוק קבלת החלטות...", "exp_correct": "המשפט האחרון מציין במפורש: אף שמבחר רחב מושך יותר מתעניינים בהתחלה (attracts more browsers), הוא בסופו של דבר בולם את הרכישה (inhibits buying).", "exp_wrong": "שאר התשובות ממציאות עובדות על מחירים או מותגים שלא מופיעות בטקסט."},
        {"passage": "For decades, neuroscientists held that the adult human brain was essentiallyimmutable, incapable of generating new neurons after childhood. However, the discovery of adult neurogenesis in the hippocampus overturned this dogma, demonstrating that neural pathways continuously reorganize in response to learning and environmental stimuli. Nevertheless, the rate of cellular regeneration declines markedly with age.", "question": "Which of the following can be inferred from the passage about the older view of the adult brain?", "options": ["It underestimated the adult brain's capacity to adapt and form new cells.", "It accurately predicted the rate of neural decline in the hippocampus.", "It was based primarily on studies of environmental stimuli in children.", "It remains the prevailing consensus among modern neuroscientists."], "correct_answer": "It underestimated the adult brain's capacity to adapt and form new cells.", "exp_translation": "במשך עשורים סברו חוקרי מוח שהמוח האנושי הבוגר הוא למעשה בלתי ניתן לשינוי (immutable)...", "exp_correct": "התפיסה הישנה טענה שהמוח הבוגר אינו מסוגל לייצר נוירונים חדשים, אך גילוי הנוירוגנזה הפריך דוגמה זו (overturned this dogma).", "exp_wrong": "התפיסה הישנה הופרכה ולכן אינה הקונצנזוס כיום (פוסל ד')."},
        {"passage": "Although the printing press is universally credited with democratizing knowledge in fifteenth-century Europe, its immediate impact was heavily contingent on local literacy rates and paper availability. In regions where parchment remained the primary medium, book production costs stayed prohibitive for decades after Gutenberg's invention. Thus, technological innovation alone was insufficient to trigger an instant cultural revolution.", "question": "The main purpose of the passage is to:", "options": ["Qualify a common claim about the immediate effects of the printing press.", "Argue that parchment was superior to paper in fifteenth-century book production.", "Demonstrate that Gutenberg's invention had no real impact on European literacy.", "Explain the mechanical process by which the printing press reduced costs."], "correct_answer": "Qualify a common claim about the immediate effects of the printing press.", "exp_translation": "למרות שמכבש הדפוס זוכה לקרדיט אוניברסיטאי על הנגשת הידע באירופה של המאה ה-15, השפעתו המיידית הייתה תלויה מאוד באוריינות מקומית וזמינות נייר...", "exp_correct": "הפועל To qualify בהבנת הנקרא משמעותו 'לסייג/למתן טענה'. הקטע מסייג את ההנחה שהדפוס חולל מהפכה מיידית בכל מקום.", "exp_wrong": "הקטע לא טוען שלדפוס לא הייתה השפעה כלל (פוסל ג'), אלא רק שהיא לא הייתה מיידית בכל אזור."},
        {"passage": "Bioluminescence in deep-sea organisms serves a multitude of evolutionary functions beyond mere predation. While the anglerfish famously uses a glowing lure to attract prey, many mesopelagic squid emit light from their ventral surfaces to match the faint downwelling sunlight—a camouflage technique known as counter-illumination. This adaptation effectively erases their silhouette from predators lurking below.", "question": "How does 'counter-illumination' protect mesopelagic squid?", "options": ["By blending their underside with the light coming from above to hide from predators underneath.", "By blinding deep-sea predators with a sudden flash of bright light.", "By mimicking the glowing lure of the anglerfish to scare away larger fish.", "By illuminating dark ocean depths so the squid can spot approaching threats."], "correct_answer": "By blending their underside with the light coming from above to hide from predators underneath.", "exp_translation": "נהורנות ביולוגית (ביו-לומינסנציה) ביצורי מעמקים משרתת שלל פונקציות אבולוציוניות מעבר לטריפה גרידא...", "exp_correct": "הקטע מסביר שהדיונונים פולטים אור מחלקם התחתון (ventral) כדי להשתלב באור השמש העמום מלמעלה וכך להעלים את הצללית שלהם מטורפים שאורבים למטה.", "exp_wrong": "הקטע לא מדבר על סנוור טורפים או חיקוי של חכאים (anglerfish)."}
    ],
    "אוצר מילים ואסוציאציות": [
        {"passage": "", "question": "MITIGATE", "options": ["למתן / להקל", "להחמיר / להסלים", "לחקור לעומק", "לשלול מכל וכל"], "correct_answer": "למתן / להקל", "exp_translation": "Mitigate = למתן, להפחית חומרה של מצב שלילי.", "exp_correct": "💡 אסוציאציה: נשמע כמו 'מיטה גייט' – אחרי יום קשוח, ברגע שעוברים את השער (Gate) ונכנסים למיטה, זה מיד ממתן ומקל על העייפות. דוגמה: Soil erosion was mitigated by planting trees.", "exp_wrong": "להחמיר = Aggravate / Exacerbate | לחקור = Investigate | לשלול = Negate."},
        {"passage": "", "question": "UBIQUITOUS", "options": ["נמצא בכל מקום / נפוץ מאוד", "נדיר / ייחודי", "דו-משמעי / מעורפל", "מיושן / עתיק"], "correct_answer": "נמצא בכל מקום / נפוץ מאוד", "exp_translation": "Ubiquitous = נמצא בכל מקום, רווח ביותר.", "exp_correct": "💡 אסוציאציה: מתחיל כמו 'אוביקט' (Object) – סמארטפונים הם אובייקט שנמצא היום בכל מקום בעולם. דוגמה: Coffee shops have become ubiquitous in modern cities.", "exp_wrong": "נדיר = Scarce / Rare | דו-משמעי = Ambiguous | מיושן = Obsolete."},
        {"passage": "", "question": "EPHEMERAL", "options": ["חולף / קצר מועד", "נצחי / קבוע", "מהותי / קריטי", "מזויף / מלאכותי"], "correct_answer": "חולף / קצר מועד", "exp_translation": "Ephemeral = בן-חלוף, מחזיק מעמד זמן קצר מאוד.", "exp_correct": "💡 אסוציאציה: נשמע כמו 'אפר' (אפר ומל) – משהו שנשרף והופך לאפר תוך שניות, זמני וחולף. דוגמה: Fame in the age of social media is often ephemeral.", "exp_wrong": "נצחי = Perpetual / Eternal | מהותי = Intrinsic | מזויף = Spurious."},
        {"passage": "", "question": "PRAGMATIC", "options": ["מעשי / תכליתי", "תיאורטי / מופשט", "קפדני / נוקשה", "נדיב / פילנתרופי"], "correct_answer": "מעשי / תכליתי", "exp_translation": "Pragmatic = מעשי, פרגמטי, מתמקד בתוצאות בשטח ולא בתיאוריות.", "exp_correct": "💡 אסוציאציה: 'פרגמטי' קיים גם בעברית – גישה פרקטית עם רגליים על הקרקע. דוגמה: We need a pragmatic approach to solve the traffic crisis.", "exp_wrong": "תיאורטי = Abstract | קפדני = Stringent | נדיב = Benevolent."},
        {"passage": "", "question": "AMBIGUOUS", "options": ["דו-משמעי / לא ברור", "שאפתני מאוד", "מוחלט / ודאי", "שנוי במחלוקת"], "correct_answer": "דו-משמעי / לא ברור", "exp_translation": "Ambiguous = דו-משמעי, מעורפל, ניתן לפירוש ביותר מדרך אחת.", "exp_correct": "💡 אסוציאציה: הקידומת Ambi פירושה 'שניים/דו' (כמו אמפיבי - חי גם בים וגם ביבשה). לכן Ambiguous = בעל שתי משמעויות. היזהר לא לבלבל עם Ambitious (שאפתן)!", "exp_wrong": "שאפתני = Ambitious (מלכודת קלאסית במבחן!) | מוחלט = Unequivocal | שנוי במחלוקת = Contentious."}
    ],
    "אלימינציה עיוורת (דקדוק והקשר)": [
        {"passage": "", "question": "Despite the witness's _____ testimony, the jury found enough corroborating evidence to convict the defendant.", "options": ["mendacious", "enthusiastically", "corroboration", "vindicated"], "correct_answer": "mendacious", "exp_translation": "למרות עדותו השקרית של העד, חבר המושבעים מצא מספיק ראיות תומכות כדי להרשיע את הנאשם.", "exp_correct": "🕵️‍♂️ טכניקת פסילה: לפני שם העצם testimony (עדות) חייב לבוא שם תואר (Adjective). אופציה ב' היא תואר הפועל (-ly), אופציה ג' היא שם עצם (-tion), ואופציה ד' היא פועל בעבר. סיומת -ious היא סיומת מובהקת של שם תואר בעל קונוטציה שלילית שמתאימה ל-Despite!", "exp_wrong": "אין צורך להכיר את המילה הקשה mendacious (שקרי) – פוסלים את שלוש האחרות על בסיס חלקי דיבר (Grammar) תוך 5 שניות."},
        {"passage": "", "question": "The new prime minister sought to _____ the polarized factions within the parliament before passing the budget.", "options": ["propitiate", "divisiveness", "reluctantly", "antagonistic"], "correct_answer": "propitiate", "exp_translation": "ראש הממשלה החדש ביקש לפייס את הסיעות המקוטבות בפרלמנט לפני העברת התקציב.", "exp_correct": "🕵️‍♂️ טכניקת פסילה: אחרי המבנה sought to חייב להופיע פועל בצורת המקור (V1). סיומת -ate (propitiate) היא היחידה שמייצגת פועל!", "exp_wrong": "divisiveness = שם עצם (-ness) | reluctantly = תואר הפועל (-ly) | antagonistic = שם תואר (-ic)."},
        {"passage": "", "question": "Rather than acting as a _____ to economic growth, strict environmental standards often spur technological innovation.", "options": ["impediment", "obstructed", "detrimentally", "stagnant"], "correct_answer": "impediment", "exp_translation": "במקום לשמש כמכשול לצמיחה כלכלית, תקנים סביבתיים מחמירים לרוב מדרבנים חדשנות טכנולוגית.", "exp_correct": "🕵️‍♂️ טכניקת פסילה: אחרי הקידומת 'acting as a ___' חייב לבוא שם עצם יחיד (Noun). סיומת -ment (impediment) היא סיומת קלאסית של שם עצם.", "exp_wrong": "obstructed = פועל | detrimentally = תואר הפועל | stagnant = שם תואר."},
        {"passage": "", "question": "The laboratory technician handled the volatile compound _____, knowing that even a minor vibration could trigger an explosion.", "options": ["gingerly", "precaution", "hazardous", "stabilize"], "correct_answer": "gingerly", "exp_translation": "טכנאי המעבדה טיפלבתרכובת הנפיצה בזהירות רבה, בידיעה שאפילו רטט קל עלול לחולל פיצוץ.", "exp_correct": "🕵️‍♂️ טכניקת פסילה: המשפט(The technician handled the compound) שלם תחבירית. המילה החסרה מתארת *כיצד* הוא טיפל בה, ולכן חסר תואר הפועל (Adverb) שמסתיים ב-ly.", "exp_wrong": "precaution = שם עצם | hazardous = שם תואר | stabilize = פועל."},
        {"passage": "", "question": "Because the treaty's clauses were phrased so _____, both nations interpreted the border agreement in their own favor.", "options": ["nebulously", "ambiguity", "obscured", "vague"], "correct_answer": "nebulously", "exp_translation": "מכיוון שסעיפי האמנה נוסחו באופן כה מעורפל, שתי המדינות פירשו את הסכם הגבול לטובתן.", "exp_correct": "🕵️‍♂️ טכניקת פסילה: המילה החסרה מתארת את הפועל הסביל were phrased (נוסחו). מי שמתאר פועל הוא תואר הפועל (Adverb) המסתיים ב-ly (nebulously).", "exp_wrong": "vague הוא שם תואר (ולכן דקדוקית שגוי כאן אחרי פועל פעולה כמו phrased), ambiguity הוא שם עצם."}
    ],
    "פירוק מורפולוגי (תחיליות וסופיות)": [
        {"passage": "", "question": "What is the meaning of the word 'CIRCUMVENT'?", "options": ["לעקוף / להתחמק (ממכשול או חוק)", "לכנס יחד למרכז", "לחתוך לשני חלקים שווים", "להכריז מראש ברבים"], "correct_answer": "לעקוף / להתחמק (ממכשול או חוק)", "exp_translation": "Circumvent = לעקוף חוק, מגבלה או מכשול בדרך מתוחכמת.", "exp_correct": "🔬 פירוק מורפולוגי: **Circum** = מסביב (כמו Circle או Circumference - היקף מעגל) + **Vent** = לבוא/ללכת. ביחד: 'ללכת מסביב' למכשול, כלומר לעקוף אותו!", "exp_wrong": "כשמכירים את הקידומת Circum (מסביב), קל לפסול תשובות שמדברות על חיתוך (Bi/Sect) או התכנסות פנימה."},
        {"passage": "", "question": "What is the meaning of the word 'COUNTERPRODUCTIVE'?", "options": ["משיג את התוצאה ההפוכה / מזיק למטרה", "יצרני ויעיל פי שניים", "מיוצר באופן המוני במפעל", "חסר כל השפעה על הסביבה"], "correct_answer": "משיג את התוצאה ההפוכה / מזיק למטרה", "exp_translation": "Counterproductive = משיג תוצאה הפוכה מהרצוי.", "exp_correct": "🔬 פירוק מורפולוגי: **Counter** = נגד / הפוך + **Produce** = לייצר + **ive** = סיומת תואר. ביחד: פועל נגד התוצאה שרצינו לייצר.", "exp_wrong": "הקידומת Counter תמיד מסמנת ניגוד או פעולת נגד (כמו Counterattack - מתקפת נגד)."},
        {"passage": "", "question": "What is the meaning of the word 'MALEVOLENT'?", "options": ["מרושע / שואף להזיק", "נדיב ובעל רצון טוב", "חלש וחסר אונים", "בלתי צפוי לחלוטין"], "correct_answer": "מרושע / שואף להזיק", "exp_translation": "Malevolent = מרושע, זדוני, מאחל רע לאחרים.", "exp_correct": "🔬 פירוק מורפולוגי: **Mal** = רע/שלילי (כמו Malfunction - תקלה, Malnutrition - תת-תזונה) + **Vol** = רצון (Voluntary). ביחד: בעל רצון רע להזיק! (ההפך המוחלט מ-Benevolent = טוב לב).", "exp_wrong": "כל מילה באמירנ\"ט שמתחילה ב-Mal נושאת קונוטציה שלילית מובהקת."},
        {"passage": "", "question": "What is the meaning of the word 'INEVITABLE'?", "options": ["בלתי נמנע / שבוודאות יקרה", "בלתי נראה לעין", "ניתן למניעה בקלות", "חסר ערך ממשי"], "correct_answer": "בלתי נמנע / שבוודאות יקרה", "exp_translation": "Inevitable = בלתי נמנע.", "exp_correct": "🔬 פירוק מורפולוגי: **In** = לא (שלילה) + **Evit** (מאותו שורש לטיני של Avoid - להימנע) + **able** = ניתן ל-. ביחד: שלא ניתן להימנע ממנו!", "exp_wrong": "הקידומת In הופכת את השורש לשלילי, והסיומת able מציינת יכולת/אפשרות."},
        {"passage": "", "question": "What is the meaning of the word 'ANACHRONISM'?", "options": ["דבר שאינו שייך לתקופתו הכרונולוגית", "שלטון ללא חוק או סדר", "פחד קיצוני ממקומות סגורים", "מכשיר למדידת עוצמת הקול"], "correct_answer": "דבר שאינו שייך לתקופתו הכרונולוגית", "exp_translation": "Anachronism = אנכרוניזם, דבר המיוחס לתקופה שאינה מתאימה לו (למשל שעון יד בסרט על ימי הביניים) או דבר מיושן מאוד.", "exp_correct": "🔬 פירוק מורפולוגי: **Ana** = נגד/אחורה + **Chron** = זמן (כמו Chronological או Synchronize) + **ism** = תופעה. ביחד: חריגה מציר הזמן!", "exp_wrong": "שלטון ללא סדר הוא Anarchy (שורש Arch = שלטון). זיהוי השורש Chron מוביל מיד לתשובה שקשורה לזמן."}
    ]
}

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

def get_user_mistakes(username, limit=8):
    c = conn.cursor()
    c.execute("SELECT question, correct_answer, translation FROM mistakes WHERE username=? ORDER BY RANDOM() LIMIT ?", (username, limit))
    return c.fetchall()

def count_user_mistakes(username):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM mistakes WHERE username=?", (username,))
    return c.fetchone()[0]

# --- הגדרת מודל AI חסינת קריסות ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

PROMPTS = {
    "השלמת משפטים": "Question type: Sentence Completion. C1/C2 academic vocabulary.",
    "ניסוח מחדש": "Question type: Restatements. Complex logical structures and inversions.",
    "הבנת הנקרא (קטע קצר)": "Question type: Reading Comprehension. Include a 3-sentence academic paragraph in 'passage'.",
    "אוצר מילים ואסוציאציות": "Question type: Vocabulary Practice. English word in 'question', 4 Hebrew translations in 'options'. Include a Hebrew mnemonic in 'exp_correct'.",
    "אלימינציה עיוורת (דקדוק והקשר)": "Question type: Grammar & Context Elimination. Sentence completion where 3 options can be eliminated via parts of speech (noun/verb/adv/adj).",
    "פירוק מורפולוגי (תחיליות וסופיות)": "Question type: Morphological Breakdown. Complex word with prefix/root/suffix breakdown in 'exp_correct'.",
    "מיקוד בטעויות עבר": "Create new high-level Sentence Completion questions testing these exact concepts/words: {mistakes_list}."
}

def generate_ai_questions(q_type, num_questions=5, custom_context=""):
    prompt_instruction = PROMPTS.get(q_type, PROMPTS["השלמת משפטים"])
    if custom_context:
        prompt_instruction = prompt_instruction.replace("{mistakes_list}", custom_context)
        
    prompt = f"""
    Create {num_questions} unique, high-level questions for the Israeli AMIRNET English exam.
    {prompt_instruction}
    Return ONLY a valid JSON array of objects with these exact keys:
    [
        {{
            "passage": "Academic paragraph ONLY if Reading Comprehension, else empty string",
            "question": "The English sentence, word, or question",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Exact match to one of the 4 options",
            "exp_translation": "תרגום מדויק לעברית",
            "exp_correct": "הסבר חד בעברית למה התשובה נכונה",
            "exp_wrong": "פירוט תמציתי בעברית למה המסיחים האחרים שגויים"
        }}
    ]
    """
    # שימוש במצב JSON מובנה ובמנגנון Fallback בין מודלים למניעת תקלות שרת
    for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']:
        try:
            m = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
            response = m.generate_content(prompt)
            data = json.loads(response.text.strip())
            if isinstance(data, list) and len(data) > 0:
                return data
        except Exception:
            continue
    return []

def fetch_ai_in_background(q_type, target_list, num_questions=5, custom_context=""):
    new_qs = generate_ai_questions(q_type, num_questions, custom_context=custom_context)
    if new_qs:
        target_list.extend(new_qs)

# --- אתחול Session State ---
defaults = {
    'current_user': None,
    'question_bank': [],
    'ai_buffer': [],
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
# 1. מסך כניסת משתמש
# ==========================================
if not st.session_state.current_user:
    st.markdown("""
        <div class='login-wrapper fade-in'>
            <div style='font-size: 38px; margin-bottom: 8px;'>🎓</div>
            <div style='font-size: 26px; font-weight: 800; color: #0f172a; margin-bottom: 6px;'>Amirnet Executive</div>
            <div style='font-size: 15px; color: #64748b; margin-bottom: 20px;'>מערכת הכנה היברידית ברמת פטור אקדמי</div>
        </div>
    """, unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 1.8, 1])
    with col_m:
        username_input = st.text_input("שם משתמש:", placeholder="הזן את שמך לשמירת מעקב אישי...")
        if st.button("כניסה למערכת", use_container_width=True):
            if username_input.strip():
                st.session_state.current_user = username_input.strip()
                st.rerun()
            else:
                st.error("יש להזין שם משתמש.")
    st.stop()

mistakes_count = count_user_mistakes(st.session_state.current_user)

# ==========================================
# 2. סרגל ניווט עליון (Header Bar)
# ==========================================
nav_c1, nav_c2 = st.columns([3.5, 1])
with nav_c1:
    st.markdown(f"""
        <div class='top-nav'>
            <div class='nav-user'>{st.session_state.current_user} • סביבת אימון אישית</div>
            <div class='nav-badge'>מאגר מילים לשיפור: {mistakes_count}</div>
        </div>
    """, unsafe_allow_html=True)
with nav_c2:
    if st.session_state.question_bank:
        if st.button("חזרה לתפריט הראשי", key="exit_top_btn", use_container_width=True):
            st.session_state.question_bank = []
            st.session_state.ai_buffer = []
            st.session_state.is_fetching = False
            st.rerun()
    else:
        if st.button("החלף משתמש", key="exit_top_btn", use_container_width=True):
            st.session_state.current_user = None
            st.rerun()

# ==========================================
# 3. דשבורד ראשי (טעינה מיידית 0.0 שניות + הזרמת AI ברקע)
# ==========================================
if not st.session_state.question_bank:
    st.markdown("<div class='hero-title fade-in'>בחר מסלול תרגול</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-subtitle fade-in'>התרגול נפתח באופן מיידי ממאגר הליבה ובמקביל מזרים שאלות AI חדשות ברקע</div>", unsafe_allow_html=True)
    
    selected_mode = None
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("השלמת משפטים (Sentence Completion)", key="mode_sc", use_container_width=True):
            selected_mode = "השלמת משפטים"
        if st.button("הבנת הנקרא (Reading Comprehension)", key="mode_rc", use_container_width=True):
            selected_mode = "הבנת הנקרא (קטע קצר)"
        if st.button("אלימינציה עיוורת (טכניקות פסילה ודקדוק)", key="mode_elim", use_container_width=True):
            selected_mode = "אלימינציה עיוורת (דקדוק והקשר)"
            
    with c2:
        if st.button("ניסוח מחדש (Restatements)", key="mode_rest", use_container_width=True):
            selected_mode = "ניסוח מחדש"
        if st.button("אוצר מילים ואסוציאציות (Vocabulary)", key="mode_voc", use_container_width=True):
            selected_mode = "אוצר מילים ואסוציאציות"
        if st.button("פירוק מורפולוגי (תחיליות, שורשים וסופיות)", key="mode_morph", use_container_width=True):
            selected_mode = "פירוק מורפולוגי (תחיליות וסופיות)"

    st.write("")
    c3, c4 = st.columns(2)
    with c3:
        if st.button(f"תרגול ממוקד בטעויות עבר ({mistakes_count})", key="mode_mistakes", use_container_width=True):
            if mistakes_count < 1:
                st.warning("עדיין אין טעויות שמורות במאגר שלך. התחל לתרגל וכל טעות תישמר כאן אוטומטית!")
            else:
                selected_mode = "מיקוד בטעויות עבר"
    with c4:
        if st.button("סימולציית בחינה (20 שאלות • עם טיימר)", key="mode_sim", use_container_width=True):
            selected_mode = "סימולציה מלאה"

    if selected_mode:
        st.session_state.exam_mode = "סימולציה" in selected_mode
        st.session_state.current_mode = selected_mode
        
        # 1. טעינה מיידית (0 שניות המתנה!) מתוך המאגר המקומי
        if st.session_state.exam_mode:
            all_local = (INSTANT_BANK["השלמת משפטים"] + INSTANT_BANK["ניסוח מחדש"] + INSTANT_BANK["הבנת הנקרא (קטע קצר)"]).copy()
            random.shuffle(all_local)
            initial_qs = all_local[:20]
        elif selected_mode == "מיקוד בטעויות עבר":
            # מתרגל מיד על בסיס שאלות ליבה בזמן שה-AI בונה שאלות חדשות על הטעויות
            initial_qs = random.sample(INSTANT_BANK["השלמת משפטים"], 5)
        else:
            initial_qs = INSTANT_BANK.get(selected_mode, INSTANT_BANK["השלמת משפטים"]).copy()
            random.shuffle(initial_qs)

        # ערבוב סדר התשובות בכל שאלה כדי שלא יהיה קבוע
        for q_item in initial_qs:
            opts = q_item["options"].copy()
            random.shuffle(opts)
            q_item["options"] = opts

        st.session_state.question_bank = initial_qs
        st.session_state.current_index = 0
        st.session_state.answered = False
        st.session_state.user_choice = None
        st.session_state.correct_count = 0
        st.session_state.start_time = time.time()
        st.session_state.ai_buffer = []
        
        # 2. שליחת פקודה מיידית ל-API ברקע לייצר שאלות חדשות ולהחליף/להוסיף אותן ברגע שמוכן!
        st.session_state.is_fetching = True
        custom_ctx = ""
        fetch_cat = "השלמת משפטים" if st.session_state.exam_mode else selected_mode
        if selected_mode == "מיקוד בטעויות עבר":
            mistakes_data = get_user_mistakes(st.session_state.current_user)
            custom_ctx = ", ".join([row[1] for row in mistakes_data])
            
        threading.Thread(
            target=fetch_ai_in_background,
            args=(fetch_cat, st.session_state.ai_buffer, 6, custom_ctx),
            daemon=True
        ).start()
        
        st.rerun()

# ==========================================
# 4. מסך תרגול פעיל (Active Practice)
# ==========================================
if st.session_state.question_bank:
    # אם ה-AI סיים לייצר שאלות חדשות ברקע - מזריקים אותן מיד להמשך הרצף!
    if st.session_state.ai_buffer:
        new_ai_qs = st.session_state.ai_buffer.copy()
        st.session_state.ai_buffer.clear()
        st.session_state.is_fetching = False
        # מחליף את השאלות העתידיות במחסנית בשאלות ה-AI הטריות ומוסיף אותן לרצף
        curr_i = st.session_state.current_index
        st.session_state.question_bank = st.session_state.question_bank[:curr_i + 2] + new_ai_qs

    total = len(st.session_state.question_bank)
    idx = st.session_state.current_index
    q = st.session_state.question_bank[idx]
    
    # אם מתקרבים לסוף המקבץ הנוכחי - מזמין עוד מנה מה-AI ברקע
    if not st.session_state.exam_mode and (total - idx <= 4) and not st.session_state.is_fetching:
        st.session_state.is_fetching = True
        threading.Thread(
            target=fetch_ai_in_background,
            args=(st.session_state.current_mode, st.session_state.ai_buffer, 5, ""),
            daemon=True
        ).start()

    # שורת סטטוס עליונה נקייה
    top_info_c1, top_info_c2 = st.columns([3, 1])
    with top_info_c1:
        ai_status = "⚡ מחובר למנוע AI חי" if not st.session_state.is_fetching else "🔄 מנוע AI מכין שאלות חדשות ברקע..."
        st.markdown(f"<span class='ai-status-badge'>{st.session_state.current_mode} • שאלה {idx + 1} מתוך {total} &nbsp;|&nbsp; {ai_status}</span>", unsafe_allow_html=True)
    with top_info_c2:
        if st.session_state.exam_mode:
            elapsed = int(time.time() - st.session_state.start_time)
            mins, secs = divmod(elapsed, 60)
            st.markdown(f"<div style='text-align: left; color: #dc2626; font-weight: 700; font-size: 16px;'>⏱️ {mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

    st.progress((idx + 1) / total)

    # קטע קריאה (אם קיים)
    if q.get('passage') and len(q['passage'].strip()) > 5:
        st.markdown(f"<div class='passage-box fade-in'>{q['passage']}</div>", unsafe_allow_html=True)
        
    # כרטיסיית השאלה
    st.markdown(f"<div class='question-box fade-in'>{q['question']}</div>", unsafe_allow_html=True)
    
    # הצגת האפשרויות
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
                st.markdown(f"<div class='ans-correct fade-in'>✓ &nbsp; {opt}</div>", unsafe_allow_html=True)
            elif opt == st.session_state.user_choice:
                st.markdown(f"<div class='ans-wrong fade-in'>✕ &nbsp; {opt}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='ans-neutral'>{opt}</div>", unsafe_allow_html=True)

    # הסבר מפורט ומובנה לאחר בחירת תשובה
    if st.session_state.answered:
        if not st.session_state.exam_mode:
            st.markdown(f"""
            <div class='explanation-container fade-in'>
                <div class='exp-block'>
                    <div class='exp-label'>תרגום לעברית:</div>
                    <div class='exp-body'>{q.get('exp_translation', '')}</div>
                </div>
                <div class='exp-block'>
                    <div class='exp-label'>הסבר התשובה הנכונה:</div>
                    <div class='exp-body'>{q.get('exp_correct', '')}</div>
                </div>
                <div class='exp-block'>
                    <div class='exp-label'>ניתוח המסיחים השגויים:</div>
                    <div class='exp-body'>{q.get('exp_wrong', '')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        if idx < total - 1:
            if st.button("לשאלה הבאה ←", use_container_width=True):
                st.session_state.current_index += 1
                st.session_state.answered = False
                st.session_state.user_choice = None
                st.rerun()
        else:
            if st.session_state.exam_mode:
                score = int(50 + (st.session_state.correct_count / total) * 100)
                st.markdown(f"""
                    <div class='question-box fade-in' style='text-align: center; direction: rtl;'>
                        <h3 style='color: #0f172a;'>סיום פרק סימולציה</h3>
                        <h1 style='color: #2563eb; font-size: 46px; margin: 10px 0;'>ציון משוער: {score}</h1>
                        <p style='color: #475569; font-size: 16px;'>ענית נכון על {st.session_state.correct_count} מתוך {total} שאלות (סף פטור אוניברסיטאי: 134).</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("חזרה לדשבורד הראשי", use_container_width=True):
                    st.session_state.question_bank = []
                    st.rerun()
            else:
                if st.button("טען מקבץ המשך ↻", use_container_width=True):
                    st.session_state.current_index = 0
                    random.shuffle(st.session_state.question_bank)
                    st.session_state.answered = False
                    st.session_state.user_choice = None
                    st.rerun()
