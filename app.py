import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# -------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------
st.set_page_config(page_title="Sales Analytics Dashboard", layout="wide")

# -------------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------------
@st.cache_data
def load_data():
    return pd.read_csv("sales_data.csv", parse_dates=["Date"])

try:
    df = load_data()
except FileNotFoundError:
    st.error("⚠️ sales_data.csv not found in this folder.")
    st.stop()

# -------------------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------------------
st.sidebar.header("🔍 Filter Options")
regions = st.sidebar.multiselect("Select Region(s):", options=df["Region"].unique(), default=df["Region"].unique())
products = st.sidebar.multiselect("Select Product(s):", options=df["Product"].unique(), default=df["Product"].unique())
filtered_df = df[(df["Region"].isin(regions)) & (df["Product"].isin(products))]

# -------------------------------------------------------------
# HEADER
# -------------------------------------------------------------
st.title("📊 Sales Analytics Dashboard")
st.markdown("Interactive view of sales and profit performance with exportable PDF report.")

# -------------------------------------------------------------
# KPI VALUES
# -------------------------------------------------------------
total_sales = int(filtered_df["Sales"].sum())
total_profit = int(filtered_df["Profit"].sum())
avg_profit_margin = round((filtered_df["Profit"].sum() / filtered_df["Sales"].sum()) * 100, 2)

# -------------------------------------------------------------
# KPI SECTION (ANIMATED)
# -------------------------------------------------------------
html_code = f"""
<style>
.metric-card {{
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    background: white;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}}
.metric-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}}
.kpi {{
    font-size: 2rem;
    font-weight: 700;
    color: #1f2937;
}}
.sub {{
    font-size: 0.9rem;
    color: #6b7280;
}}
</style>

<div style="display:flex; justify-content:center; gap:1.5rem;">
    <div class="metric-card" style="background:#e0e7ff; width:200px;">
        💰<br><span id="salesCounter" class="kpi">0</span><br>
        <span class="sub">Total Sales</span>
    </div>
    <div class="metric-card" style="background:#d1fae5; width:200px;">
        📈<br><span id="profitCounter" class="kpi">0</span><br>
        <span class="sub">Total Profit</span>
    </div>
    <div class="metric-card" style="background:#fee2e2; width:200px;">
        📊<br><span id="marginCounter" class="kpi">0</span><br>
        <span class="sub">Avg Profit Margin</span>
    </div>
</div>

<script>
function animateValue(id, start, end, duration, suffix="") {{
  const obj = document.getElementById(id);
  let startTimestamp = null;
  const step = (timestamp) => {{
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    obj.innerHTML = Math.floor(progress * (end - start) + start).toLocaleString() + suffix;
    if (progress < 1) {{
      window.requestAnimationFrame(step);
    }}
  }};
  window.requestAnimationFrame(step);
}}

setTimeout(() => {{
    animateValue('salesCounter', 0, {total_sales}, 1200, '');
    animateValue('profitCounter', 0, {total_profit}, 1200, '');
    animateValue('marginCounter', 0, {avg_profit_margin}, 1200, '%');
}}, 300);
</script>
"""
components.html(html_code, height=230)

st.markdown("---")

# -------------------------------------------------------------
# CHARTS
# -------------------------------------------------------------
sales_trend = px.line(filtered_df, x="Date", y="Sales", color="Region", markers=True, template="plotly_white")
region_bar = px.bar(filtered_df.groupby("Region")[["Sales", "Profit"]].sum().reset_index(),
                    x="Region", y=["Sales", "Profit"], barmode="group",
                    template="plotly_white", color_discrete_sequence=["#6366f1", "#34d399"])
product_pie = px.pie(filtered_df, names="Product", values="Sales",
                     template="plotly_white", color_discrete_sequence=px.colors.qualitative.Set3)

st.subheader("📅 Sales Trend Over Time")
st.plotly_chart(sales_trend, use_container_width=True)
col1, col2 = st.columns(2)
with col1:
    st.subheader("🏙️ Sales vs Profit by Region")
    st.plotly_chart(region_bar, use_container_width=True)
with col2:
    st.subheader("📦 Sales Share by Product")
    st.plotly_chart(product_pie, use_container_width=True)

# -------------------------------------------------------------
# DOWNLOAD PDF SECTION
# -------------------------------------------------------------
import io
import plotly.io as pio

if st.button("Generate & Download PDF Report with Charts"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Sales Analytics Report", ln=True, align="C")
    pdf.ln(10)

    # Summary
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        0, 10,
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"Total Sales: ${total_sales:,}\n"
        f"Total Profit: ${total_profit:,}\n"
        f"Avg Profit Margin: {avg_profit_margin}%\n"
    )
    pdf.ln(5)

    # -----------------------
    # Add charts as images
    # -----------------------
    charts = {
        "Sales Trend Over Time": sales_trend,
        "Sales vs Profit by Region": region_bar,
        "Sales Share by Product": product_pie
    }

    for title, fig in charts.items():
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 8, title, ln=True)
        pdf.ln(2)

        # Convert Plotly figure to PNG in-memory
        img_bytes = pio.to_image(fig, format="png")

        # Use BytesIO to write into FPDF
        img_buffer = io.BytesIO(img_bytes)
        pdf.image(img_buffer, x=15, w=180)
        pdf.ln(10)

    # Footer
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, "Generated by Nagaraju K | Streamlit Sales Dashboard", align="C")

    # Save and offer download
    pdf_bytes = pdf.output(dest="S").encode("latin1")
    st.download_button(
        label="⬇️ Download PDF with Charts",
        data=pdf_bytes,
        file_name=f"Sales_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
    )
