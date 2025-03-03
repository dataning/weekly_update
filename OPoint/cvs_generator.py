import pandas as pd

# Simulated fake data with 16 rows
data = [
    # FakeCorp entries
    {
        "Company": "FakeCorp",
        "News_Type": "Company News",
        "Article_Title": "FakeCorp Launches Revolutionary Product",
        "Source": "Tech Insider",
        "Date": "01 March 2025",
        "Content": ("FakeCorp has unveiled a revolutionary product designed to disrupt the industry and "
                    "set new market standards in technology.")
    },
    {
        "Company": "FakeCorp",
        "News_Type": "Competitor & Customer News",
        "Article_Title": "No news updates this week",
        "Source": None,
        "Date": None,
        "Content": None
    },
    # EcoTech entries
    {
        "Company": "EcoTech",
        "News_Type": "Company News",
        "Article_Title": "EcoTech Secures $2B in Funding",
        "Source": "Financial Times",
        "Date": "28 February 2025",
        "Content": ("EcoTech has secured $2 billion in funding to expand its renewable energy solutions and "
                    "enhance its global presence in sustainable technology.")
    },
    {
        "Company": "EcoTech",
        "News_Type": "Competitor & Customer News",
        "Article_Title": "No news updates this week",
        "Source": None,
        "Date": None,
        "Content": None
    },
    # GreenWave entries
    {
        "Company": "GreenWave",
        "News_Type": "Company News",
        "Article_Title": "GreenWave Expands into European Markets",
        "Source": "Bloomberg",
        "Date": "27 February 2025",
        "Content": ("GreenWave has announced its expansion into several key European markets, aiming to boost "
                    "its sustainable technology portfolio.")
    },
    {
        "Company": "GreenWave",
        "News_Type": "Competitor & Customer News",
        "Article_Title": "Major Partnership Announced with Global Firm",
        "Source": "Reuters",
        "Date": "27 February 2025",
        "Content": ("GreenWave has formed a major partnership with a global firm to accelerate the deployment "
                    "of sustainable technologies across multiple markets.")
    },
    # FutureTech entries
    {
        "Company": "FutureTech",
        "News_Type": "Company News",
        "Article_Title": "FutureTech Unveils AI-Powered Solutions",
        "Source": "Wired",
        "Date": "26 February 2025",
        "Content": ("FutureTech has introduced a new suite of AI-powered solutions designed to streamline operations "
                    "and improve customer experiences.")
    },
    {
        "Company": "FutureTech",
        "News_Type": "Competitor & Customer News",
        "Article_Title": "Market Challenges Ahead, Analysts Warn",
        "Source": "Reuters",
        "Date": "26 February 2025",
        "Content": ("Analysts warn that rising market challenges and global competition could impact FutureTech's "
                    "growth prospects in the coming quarters.")
    },
    # Next set of companies with additional fake data
    {
        "Company": "Innova Solutions",
        "News_Type": "Company News",
        "Article_Title": "Innova Solutions Merges with TechDynamics",
        "Source": "Forbes",
        "Date": "02 March 2025",
        "Content": ("Innova Solutions has merged with TechDynamics in a move aimed at consolidating their positions "
                    "in the tech industry and fostering innovation.")
    },
    {
        "Company": "Innova Solutions",
        "News_Type": "Competitor & Customer News",
        "Article_Title": "No news updates this week",
        "Source": None,
        "Date": None,
        "Content": None
    },
    {
        "Company": "Solaris Energy",
        "News_Type": "Company News",
        "Article_Title": "Solaris Energy Introduces New Solar Panels",
        "Source": "Energy Today",
        "Date": "01 March 2025",
        "Content": ("Solaris Energy has introduced a new range of solar panels that promise increased efficiency and "
                    "longer durability for residential and commercial installations.")
    },
    {
        "Company": "Solaris Energy",
        "News_Type": "Competitor & Customer News",
        "Article_Title": "Industry Leaders Meet at Annual Summit",
        "Source": "CNBC",
        "Date": "28 February 2025",
        "Content": ("Industry leaders, including Solaris Energy executives, met at the annual summit to discuss new "
                    "trends and challenges in the renewable energy sector.")
    },
    {
        "Company": "CyberNetix",
        "News_Type": "Company News",
        "Article_Title": "CyberNetix Enhances Cybersecurity Platform",
        "Source": "ZDNet",
        "Date": "02 March 2025",
        "Content": ("CyberNetix has rolled out major enhancements to its cybersecurity platform, aimed at providing "
                    "better protection against emerging threats in the digital landscape.")
    },
    {
        "Company": "CyberNetix",
        "News_Type": "Competitor & Customer News",
        "Article_Title": "No news updates this week",
        "Source": None,
        "Date": None,
        "Content": None
    }
]

# Create the DataFrame
df = pd.DataFrame(data)

# Display the DataFrame
print(df)