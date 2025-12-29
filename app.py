import random                    # Nejauši skaitļi (īpašumi, pāri, jautājumi)
import numpy as np              # Nejaušas izvēles no masīviem
import pandas as pd             # CSV datu ielāde/apstrāde
import streamlit as st          # Streamlit web interfeiss

st.set_page_config(             # Lapas konfigurācija
    "Rīgas dzīvokļu cenu minēšanas spēle",  # Cilnes nosaukums
    "🏠",                      # Ikona
    "centered",                # Izkārtojums
)

# ---------- STILS ----------
st.markdown(                    # Pielāgots CSS
    """
    <style>
    html, body, [class*="css"]  {
        font-family: 'Segoe UI', sans-serif;
        background-color: #0f172a;
        color: #000000;
    }
    .main-title {
        font-size: 2.2rem; font-weight: 700;
        color: #f97316; text-align: center; margin-bottom: 0.3rem;
    }
    .main-subtitle {
        font-size: 0.95rem; color: #9ca3af;
        text-align: center; margin-bottom: 1.5rem;
    }
    h2, h3, h4 { color: #000000 !important; }
    .card {
        border-radius: 12px; padding: 1rem 1.2rem;
        background: radial-gradient(circle at top left, #1f2933, #020617);
        border: 1px solid #1f2937;
        box-shadow: 0 10px 25px rgba(15,23,42,0.7);
    }
    .card-header {
        font-size: 0.9rem; color: #9ca3af;
        text-transform: uppercase; letter-spacing: 0.08em;
    }
    .card-value {
        font-size: 1.3rem; font-weight: 700; color: #fbbf24;
    }
    .stButton > button {
        border-radius: 999px; border: none;
        padding: 0.5rem 1.4rem;
        background: linear-gradient(90deg, #f97316, #facc15);
        color: #02121f; font-weight: 600; cursor: pointer;
    }
    .stButton > button:hover {
        box-shadow: 0 4px 18px rgba(248, 181, 0, 0.6);
        transform: translateY(-1px);
    }
    .stRadio div[role="radiogroup"] > label {
        padding: 0.25rem 0.6rem; border-radius: 999px;
    }
    .stRadio div[role="radiogroup"] > label:hover {
        background: rgba(249,115,22,0.12);
    }
    hr { border-color: #1f2937; }
    </style>
    """,
    unsafe_allow_html=True,      # Atļauj HTML/CSS
)

# ---------- DATI ----------
@st.cache_data                  # Kešo ielādētos datus
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)      # Nolasa CSV
    if "op_type" in df.columns: # Atstāj tikai “For sale”/“For rent”
        df = df[df["op_type"].str.contains("For sale|For rent", case=False, na=False)]
    df = df.dropna(subset=["price", "area"])          # Izmet, ja nav cenas/platības
    df["price"] = pd.to_numeric(df["price"], errors="coerce")  # Cena kā skaitlis
    df["area"] = pd.to_numeric(df["area"], errors="coerce")    # Platība kā skaitlis
    df = df.dropna(subset=["price", "area"])          # Vēlreiz izmet nederīgos
    df = df[df["price"] > 0].reset_index(drop=True)   # Atstāj tikai pozitīvas cenas
    return df                                         # Atgriež tīru DataFrame

try:
    df = load_data("riga.csv")    # Ielādē galveno datu failu
    if df.empty:                  # Ja nav ierakstu
        st.error("Datu fails ir tukšs vai nav ielādējies.")  # Ziņo par problēmu
        st.stop()                 # Aptur app
except Exception as e:            # Ja “riga.csv” ielāde neizdodas
    st.error(f"Neizdevās ielādēt datus: {e}")         # Parāda kļūdu
    st.stop()                     # Aptur app

df_rent = df[df["op_type"].str.contains(             # Īres datu kopa
    "rent", case=False, na=False
)].reset_index(drop=True)

df_sale = df[df["op_type"].str.contains(             # Pārdošanas datu kopa
    "sale", case=False, na=False
)].reset_index(drop=True)

try:
    quiz_df = pd.read_csv("real_estate_quiz_lv.csv") # Ielādē viktorīnas jautājumus
except Exception:
    quiz_df = pd.DataFrame()                         # Ja neizdodas – tukšs DF

