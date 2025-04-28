import setuptools

setuptools.setup(
    name="streamlit-datagrid",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Streamlit component for interactive DataGrid visualization",
    long_description="A custom Streamlit component that creates an interactive and editable data grid using Highcharts DataGrid",
    long_description_content_type="text/plain",
    url="",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "streamlit>=1.0.0",
        "pandas>=1.0.0",
        "numpy>=1.18.0",
        "jinja2>=2.11.0",
    ]
)