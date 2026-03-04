import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.title("Carbon Intelligence Dashboard")

response = requests.get("http://localhost:8000/api/emissions/by-category")

if response.status_code == 200:
    data = response.json()

    df = pd.DataFrame(list(data.items()), columns=["Category", "Emissions"])

    st.subheader("Emissions by Category")

    fig = px.bar(df, x="Category", y="Emissions")

    st.plotly_chart(fig)

else:
    st.write("API not responding")
    