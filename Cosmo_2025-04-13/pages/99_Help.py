import streamlit as st
import theme

# Set page config and apply theme
theme.set_page_config()
theme.apply_theme()
theme.render_navbar()
theme.render_sidebar_js()

# Help page content

st.header("Getting Started")
st.markdown("Welcome to Gravity! Here's how to get started with our application:")
st.markdown("- Use the sidebar on the left to navigate between different tools")
st.markdown("- Click on the navigation links above to access different pages")
st.markdown("- Search for specific content using the search box")

st.header("Key Features")
st.subheader("News Search")
st.markdown("Find and analyze news articles from various sources. You can filter by date, source, and keywords.")

st.subheader("Newsletter Generator")
st.markdown("Create professional newsletters from your curated content with beautiful templates.")

st.subheader("Content Analysis")
st.markdown("Get insights from your content including sentiment analysis, keyword extraction, and more.")

st.header("Frequently Asked Questions")
with st.expander("How do I save my newsletter template?"):
    st.markdown("To save your newsletter template, click the 'Save' button in the Newsletter Generator tool. Your template will be stored for future use.")

with st.expander("Can I export my results?"):
    st.markdown("Yes, you can export your results in various formats including PDF, CSV, and HTML. Look for the export options in each tool.")

with st.expander("How do I share my newsletter?"):
    st.markdown("After creating your newsletter, click the 'Share' button to generate a shareable link or to download it for distribution.")

# Add more FAQ items as needed

# Add contact information
st.header("Need More Help?")
st.markdown("Contact our support team at support@gravity-app.com or visit our [help documentation](https://gravity-app.com/docs).")

# Add the footer
theme.render_footer()