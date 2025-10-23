import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Выжили бы вы Титанике?", page_icon="🚢", layout="centered")

# Показать ли тестовые кнопки (для отладки)
SHOW_TESTS = False

@st.cache_data
def load_data() -> pd.DataFrame:
    csv_path = Path(__file__).with_name("model.csv")
    if csv_path.exists():
        df = pd.read_csv(csv_path, encoding="utf-8")
    else:
        DATA = [
            ("Дети","0-18",1,0.714), ("Дети","0-18",2,0.793), ("Дети","0-18",3,0.364),
            ("Женщины","18-25",1,1.000), ("Женщины","18-25",2,0.962), ("Женщины","18-25",3,0.708),
            ("Женщины","25-35",1,0.958), ("Женщины","25-35",2,0.941), ("Женщины","25-35",3,0.435),
            ("Женщины","35-45",1,1.000), ("Женщины","35-45",2,0.846), ("Женщины","35-45",3,0.563),
            ("Женщины","45-55",1,0.962), ("Женщины","45-55",2,1.000), ("Женщины","45-55",3,0.375),
            ("Женщины","55+",1,1.000), ("Женщины","55+",2,0.667), ("Женщины","55+",3,0.063),
            ("Мужчины","18-25",1,0.083), ("Мужчины","18-25",2,0.029), ("Мужчины","18-25",3,0.074),
            ("Мужчины","25-35",1,0.367), ("Мужчины","25-35",2,0.053), ("Мужчины","25-35",3,0.149),
            ("Мужчины","35-45",1,0.364), ("Мужчины","35-45",2,0.036), ("Мужчины","35-45",3,0.042),
            ("Мужчины","45-55",1,0.220), ("Мужчины","45-55",2,0.000), ("Мужчины","45-55",3,0.083),
            ("Мужчины","55+",1,0.107), ("Мужчины","55+",2,0.100), ("Мужчины","55+",3,0.000),
        ]
        df = pd.DataFrame(DATA, columns=["Cohort","AgeBand","Class","SurvivalCoef"])
    df["Class"] = df["Class"].astype(int)
    df["SurvivalCoef"] = df["SurvivalCoef"].astype(float)
    return df

df = load_data()

def age_band(age: float) -> str:
    # 0–17, 18–25, 26–35, 36–45, 46–55, 56+
    if age < 18:
        return "0-18"      # дети до 18, не включая 18
    if age <= 25:
        return "18-25"
    if age <= 35:
        return "25-35"
    if age <= 45:
        return "35-45"
    if age <= 55:
        return "45-55"
    return "55+"

def normalize_gender_label(g: str) -> str:
    """Приводим любые варианты 'мужчина/мужчины' и 'женщина/женщины' к формам в датасете."""
    g = (g or "").strip().lower()
    if g.startswith("муж"):   # 'мужчина', 'муж', 'мужчины' — всё сюда
        return "Мужчины"
    return "Женщины"          # по умолчанию считаем 'женщины/женщина'

def cohort(gender: str, age: float) -> str:
    return "Дети" if age_band(age) == "0-18" else normalize_gender_label(gender)

def class_by_budget_rub(budget: float) -> str:
    # <100k — сообщение; 100–229999: 3; 230–499999: 2; >=500k: 1
    if budget < 100_000:
        return "Вы бы не смогли купить билет на Титаник"
    if budget < 230_000:
        return "3"
    if budget < 499_000:
        return "2"
    return "1"

# ===== UI =====
st.title("🚢 Выжили бы вы на Титанике?")
st.caption("Считаем по полу, возрасту и стоимости билета.")

with st.sidebar:
    st.header("Ввод")
    # можно оставить 'Женщины/Мужчины' или 'Женщина/Мужчина' — нормализация всё поправит
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
        "3) Вероятность выживания рассчитывается с помощью доли выживших в каждом возрастном диапазоне в зависимости от класса билета. Например, если доля — 0,9, то вероятность выживания — 90%."
    )

# Тестовые кнопки (включаются флагом сверху)
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


# ===== Исторический контекст =====
st.markdown("---")  # разделительная линия
st.markdown(
    """
    <div style="background-color:#f8fafc; padding:25px 30px; border-radius:12px; border:1px solid #e2e8f0;">
    <h2 style="margin-top:0;">Исторический контекст</h2>

    <p>В ночь на 15 апреля 1912 года крупнейший на тот момент океанский лайнер <b>«Титаник»</b> столкнулся с айсбергом 
    и затонул в холодных водах Атлантики. На борту находились более <b>2200 человек</b>, но выжила лишь треть.</p>

    <p>Жертвы катастрофы распределялись неравномерно. <i>«Титаник»</i> был не просто кораблём — 
    он отражал социальное устройство общества начала XX века.</p>

    <p><b>Первый класс</b> — богатейшие пассажиры: просторные каюты, рестораны и доступ к шлюпкам в первую очередь. 
    Медианная стоимость билета — <b>92 фунта стерлинга</b>, что составляет примерно <b>14,5 тыс. современных долларов</b> 
    или чуть больше <b>1 млн рублей</b>.</p>

    <p><b>Второй класс</b> — средний класс: учителя, клерки, эмигранты с накоплениями. 
    В среднем за билет второго класса нужно было отдать <b>20 фунтов</b> 
    (около <b>3,2 тыс. современных долларов</b> или <b>250 тыс. рублей</b>).</p>

    <p><b>Третий класс</b> — беднейшие переселенцы, стремившиеся в Новый Свет; 
    их каюты находились внизу, выходы были ограничены. 
    Билет можно было купить за <b>12 фунтов</b>, что в пересчёте на современные доллары составило бы 
    примерно <b>1 750</b>, а на рубли — <b>140 тыс.</b></p>

    <p>Тогда действовало негласное правило: <i>«женщины и дети — первыми в шлюпки»</i>. 
    Но даже оно работало по-разному в зависимости от класса. 
    <b>Женщина из первого класса</b> имела почти гарантированные шансы выжить, 
    тогда как <b>мужчина из третьего</b> — практически никакие.</p>
    </div>
    """,
    unsafe_allow_html=True
)
