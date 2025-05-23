import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_dynamic_filters import DynamicFilters
from io import BytesIO

# Load data
df = pd.read_excel('Sales_Data.xlsx')

# Convert Date to datetime if not already
if 'Date' in df.columns:
    df['Date'] = pd.to_datetime(df['Date'])
    # Extract Year, Month, Day, Weekday, Weekend
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month_name()
    df['Day'] = df['Date'].dt.day
    df['Weekday'] = df['Date'].dt.day_name()
    df['Weekend'] = df['Date'].dt.weekday >= 5  # Saturday or Sunday

# List of possible filter columns
possible_filters = ['Year', 'Month', 'Day', 'Weekday', 'Weekend', 'Channel', 'Region']
available_filters = [col for col in possible_filters if col in df.columns]

# Dashboard title and introduction
st.title('D2C Sales Dashboard')
st.markdown("Explore real-time sales trends and performance by region and channel.")

# Initialize dynamic filters
dynamic_filters = DynamicFilters(df, filters=available_filters)

# Display filters in the sidebar
with st.sidebar:
    st.write("Apply filters in any order:")
    dynamic_filters.display_filters(location='sidebar')

# Get filtered dataframe
filtered_df = dynamic_filters.filter_df()

# Export options
with st.sidebar:
    st.write("Export Options:")
    export_format = st.radio("Export as:", ["CSV", "Excel"])
    if st.button("Export Filtered Data"):
        if export_format == "CSV":
            st.download_button(
                label="Download CSV",
                data=filtered_df.to_csv(index=False).encode(),
                file_name="filtered_data.csv",
                mime="text/csv"
            )
        else:
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                filtered_df.to_excel(writer, index=False)
            st.download_button(
                label="Download Excel",
                data=buffer,
                file_name="filtered_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Helper function to display chart or table per section
def display_chart_or_table(df, group_col, value_col, title, chart_type='line', is_date=False):
    grouped = df.groupby(group_col)[value_col].sum().reset_index()
    grouped['Sales_M'] = grouped[value_col] / 1_000_000

    st.subheader(title)
    view = st.radio(f"View {title}:", ["Chart", "Table"], key=f"{title}_view", horizontal=True)
    
    if view == "Chart":
        if chart_type == 'line':
            fig = px.line(
                grouped,
                x=group_col,
                y='Sales_M',
                labels={'Sales_M': 'Sales (M)'},
                title=title
            )
        elif chart_type == 'bar':
            fig = px.bar(
                grouped,
                x=group_col,
                y='Sales_M',
                labels={'Sales_M': 'Sales (M)'},
                title=title
            )
        if is_date:
            fig.update_traces(hovertemplate=f'<b>{group_col}:</b> %{{x}}<br><b>Sales:</b> %{{y:.2f}} M')
        else:
            fig.update_traces(hovertemplate=f'<b>{group_col}:</b> %{{x}}<br><b>Sales:</b> %{{y:.2f}} M')
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Show table with all columns from original data
        cols_to_show = [c for c in filtered_df.columns if c != 'Weekend' or not pd.api.types.is_bool_dtype(filtered_df[c])]
        st.dataframe(filtered_df[cols_to_show], use_container_width=True)

# Sales Trend by Date
if 'Date' in filtered_df.columns:
    display_chart_or_table(filtered_df, 'Date', 'Sales', 'Sales Trend by Date', 'line', is_date=True)

# Sales by Region
if 'Region' in filtered_df.columns:
    display_chart_or_table(filtered_df, 'Region', 'Sales', 'Sales by Region', 'bar')

# Sales by Channel
if 'Channel' in filtered_df.columns:
    display_chart_or_table(filtered_df, 'Channel', 'Sales', 'Sales by Channel', 'bar')
