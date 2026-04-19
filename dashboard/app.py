import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from google.cloud import bigquery
import os
from dotenv import load_dotenv

# Load env
load_dotenv()
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
BQ_DATASET_NAME = os.getenv('BQ_DATASET_NAME', 'claude_economic_index')

st.set_page_config(page_title="Claude AI Economic Index", layout="wide")

# --- Theme / CSS Enhancement ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Premium Metric Card Styling */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #B5D4F4 !important; /* Lighter blue for prominence */
    }
    
    div[data-testid="metric-container"] {
        background: rgba(24, 95, 165, 0.15) !important; /* Visible Blue Fill */
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border-color: #185FA5;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0E1117;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Animation for charts */
    .element-container {
        animation: fadeIn 0.8s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Aggressive Global Layout Compression */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    [data-testid="stVerticalBlock"] > div {
        gap: 0.5rem !important;
    }
    
    [data-testid="stHeader"] {
        display: none !important;
    }
    
    .stHeader {
        margin-top: -2.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

COLORS = {
    'primary_blue': '#185FA5',
    'secondary_teal': '#1D9E75',
    'accent_amber': '#BA7517',
    'neutral_gray': '#888780',
    'success_green': '#3B6D11',
    'danger_coral': '#D85A30'
}

# Set Plotly default template
px.defaults.template = "plotly_dark"
pio.templates.default = "plotly_dark"

# --- Shared Utilities ---
@st.cache_data(ttl=3600)
def load_bq_table(table_name):
    client = bigquery.Client(project=GCP_PROJECT_ID)
    query = f"SELECT * FROM `{GCP_PROJECT_ID}.{BQ_DATASET_NAME}.{table_name}`"
    df = client.query(query).to_dataframe()
    return df.drop_duplicates() # Fix duplicate row issue from pipeline

@st.cache_data(ttl=3600)
def fetch_silver_query(where_clause):
    client = bigquery.Client(project=GCP_PROJECT_ID)
    query = f"SELECT * FROM `{GCP_PROJECT_ID}.{BQ_DATASET_NAME}.silver_aei` WHERE {where_clause}"
    return client.query(query).to_dataframe()

def truncate_label(text, max_chars=40):
    if not isinstance(text, str): return text
    return text[:max_chars] + "..." if len(text) > max_chars else text

def wrap_label(text, width=60):
    if not isinstance(text, str): return text
    import textwrap
    return "<br>".join(textwrap.wrap(text, width=width))

# --- Page: Geographic Analysis ---
def show_geo():
    st.header("Global Claude AI Usage — Geographic Distribution")
    
    df_map = load_bq_table("gold_chart1_world_heatmap")
    df_drill = load_bq_table("gold_chart2_state_drilldown")
    
    if df_map.empty or df_drill.empty:
        st.warning("Geographic data unavailable.")
        return

    total_countries = df_map['geo_id'].nunique()
    top_country = df_map.loc[df_map['usage_pct'].idxmax()]
    gt_1pct = len(df_map[df_map['usage_pct'] > 1.0])
    subnational_regions = df_drill['geo_id'].nunique()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Countries", total_countries)
    c2.metric("Total Subnational Regions", subnational_regions)
    c3.metric("Top country by usage", f"{top_country['country_name']} ({top_country['usage_pct']:.1f}%)")
    c4.metric("Country with share >1%", gt_1pct)
    
    # --- Manual Hierarchy Construction ---
    df_map['continent_name'] = df_map['continent_name'].fillna('Unknown')
    df_map['country_name'] = df_map['country_name'].fillna('Unknown')
    
    cont_totals = df_map.groupby('continent_name')['usage_pct'].sum().reset_index()
    global_total = cont_totals['usage_pct'].sum()
    
    cont_order = ['North America', 'South America', 'Africa', 'Oceania', 'Asia', 'Europe', 'Unknown']
    cont_totals['rank'] = cont_totals['continent_name'].map({c: i for i, c in enumerate(cont_order)}).fillna(99)
    cont_totals = cont_totals.sort_values('rank')

    ids, labels, parents, values = [], [], [], []
    
    # Add Root
    ids.append("Global")
    labels.append("Global Usage")
    parents.append("")
    values.append(global_total)
    
    for _, row in cont_totals.iterrows():
        c_name = row['continent_name']
        ids.append(c_name)
        labels.append(c_name)
        parents.append("Global")
        values.append(row['usage_pct'])
        
        countries = df_map[df_map['continent_name'] == c_name].sort_values('usage_pct', ascending=False)
        for _, c_row in countries.iterrows():
            ids.append(f"{c_name}_{c_row['geo_id']}")
            labels.append(c_row['country_name'])
            parents.append(c_name)
            values.append(c_row['usage_pct'])

    import plotly.graph_objects as go
    fig1 = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values,
        branchvalues="total",
        textinfo="label+value", 
        texttemplate="<b>%{label}</b><br>%{value:.1f}%",
        marker=dict(
            colors=values, 
            colorscale=[[0, '#B5D4F4'], [1, '#042C53']]
        ),
        tiling=dict(packing='binary', pad=2),
        sort=False 
    ))
    
    fig1.update_traces(
        textinfo="label+value",
        texttemplate="<b>%{label}</b><br>%{value:.1f}%"
    )
    
    fig1.update_layout(
        height=450, 
        margin=dict(t=10, l=10, r=10, b=10),
        uniformtext=dict(minsize=8, mode='hide')
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Drilldown
    c_drill1, c_drill2 = st.columns([1, 2])
    with c_drill1:
        drill_countries = sorted(df_drill['country_name'].dropna().unique().tolist())
        default_idx = drill_countries.index("United States") if "United States" in drill_countries else 0
        selected_country = st.selectbox("Subnational Selection", drill_countries, index=default_idx)
    
    drill_filtered = df_drill[df_drill['country_name'] == selected_country].sort_values('usage_pct', ascending=True).tail(15)
    
    fig2 = px.bar(
        drill_filtered, x='usage_pct', y='region_code', orientation='h',
        color_discrete_sequence=[COLORS['primary_blue']],
        text='usage_pct',
        height=320 # Squeezed height
    )
    fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig2.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        xaxis_title=None, yaxis_title=None
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Move narrative text to the bottom
    st.markdown("---")
    st.markdown("### Regional Insights")
    st.markdown("""
    > The United States, India, Japan, the United Kingdom, and South Korea account for the largest shares of global Claude usage. 
    > Usage is strongly correlated with GDP per capita — wealthier countries show higher per-capita AI adoption.
    > 
    > Within countries, usage is often concentrated in tech-heavy regions with high concentrations of knowledge workers 
    > (such as California, New York, and Washington), significantly exceeding national averages.
    """)

# --- Page: Time & Productivity ---
def show_time():
    st.header("AI-Driven Productivity Gains — Time Saved Across Task Types")
    st.markdown("""
    Estimates of how long tasks take with and without AI assistance, 
    derived from Claude's own assessment of each conversation. 
    All times are in hours.
    """)
    
    df_time = load_bq_table("gold_chart3_time_saved")
    if not df_time.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg baseline time (hrs)", f"{df_time['human_only_time_hrs'].mean():.2f}")
        c2.metric("Avg time with AI (hrs)", f"{df_time['human_with_ai_time_hrs'].mean():.2f}")
        c3.metric("Avg time saved (hrs)", f"{df_time['time_saved_hrs'].mean():.2f}")
        c4.metric("Avg time reduction (%)", f"{df_time['pct_time_saved'].mean():.1f}%")
        
        st.markdown("---")
        st.markdown("""
        ### Analysis: The Productivity Multiplier
        The data reveals a stark contrast in cognitive labor requirements. Claude dramatically reduces the time 
        required for complex, research-intensive, and writing-heavy tasks. Software development and technical 
        documentation — which might take a professional several hours unassisted — are completed in a fraction 
        of the time with AI support.
        """)

        # Round and Wrap
        top_20 = df_time.sort_values('time_saved_hrs', ascending=False).head(20).copy()
        top_20['human_only_time_hrs'] = top_20['human_only_time_hrs'].round(2)
        top_20['human_with_ai_time_hrs'] = top_20['human_with_ai_time_hrs'].round(2)
        top_20['wrapped_task'] = top_20['onet_task'].apply(lambda x: wrap_label(x, width=70))
        
        with st.container(height=600):
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=top_20['wrapped_task'],
                x=top_20['human_only_time_hrs'],
                name='Baseline (Human Only)',
                orientation='h',
                marker=dict(color=COLORS['secondary_teal']),
                text=top_20['human_only_time_hrs'].apply(lambda x: f"{x:.1f}h"),
                textposition='outside'
            ))
            fig.add_trace(go.Bar(
                y=top_20['wrapped_task'],
                x=top_20['human_with_ai_time_hrs'],
                name='With AI Assistance',
                orientation='h',
                marker=dict(color=COLORS['primary_blue']),
                text=top_20['human_with_ai_time_hrs'].apply(lambda x: f"{x:.1f}h"),
                textposition='outside'
            ))
            fig.update_layout(
                barmode='group', 
                title="Top 20 Tasks by Absolute Time Saved (Hrs)",
                xaxis_title="Hours",
                yaxis={'categoryorder':'total ascending', 'automargin': True},
                margin=dict(l=450, r=80, t=40, b=40),
                height=1200,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.info("💡 Note: Tasks are sorted by total hours saved. High-complexity technical tasks show the largest absolute gains.")
    else:
        st.warning("Time Saved data is building or unavailable.")

# --- Page: Education & Skills ---
def show_edu():
    st.header("Education vs. AI Knowledge — The Skill Gap")
    st.markdown("""
    This page visualizes the 'Education Delta' — the difference between the human certifications 
    formally required for a task and the knowledge level Claude demonstrates. 
    A **positive gap** indicates Claude exceeds parity; a **negative gap** shows where human 
    specialization still holds a knowledge lead.
    """)
    
    df_edu = load_bq_table("gold_chart4_education_scatter")
    if not df_edu.empty:
        df_edu['onet_task_short'] = df_edu['onet_task'].apply(truncate_label)
        
        # Calculate derived counts
        ai_exceeds = df_edu[df_edu['education_comparison'] == 'AI exceeds']
        human_exceeds = df_edu[df_edu['education_comparison'] == 'Human exceeds']
        comparable = df_edu[df_edu['education_comparison'] == 'Comparable']
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg AI Knowledge Lead", f"+{(df_edu['ai_education_years_mean'] - df_edu['human_education_years_mean']).mean():.1f} yrs")
        c2.metric("AI Specialization Lead", f"{len(ai_exceeds)} tasks")
        c3.metric("Human Specialization Lead", f"{len(human_exceeds)} tasks")
        c4.metric("AI-Human Comparable", f"{len(comparable)} tasks")
        
        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["🏆 Skill Gap Leaders", "🔋 Dominant Use Cases", "🔍 Task Data Hub"])

        with tab1:
            st.subheader("Where Claude Exceeds vs. Trails Human Education Requirements")
            st.info("Positive delta (Blue) = AI exceeds required human education. Negative delta (Coral) = Human exceeds AI level.")
            
            # --- AI Leads ---
            st.markdown("#### 🏆 Top 20 AI Knowledge Leads")
            with st.container(height=330): # Reduced height for single pageview
                top_ai = df_edu.sort_values('ai_vs_human_delta', ascending=False).head(20).copy()
                top_ai['ai_vs_human_delta'] = top_ai['ai_vs_human_delta'].round(2) # Force rounding
                top_ai['wrapped_task'] = top_ai['onet_task'].apply(lambda x: wrap_label(x, width=70))
                
                fig_top = px.bar(top_ai, x='ai_vs_human_delta', y='wrapped_task', orientation='h',
                                 labels={'ai_vs_human_delta': 'Education Gap (Yrs)', 'wrapped_task': 'Work Task'},
                                 color_discrete_sequence=[COLORS['primary_blue']],
                                 text='ai_vs_human_delta', # Added text label
                                 height=1200) 
                fig_top.update_layout(
                    yaxis={'categoryorder':'total ascending', 'automargin': True},
                    margin=dict(l=450, r=60, t=10, b=10), # Slight more right margin for text
                    font=dict(size=12)
                )
                fig_top.update_traces(texttemplate='%{text:+.1f} yrs', textposition='outside')
                st.plotly_chart(fig_top, use_container_width=True)

            # --- Human Leads ---
            st.markdown("#### 🏹 Top 20 Human Knowledge Leads")
            with st.container(height=330):
                top_human = df_edu.sort_values('ai_vs_human_delta', ascending=True).head(20).copy()
                top_human['ai_vs_human_delta'] = top_human['ai_vs_human_delta'].round(2) # Force rounding
                top_human['wrapped_task'] = top_human['onet_task'].apply(lambda x: wrap_label(x, width=70))
                
                fig_bot = px.bar(top_human, x='ai_vs_human_delta', y='wrapped_task', orientation='h',
                                 labels={'ai_vs_human_delta': 'Education Gap (Yrs)', 'wrapped_task': 'Work Task'},
                                 color_discrete_sequence=[COLORS['danger_coral']],
                                 text='ai_vs_human_delta', # Added text label
                                 height=1200)
                fig_bot.update_layout(
                    yaxis={'categoryorder':'total descending', 'automargin': True},
                    margin=dict(l=450, r=60, t=10, b=10),
                    font=dict(size=12)
                )
                fig_bot.update_traces(texttemplate='%{text:+.1f} yrs', textposition='outside')
                st.plotly_chart(fig_bot, use_container_width=True)

        with tab2:
            st.subheader("Education Gap for Most Frequent Tasks")
            st.markdown("Analyzing the skill gap for the tasks that appear most frequently in the dataset.")
            
            with st.container(height=700): # Scrollable container for the larger set of tasks
                top_usage = df_edu.sort_values('task_usage_pct', ascending=False).head(25).copy()
                top_usage['wrapped_task'] = top_usage['onet_task'].apply(lambda x: wrap_label(x, width=70))
                
                fig_usage = go.Figure()
                fig_usage.add_trace(go.Bar(
                    name='Human Education Req',
                    y=top_usage['wrapped_task'],
                    x=top_usage['human_education_years_mean'],
                    orientation='h',
                    marker_color=COLORS['secondary_teal'],
                    text=top_usage['human_education_years_mean'].apply(lambda x: f"{x:.1f} yrs"),
                    textposition='outside'
                ))
                fig_usage.add_trace(go.Bar(
                    name='AI Demonstrated Knowledge',
                    y=top_usage['wrapped_task'],
                    x=top_usage['ai_education_years_mean'],
                    orientation='h',
                    marker_color=COLORS['primary_blue'],
                    text=top_usage['ai_education_years_mean'].apply(lambda x: f"{x:.1f} yrs"),
                    textposition='outside'
                ))
                fig_usage.update_layout(
                    barmode='group',
                    xaxis_title="Equivalent Years of Education",
                    yaxis={'categoryorder':'total ascending', 'automargin': True},
                    margin=dict(l=450, r=80, t=10, b=10), # More room for side labels
                    height=1500, # Tall chart for 25 wrapped bar groups
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_usage, use_container_width=True)

        with tab3:
            st.subheader("Detailed Task Taxonomy")
            st.markdown("Search and filter the full analysis of 3,000+ tasks.")
            
            # Search filter
            search_query = st.text_input("Search for a specific task...", "")
            df_display = df_edu.copy()
            if search_query:
                df_display = df_display[df_display['onet_task'].str.contains(search_query, case=False)]
            
            # Format and show dataframe
            df_formatted = df_display[[
                'onet_task', 'human_education_years_mean', 'ai_education_years_mean', 
                'ai_vs_human_delta', 'education_comparison'
            ]].rename(columns={
                'onet_task': 'Work Task',
                'human_education_years_mean': 'Human Edu (Yrs)',
                'ai_education_years_mean': 'AI Knowledge (Yrs)',
                'ai_vs_human_delta': 'Gap',
                'education_comparison': 'Status'
            })
            
            st.dataframe(
                df_formatted.sort_values('Gap', ascending=False),
                column_config={
                    "Human Edu (Yrs)": st.column_config.NumberColumn(format="%.1f"),
                    "AI Knowledge (Yrs)": st.column_config.NumberColumn(format="%.1f"),
                    "Gap": st.column_config.NumberColumn(format="%.1f 🎓"),
                    "Work Task": st.column_config.TextColumn(width="large")
                },
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("Education data unavailable.")

# --- Navigation & Sidebar Construction ---
# Define the pages
pg1 = st.Page(show_geo, title="Geographic Analysis", icon="🌍", default=True)
pg2 = st.Page(show_time, title="Time & Productivity", icon="⏱️")
pg3 = st.Page(show_edu, title="Education & Skills", icon="🎓")

# Setup navigation (hidden handles manual placement)
pg = st.navigation([pg1, pg2, pg3], position="hidden")

# Now build the sidebar in the requested order
st.sidebar.title("Claude AI Economic Index")
st.sidebar.info("📅 **Survey date:** Feb 5–12, 2026")
st.sidebar.markdown("---")

# Manually trigger the navigation link UI in the sidebar
with st.sidebar:
    st.page_link(pg1, label="Geographic Analysis", icon="🌍")
    st.page_link(pg2, label="Time & Productivity", icon="⏱️")
    st.page_link(pg3, label="Education & Skills", icon="🎓")

# Run the selected page
pg.run()
