import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Выжил бы ты на Титанике?", page_icon="🚢", layout="centered")

# Показать ли тестовые кнопки (для отладки)
SHOW_TESTS = False

@st.cache_data
def load_data() -> pd.DataFrame:
    csv_path = Path(__file__).with_name("model.csv")
    if csv_path.exists():
        df = pd.read_csv(csv_path, encoding="utf-8")
    else:
        DATA = [
            ("Дети","0-18",1,0.909), ("Дети","0-18",2,0.900), ("Дети","0-18",3,0.347),
            ("Женщина","18-25",1,1.000), ("Женщина","18-25",2,0.933), ("Женщина","18-25",3,0.500),
            ("Женщина","25-35",1,0.929), ("Женщина","25-35",2,0.923), ("Женщина","25-35",3,0.435),
            ("Женщина","35-45",1,1.000), ("Женщина","35-45",2,0.833), ("Женщина","35-45",3,0.300),
            ("Женщина","45-55",1,0.929), ("Женщина","45-55",2,1.000), ("Женщина","45-55",3,0.000),
            ("Женщина","55+",1,1.000), ("Женщина","55+",2,0.500), ("Женщина","55+",3,0.309),
            ("Мужчина","18-25",1,0.125), ("Мужчина","18-25",2,0.050), ("Мужчина","18-25",3,0.107),
            ("Мужчина","25-35",1,0.550), ("Мужчина","25-35",2,0.083), ("Мужчина","25-35",3,0.207),
            ("Мужчина","35-45",1,0.522), ("Мужчина","35-45",2,0.063), ("Мужчина","35-45",3,0.056),
            ("Мужчина","45-55",1,0.346), ("Мужчина","45-55",2,0.000), ("Мужчина","45-55",3,0.091),
            ("Мужчина","55+",1,0.150), ("Мужчина","55+",2,0.167), ("Мужчина","55+",3,0.000),
        ]
        df = pd.DataFrame(DATA, columns=["Cohort","AgeBand","Class","SurvivalCoef"])
    df["Class"] = df["Class"].astype(int)
    df["SurvivalCoef"] = df["SurvivalCoef"].astype(float)
    return df

df = load_data()

def age_band(age: float) -> str:
    # Границы включительно: 0–18, 18–25, 25–35, 35–45, 45–55, 55+
    if age <= 18: return "0-18"
    if age <= 25: return "18-25"
    if age <= 35: return "25-35"
    if age <= 45: return "35-45"
    if age <= 55: return "45-55"
    return "55+"

def cohort(gender: str, age: float) -> str:
    return "Дети" if age <= 18 else gender

def class_by_budget_rub(budget: float) -> str:
    # <100k — специальное сообщение; 100–229999: 3; 230–499999: 2; >=500k: 1
    if budget < 100_000:
        return "Вы бы не смогли купить билет на Титаник"
    if budget < 230_000:
        return "3"
    if budget < 499_000:
        return "2"
    return "1"

# ===== UI =====
st.title("🚢 Выжил бы ты на Титанике?")
st.caption("Пол → возраст → класс по бюджету → коэффициент выживаемости из таблицы.")

with st.sidebar:
    st.header("Ввод")
    gender = st.selectbox("Пол", ["Женщина", "Мужчина"])
    age = st.number_input("Возраст (полных лет)", min_value=0, max_value=110, value=25, step=1)
    budget = st.number_input("Сколько бы вы потратили на билет (в современных рублях)", min_value=0, value=250_000, step=10_000, format="%i")

band = age_band(age)
coh = cohort(gender, age)
klass = class_by_budget_rub(budget)

st.subheader("Результат")
col1, col2, col3 = st.columns(3)

# Если класс — текст про отсутствие билета, показываем метрику коротко и отдельное предупреждение
if klass in {"1", "2", "3"}:
    class_display = klass
    no_ticket_msg = None
else:
    class_display = "—"
    no_ticket_msg = klass

col1.metric("Когорта", coh)
col2.metric("Возрастной диапазон", band)
col3.metric("Класс по бюджету", class_display)

if no_ticket_msg:
    st.warning(no_ticket_msg)

# Поиск коэффициента
coef_text = "N/A"
coef_val = None
if klass in {"1", "2", "3"}:
    row = df[(df["Cohort"] == coh) & (df["AgeBand"] == band) & (df["Class"] == int(klass))]
    if not row.empty:
        coef_val = float(row["SurvivalCoef"].iloc[0])
        coef_text = f"{coef_val*100:.1f}%"
    else:
        coef_text = "нет данных"
elif no_ticket_msg:
    coef_text = "0.0%"  # Нет билета → 0%

st.markdown(f"### Вероятность выживания: **{coef_text}**")
if coef_val is not None:
    st.progress(min(max(coef_val, 0.0), 1.0))

with st.expander("Пояснение"):
    st.write(
        "1) Ввод: пол, возраст и бюджет в рублях.\n"
        "2) Класс по порогам: 3 кл. 100–230 тыс., 2 кл. 230–499 тыс., 1 кл. ≥500 тыс.\n"
        "3) По (когорта, возрастной диапазон, класс) берём коэффициент из `model.csv`.\n"
        "4) Показываем в процентах и прогресс-баре."
    )

# Тестовые кнопки (можно включить флагом)
if SHOW_TESTS:
    st.subheader("Тесты")
    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("Женщина, 22 г., 150k ₽ → 50.0%"):
            st.session_state["gender"] = "Женщина"
            st.session_state["age"] = 22
            st.session_state["budget"] = 150_000
            st.experimental_rerun()
    with colB:
        if st.button("Женщина, 30 л., 250k ₽ → 92.3%"):
            st.session_state["gender"] = "Женщина"
            st.session_state["age"] = 30
            st.session_state["budget"] = 250_000
            st.experimental_rerun()
    with colC:
        if st.button("Мужчина, 28 л., 520k ₽ → 55.0%"):
            st.session_state["gender"] = "Мужчина"
            st.session_state["age"] = 28
            st.session_state["budget"] = 520_000
            st.experimental_rerun()