# ---------- STATE ----------
defaults = {                                         # Noklusējuma state vērtības
    "score": 0,                                      # Kopējie punkti
    "rounds": 0,                                     # Raundu skaits
    "current_idx": random.randint(0, len(df) - 1),   # Aktuālā īpašuma indekss
    "last_result": None,                             # Pēdējais rezultāts
    "total_error": 0.0,                              # Kopējā kļūda %
    "average_error": 0.0,                            # Vidējā kļūda %
    "pair_idx": None,                                # Pārī izvēlētie īpašumi
    "quiz_question_number": 0,                       # Pašreizējais viktorīnas jautājums
    "quiz_finished": False,                          # Viktorīna pabeigta / nav
    "next_q_prev_clicked": False,                    # Iepriekšējais “Nākošais” stāvoklis
}
for k, v in defaults.items():                        # Pāriet pāri visiem state key
    st.session_state.setdefault(k, v)                # Ja nav – uzstāda default vērtību

# ---------- PALĪGFUNKCIJAS ----------
def reset_game():                                    # Atjauno spēli no nulles
    for k in ["score", "rounds", "total_error", "average_error"]:
        st.session_state[k] = 0                      # Nokrāso punktus/kļūdu uz 0
    st.session_state["current_idx"] = random.randint(0, len(df) - 1)  # Jauns īpašums
    st.session_state["pair_idx"] = None              # Notīra pāri
    st.session_state["last_result"] = None           # Notīra pēdējo rezultātu
    st.session_state["quiz_question_number"] = 0     # Sāk viktorīnu no sākuma
    st.session_state["quiz_finished"] = False        # Atzīmē, ka nav pabeigta

def choose_new_property():                           # Izvēlas jaunu īpašumu minēšanai
    st.session_state.current_idx = random.randint(0, len(df) - 1)  # Nejaušs indekss
    st.session_state.last_result = None              # Notīra rezultātu

def calculate_points(error_pct: float) -> int:       # Punktu aprēķins pēc kļūdas
    if error_pct <= 5:    return 5                   # ≤5% → 5 punkti
    if error_pct <= 10:   return 3                   # ≤10% → 3 punkti
    if error_pct <= 20:   return 2                   # ≤20% → 2 punkti
    return 1                                         # Citādi → 1 punkts

def choose_new_pair():                               # Izvēlas jaunu īpašumu pāri
    use_rent = random.choice([True, False])          # Nejauši izvēlas īre/pārdošana
    pool = df_rent if (use_rent and len(df_rent) >= 2) else df_sale  # Pamata kopa
    if len(pool) < 2:                                # Ja pamata kopā nav 2 ierakstu
        other = df_sale if pool is df_rent else df_rent  # Ņem otru kopu
        if len(other) < 2:                           # Ja arī tur nepietiek
            st.session_state.pair_idx = None         # Nav iespējams izveidot pāri
            return                                   # Izlec ārā
        pool = other                                 # Izmanto otru kopu
    idx = np.random.choice(len(pool), size=2, replace=False)  # 2 nejauši indeksi
    st.session_state.pair_idx = (                    # Saglabā pāri state
        "rent" if pool is df_rent else "sale",       # Pāra tips
        idx[0], idx[1],                              # Abas rindas
    )
    st.session_state.last_result = None              # Notīra rezultātu

HOUSE_TYPE_MAP = {                                   # Māju tipu tulkojumi
    "Brick": "Ķieģeļu māja",
    "Brick-Panel": "Ķieģeļu-paneļu māja",
    "Panel": "Paneļu māja",
    "Panel-Brick": "Paneļu-ķieģeļu māja",
    "Wood": "Koka māja",
    "Masonry": "Mūra māja",
}
CONDITION_MAP = {                                    # Stāvokļu tulkojumi
    "All amenities": "Ar visām ērtībām",
    "Partial amenities": "Daļējas ērtības",
    "Without amenities": "Bez ērtībām",
}

