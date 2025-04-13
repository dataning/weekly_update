import streamlit as st
import numpy as np
import pandas as pd

# App title and header
st.title("Dummy Streamlit App")
st.header("Welcome to the Dummy App")

# Introduction or description
st.write("This is a simple Streamlit app demonstrating interactive features.")

# Generate some dummy data
def generate_data():
    # Create 10 random numbers between 1 and 100
    numbers = np.random.randint(1, 101, size=10)
    # Calculate the square of each number
    squares = numbers ** 2
    # Create a pandas DataFrame from the data
    data = pd.DataFrame({
        "Number": numbers,
        "Square": squares
    })
    return data

# Display the data for the first time
data = generate_data()
st.subheader("Random Data")
st.dataframe(data)

# Create a button that regenerates the data when clicked
if st.button("Generate New Data"):
    data = generate_data()
    st.dataframe(data)
    st.success("Data updated!")

# Optionally, you might want to include some plots
st.subheader("Data Visualization")
if st.checkbox("Show bar chart"):
    st.bar_chart(data.set_index("Number"))