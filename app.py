import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Выжил бы ты на Титанике?", page_icon="🚢", layout="centered")

@st.cache_data
def load_data() -> pd.DataFrame:
    csv_path = Path(__file__).with_name("model.csv")
    if csv_path.exists():
        df = pd.read_csv(csv_path, encoding="utf-8")
    else:
        DATA = [
            ("Дети","0-18",1,0.909), ("Дети","0-18",2,0.900), ("Дети","0-18",3,0.347),
            ("Женщины","18-25",1,1.000), ("Женщины","18-25",2,0.933), ("Женщины","18-25",3,0.500),
            ("Женщины","25-35",1,0.929), ("Женщины","25-35",2,0.923), ("Женщины","25-35",3,0.435),
            ("Женщины","35-45",1,1.000), ("Женщины","35-45",2,0.833), ("Женщины","35-45",3,0.300),
            ("Женщины","45-55",1,0.929), ("Женщины","45-55",2,1.000), ("Женщины","45-55",3,0.000),
            ("Женщины","55+",1,1.000), ("Женщины","55+",2,0.500), ("Женщины","55+",3,0.309),
            ("Мужчины","18-25",1,0.125), ("Мужчины","18-25",2,0.050), ("Мужчины","18-25",3,0.107),
            ("Мужчины","25-35",1,0.550), ("Мужчины","25-35",2,0.083), ("Мужчины","25-35",3,0.207),
            ("Мужчины","35-45",1,0.522), ("Мужчины","35-45",2,0.063), ("Мужчины","35-45",3,0.056),
            ("Мужчины","45-55",1,0.346), ("Мужчины","45-55",2,0.000), ("Мужчины","45-55",3,0.091),
            ("Мужчины","55+",1,0.150), ("Мужчины","55+",2,0.167), ("Мужчины","55+",3,0.000),
        ]
        df = pd.DataFrame(DATA, columns=["Cohort","AgeBand","Class","SurvivalCoef"])
    # типы
    df["Class"] = df["Class"].astype(int)
    df["SurvivalCoef"] = df["SurvivalCoef"].astype(float)
    return df

df = load_data()

def age_band(age: float) -> str:
    if age < 18: return "0-18"
    if age < 25:  return "18-25"
    if age < 35:  return "25-35"
    if age < 45:  return "35-45"
    if age < 55:  return "45-55"
    return "55+"

def cohort(gender: str, age: float) -> str:
    return "Дети" if age < 18 else gender

def class_by_budget_rub(budget: float) -> str:
    if budget < 100_000:
        return "Вы бы не смогли купить билет на Титаник"
    if budget < 230_000:
        return "3"
    if budget < 499_000:
        return "2"
    return "1"

st.title("🚢 Выжил бы ты на Титанике?")
st.caption("Модель на агрегированных данных: пол → возраст → класс по бюджету → коэффициент выживаемости из таблицы.")

with st.sidebar:
    st.header("Ввод")
    gender = st.selectbox("Пол", ["Женщины", "Мужчины"])
    age = st.number_input("Возраст (полных лет)", min_value=0, max_value=110, value=25, step=1)
    budget = st.number_input("Бюджет на билет (₽)", min_value=0, value=250_000, step=10_000, format="%i")
    gap_policy = st.radio(
        "Как трактовать окно 400–499 тыс. ₽?",
        ["Неопределённо (показать N/A)", "Отнести к 2-му классу", "Отнести к 1-му классу"],
        index=0
    )

band = age_band(age)
coh = cohort(gender, age)
klass = class_by_budget_rub(budget, gap_policy)

st.subheader("Результат")
col1, col2, col3 = st.columns(3)
col1.metric("Когорта", coh)
col2.metric("Возрастной диапазон", band)
col3.metric("Класс по бюджету", klass if klass in {"1","2","3"} else klass)

coef_text = "N/A"
coef_val = None

if klass in {"1","2","3"}:
    row = df[(df["Cohort"]==coh) & (df["AgeBand"]==band) & (df["Class"]==int(klass))]
    if not row.empty:
        coef_val = float(row["SurvivalCoef"].iloc[0])
        coef_text = f"{coef_val*100:.1f}%"
    else:
        coef_text = "нет данных"
elif klass == "ниже 3-го класса":
    coef_text = "0.0%"  # логика: билет не куплен → шанс 0
else:
    coef_text = "N/A"

st.markdown(f"### Вероятность выживания: **{coef_text}**")
if coef_val is not None:
    st.progress(min(max(coef_val,0.0),1.0))

with st.expander("Пояснение"):
    st.write(
        "1) Ввод: пол, возраст и бюджет в рублях.\n"
        "2) Класс по порогам: 3 кл. 100–230 тыс., 2 кл. 230–499 тыс., 1 кл. ≥500 тыс.\n"
        "3) По (когорта, возрастной диапазон, класс) берём коэффициент из `model.csv`.\n"
        "4) Показываем в процентах и прогресс-баре."
    )

st.subheader("Тесты")
colA, colB, colC = st.columns(3)
with colA:
    if st.button("Женщина, 22 г., 150k ₽ → 50.0%"):
        st.session_state["gender"]="Женщины"; st.session_state["age"]=22; st.session_state["budget"]=150_000; st.experimental_rerun()
with colB:
    if st.button("Женщина, 30 л., 250k ₽ → 92.3%"):
        st.session_state["gender"]="Женщины"; st.session_state["age"]=30; st.session_state["budget"]=250_000; st.experimental_rerun()
with colC:
    if st.button("Мужчина, 28 л., 520k ₽ → 55.0%"):
        st.session_state["gender"]="Мужчины"; st.session_state["age"]=28; st.session_state["budget"]=520_000; st.experimental_rerun()

# sync session state (optional)
if "gender" in st.session_state: gender = st.session_state["gender"]
if "age" in st.session_state: age = st.session_state["age"]
if "budget" in st.session_state: budget = st.session_state["budget"]
