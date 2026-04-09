import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Copytrading Rechner",
    layout="wide"
)

# =========================================================
# STYLES
# =========================================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.5rem;
    }
    div[data-testid="stMetricValue"] {
        font-weight: 800;
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.header("⚙️ Einstellungen")

investment = st.sidebar.number_input(
    "Investor Kapital ($)",
    min_value=0,
    value=10000,
    step=1000,
    help="Kapital pro Investor in USD."
)

factor = st.sidebar.selectbox(
    "Faktor",
    [1.0, 1.5, 2.0],
    index=1,
    help="Hebel bzw. Faktor auf das Investor-Kapital."
)

commission_rate = st.sidebar.slider(
    "Kommission (%)",
    min_value=0.0,
    max_value=1.0,
    value=0.75,
    step=0.01,
    help="Monatliche Kommission auf das investierte Kapital."
) / 100

duration = st.sidebar.selectbox(
    "Vertriebler Zeitraum",
    [3, 6, 9, 12],
    index=3,
    help="Welcher Zeitraum soll oben in der Übersicht gezeigt werden."
)

leader_active = st.sidebar.checkbox(
    "Vertriebsleiter aktivieren",
    value=False,
    help="Wenn aktiv, erhält der Vertriebsleiter einen Anteil vom Vertriebler-Bonus."
)

leader_pct = 0.0
if leader_active:
    leader_pct = st.sidebar.slider(
        "Vertriebsleiter Anteil (%)",
        min_value=0,
        max_value=50,
        value=10,
        step=1,
        help="Anteil des Vertriebsleiters am Vertriebler-Bonus."
    ) / 100

st.sidebar.subheader("🤝 Bonus (%)")

bonus_map = {
    3: st.sidebar.slider(
        "3 Monate (%)",
        min_value=0,
        max_value=100,
        value=20,
        step=1,
        help="Bonus-Anteil des Vertriebler-Topfs bei 3 Monaten."
    ),
    6: st.sidebar.slider(
        "6 Monate (%)",
        min_value=0,
        max_value=100,
        value=30,
        step=1,
        help="Bonus-Anteil des Vertriebler-Topfs bei 6 Monaten."
    ),
    9: st.sidebar.slider(
        "9 Monate (%)",
        min_value=0,
        max_value=100,
        value=40,
        step=1,
        help="Bonus-Anteil des Vertriebler-Topfs bei 9 Monaten."
    ),
    12: st.sidebar.slider(
        "12 Monate (%)",
        min_value=0,
        max_value=100,
        value=50,
        step=1,
        help="Bonus-Anteil des Vertriebler-Topfs bei 12 Monaten."
    ),
}
bonus_map = {k: v / 100 for k, v in bonus_map.items()}

st.sidebar.subheader("📈 Gewinnaufteilung")

vertriebler_profit_pct = st.sidebar.slider(
    "Vertriebler Gewinn (%)",
    min_value=0,
    max_value=100,
    value=15,
    step=1,
    help="Anteil des Vertrieblers an der Rendite / Gewinnaufteilung."
) / 100

j_profit_pct = st.sidebar.slider(
    "J Gewinn (%)",
    min_value=0,
    max_value=100,
    value=10,
    step=1,
    help="Anteil von Partei J an der Rendite / Gewinnaufteilung."
) / 100

annual_return = st.sidebar.slider(
    "Jahresgewinn (%)",
    min_value=10,
    max_value=50,
    value=30,
    step=1,
    help="Theoretische Jahresrendite vor Gebühren."
)

fee_return = st.sidebar.slider(
    "Nach Gebühren (%)",
    min_value=10,
    max_value=50,
    value=25,
    step=1,
    help="Jahresrendite nach Handelsgebühren."
)

monthly_return = fee_return / 100 / 12

# =========================================================
# FARBEN
# =========================================================
COLOR_VERTRIEBLER = "#2563eb"     # blau
COLOR_LEADER = "#60a5fa"          # hellblau
COLOR_JJ = "#f97316"              # orange
COLOR_J = "#22c55e"               # grün
COLOR_GAIN = "#16a34a"            # dunkleres grün
COLOR_WARN = "#ef4444"            # rot

# =========================================================
# BERECHNUNG
# =========================================================
months = [1, 3, 6, 9, 12]
capital = investment * factor

def get_bonus_pct_for_month(month: int) -> float:
    if month >= 12:
        return bonus_map[12]
    if month >= 9:
        return bonus_map[9]
    if month >= 6:
        return bonus_map[6]
    if month >= 3:
        return bonus_map[3]
    return 0.0

def calc(month: int) -> dict:
    commission_total = capital * commission_rate * month

    # Kommissionslogik je Monat:
    # 1M = 0%, 3M = 20%, 6M = 30%, 9M = 40%, 12M = 50%
    bonus_pct = get_bonus_pct_for_month(month)

    # Gesamter Vertriebler-Topf (inkl. evtl. Vertriebsleiter)
    vertriebler_bonus_pool = commission_total * bonus_pct

    # Vertriebsleiter Anteil vom Vertriebler-Topf
    vertriebsleiter_commission = vertriebler_bonus_pool * leader_pct if leader_active else 0.0
    vertriebler_commission = vertriebler_bonus_pool - vertriebsleiter_commission

    # Restliche Kommissionen gehen an J+J und J
    remaining_commission = commission_total - vertriebler_bonus_pool
    jj_commission = remaining_commission * 0.60
    j_commission = remaining_commission * 0.40

    # Gewinn / Rendite
    value = capital * ((1 + monthly_return) ** month)
    profit_total = value - capital

    vertriebler_profit = profit_total * vertriebler_profit_pct
    j_profit = profit_total * j_profit_pct

    return {
        "Monat": month,
        "Kapital": round(capital, 2),
        "Kommission Gesamt": round(commission_total, 2),
        "Bonus %": round(bonus_pct * 100, 2),

        "Vertriebler Kommission": round(vertriebler_commission, 2),
        "Vertriebsleiter Kommission": round(vertriebsleiter_commission, 2),
        "J+J Kommission": round(jj_commission, 2),
        "J Kommission": round(j_commission, 2),

        "Gewinn Gesamt": round(profit_total, 2),
        "Vertriebler Gewinn": round(vertriebler_profit, 2),
        "J Gewinn": round(j_profit, 2),

        "Vertriebler Gesamt": round(vertriebler_commission + vertriebler_profit, 2),
        "J Gesamt": round(j_commission + j_profit, 2),
    }

df = pd.DataFrame([calc(m) for m in months])
row = df[df["Monat"] == duration].iloc[0]

# =========================================================
# ÜBERSICHT
# =========================================================
st.markdown(f"## 💰 Übersicht ({duration} Monate)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "🔵 Vertriebler",
        f"${row['Vertriebler Gesamt']:,.0f}",
        help="Komplette Einnahmen des Vertrieblers: Kommission + Gewinn."
    )
    st.markdown(
        f"<div style='color:{COLOR_VERTRIEBLER}; font-weight:700;'>Kommission: ${row['Vertriebler Kommission']:,.0f}</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div style='color:{COLOR_GAIN}; font-weight:700;'>Gewinn: ${row['Vertriebler Gewinn']:,.0f}</div>",
        unsafe_allow_html=True
    )

with col2:
    st.metric(
        "🔷 Vertriebsleiter",
        f"${row['Vertriebsleiter Kommission']:,.0f}",
        help="Kommissionsanteil des Vertriebsleiters aus dem Vertriebler-Topf."
    )
    st.markdown(
        f"<div style='color:{COLOR_LEADER}; font-weight:700;'>Kommission: ${row['Vertriebsleiter Kommission']:,.0f}</div>",
        unsafe_allow_html=True
    )
    st.caption("Kein separater Gewinnanteil")

with col3:
    st.metric(
        "🟠 J+J",
        f"${row['J+J Kommission']:,.0f}",
        help="Kommissionsanteil von J+J. Verhältnis im Resttopf: 60%."
    )
    st.markdown(
        f"<div style='color:{COLOR_JJ}; font-weight:700;'>Kommission: ${row['J+J Kommission']:,.0f}</div>",
        unsafe_allow_html=True
    )
    st.caption("Kein separater Gewinnanteil")

with col4:
    st.metric(
        "🟢 J",
        f"${row['J Gesamt']:,.0f}",
        help="Komplette Einnahmen von J: Kommission + Gewinn."
    )
    st.markdown(
        f"<div style='color:{COLOR_J}; font-weight:700;'>Kommission: ${row['J Kommission']:,.0f}</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div style='color:{COLOR_GAIN}; font-weight:700;'>Gewinn: ${row['J Gewinn']:,.0f}</div>",
        unsafe_allow_html=True
    )

# =========================================================
# KOMMISSIONEN VERTEILUNG
# =========================================================
st.markdown("### 📊 Kommissionen Verteilung")

comm_df = df[[
    "Monat",
    "Vertriebler Kommission",
    "Vertriebsleiter Kommission",
    "J+J Kommission",
    "J Kommission",
    "Kommission Gesamt",
    "Bonus %",
]].copy()

fig1 = px.bar(
    comm_df,
    x="Monat",
    y=[
        "Vertriebler Kommission",
        "Vertriebsleiter Kommission",
        "J+J Kommission",
        "J Kommission"
    ],
    text_auto=".0f",
    barmode="stack",
    color_discrete_map={
        "Vertriebler Kommission": COLOR_VERTRIEBLER,
        "Vertriebsleiter Kommission": COLOR_LEADER,
        "J+J Kommission": COLOR_JJ,
        "J Kommission": COLOR_J,
    },
    labels={
        "value": "USD",
        "Monat": "Monat",
        "variable": "Partei",
    },
)

fig1.update_traces(
    hovertemplate="<b>%{fullData.name}</b><br>Monat: %{x}<br>Wert: $%{y:,.0f}<extra></extra>",
    textfont_size=13
)

fig1.update_layout(
    hovermode="x unified",
    legend_title_text="Partei",
    margin=dict(t=30, l=10, r=10, b=10),
)

st.plotly_chart(
    fig1,
    use_container_width=True,
    key="comm_chart"
)

# =========================================================
# VERTRIEBLER EINNAHMEN
# =========================================================
st.markdown("### 📊 Vertriebler Einnahmen")

vertrieb_df = df[[
    "Monat",
    "Vertriebler Kommission",
    "Vertriebler Gewinn",
    "Vertriebler Gesamt",
]].copy()

fig2 = px.bar(
    vertrieb_df,
    x="Monat",
    y=["Vertriebler Kommission", "Vertriebler Gewinn"],
    text_auto=".0f",
    barmode="stack",
    color_discrete_map={
        "Vertriebler Kommission": COLOR_VERTRIEBLER,
        "Vertriebler Gewinn": COLOR_GAIN,
    },
    labels={
        "value": "USD",
        "Monat": "Monat",
        "variable": "Bestandteil",
    },
)

fig2.update_traces(
    hovertemplate="<b>%{fullData.name}</b><br>Monat: %{x}<br>Wert: $%{y:,.0f}<extra></extra>",
    textfont_size=13
)

fig2.update_layout(
    hovermode="x unified",
    legend_title_text="Bestandteil",
    margin=dict(t=30, l=10, r=10, b=10),
)

st.plotly_chart(
    fig2,
    use_container_width=True,
    key="vertriebler_income_chart"
)

# =========================================================
# PIE CHARTS
# =========================================================
st.markdown("### 📊 Verteilungen")

pie_col1, pie_col2 = st.columns(2)

with pie_col1:
    st.markdown("**Gesamteinnahmen Verteilung**")

    pie_total = px.pie(
        names=["Vertriebler", "Vertriebsleiter", "J+J", "J"],
        values=[
            row["Vertriebler Gesamt"],
            row["Vertriebsleiter Kommission"],
            row["J+J Kommission"],
            row["J Gesamt"],
        ],
        color=["Vertriebler", "Vertriebsleiter", "J+J", "J"],
        color_discrete_map={
            "Vertriebler": COLOR_VERTRIEBLER,
            "Vertriebsleiter": COLOR_LEADER,
            "J+J": COLOR_JJ,
            "J": COLOR_J,
        },
    )
    pie_total.update_traces(
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Wert: $%{value:,.0f}<br>Anteil: %{percent}<extra></extra>"
    )
    pie_total.update_layout(
        margin=dict(t=20, l=10, r=10, b=10),
        showlegend=True,
    )
    st.plotly_chart(
        pie_total,
        use_container_width=True,
        key="pie_total"
    )

with pie_col2:
    st.markdown("**Vertriebler Einnahmen (Kommission vs Gewinn)**")

    pie_vertrieb = px.pie(
        names=["Kommission", "Gewinn"],
        values=[
            row["Vertriebler Kommission"],
            row["Vertriebler Gewinn"],
        ],
        color=["Kommission", "Gewinn"],
        color_discrete_map={
            "Kommission": COLOR_VERTRIEBLER,
            "Gewinn": COLOR_GAIN,
        },
    )
    pie_vertrieb.update_traces(
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Wert: $%{value:,.0f}<br>Anteil: %{percent}<extra></extra>"
    )
    pie_vertrieb.update_layout(
        margin=dict(t=20, l=10, r=10, b=10),
        showlegend=True,
    )
    st.plotly_chart(
        pie_vertrieb,
        use_container_width=True,
        key="pie_vertrieb"
    )

# =========================================================
# HEATMAP / ENTSCHEIDUNGSHILFE
# =========================================================
st.markdown("### 🔥 Welche Laufzeit lohnt sich für den Vertriebler?")

# Für diese Heatmap rechnen wir den Vertriebler-Endwert je gewählter Laufzeit.
decision_rows = []

for choice in [3, 6, 9, 12]:
    # Für die Entscheidung wird genau der jeweilige Zeitraum als Betrachtungspunkt genutzt.
    tmp = calc(choice)
    total_income = tmp["Vertriebler Gesamt"]
    total_bonus = tmp["Vertriebler Kommission"]
    total_gain = tmp["Vertriebler Gewinn"]
    decision_rows.append({
        "Laufzeit": f"{choice} Monate",
        "Einnahmen": round(total_income, 2),
        "Bonus": round(total_bonus, 2),
        "Gewinn": round(total_gain, 2),
    })

decision_df = pd.DataFrame(decision_rows)
best_income = decision_df["Einnahmen"].max()
decision_df["Verpasst vs. beste Wahl"] = decision_df["Einnahmen"] - best_income
decision_df["Verpasst %"] = (decision_df["Verpasst vs. beste Wahl"] / best_income * 100).round(1)

# Verständliche Tabelle
display_df = decision_df.copy()
display_df["Einnahmen"] = display_df["Einnahmen"].round(0).astype(int)
display_df["Bonus"] = display_df["Bonus"].round(0).astype(int)
display_df["Gewinn"] = display_df["Gewinn"].round(0).astype(int)
display_df["Verpasst vs. beste Wahl"] = display_df["Verpasst vs. beste Wahl"].round(0).astype(int)

def style_decision(val):
    if isinstance(val, (int, float)):
        if val == 0:
            return "background-color:#14532d;color:white;font-weight:700;"
        if val < 0:
            return "background-color:#7f1d1d;color:white;font-weight:700;"
    return ""

st.dataframe(display_df, use_container_width=True)

# Zusätzlich einfache Heatmap als visuelle Hilfe
heat_source = decision_df[["Laufzeit", "Einnahmen", "Verpasst vs. beste Wahl"]].copy()
heat_long = heat_source.melt(
    id_vars="Laufzeit",
    value_vars=["Einnahmen", "Verpasst vs. beste Wahl"],
    var_name="Kennzahl",
    value_name="Wert"
)

fig_heat = px.density_heatmap(
    heat_long,
    x="Kennzahl",
    y="Laufzeit",
    z="Wert",
    text_auto=".0f",
    color_continuous_scale=[
        [0.0, "#7f1d1d"],
        [0.5, "#374151"],
        [1.0, "#22c55e"],
    ],
    labels={
        "Kennzahl": "Kennzahl",
        "Laufzeit": "Vertriebler-Option",
        "Wert": "USD",
    },
)

fig_heat.update_traces(
    hovertemplate="<b>%{y}</b><br>%{x}: $%{z:,.0f}<extra></extra>"
)
fig_heat.update_layout(
    margin=dict(t=20, l=10, r=10, b=10),
    coloraxis_colorbar_title="USD"
)

st.plotly_chart(
    fig_heat,
    use_container_width=True,
    key="decision_heatmap"
)

st.caption(
    "Grün zeigt die beste Entscheidung. Rot zeigt, was dem Vertriebler gegenüber der besten Wahl entgeht. "
    "Gewinnaufteilung bleibt separat enthalten, der Bonus steigt mit längerer Laufzeit."
)