# ---------- GALVENE ----------
st.markdown(                                         # Galvenais virsraksts
    '<div class="main-title">🏠 Rīgas dzīvokļu cenu minēšanas spēle</div>',
    unsafe_allow_html=True,
)
st.markdown(                                         # Apakšvirsraksts
    '<div class="main-subtitle">Miniet cenas, salīdziniet īpašumus un pārbaudiet zināšanas par nekustamo īpašumu.</div>',
    unsafe_allow_html=True,
)
st.markdown("---")                                   # Atdaloša līnija

# ---------- SIDEBAR ----------
with st.sidebar:                                     # Sānjoslas saturs
    st.markdown("### Spēles statuss")                # Sānjoslas virsraksts

    st.markdown(                                     # Kartiņa: kopējie punkti
        f"""
        <div class="card">
            <div class="card-header">Punkti kopā</div>
            <div class="card-value">{st.session_state.score}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(                                     # Kartiņa: raundi
        f"""
        <div class="card" style="margin-top:0.7rem;">
            <div class="card-header">Raundi</div>
            <div class="card-value">{st.session_state.rounds}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.rounds > 0:                  # Ja ir vismaz 1 raunds
        st.markdown(                                 # Kartiņa: vidējā kļūda
            f"""
            <div class="card" style="margin-top:0.7rem;">
                <div class="card-header">Vidējā kļūda</div>
                <div class="card-value">{st.session_state.average_error:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("---")                               # Atdaloša līnija
    if st.button("Atjaunot rezultātu"):              # Poga reset
        reset_game()                                 # Atjauno spēli

    mode = st.radio(                                 # Režīma izvēle
        "Režīms:",
        ["Cenu minēšana", "Kurš ir dārgāks?", "Viktorīna"],
    )
    with st.expander("Punktu sistēma"):              # TL;DR par punktiem
        st.markdown(
            """
            **Cenu minēšana**
            - Kļūda ≤ 5% → 5 punkti  
            - Kļūda ≤ 10% → 3 punkti  
            - Kļūda ≤ 20% → 2 punkti  
            - Citādi → 1 punkts  

            **Kurš ir dārgāks?**
            - Pareizi uzminēts pāris → +1 punkts  

            **Viktorīna**
            - Pareiza atbilde → +1 punkts  
            """
        )

# ---------- 1. CENU MINĒŠANA ----------
if mode == "Cenu minēšana":                          # Ja izvēlēts minēšanas režīms
    prop = df.iloc[st.session_state.current_idx]     # Aktuālais īpašums
    st.subheader("Īpašuma apraksts")                 # Sekcijas virsraksts

    op_raw = str(prop.get("op_type", "")).lower()    # Darījuma tipa teksts
    if "rent" in op_raw:                             # Ja īre
        st.markdown("Šis īpašums ir **IZĪRĒŠANAI**.")
    elif "sale" in op_raw:                           # Ja pārdošana
        st.markdown("Šis īpašums ir **PĀRDOŠANAI**.")
    else:                                            # Ja nav zināms
        st.markdown("Darījuma tips nav zināms.")

    col1, col2 = st.columns(2)                       # Divas info kolonnas
    with col1:
        st.write(f"**Rajons:** {prop.get('district', 'Nav dati')}")  # Rajons
        st.write(f"**Iela:** {prop.get('street', 'Nav dati')}")      # Iela
        st.write(f"**Istabas:** {prop.get('rooms', 'Nav dati')}")    # Istabas
        st.write(f"**Platība:** {prop.get('area', 'Nav')} m²")       # Platība
    with col2:
        if {"floor", "total_floors"}.issubset(prop.index):           # Ja ir stāvi
            floor = int(float(prop["floor"]))                        # Stāvs
            total_floors = int(float(prop["total_floors"]))          # Kopā stāvi
            st.write(f"**Stāvs:** {floor}/{total_floors}")           # Rāda stāvu
        if "house_type" in prop.index:                              # Ja ir mājas tips
            ht = str(prop["house_type"])                             # Iegūst tipu
            st.write(f"**Mājas tips:** {HOUSE_TYPE_MAP.get(ht, ht)}")# Tulko/atstāj
        if "condition" in prop.index:                               # Ja ir stāvoklis
            cond = str(prop["condition"])                            # Iegūst stāvokli
            st.write(f"**Stāvoklis:** {CONDITION_MAP.get(cond, cond)}")  # Tulko/atstāj

    st.markdown("---")                                # Atdaloša līnija
    st.subheader("Tavs minējums")                     # Minējuma sekcija
    guess = st.number_input(                          # Ievades lauks cenai
        "Ievadi cenu (EUR):", 0, step=1000, format="%d"
    )
    col_btn1, col_btn2, _ = st.columns([2, 2, 3])     # Pogas un tukšums
    with col_btn1:
        confirm_clicked = st.button("Apstiprināt minējumu")  # Apstiprinājuma poga
    with col_btn2:
        next_clicked = st.button("Nākošais īpašums")         # Nākamā īpašuma poga

    if confirm_clicked:                                      # Ja apstiprina minējumu
        real_price = float(prop["price"])                    # Reālā cena
        if real_price <= 0:                                  # Ja nederīga cena
            st.warning("Šim īpašumam nav korektas cenas, izvēlamies citu.")  # Brīdinājums
            choose_new_property()                            # Izvēlas citu īpašumu
        else:
            error_pct = abs(guess - real_price) / real_price * 100  # Kļūda %
            points = calculate_points(error_pct)                     # Punkti
            st.session_state.score += points                         # Pievieno punktus
            st.session_state.rounds += 1                             # + raunds
            st.session_state.total_error += error_pct                # Pieskaita kļūdu
            st.session_state.average_error = (                       # Jauna vidējā kļūda
                st.session_state.total_error / st.session_state.rounds
            )
            st.session_state.last_result = {                         # Saglabā rezultātu
                "real_price": real_price,
                "guess": guess,
                "error_pct": error_pct,
                "points": points,
            }
            st.markdown("### Tavs rezultāts")                        # Rezultātu virsraksts
            st.write(f"Reālā cena: **{real_price:,.0f} EUR**")       # Reālā cena
            st.write(f"Tavs minējums: **{guess:,.0f} EUR**")         # Minējums
            st.write(f"Kļūda: **{error_pct:.1f}%**")                 # Kļūda %
            st.write(f"Punkti par šo raundu: **{points}**")          # Punkti

    if next_clicked:                                            # Ja “Nākošais īpašums”
        choose_new_property()                                   # Izvēlas citu

    if {"lat", "lon"}.issubset(prop.index):                    # Ja ir koordinātes
        try:
            map_df = pd.DataFrame({                            # DataFrame kartei
                "lat": [float(prop["lat"])],
                "lon": [float(prop["lon"])],
            })
            st.subheader("Atrašanās vieta kartē")              # Kartes virsraksts
            st.map(map_df, zoom=14)                            # Karte ar punktu
        except Exception:                                      # Ja kļūda
            pass                                               # Klusi ignorē

# ---------- 2. KURŠ IR DĀRGĀKS? ----------
elif mode == "Kurš ir dārgāks?":                   # Salīdzināšanas režīms
    st.subheader("Kurš ir dārgāks?")               # Virsraksts
    if st.session_state.pair_idx is None:          # Ja pāris nav izvēlēts
        choose_new_pair()                          # Izvēlas jaunu pāri
    if st.session_state.pair_idx is None:          # Ja joprojām nav pāra
        st.warning("Nav pietiekami daudz datu, lai izveidotu pāri.")  # Brīdinājums
        st.stop()                                  # Aptur režīmu

    pair_type, idx_a, idx_b = st.session_state.pair_idx  # Izpako pāri
    df_pair = df_rent if pair_type == "rent" else df_sale  # Avota DataFrame
    prop_a, prop_b = df_pair.iloc[idx_a], df_pair.iloc[idx_b]  # Abi īpašumi

    col_a, col_b = st.columns(2)                  # Divas kolonnas
    with col_a:
        st.markdown("#### Īpašums A")             # A virsraksts
        st.write(f"Rajons: {prop_a['district']}") # A rajons
        st.write(f"Istabas: {prop_a['rooms']}")   # A istabas
        st.write(f"Platība: {prop_a['area']} m²") # A platība
    with col_b:
        st.markdown("#### Īpašums B")             # B virsraksts
        st.write(f"Rajons: {prop_b['district']}") # B rajons
        st.write(f"Istabas: {prop_b['rooms']}")   # B istabas
        st.write(f"Platība: {prop_b['area']} m²") # B platība

    col_btn1, col_btn2 = st.columns(2)            # Divas pogu kolonnas
    with col_btn1:
        choose_a = st.button("A ir dārgāks")      # A kā dārgāks
    with col_btn2:
        choose_b = st.button("B ir dārgāks")      # B kā dārgāks

    if choose_a or choose_b:                      # Ja kāda izvēle izdarīta
        price_a, price_b = float(prop_a["price"]), float(prop_b["price"])  # Cenas
        st.session_state.rounds += 1              # + raunds
        if (choose_a and price_a >= price_b) or (choose_b and price_b >= price_a):
            st.success("Pareizi!")                # Pareizi
            st.session_state.score += 1           # +1 punkts
        else:
            st.error("Garām!")                    # Nepareizi
        st.write(f"A cena: **{price_a:,.0f} EUR**")  # A cena
        st.write(f"B cena: **{price_b:,.0f} EUR**")  # B cena
        choose_new_pair()                         # Nākamais pāris

# ---------- 3. VIKTORĪNA ----------
else:                                              # Viktorinai
    st.subheader("Viktorīna par nekustamajiem īpašumiem")  # Virsraksts
    if quiz_df.empty:                             # Ja nav jautājumu
        st.warning("Nav atrasts fails real_estate_quiz_lv.csv – nevar ielādēt viktorīnu.")  # Info
    else:
        if st.session_state.quiz_question_number >= len(quiz_df):  # Ja visi jautājumi iziets
            st.session_state.quiz_finished = True                  # Atzīmē pabeigtu

        if st.session_state.quiz_finished:       # Ja pabeigta
            st.write("Viktorīna pabeigta!")      # Paziņojums
            st.write(f"Kopējais punktu skaits: **{st.session_state.score}**")  # Gala punkti
        else:
            i = st.session_state.quiz_question_number  # Pašreizējais jautājums
            row = quiz_df.iloc[i]               # Jautājuma rinda
            st.write(f"Jautājums {i + 1} no {len(quiz_df)}")  # Numurs
            st.write(row["question"])           # Teksts

            def opt(col, label):                # Palīgfunkcija atbildei
                return str(row[col]) if pd.notna(row[col]) else f"[Trūkst atbildes {label}]"

            options_list = [                    # 4 atbilžu varianti
                f"A: {opt('option_a','A')}",
                f"B: {opt('option_b','B')}",
                f"C: {opt('option_c','C')}",
                f"D: {opt('option_d','D')}",
            ]

            radio_key = f"quiz_answer_q{i}"     # Unikāls radio key
            chosen = st.radio(                  # Radio izvēle
                "Izvēlies atbildi:", options_list, key=radio_key
            )

            q_state_key = f"quiz_answered_q{i}" # Vai šis jautājums jau atbildēts
            st.session_state.setdefault(q_state_key, False)  # Default False

            col_q1, col_q2 = st.columns(2)      # Kolonnas pogām
            with col_q1:
                check = st.button("Pārbaudīt atbildi")    # Pārbaudīt
            with col_q2:
                next_q = st.button("Nākošais jautājums")  # Nākamais jautājums

            if check and not st.session_state[q_state_key]:      # Pārbauda tikai 1×
                if not chosen:                                   # Ja nav atbildes
                    st.warning("Vispirms izvēlies atbildi.")     # Brīdinājums
                else:
                    chosen_letter = chosen.split(":")[0].strip() # Izvēlētais burts
                    correct = str(row["correct_option"]).strip() # Pareizais burts
                    st.session_state.rounds += 1                 # + raunds
                    if chosen_letter == correct:                 # Ja pareizi
                        st.success("Pareizi!")                   # Ziņa
                        st.session_state.score += 1              # +1 punkts
                    else:
                        st.error(f"Garām! Pareizā atbilde ir {correct}.")  # Nepareizi
                    st.session_state[q_state_key] = True         # Atzīmē kā atbildētu

            if next_q and not st.session_state.next_q_prev_clicked:  # Edge detect uz “Nākošais”
                st.session_state.quiz_question_number += 1           # Ejam uz nākamo
            st.session_state.next_q_prev_clicked = next_q            # Saglabā pogas stāvokli