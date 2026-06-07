import os
import math
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm

st.set_page_config(
    page_title="Growth and Carbon Decoupling",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_DIR, "data")
if not os.path.exists(os.path.join(DATA_DIR, "master_long.csv")):
    DATA_DIR = APP_DIR

PERIODS = [
    (1850, 1913, "1850–1913", "Industrialization and empire"),
    (1914, 1945, "1914–1945", "War and mobilization"),
    (1946, 1973, "1946–1973", "Postwar growth / Great Acceleration"),
    (1974, 2000, "1974–2000", "After the oil shocks"),
    (2001, 2022, "2001–2022", "Globalization and climate policy"),
]

EVENTS = [
    (1945, "Postwar growth", "The beginning of postwar mass production and consumption."),
    (1973, "First oil shock", "A major disruption of cheap fossil energy."),
    (1979, "Second oil shock", "A second energy shock reinforcing efficiency and energy security concerns."),
    (1990, "IPCC FAR", "The first IPCC Assessment Report brought climate change into global policy debate."),
    (1997, "Kyoto Protocol", "A binding framework for emissions reduction targets among industrialized countries."),
    (2001, "China joins WTO", "A turning point in global manufacturing and carbon-intensive production relocation."),
    (2008, "Financial crisis", "A temporary economic shock with short-term emissions effects."),
    (2015, "Paris Agreement", "Decarbonization became a shared global policy target."),
    (2020, "COVID-19 shock", "A temporary fall in emissions caused by disrupted economic activity."),
]

@st.cache_data
def load_data():
    master = pd.read_csv(os.path.join(DATA_DIR, "master_long.csv"))
    co2 = pd.read_csv(os.path.join(DATA_DIR, "co2_annual_long.csv"))
    maddison = pd.read_csv(os.path.join(DATA_DIR, "maddison_long.csv"))
    urban = pd.read_csv(os.path.join(DATA_DIR, "urbanization_long.csv"))
    return master, co2, maddison, urban

master, co2, maddison, urban = load_data()

# Basic derived variables
master = master.copy()
for col in ["co2_tonnes", "gdppc_2011_intl", "population_persons_est", "gdp_total_2011_intl_est", "urbanization_rate", "fossil_co2_tonnes_gcb", "consumption_co2_tonnes_gcb"]:
    if col in master.columns:
        master[col] = pd.to_numeric(master[col], errors="coerce")
master["co2_per_capita_tonnes"] = master["co2_tonnes"] / master["population_persons_est"]
master["carbon_intensity"] = master["co2_tonnes"] / master["gdp_total_2011_intl_est"]
master["fossil_intensity"] = master["fossil_co2_tonnes_gcb"] / master["gdp_total_2011_intl_est"]

COUNTRIES = sorted(master.loc[master["country"].notna(), "country"].drop_duplicates())
VARIABLES = {
    "CO₂ emissions (tonnes)": "co2_tonnes",
    "GDP per capita (2011 int'l $)": "gdppc_2011_intl",
    "Population (estimated persons)": "population_persons_est",
    "Urbanization rate (%)": "urbanization_rate",
    "Fossil CO₂ emissions, GCB (tonnes)": "fossil_co2_tonnes_gcb",
    "Consumption CO₂ emissions, GCB (tonnes)": "consumption_co2_tonnes_gcb",
    "CO₂ per capita (tonnes/person)": "co2_per_capita_tonnes",
    "Carbon intensity (CO₂/GDP)": "carbon_intensity",
    "Fossil intensity (fossil CO₂/GDP)": "fossil_intensity",
}

