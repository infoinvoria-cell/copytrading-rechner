import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Rechner",
    layout="wide"
)

# =========================================================
# STYLES
# =========================================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.1rem;
        padding-bottom: 1.6rem;
        max-width: 1400px;
    }
    div[data-testid="stMetricValue"] {
        font-weight: 800;
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 700;
    }
    .small-breakdown {
        font-size: 0.95rem;
        font-weight: 700;
        line-height: 1.45;
        margin-top: 0.15rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# FARBEN
# =========================================================
COLOR_VERTRIEBLER = "#2563eb"   # blau
COLOR_LEADER = "#60a5fa"        # hellblau
COLOR_JJ = "#f97316"            # orange
COLOR_J = "#22c55e"             # grün
COLOR_GAIN = "#16a34a"          # dunkleres grün
COLOR_RED = "#ef4444"           # rot
COLOR_J4J = "#f97316"           # J4J = orange

# =========================================================
# HILFSFUNKTIONEN
# =========================================================
def money(x: float) -> str:
    return f"${x:,.0f}"

def pct(x: float) -> str:
    return f"{x:.1f}%"

def bonus_pct_for_month(month: int, bonus_map: dict[int, float]) -> float:
    if month >= 12:
        return bonus_map[12]
    if month >= 9:
        return bonus_map[9]
    if month >= 6:
        return bonus_map[6]
    if month >= 3:
        return bonus_map[3]
    return 0.0

def render_breakdown_line(label: str, value: float, color: str) -> None:
    st.markdown(
        f"<div class='small-breakdown' style='color:{color};'>{label}: {money(value)}</div>",
        unsafe_allow_html=True,
    )

# =========================================================
# SIDEBAR - HAUPTAUSWAHL
# =========================================================
st.sidebar.header("⚙️ Einstellungen")

rechner_variante = st.sidebar.selectbox(
    "Rechner Variante",
    options=["1", "2"],
    index=0,
    help="Variante 1 = bisheriger Rechner. Variante 2 = neuer Sub-IB / Master-IB Rechner."
)

# =========================================================
# VARIANTE 1
# =========================================================
if rechner_variante == "1":
    st.sidebar.subheader("Variante 1")

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
        help="Dieser Zeitraum wird oben in der Übersicht dargestellt."
    )

    leader_active = st.sidebar.checkbox(
        "Vertriebsleiter aktivieren",
        value=False,
        help="Wenn aktiv, erhält der Vertriebsleiter einen Anteil aus dem Vertriebler-Bonus."
    )

    leader_pct = 0.0
    if leader_active:
        leader_pct = st.sidebar.slider(
            "Vertriebsleiter Anteil (%)",
            min_value=0,
            max_value=50,
            value=10,
            step=1,
            help="Anteil des Vertriebsleiters am Vertriebler-Kommissionstopf."
        ) / 100

    st.sidebar.subheader("🤝 Vertriebler Bonus (%)")

    bonus_map = {
        3: st.sidebar.slider(
            "3 Monate (%)",
            min_value=0,
            max_value=100,
            value=20,
            step=1,
            help="Bonus-Anteil bei 3 Monaten."
        ),
        6: st.sidebar.slider(
            "6 Monate (%)",
            min_value=0,
            max_value=100,
            value=30,
            step=1,
            help="Bonus-Anteil bei 6 Monaten."
        ),
        9: st.sidebar.slider(
            "9 Monate (%)",
            min_value=0,
            max_value=100,
            value=40,
            step=1,
            help="Bonus-Anteil bei 9 Monaten."
        ),
        12: st.sidebar.slider(
            "12 Monate (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=1,
            help="Bonus-Anteil bei 12 Monaten."
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
        help="Anteil des Vertrieblers an der Trading-Rendite."
    ) / 100

    j_profit_pct = st.sidebar.slider(
        "J Gewinn (%)",
        min_value=0,
        max_value=100,
        value=10,
        step=1,
        help="Anteil von Partei J an der Trading-Rendite."
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
        help="Rendite nach Handelsgebühren."
    )

    monthly_return = fee_return / 100 / 12
    months = [1, 3, 6, 9, 12]
    capital = investment * factor

    def calc_variant_1(month: int) -> dict:
        commission_total = capital * commission_rate * month

        bonus_pct = bonus_pct_for_month(month, bonus_map)
        vertriebler_bonus_pool = commission_total * bonus_pct

        vertriebsleiter_commission = vertriebler_bonus_pool * leader_pct if leader_active else 0.0
        vertriebler_commission = vertriebler_bonus_pool - vertriebsleiter_commission

        remaining_commission = commission_total - vertriebler_bonus_pool
        jj_commission = remaining_commission * 0.60
        j_commission = remaining_commission * 0.40

        value = capital * ((1 + monthly_return) ** month)
        profit_total = value - capital

        vertriebler_profit = profit_total * vertriebler_profit_pct
        j_profit = profit_total * j_profit_pct

        return {
            "Monat": month,
            "Kommission Gesamt": commission_total,
            "Bonus %": bonus_pct * 100,

            "Vertriebler Kommission": vertriebler_commission,
            "Vertriebsleiter Kommission": vertriebsleiter_commission,
            "J+J Kommission": jj_commission,
            "J Kommission": j_commission,

            "Gewinn Gesamt": profit_total,
            "Vertriebler Gewinn": vertriebler_profit,
            "J Gewinn": j_profit,

            "Vertriebler Gesamt": vertriebler_commission + vertriebler_profit,
            "J Gesamt": j_commission + j_profit,
        }

    df = pd.DataFrame([calc_variant_1(m) for m in months])
    row = df[df["Monat"] == duration].iloc[0]

    # =====================================================
    # ÜBERSICHT
    # =====================================================
    st.markdown(f"## 💰 Übersicht ({duration} Monate)")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🔵 Vertriebler",
            money(row["Vertriebler Gesamt"]),
            help="Komplette Einnahmen des Vertrieblers: Kommission + Gewinn."
        )
        render_breakdown_line("Kommission", row["Vertriebler Kommission"], COLOR_VERTRIEBLER)
        render_breakdown_line("Gewinn", row["Vertriebler Gewinn"], COLOR_GAIN)

    with col2:
        st.metric(
            "🔷 Vertriebsleiter",
            money(row["Vertriebsleiter Kommission"]),
            help="Kommissionsanteil des Vertriebsleiters."
        )
        render_breakdown_line("Kommission", row["Vertriebsleiter Kommission"], COLOR_LEADER)
        st.caption("Kein separater Gewinnanteil")

    with col3:
        st.metric(
            "🟠 J+J",
            money(row["J+J Kommission"]),
            help="Kommissionsanteil von J+J innerhalb des Resttopfs."
        )
        render_breakdown_line("Kommission", row["J+J Kommission"], COLOR_JJ)
        st.caption("Kein separater Gewinnanteil")

    with col4:
        st.metric(
            "🟢 J",
            money(row["J Gesamt"]),
            help="Komplette Einnahmen von J: Kommission + Gewinn."
        )
        render_breakdown_line("Kommission", row["J Kommission"], COLOR_J)
        render_breakdown_line("Gewinn", row["J Gewinn"], COLOR_GAIN)

    # =====================================================
    # KOMMISSIONEN VERTEILUNG
    # =====================================================
    st.markdown("### 📊 Kommissionen Verteilung")

    comm_df = df[[
        "Monat",
        "Vertriebler Kommission",
        "Vertriebsleiter Kommission",
        "J+J Kommission",
        "J Kommission"
    ]].copy()

    fig1 = px.bar(
        comm_df,
        x="Monat",
        y=[
            "Vertriebler Kommission",
            "Vertriebsleiter Kommission",
            "J+J Kommission",
            "J Kommission",
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

    st.plotly_chart(fig1, use_container_width=True, key="v1_commission_chart")

    # =====================================================
    # VERTRIEBLER EINNAHMEN
    # =====================================================
    st.markdown("### 📊 Vertriebler Einnahmen")

    vertrieb_df = df[[
        "Monat",
        "Vertriebler Kommission",
        "Vertriebler Gewinn",
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

    st.plotly_chart(fig2, use_container_width=True, key="v1_vertriebler_income_chart")

    # =====================================================
    # PIE CHARTS
    # =====================================================
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

        st.plotly_chart(pie_total, use_container_width=True, key="v1_pie_total")

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

        st.plotly_chart(pie_vertrieb, use_container_width=True, key="v1_pie_vertrieb")

    # =====================================================
    # ENTSCHEIDUNGSHILFE
    # =====================================================
    st.markdown("### 🔥 Welche Laufzeit lohnt sich für den Vertriebler?")

    decision_rows = []
    for choice in [3, 6, 9, 12]:
        tmp = calc_variant_1(choice)
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

    st.dataframe(
        decision_df.assign(
            Einnahmen=decision_df["Einnahmen"].round(0).astype(int),
            Bonus=decision_df["Bonus"].round(0).astype(int),
            Gewinn=decision_df["Gewinn"].round(0).astype(int),
            **{
                "Verpasst vs. beste Wahl": decision_df["Verpasst vs. beste Wahl"].round(0).astype(int)
            }
        ),
        use_container_width=True
    )

    heat_long = decision_df[["Laufzeit", "Einnahmen", "Verpasst vs. beste Wahl"]].melt(
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
            "Laufzeit": "Option",
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

    st.plotly_chart(fig_heat, use_container_width=True, key="v1_decision_heatmap")

    st.caption(
        "Grün zeigt die beste Entscheidung. Rot zeigt, was dem Vertriebler gegenüber der besten Wahl entgeht."
    )

# =========================================================
# VARIANTE 2
# =========================================================
else:
    st.sidebar.subheader("Variante 2")

    investment = st.sidebar.number_input(
        "Investor Kapital ($)",
        min_value=0,
        value=10000,
        step=1000,
        help="Kapital pro Investor in USD."
    )

    factor = st.sidebar.selectbox(
        "Zinsfaktor",
        [1.0, 1.5, 2.0],
        index=1,
        help="Faktor auf das Investor-Kapital."
    )

    commission_rate = st.sidebar.slider(
        "Kommission (%)",
        min_value=0.0,
        max_value=3.0,
        value=1.75,
        step=0.01,
        help="Monatliche Brutto-Kommission auf das investierte Kapital."
    ) / 100

    leader_active = st.sidebar.checkbox(
        "Vertriebsleiter aktivieren",
        value=False,
        help="Wenn aktiv, erhält der Vertriebsleiter einen Anteil aus dem Vertriebler-Anteil."
    )

    leader_pct = 0.0
    if leader_active:
        leader_pct = st.sidebar.slider(
            "Vertriebsleiter Anteil vom Vertriebler (%)",
            min_value=0,
            max_value=50,
            value=10,
            step=1,
            help="Anteil, der vom Vertriebler-Anteil an den Vertriebsleiter geht."
        ) / 100

    st.sidebar.subheader("🤝 Sub-IB / Master-IB")

    sub_ib_rebate_pct = st.sidebar.slider(
        "Laufende Kommissionsquote (%)",
        min_value=0,
        max_value=100,
        value=75,
        step=1,
        help="Wie viel Prozent der Brutto-Kommissionen als laufender Sub-IB / Master-IB Topf ankommen."
    ) / 100

    j4j_master_pct = st.sidebar.slider(
        "J4J / Master-IB Anteil (%)",
        min_value=20,
        max_value=40,
        value=25,
        step=1,
        help="Anteil von J4J innerhalb des laufenden Sub-IB / Master-IB Topfs. Der Rest geht an den Vertriebler."
    ) / 100

    vertriebler_sub_ib_pct = 1 - j4j_master_pct

    st.sidebar.subheader("📈 Gewinn")

    trading_return_after_fees = st.sidebar.slider(
        "Trading-Gewinn nach Gebühren (%)",
        min_value=10,
        max_value=50,
        value=25,
        step=1,
        help="Netto-Jahresgewinn. In Variante 2 geht der komplette Trading-Gewinn an J4J."
    ) / 100

    months = [1, 3, 6, 9, 12]
    capital = investment * factor
    monthly_return = trading_return_after_fees / 12

    def calc_variant_2(month: int) -> dict:
        gross_commission_total = capital * commission_rate * month

        # Laufender Pool, der über Sub-IB / Master-IB überhaupt verteilt wird
        sub_ib_pool_total = gross_commission_total * sub_ib_rebate_pct

        # Aufteilung dieses Pools:
        # Vertriebler = 60-80%
        # J4J = 20-40%
        vertriebler_pool_before_leader = sub_ib_pool_total * vertriebler_sub_ib_pct
        j4j_commission = sub_ib_pool_total * j4j_master_pct

        vertriebsleiter_commission = vertriebler_pool_before_leader * leader_pct if leader_active else 0.0
        vertriebler_commission = vertriebler_pool_before_leader - vertriebsleiter_commission

        # Trading-Gewinn komplett an J4J
        value = capital * ((1 + monthly_return) ** month)
        trading_profit_total = value - capital
        j4j_profit = trading_profit_total

        return {
            "Monat": month,
            "Kapital": capital,

            "Brutto Kommission Gesamt": gross_commission_total,
            "Laufender Pool": sub_ib_pool_total,

            "Vertriebler Kommission": vertriebler_commission,
            "Vertriebsleiter Kommission": vertriebsleiter_commission,
            "J4J Kommission": j4j_commission,

            "J4J Gewinn": j4j_profit,

            "Vertriebler Gesamt": vertriebler_commission,
            "Vertriebsleiter Gesamt": vertriebsleiter_commission,
            "J4J Gesamt": j4j_commission + j4j_profit,

            # Kumuliert = in dieser Logik ohnehin bereits kumulativ,
            # da pro Monat mit month multipliziert wird.
            "Kumuliert Vertriebler": vertriebler_commission,
            "Kumuliert Vertriebsleiter": vertriebsleiter_commission,
            "Kumuliert J4J": j4j_commission,
        }

    df2 = pd.DataFrame([calc_variant_2(m) for m in months])
    row2 = df2[df2["Monat"] == 12].iloc[0]

    # =====================================================
    # ÜBERSICHT
    # =====================================================
    st.markdown("## 💰 Übersicht Variante 2 (12 Monate)")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "🔵 Vertriebler",
            money(row2["Vertriebler Gesamt"]),
            help="Laufende Kommissionen des Vertrieblers aus dem Sub-IB Modell."
        )
        render_breakdown_line("Kommission", row2["Vertriebler Kommission"], COLOR_VERTRIEBLER)
        st.caption("Kein separater Trading-Gewinn")

    with col2:
        st.metric(
            "🔷 Vertriebsleiter",
            money(row2["Vertriebsleiter Gesamt"]),
            help="Anteil des Vertriebsleiters aus dem Vertriebler-Anteil."
        )
        render_breakdown_line("Kommission", row2["Vertriebsleiter Kommission"], COLOR_LEADER)
        st.caption("Kein separater Trading-Gewinn")

    with col3:
        st.metric(
            "🟠 J4J",
            money(row2["J4J Gesamt"]),
            help="J4J erhält in Variante 2 den Master-IB Anteil der laufenden Kommissionen plus den kompletten Trading-Gewinn."
        )
        render_breakdown_line("Kommission", row2["J4J Kommission"], COLOR_J4J)
        render_breakdown_line("Gewinn", row2["J4J Gewinn"], COLOR_GAIN)

    # =====================================================
    # KUMULIERTE KOMMISSIONEN
    # =====================================================
    st.markdown("### 📊 Kumulierte Kommissionen")

    cumulative_df = df2[[
        "Monat",
        "Kumuliert Vertriebler",
        "Kumuliert Vertriebsleiter",
        "Kumuliert J4J"
    ]].copy()

    fig_v2_comm = px.bar(
        cumulative_df,
        x="Monat",
        y=[
            "Kumuliert Vertriebler",
            "Kumuliert Vertriebsleiter",
            "Kumuliert J4J"
        ],
        text_auto=".0f",
        barmode="stack",
        color_discrete_map={
            "Kumuliert Vertriebler": COLOR_VERTRIEBLER,
            "Kumuliert Vertriebsleiter": COLOR_LEADER,
            "Kumuliert J4J": COLOR_J4J
        },
        labels={
            "value": "USD",
            "Monat": "Monat",
            "variable": "Partei",
        }
    )

    fig_v2_comm.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Monat: %{x}<br>Kumuliert: $%{y:,.0f}<extra></extra>",
        textfont_size=13
    )
    fig_v2_comm.update_layout(
        hovermode="x unified",
        legend_title_text="Partei",
        margin=dict(t=30, l=10, r=10, b=10),
    )

    st.plotly_chart(fig_v2_comm, use_container_width=True, key="v2_commission_chart")

    # =====================================================
    # EINNAHMEN NACH PARTEI
    # =====================================================
    st.markdown("### 📊 Gesamteinnahmen nach Partei (12 Monate)")

    totals_v2 = pd.DataFrame({
        "Partei": ["Vertriebler", "Vertriebsleiter", "J4J"],
        "Wert": [
            row2["Vertriebler Gesamt"],
            row2["Vertriebsleiter Gesamt"],
            row2["J4J Gesamt"]
        ]
    })

    fig_v2_total_bar = px.bar(
        totals_v2,
        x="Partei",
        y="Wert",
        text_auto=".0f",
        color="Partei",
        color_discrete_map={
            "Vertriebler": COLOR_VERTRIEBLER,
            "Vertriebsleiter": COLOR_LEADER,
            "J4J": COLOR_J4J
        },
        labels={
            "Wert": "USD",
            "Partei": "Partei"
        }
    )

    fig_v2_total_bar.update_traces(
        hovertemplate="<b>%{x}</b><br>Gesamt: $%{y:,.0f}<extra></extra>",
        textfont_size=13
    )
    fig_v2_total_bar.update_layout(
        showlegend=False,
        margin=dict(t=30, l=10, r=10, b=10),
    )

    st.plotly_chart(fig_v2_total_bar, use_container_width=True, key="v2_total_bar")

    # =====================================================
    # PIE CHARTS
    # =====================================================
    st.markdown("### 📊 Verteilungen")

    pie_col1, pie_col2 = st.columns(2)

    with pie_col1:
        st.markdown("**Gesamteinnahmen Verteilung**")

        pie_v2_total = px.pie(
            names=["Vertriebler", "Vertriebsleiter", "J4J"],
            values=[
                row2["Vertriebler Gesamt"],
                row2["Vertriebsleiter Gesamt"],
                row2["J4J Gesamt"]
            ],
            color=["Vertriebler", "Vertriebsleiter", "J4J"],
            color_discrete_map={
                "Vertriebler": COLOR_VERTRIEBLER,
                "Vertriebsleiter": COLOR_LEADER,
                "J4J": COLOR_J4J
            }
        )

        pie_v2_total.update_traces(
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Wert: $%{value:,.0f}<br>Anteil: %{percent}<extra></extra>"
        )
        pie_v2_total.update_layout(
            margin=dict(t=20, l=10, r=10, b=10),
            showlegend=True,
        )

        st.plotly_chart(pie_v2_total, use_container_width=True, key="v2_pie_total")

    with pie_col2:
        st.markdown("**J4J Einnahmen (Kommission vs Gewinn)**")

        pie_v2_j4j = px.pie(
            names=["Kommission", "Gewinn"],
            values=[
                row2["J4J Kommission"],
                row2["J4J Gewinn"]
            ],
            color=["Kommission", "Gewinn"],
            color_discrete_map={
                "Kommission": COLOR_J4J,
                "Gewinn": COLOR_GAIN
            }
        )

        pie_v2_j4j.update_traces(
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Wert: $%{value:,.0f}<br>Anteil: %{percent}<extra></extra>"
        )
        pie_v2_j4j.update_layout(
            margin=dict(t=20, l=10, r=10, b=10),
            showlegend=True,
        )

        st.plotly_chart(pie_v2_j4j, use_container_width=True, key="v2_pie_j4j")

    # =====================================================
    # ENTSCHEIDUNGSHILFE - MASTER IB SPLIT
    # =====================================================
    st.markdown("### 🔥 Wirkung des J4J / Master-IB Anteils")

    compare_rows = []
    for master_pct in [0.20, 0.25, 0.30, 0.35, 0.40]:
        vertriebler_share = 1 - master_pct

        gross_commission_total = capital * commission_rate * 12
        sub_ib_pool_total = gross_commission_total * sub_ib_rebate_pct

        vertriebler_before_leader = sub_ib_pool_total * vertriebler_share
        leader_val = vertriebler_before_leader * leader_pct if leader_active else 0.0
        vertriebler_val = vertriebler_before_leader - leader_val
        j4j_comm_val = sub_ib_pool_total * master_pct

        value_12 = capital * ((1 + monthly_return) ** 12)
        profit_12 = value_12 - capital
        j4j_total = j4j_comm_val + profit_12

        compare_rows.append({
            "J4J Anteil": f"{int(master_pct * 100)}%",
            "Vertriebler": round(vertriebler_val),
            "Vertriebsleiter": round(leader_val),
            "J4J": round(j4j_total),
        })

    compare_df = pd.DataFrame(compare_rows)

    st.dataframe(compare_df, use_container_width=True)

    fig_compare = px.bar(
        compare_df,
        x="J4J Anteil",
        y=["Vertriebler", "Vertriebsleiter", "J4J"],
        text_auto=True,
        barmode="stack",
        color_discrete_map={
            "Vertriebler": COLOR_VERTRIEBLER,
            "Vertriebsleiter": COLOR_LEADER,
            "J4J": COLOR_J4J
        },
        labels={
            "value": "USD",
            "variable": "Partei"
        }
    )
    fig_compare.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>J4J Anteil: %{x}<br>Wert: $%{y:,.0f}<extra></extra>",
        textfont_size=13
    )
    fig_compare.update_layout(
        hovermode="x unified",
        legend_title_text="Partei",
        margin=dict(t=30, l=10, r=10, b=10),
    )

    st.plotly_chart(fig_compare, use_container_width=True, key="v2_compare_chart")

    st.caption(
        "Variante 2: Der laufende Sub-IB / Master-IB Pool wird zwischen Vertriebler und J4J aufgeteilt. "
        "J4J erhält zusätzlich den kompletten Trading-Gewinn."
    )