# Theme CSS: GCB-inspired, not copied
st.markdown("""
<style>
    .block-container {padding-top: 1.0rem; padding-bottom: 4rem;}
    section[data-testid="stSidebar"] {display: none !important;}
    .top-news {
        background:#f4c400; color:#050505; padding:.55rem 1.2rem; font-weight:600;
        margin:-1rem -1rem 0 -1rem;
    }
    .top-nav {
        background: linear-gradient(180deg, rgba(93,70,0,.98), rgba(64,47,0,.98));
        padding: 0;
        margin: 0 0 1rem 0;
        border-bottom: 1px solid rgba(255,255,255,.12);
        width: 100%;
        box-sizing: border-box;
    }
    div[data-testid="stRadio"] {
        background: linear-gradient(180deg, rgba(93,70,0,.98), rgba(64,47,0,.98));
        padding: .45rem 1.4rem .55rem 1.4rem;
        margin: 0 0 1.4rem 0;
        border-top: 1px solid rgba(255,255,255,.10);
        border-bottom: 1px solid rgba(0,0,0,.18);
        width: 100% !important;
        box-sizing: border-box;
        border-radius: 0;
    }
    div[data-testid="stRadio"] > div,
    div[data-testid="stRadio"] div[role="radiogroup"] {
        width: 100% !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        gap: 1.2rem !important;
        flex-wrap: nowrap !important;
    }
    div[data-testid="stRadio"] label {
        background: transparent !important;
        border: 0 !important;
        padding: .35rem .25rem !important;
        color: #fff6d7 !important;
        font-weight: 800;
        font-size: 1.05rem;
        white-space: nowrap !important;
    }
    div[data-testid="stRadio"] label p {color:#fff6d7 !important; font-size:1.05rem !important;}
    div[data-testid="stRadio"] label:hover p {color:#ffffff !important;}
    div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {display:none;}
    p, li {font-size: 1.03rem; line-height: 1.68;}
    .hero {
        border-radius: 0px 0px 18px 18px;
        padding: 5.5rem 3rem 4.8rem 3rem;
        margin-bottom: 1.4rem;
        background:
            linear-gradient(90deg, rgba(0,0,0,.78), rgba(88,62,0,.55), rgba(0,0,0,.76)),
            radial-gradient(circle at 15% 20%, rgba(255,211,80,.55), transparent 28%),
            radial-gradient(circle at 72% 35%, rgba(255,175,15,.35), transparent 35%),
            linear-gradient(135deg, #0c0b08 0%, #7a5d00 45%, #0a0907 100%);
        color: white;
        box-shadow: 0 12px 42px rgba(0,0,0,.18);
    }
    .hero .label {letter-spacing: .38em; text-transform: uppercase; color: #f9d66a; font-size: .84rem; font-weight: 700;}
    .hero h1 {font-size: 3.15rem; line-height: 1.05; margin: .7rem 0 .4rem 0; font-weight: 600;}
    .hero p {font-size: 1.15rem; max-width: 960px; color: #fff6d7;}
    .gold-card {
        padding: 1.2rem 1.3rem;
        border-radius: 14px;
        border: 1px solid rgba(142, 111, 0, .25);
        background: linear-gradient(180deg, #fffdf4, #ffffff);
        box-shadow: 0 8px 22px rgba(0,0,0,.05);
        min-height: 125px;
    }
    .gold-card h3 {margin-top:0; color:#6a5100;}
    .metric-card {
        border-left: 5px solid #a67c00;
        padding: 0.8rem 1rem;
        background: #fffaf0;
        border-radius: 10px;
    }
    h1, h2, h3 {letter-spacing: -0.02em;}
    div[data-testid="stMetricValue"] {color:#6a5100;}
    .small-note {font-size:.88rem;color:#666;}
</style>
""", unsafe_allow_html=True)

# Top navigation, inspired by public data-hub sites
st.markdown('<div class="top-nav">', unsafe_allow_html=True)
page = st.radio(
    "Navigation",
    ["Home", "About", "Data", "Correlation", "Regression", "Timeline", "Conclusion", "Sources & Method"],
    horizontal=True,
    label_visibility="collapsed",
)
st.markdown('</div>', unsafe_allow_html=True)


def hero(title, subtitle=""):
    st.markdown(f"""
    <div class="hero">
        <div class="label">Digital History Project</div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def add_event_lines(fig, years=None):
    years = years or [1945, 1973, 1979, 1990, 1997, 2001, 2008, 2015, 2020]
    for y in years:
        fig.add_vline(x=y, line_width=1, line_dash="dot", opacity=0.35)
    return fig


def period_label(year):
    for start, end, label, desc in PERIODS:
        if start <= year <= end:
            return label
    return "Other"


def clean_for_regression(df, y_col, x_cols):
    cols = ["year", "country", y_col] + x_cols
    d = df[cols].copy().dropna()
    for c in [y_col] + x_cols:
        d = d[pd.to_numeric(d[c], errors="coerce") > 0]
    return d


def run_ols(df, y_col, x_cols, log=True):
    d = clean_for_regression(df, y_col, x_cols)
    if len(d) < len(x_cols) + 5:
        return None, d
    y = np.log(d[y_col]) if log else d[y_col]
    X = pd.DataFrame(index=d.index)
    for c in x_cols:
        X[f"log_{c}" if log else c] = np.log(d[c]) if log else d[c]
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    return model, d


def format_big(v):
    if pd.isna(v):
        return "n/a"
    abs_v = abs(v)
    if abs_v >= 1e12: return f"{v/1e12:.2f}T"
    if abs_v >= 1e9: return f"{v/1e9:.2f}B"
    if abs_v >= 1e6: return f"{v/1e6:.2f}M"
    if abs_v >= 1e3: return f"{v/1e3:.2f}K"
    return f"{v:.2f}"

if page == "Home":
    hero("When Did Growth Begin to Leave Carbon Behind?", "A web-based digital narrative about economic growth, carbon emissions, fossil energy, and historical decoupling.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class="gold-card"><h3>Main question</h3><p>When, where, and why did economic growth begin to decouple from carbon emissions?</p></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="gold-card"><h3>Historical frame</h3><p>J. R. McNeill’s <em>Something New Under the Sun</em> frames twentieth-century growth as fossil-fuel-intensive environmental change.</p></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="gold-card"><h3>Argument</h3><p>Decoupling was not automatic. It was uneven, fragile, and shaped by crises, fossil fuel dependence, policy, and global restructuring.</p></div>""", unsafe_allow_html=True)

    st.markdown("## Project logic")
    st.write("""
    This site is designed as a digital history project, not just a statistical dashboard. The raw data are available in the Data page, but the main story is built through correlation, regression, historical events, and interpretation.
    """)
    st.markdown("""
    **Reading path:**
    1. Start with the long-run coupling between growth, population, fossil energy, and CO₂.
    2. Examine whether the relationship weakened after major historical turning points such as the 1970s oil shocks.
    3. Use regression coefficients as historical evidence for changing relationships, not as predictions.
    4. Connect the quantitative patterns to historical events and the final interpretation.
    """)

    latest = master[master["year"].eq(master["year"].max())]
    st.markdown("## Data overview")
    a,b,c,d = st.columns(4)
    st.caption("This overview simply tells the reader the scope of the dataset: how many countries/entities, years, rows, and CO₂ observations are available. It is not the argument itself; it is the data inventory behind the project.")
    a.metric("Countries/entities", f"{master['country'].nunique():,}")
    b.metric("Year range", f"{int(master['year'].min())}–{int(master['year'].max())}")
    c.metric("Rows", f"{len(master):,}")
    d.metric("CO₂ observations", f"{master['co2_tonnes'].notna().sum():,}")

elif page == "About":
    hero("About the Project", "Question, method, and historical argument.")
    st.markdown("""

    ## Main historical question
    **When, where, and why did economic growth begin to decouple from carbon emissions?**

    ## Working argument
    Decoupling should not be understood as the natural endpoint of modernization. It was a historically contingent process shaped by fossil-fuel dependence, the oil shocks, energy efficiency, industrial restructuring, climate governance, and global economic change.

    ## Method
    This project combines data visualization, correlation analysis, OLS regression, and historical timeline annotation. The goal is not to predict emissions, but to translate quantitative patterns into historical interpretation.
    """)

elif page == "Data":
    hero("The Data Hub", "Explore the historical data used in this project by country, variable, and time period.")
    st.markdown("### Select data")
    col1, col2, col3 = st.columns([1.2,1.5,1.2])
    with col1:
        countries = st.multiselect("Country / entity", COUNTRIES, default=[c for c in ["United States", "United Kingdom", "China", "South Korea"] if c in COUNTRIES])
    with col2:
        vars_selected = st.multiselect("Variables", list(VARIABLES.keys()), default=["CO₂ emissions (tonnes)", "GDP per capita (2011 int'l $)", "Population (estimated persons)"])
    with col3:
        year_min, year_max = int(master["year"].min()), int(master["year"].max())
        years = st.slider("Year range", year_min, year_max, (1850, min(2022, year_max)))

    df = master[(master["country"].isin(countries)) & (master["year"].between(years[0], years[1]))].copy()
    if not countries or not vars_selected:
        st.info("Choose at least one country and one variable.")
    else:
        for label in vars_selected:
            col = VARIABLES[label]
            if df[col].notna().sum() == 0:
                st.warning(f"No available values for {label} in the selected range.")
                continue
            fig = px.line(df, x="year", y=col, color="country", title=label, labels={"year":"Year", col:label, "country":"Country"})
            add_event_lines(fig)
            fig.update_layout(height=420, legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("### Raw data preview")
        show_cols = ["country", "code", "year"] + [VARIABLES[v] for v in vars_selected if VARIABLES[v] in df.columns]
        st.dataframe(df[show_cols].sort_values(["country","year"]), use_container_width=True, height=360)
        st.download_button("Download selected data as CSV", df[show_cols].to_csv(index=False).encode("utf-8"), "selected_decoupling_data.csv", "text/csv")

elif page == "Correlation":
    hero("Correlation Explorer", "Explore how growth, population, urbanization, fossil carbon, and CO₂ moved together historically.")
    st.markdown("""
    **What this page shows**

    This page is not meant to prove a final answer by itself. It is a place to visually inspect whether two historical variables moved together. For example, if GDP per capita and CO₂ emissions rise together, that suggests a strong coupling between economic growth and carbon emissions. If the trend becomes flatter in later periods, that may suggest that the relationship weakened over time.

    Correlation should be read carefully. A high correlation does not mean that one variable directly caused the other. In this project, correlation is used as a starting point for historical interpretation. The main question is not simply whether two numbers are related, but what kind of historical system made them move together.
    """)
    c1,c2,c3,c4 = st.columns([1.2,1.2,1,1])
    with c1:
        x_label = st.selectbox("X variable", list(VARIABLES.keys()), index=list(VARIABLES.keys()).index("GDP per capita (2011 int'l $") if "GDP per capita (2011 int'l $" in VARIABLES else 1)
    with c2:
        y_label = st.selectbox("Y variable", list(VARIABLES.keys()), index=list(VARIABLES.keys()).index("CO₂ emissions (tonnes)"))
    with c3:
        period_choice = st.selectbox("Historical period", ["All"] + [p[2] for p in PERIODS], index=0)
    with c4:
        log_axes = st.checkbox("Log axes", value=True)
    x_col, y_col = VARIABLES[x_label], VARIABLES[y_label]
    d = master.copy()
    d = d[d[x_col].notna() & d[y_col].notna() & (d[x_col] > 0) & (d[y_col] > 0)]
    d["period"] = d["year"].apply(period_label)
    if period_choice != "All":
        d = d[d["period"] == period_choice]
    if len(d) == 0:
        st.warning("No data are available for this selection.")
    else:
        fig = px.scatter(d, x=x_col, y=y_col, color="period", hover_name="country", hover_data=["year"],
                         trendline="ols", title=f"{x_label} vs {y_label}", labels={x_col:x_label, y_col:y_label})
        if log_axes:
            fig.update_xaxes(type="log")
            fig.update_yaxes(type="log")
        fig.update_layout(height=650, legend_title_text="Period")
        st.plotly_chart(fig, use_container_width=True)
        corr = d[[x_col,y_col]].corr().iloc[0,1]
        st.markdown(f"""
        **How to read this graph**

        Each dot represents an observation in the dataset. The trendline summarizes the overall direction of the relationship. If the line is steep, the two variables are moving together strongly. If it is flatter, the relationship is weaker. In this project, this matters because decoupling means that economic growth and CO₂ emissions become less tightly connected over time.

        For the current selection, the Pearson correlation is **{corr:.3f}**. A value close to 1 means that the two variables move together strongly, while a value closer to 0 means that the relationship is weaker. This number is useful as a descriptive signal, but it should not be treated as causal proof.
        """)

    st.markdown("""
    **Recommended checks**

    The most important relationship to examine is GDP per capita and CO₂ emissions, because this directly addresses the question of whether economic growth remained tied to carbon emissions. A second important relationship is fossil CO₂ and total CO₂ emissions, because it shows whether fossil carbon use is the mechanism behind emissions. Urbanization and population are supporting variables. They help explain the broader historical setting, but they are not the main definition of decoupling.
    """)

elif page == "Regression":
    hero("Regression Results", "Use OLS coefficients as historical evidence for how tightly growth and carbon were linked.")
    st.markdown("### Model")
    model_type = st.selectbox("Choose model", [
        "Basic: log(CO₂) ~ log(GDPpc) + log(Population)",
        "Urbanization: log(CO₂) ~ log(GDPpc) + log(Population) + Urbanization",
        "Fossil mechanism: log(CO₂) ~ log(GDPpc) + log(Population) + log(Fossil CO₂)",
    ])
    y_col = "co2_tonnes"
    if model_type.startswith("Basic"):
        x_cols = ["gdppc_2011_intl", "population_persons_est"]
    elif model_type.startswith("Urbanization"):
        x_cols = ["gdppc_2011_intl", "population_persons_est", "urbanization_rate"]
    else:
        x_cols = ["gdppc_2011_intl", "population_persons_est", "fossil_co2_tonnes_gcb"]
    st.latex(r"\log(CO_2) = \alpha + \beta_1 \log(GDPpc) + \beta_2 \log(Population) + \cdots + \epsilon")
    st.markdown("The most important number is the **GDP per capita coefficient**. Higher values mean growth was more tightly associated with emissions.")

    results=[]
    for start,end,label,desc in PERIODS:
        d=master[master["year"].between(start,end)].copy()
        model, used = run_ols(d, y_col, x_cols, log=True)
        if model is not None:
            coef_name = "log_gdppc_2011_intl"
            results.append({
                "period":label,
                "historical_context":desc,
                "n":int(model.nobs),
                "gdp_coef":model.params.get(coef_name, np.nan),
                "gdp_ci_low":model.conf_int().loc[coef_name,0] if coef_name in model.params.index else np.nan,
                "gdp_ci_high":model.conf_int().loc[coef_name,1] if coef_name in model.params.index else np.nan,
                "r2":model.rsquared,
            })
    res=pd.DataFrame(results)
    if res.empty:
        st.warning("Not enough data for this model. Try the basic model.")
    else:
        fig=px.bar(res, x="period", y="gdp_coef", error_y=res["gdp_ci_high"]-res["gdp_coef"], error_y_minus=res["gdp_coef"]-res["gdp_ci_low"],
                   hover_data=["historical_context","n","r2"], title="GDP per capita coefficient by historical period", labels={"period":"Period","gdp_coef":"GDPpc coefficient"})
        fig.update_layout(height=520)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("""
        **Interpretation:** If the coefficient falls after 1973, this supports the idea that the growth–carbon relationship weakened after the oil shocks. If it stays high, decoupling is weaker or incomplete.
        """)
        st.dataframe(res, use_container_width=True)

    st.markdown("## Model comparison for the full sample")
    compare_rows=[]
    models = {
        "Basic": ["gdppc_2011_intl", "population_persons_est"],
        "Urbanization": ["gdppc_2011_intl", "population_persons_est", "urbanization_rate"],
        "Fossil mechanism": ["gdppc_2011_intl", "population_persons_est", "fossil_co2_tonnes_gcb"],
    }
    for name, xs in models.items():
        mod, used = run_ols(master, y_col, xs, log=True)
        if mod is not None:
            compare_rows.append({"model":name, "n":int(mod.nobs), "GDPpc coefficient":mod.params.get("log_gdppc_2011_intl",np.nan), "R²":mod.rsquared})
    comp=pd.DataFrame(compare_rows)
    if not comp.empty:
        st.dataframe(comp, use_container_width=True)
        fig=px.bar(comp, x="model", y="GDPpc coefficient", hover_data=["n","R²"], title="How GDPpc coefficient changes by model")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Timeline":
    hero("Historical Timeline", "Major events that may have changed the relationship between growth, energy, and carbon emissions.")
    st.markdown("### Events")
    for year, name, desc in EVENTS:
        st.markdown(f"""
        <div class="metric-card"><strong>{year} — {name}</strong><br>{desc}</div>
        """, unsafe_allow_html=True)
        st.write("")

    st.markdown("### Events over the global CO₂ curve")
    world = master[master["country"].isin(["World"])]
    if world.empty:
        # fallback sum of entities by year, avoiding aggregates may be imperfect
        world = master.groupby("year", as_index=False)["co2_tonnes"].sum()
        world["country"]="World estimate from available entries"
    fig=px.line(world.dropna(subset=["co2_tonnes"]), x="year", y="co2_tonnes", title="CO₂ emissions with historical turning points", labels={"year":"Year","co2_tonnes":"CO₂ emissions"})
    add_event_lines(fig)
    fig.update_layout(height=520)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("The event markers are not explanations by themselves. They are prompts for historical interpretation: did the pattern bend before, during, or after the event?")

elif page == "Conclusion":
    hero("Conclusion", "The final interpretation of the project.")
    st.markdown("""
    **Core conclusion**

    The central argument of this project is that decoupling was not an automatic, universal, or complete result of modernization. Economic growth and CO₂ emissions were historically coupled because modern industrial growth depended heavily on fossil-carbon energy systems. In other words, GDP did not rise in isolation. It rose through coal, oil, gas, mass production, expanding transport systems, urbanization, and energy-intensive consumption. Before asking when growth and carbon began to separate, this project first shows that they were historically connected in the first place.

    **What the project argues**

    This project argues that the weakening relationship between growth and carbon emissions should be understood as a historical process rather than a simple policy indicator. If carbon intensity declines, that means the economy is producing less CO₂ per unit of GDP. This can be an early sign of relative decoupling. However, it does not automatically mean that total emissions are falling. A country or the world economy can become less carbon-intensive while still emitting more CO₂ in total. For that reason, the project distinguishes between relative decoupling and absolute decoupling. Absolute decoupling is the stricter case: GDP continues to rise while total CO₂ emissions fall.

    The project also argues that fossil carbon is the key mechanism connecting growth and emissions. GDP itself does not emit carbon. Growth becomes carbon-intensive when it depends on fossil fuels and fossil-based energy systems. This is why fossil carbon usage is important in the analysis. If the relationship between GDP and CO₂ weakens after fossil carbon is considered, that suggests that the deeper historical issue is not growth in the abstract, but the fossil-energy structure through which growth was produced.

    The historical timeline matters because the growth-carbon relationship did not change in a vacuum. The postwar Great Acceleration intensified the connection between mass economic growth and fossil energy. The oil shocks of the 1970s exposed the vulnerability of cheap fossil-fuel dependence and encouraged energy efficiency and restructuring in some economies. Later, climate agreements and global supply chains changed how emissions were measured, governed, and sometimes displaced. These events do not explain everything by themselves, but they provide turning points through which the data can be interpreted historically.

    **Final interpretation**

    The deeper conclusion is that decoupling should not be treated as the natural endpoint of economic development. It is better understood as a fragile and uneven historical process shaped by fossil-fuel dependence, energy crises, policy choices, industrial restructuring, and global economic change. The question is therefore not only whether GDP grew while CO₂ declined. The more important historical question is how growth itself was reorganized away from fossil carbon, or why it remained dependent on it.
    """)

elif page == "Sources & Method":
    hero("Sources & Method", "Data sources used in this project.")
    st.markdown("""
    ## Data sources

    - **Maddison Project Database 2023**: GDP per capita and population estimates.
    - **Our World in Data CO₂ dataset**: annual CO₂ emissions by country/entity.
    - **Global Carbon Budget 2025**: territorial and consumption-based fossil carbon emissions.
    - **UN World Urbanization Prospects**: urbanization and population estimates.
    """)
