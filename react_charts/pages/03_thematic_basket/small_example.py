import streamlit as st
import pandas as pd
import json
import random
import streamlit.components.v1 as components

# Set page configuration
st.set_page_config(
    page_title="S&P 500 Companies Treemap",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add title and description
st.title("S&P 500 Companies Treemap")
st.markdown("""
This visualization shows S&P 500 companies grouped by sector and industry. 
The size of each block represents market capitalization, while the color indicates 1-month performance.
""")

# Generate sample data with a consistent three-level hierarchy
def generate_sample_data():
    sectors = [
        'Technology', 'Financial', 'Consumer Cyclical', 'Communication Services',
        'Healthcare', 'Consumer Defensive', 'Industrials', 'Real Estate',
        'Energy', 'Utilities', 'Basic Materials'
    ]
    
    industries_by_sector = {
        'Technology': ['Software', 'Semiconductors', 'Hardware', 'IT Services'],
        'Financial': ['Banks', 'Insurance', 'Asset Management', 'Fintech'],
        'Consumer Cyclical': ['Retail', 'Automotive', 'Leisure', 'Apparel'],
        'Communication Services': ['Media', 'Telecom', 'Entertainment', 'Social Media'],
        'Healthcare': ['Pharmaceuticals', 'Medical Devices', 'Healthcare Providers', 'Biotech'],
        'Consumer Defensive': ['Food', 'Household Products', 'Personal Care', 'Retail Defensive'],
        'Industrials': ['Aerospace', 'Machinery', 'Transportation', 'Business Services'],
        'Real Estate': ['Residential REITs', 'Commercial REITs', 'Office REITs', 'Industrial REITs'],
        'Energy': ['Oil & Gas Production', 'Oil & Gas Storage', 'Renewable Energy', 'Energy Services'],
        'Utilities': ['Electric Utilities', 'Water Utilities', 'Gas Utilities', 'Multi-Utilities'],
        'Basic Materials': ['Chemicals', 'Metals & Mining', 'Paper & Forest', 'Industrial Gases']
    }
    
    companies = []
    for sector, industries in industries_by_sector.items():
        for industry in industries:
            # Generate 3-5 companies per industry
            for i in range(random.randint(3, 5)):
                symbol = f"{industry[:2]}{i}".upper()
                name = f"{industry} Corp {i}"
                market_cap = random.randint(100, 1000) * 1e8
                old_price = random.randint(50, 500)
                new_price = old_price * (1 + random.uniform(-0.15, 0.15))
                performance = 100 * (new_price - old_price) / old_price
                
                # Add more metrics for the enhanced tooltip
                pe_ratio = round(random.uniform(10, 40), 2)
                dividend_yield = round(random.uniform(0, 5), 2)
                revenue_growth = round(random.uniform(-10, 30), 2)
                debt_to_equity = round(random.uniform(0.1, 2.0), 2)
                ebitda_margin = round(random.uniform(5, 40), 2)
                
                companies.append({
                    'Symbol': symbol,
                    'Name': name,
                    'Sector': sector,
                    'Industry': industry,
                    'Market Cap': market_cap,
                    'Price': new_price,
                    'OldPrice': old_price,
                    'Performance': performance,
                    'PE Ratio': pe_ratio,
                    'Dividend Yield': dividend_yield,
                    'Revenue Growth': revenue_growth,
                    'Debt to Equity': debt_to_equity,
                    'EBITDA Margin': ebitda_margin
                })
    
    df = pd.DataFrame(companies)
    return df, sectors, industries_by_sector

# Format for Highcharts treemap
def format_for_highcharts(df, sectors, industries_by_sector):
    data = []
    
    # Add sector nodes (level 1)
    for sector in sectors:
        sector_df = df[df['Sector'] == sector]
        if not sector_df.empty:
            sector_perf = sector_df['Performance'].mean()
            # Calculate sector-level metrics
            avg_pe = sector_df['PE Ratio'].mean()
            avg_dividend = sector_df['Dividend Yield'].mean()
            avg_growth = sector_df['Revenue Growth'].mean()
            
            # Force convert all values to strings to ensure proper rendering in tooltip
            data.append({
                'id': sector,
                'name': sector.upper(),
                'colorValue': sector_perf,
                # Use string values for everything to avoid JavaScript type conversion issues
                'custom': {
                    'fullName': sector,
                    'performance': f"{sector_perf:+.2f}%",
                    'avgPE': f"{round(avg_pe, 2)}",
                    'avgDividend': f"{round(avg_dividend, 2)}%",
                    'avgGrowth': f"{round(avg_growth, 2)}%",
                    'companyCount': f"{len(sector_df)}",
                    'totalMarketCap': f"${sector_df['Market Cap'].sum()/1e9:.1f}B"
                }
            })
    
    # Add industry nodes (level 2) with calculated performance
    for sector in sectors:
        sector_industries = df[df['Sector'] == sector]['Industry'].unique()
        for industry in sector_industries:
            industry_df = df[(df['Sector'] == sector) & (df['Industry'] == industry)]
            if not industry_df.empty:
                industry_perf = industry_df['Performance'].mean()
                # Calculate industry-level metrics
                avg_pe = industry_df['PE Ratio'].mean()
                avg_dividend = industry_df['Dividend Yield'].mean()
                avg_growth = industry_df['Revenue Growth'].mean()
                avg_debt = industry_df['Debt to Equity'].mean()
                
                data.append({
                    'id': f"{sector}_{industry}",
                    'name': industry.upper(),
                    'parent': sector,
                    'colorValue': industry_perf,
                    'custom': {
                        'fullName': industry,
                        'sector': sector,
                        'performance': f"{industry_perf:+.2f}%",
                        'avgPE': f"{round(avg_pe, 2)}",
                        'avgDividend': f"{round(avg_dividend, 2)}%",
                        'avgGrowth': f"{round(avg_growth, 2)}%",
                        'avgDebt': f"{round(avg_debt, 2)}",
                        'companyCount': f"{len(industry_df)}",
                        'totalMarketCap': f"${industry_df['Market Cap'].sum()/1e9:.1f}B"
                    }
                })
    
    # Add company nodes (level 3)
    for _, row in df.iterrows():
        perf = row['Performance']
        perf_str = f"{perf:+.2f}%"
        data.append({
            'name': row['Symbol'],
            'id': row['Symbol'],
            'value': row['Market Cap'],
            'parent': f"{row['Sector']}_{row['Industry']}",
            'colorValue': perf,
            'custom': {
                'fullName': row['Name'],
                'sector': row['Sector'],
                'industry': row['Industry'],
                'performance': perf_str,
                'marketCap': f"${row['Market Cap']/1e9:.1f}B",
                'price': f"${row['Price']:.2f}",
                'peRatio': f"{row['PE Ratio']}",
                'dividendYield': f"{row['Dividend Yield']}%",
                'revenueGrowth': f"{row['Revenue Growth']}%",
                'debtToEquity': f"{row['Debt to Equity']}",
                'ebitdaMargin': f"{row['EBITDA Margin']}%"
            }
        })
    
    return data

# Load or generate data
df, sectors, industries_by_sector = generate_sample_data()

# Sidebar filters
st.sidebar.header("Filters")
selected_sectors = st.sidebar.multiselect("Select Sectors", options=sorted(sectors), default=sectors)

# Get industries for selected sectors
available_industries = []
for sector in selected_sectors:
    if sector in industries_by_sector:
        available_industries.extend(industries_by_sector[sector])

selected_industries = st.sidebar.multiselect(
    "Select Industries", 
    options=sorted(set(available_industries)), 
    default=list(set(available_industries))
)

min_perf, max_perf = float(df['Performance'].min()), float(df['Performance'].max())
perf_range = st.sidebar.slider(
    "Performance Range (%)",
    min_value=round(min_perf, 1),
    max_value=round(max_perf, 1),
    value=(round(min_perf, 1), round(max_perf, 1))
)

filtered_df = df[
    (df['Sector'].isin(selected_sectors)) &
    (df['Industry'].isin(selected_industries)) &
    (df['Performance'] >= perf_range[0]) &
    (df['Performance'] <= perf_range[1])
]

if st.sidebar.checkbox("Show Data Table", value=False):
    st.subheader("Company Data")
    display_cols = ['Symbol', 'Name', 'Sector', 'Industry', 'Market Cap', 'Performance', 'PE Ratio', 'Dividend Yield']
    st.dataframe(filtered_df[display_cols], use_container_width=True)

highcharts_data = format_for_highcharts(filtered_df, selected_sectors, industries_by_sector)

# Build Highcharts HTML with improved styling and enhanced tooltips
highcharts_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S&P 500 Companies Treemap</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/treemap.js"></script>
    <script src="https://code.highcharts.com/modules/heatmap.js"></script>
    <script src="https://code.highcharts.com/modules/exporting.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/js/all.min.js"></script>
    <style>
        body {{ background-color: transparent; color: white; font-family: Arial, sans-serif; margin:0; padding:0 }}
        #container {{ height:700px; width:100% }}
        
        /* Enhanced tooltip styling */
        .highcharts-tooltip {{
            filter: drop-shadow(0 2px 6px rgba(0,0,0,0.5)) !important;
        }}
        
        /* Custom tooltip styles - apply directly to tooltip elements */
        .tooltip-header {{
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 8px;
            color: #fff;
        }}
        
        .tooltip-row {{
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
        }}
        
        .tooltip-key {{
            color: #ccc;
        }}
        
        .tooltip-value {{
            font-weight: bold;
            text-align: right;
        }}
        
        .tooltip-positive {{
            color: #2ecc59;
        }}
        
        .tooltip-negative {{
            color: #f73539;
        }}
        
        .tooltip-divider {{
            border: 0;
            height: 1px;
            background-color: #555;
            margin: 10px 0;
        }}
        
        .tooltip-footer {{
            color: #aaa;
            font-size: 11px;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
<div id="container"></div>
<script>
// Plugin for performance coloring on Level 1 only
Highcharts.addEvent(Highcharts.Series, 'drawDataLabels', function() {{
    if (this.type === 'treemap') {{
        this.points.forEach(pt => {{
            // Color the sector headers by their performance
            if (pt.node.level === 1 && Number.isFinite(pt.value)) {{
                try {{
                    const total = pt.node.children.reduce(
                        (sum, c) => sum + (c.point.value || 0), 0
                    );
                    const perf = 100 * (pt.value - total) / (total || 1);
                    if (pt.dlOptions) {{
                        pt.dlOptions.backgroundColor = this.colorAxis.toColor(perf);
                    }}
                }} catch (err) {{
                    console.warn('Error calculating sector performance:', err);
                }}
            }}
            
            // Dynamically adjust company label size based on box area
            if (pt.node.level === 3 && pt.shapeArgs) {{
                try {{
                    // Calculate box area
                    const area = pt.shapeArgs.width * pt.shapeArgs.height;
                    
                    // Formula from the original example: base size + area-proportional addition, with max cap
                    const fontSize = Math.min(32, 7 + Math.round(area * 0.0008));
                    
                    if (pt.dataLabel && pt.dataLabel.text) {{
                        pt.dataLabel.css({{
                            fontSize: fontSize + 'px'
                        }});
                    }}
                }} catch (err) {{
                    console.warn('Error adjusting company label size:', err);
                }}
            }}
        }});
    }}
}});

Highcharts.chart('container', {{
    chart: {{ 
        backgroundColor: '#252931',
        spacing: [10, 10, 0, 10]
    }},
    
    credits: {{ enabled: false }},
    
    colorAxis: {{
        minColor: '#f73539', 
        maxColor: '#2ecc59',
        stops: [[0,'#f73539'],[0.5,'#414555'],[1,'#2ecc59']],
        min: -10, 
        max: 10,
        labels: {{ 
            overflow: 'allow',
            format: '{{value}}%',
            style: {{ color: 'white' }},
            formatter: function() {{
                return (this.value > 0 ? '+' : '') + this.value + '%';
            }}
        }},
        legend: {{
            align: 'center',
            layout: 'horizontal',
            verticalAlign: 'bottom',
            floating: true,
            y: -40,
            symbolHeight: 12,
            itemStyle: {{ color: 'white' }}
        }}
    }},
    
    series: [{{
        name: 'All',
        type: 'treemap',
        layoutAlgorithm: 'squarified',
        allowDrillToNode: true,
        borderColor: '#252931',
        nodeSizeBy: 'leaf',
        dataLabels: {{ enabled: false }},
        levels: [
            {{ // Level 1 – Sectors
                level: 1,
                borderWidth: 3,
                dataLabels: {{
                    enabled: true,
                    headers: true,
                    align: 'left',
                    padding: 3,
                    style: {{
                        fontWeight: 'bold',
                        fontSize: '0.7em',
                        textTransform: 'uppercase',
                        color: 'white'
                    }}
                }}
            }},
            {{                 // Level 2 – Industries
                level: 2,
                groupPadding: 1,
                dataLabels: {{
                    enabled: true,
                    headers: true,
                    align: 'center',
                    backgroundColor: 'gray',
                    borderWidth: 1,
                    borderColor: '#252931',
                    padding: 0,
                    allowOverlap: true,  // Allow labels to overlap
                    style: {{
                        fontWeight: 'normal',
                        fontSize: '0.5em',
                        textTransform: 'uppercase',
                        color: 'white',
                        textOverflow: 'ellipsis'  // Add ellipsis for overflow
                    }}
                }}
            }},
            {{ // Level 3 – Companies
                level: 3,
                dataLabels: {{
                    enabled: true,
                    align: 'center',
                    shape: 'callout',
                    format: '{{point.name}}<br><span style="font-size:0.7em">{{point.custom.performance}}</span>',
                    style: {{ 
                        color: 'white',
                        textOutline: 'none'  // Cleaner text
                    }}
                }}
            }}
        ],
        tooltip: {{
            followPointer: true,
            outside: true,
            useHTML: true,
            hideDelay: 100,
            formatter: function() {{
                const p = this.point;
                if (!p) return '';
                
                // Get node level
                const level = p.node.level;
                let tooltipClass = '';
                
                // Start with title
                let html = `<div style="font-weight:bold; font-size:16px; margin-bottom:8px">${{p.name}}</div>`;
                
                // Show full name if different from display name
                if (p.custom && p.custom.fullName && p.custom.fullName !== p.name) {{
                    html += `<div style="font-size:13px; margin-bottom:8px">${{p.custom.fullName}}</div>`;
                }}
                
                // LEVEL 3 - COMPANY TOOLTIP
                if (level === 3) {{
                    // Basic information
                    html += `<div class="tooltip-section">Company Overview</div>`;
                    html += `<table class="tooltip-table">
                        <tr>
                            <td><span class="tooltip-key">Sector:</span></td>
                            <td>${{p.custom.sector}}</td>
                        </tr>
                        <tr>
                            <td><span class="tooltip-key">Industry:</span></td>
                            <td>${{p.custom.industry}}</td>
                        </tr>
                    </table>`;
                    
                    // Key metrics
                    html += `<div class="tooltip-section">Financial Metrics</div>`;
                    
                    const performanceClass = parseFloat(p.custom.performance) >= 0 ? 'tooltip-positive' : 'tooltip-negative';
                    const growthClass = parseFloat(p.custom.revenueGrowth) >= 0 ? 'tooltip-positive' : 'tooltip-negative';
                    
                    html += `<table class="tooltip-table">
                        <tr>
                            <td><span class="tooltip-key">Market Cap:</span></td>
                            <td>${{p.custom.marketCap}}</td>
                            <td><span class="tooltip-key">Price:</span></td>
                            <td>${{p.custom.price}}</td>
                        </tr>
                        <tr>
                            <td><span class="tooltip-key">Performance:</span></td>
                            <td class="${{performanceClass}}">${{p.custom.performance}}</td>
                            <td><span class="tooltip-key">P/E Ratio:</span></td>
                            <td>${{p.custom.peRatio}}</td>
                        </tr>
                        <tr>
                            <td><span class="tooltip-key">Dividend:</span></td>
                            <td>${{p.custom.dividendYield}}</td>
                            <td><span class="tooltip-key">EBITDA:</span></td>
                            <td>${{p.custom.ebitdaMargin}}</td>
                        </tr>
                        <tr>
                            <td><span class="tooltip-key">Growth:</span></td>
                            <td class="${{growthClass}}">${{p.custom.revenueGrowth}}</td>
                            <td><span class="tooltip-key">Debt/Equity:</span></td>
                            <td>${{p.custom.debtToEquity}}</td>
                        </tr>
                    </table>`;
                }}
                
                // LEVEL 2 - INDUSTRY TOOLTIP
                else if (level === 2) {{
                    // Industry overview
                    html += `<div class="tooltip-section">Industry Overview</div>`;
                    html += `<table class="tooltip-table">
                        <tr>
                            <td><span class="tooltip-key">Sector:</span></td>
                            <td>${{p.custom.sector}}</td>
                        </tr>
                        <tr>
                            <td><span class="tooltip-key">Companies:</span></td>
                            <td>${{p.custom.companyCount}}</td>
                            <td><span class="tooltip-key">Total Market Cap:</span></td>
                            <td>${{p.custom.totalMarketCap}}</td>
                        </tr>
                    </table>`;
                    
                    // Industry metrics
                    html += `<div class="tooltip-section">Industry Averages</div>`;
                    
                    const performanceClass = parseFloat(p.custom.performance) >= 0 ? 'tooltip-positive' : 'tooltip-negative';
                    const growthClass = parseFloat(p.custom.avgGrowth) >= 0 ? 'tooltip-positive' : 'tooltip-negative';
                    
                    html += `<table class="tooltip-table">
                        <tr>
                            <td><span class="tooltip-key">Performance:</span></td>
                            <td class="${{performanceClass}}">${{p.custom.performance}}</td>
                            <td><span class="tooltip-key">Avg P/E:</span></td>
                            <td>${{p.custom.avgPE}}</td>
                        </tr>
                        <tr>
                            <td><span class="tooltip-key">Avg Dividend:</span></td>
                            <td>${{p.custom.avgDividend}}</td>
                            <td><span class="tooltip-key">Avg Growth:</span></td>
                            <td class="${{growthClass}}">${{p.custom.avgGrowth}}</td>
                        </tr>
                        <tr>
                            <td><span class="tooltip-key">Avg Debt/Equity:</span></td>
                            <td>${{p.custom.avgDebt}}</td>
                        </tr>
                    </table>`;
                }}
                
                // LEVEL 1 - SECTOR TOOLTIP
                else if (level === 1) {{
                    // Sector overview
                    html += `<div class="tooltip-section">Sector Overview</div>`;
                    html += `<table class="tooltip-table">
                        <tr>
                            <td><span class="tooltip-key">Companies:</span></td>
                            <td>${{p.custom.companyCount}}</td>
                            <td><span class="tooltip-key">Total Market Cap:</span></td>
                            <td>${{p.custom.totalMarketCap}}</td>
                        </tr>
                    </table>`;
                    
                    // Sector metrics
                    html += `<div class="tooltip-section">Sector Averages</div>`;
                    
                    const performanceClass = parseFloat(p.custom.performance) >= 0 ? 'tooltip-positive' : 'tooltip-negative';
                    const growthClass = parseFloat(p.custom.avgGrowth) >= 0 ? 'tooltip-positive' : 'tooltip-negative';
                    
                    html += `<table class="tooltip-table">
                        <tr>
                            <td><span class="tooltip-key">Performance:</span></td>
                            <td class="${{performanceClass}}">${{p.custom.performance}}</td>
                            <td><span class="tooltip-key">Avg P/E:</span></td>
                            <td>${{p.custom.avgPE}}</td>
                        </tr>
                        <tr>
                            <td><span class="tooltip-key">Avg Dividend:</span></td>
                            <td>${{p.custom.avgDividend}}</td>
                            <td><span class="tooltip-key">Avg Growth:</span></td>
                            <td class="${{growthClass}}">${{p.custom.avgGrowth}}</td>
                        </tr>
                    </table>`;
                }}
                
                return html;
            }}
        }},
        data: {json.dumps(highcharts_data)}
    }}],
    
    title: {{ 
        text: 'S&P 500 Companies', 
        align: 'left', 
        style: {{ color: 'white' }} 
    }},
    
    subtitle: {{ 
        text: 'Click to drill down. Size = Market Cap, Color = Performance',
        align: 'left', 
        style: {{ color: 'silver' }} 
    }},
    
    breadcrumbs: {{
        buttonTheme: {{
            style: {{ color: 'silver' }},
            states: {{
                hover: {{ fill: '#333' }},
                select: {{ style: {{ color: 'white' }} }}
            }}
        }}
    }},
    
    exporting: {{
        sourceWidth: 1200, 
        sourceHeight: 800,
        buttons: {{
            fullscreen: {{ 
                text: '<i class="fa fa-arrows-alt"></i> Fullscreen',
                onclick: function() {{ this.fullscreen.toggle(); }}
            }},
            contextButton: {{
                menuItems: ['downloadPNG', 'downloadJPEG', 'downloadPDF', 'downloadSVG'],
                text: '<i class="fa fa-share-alt"></i> Export',
                symbol: void 0,
                y: -2
            }}
        }}
    }},
    
    navigation: {{
        buttonOptions: {{
            theme: {{
                fill: '#252931',
                style: {{ color: 'silver', whiteSpace: 'nowrap' }},
                states: {{
                    hover: {{ fill: '#333', style: {{ color: 'white' }} }}
                }}
            }},
            symbolStroke: 'silver',
            useHTML: true,
            y: -2
        }}
    }}
}});
</script>
</body>
</html>
"""

st.subheader("S&P 500 Companies Treemap")
components.html(highcharts_html, height=750, scrolling=False)

# Download buttons
col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "Download Data as CSV",
        data=filtered_df.to_csv(index=False).encode('utf-8'),
        file_name='sp500_companies.csv',
        mime='text/csv'
    )
with col2:
    st.download_button(
        "Download JSON for Highcharts",
        data=json.dumps(highcharts_data, indent=2),
        file_name='sp500_treemap_data.json',
        mime='application/json'
    )

# Footer
st.markdown("---")
st.markdown("""
This treemap shows S&P 500 companies in a three-level hierarchy:
- **Level 1**: Sectors (uppercase, left-aligned)
- **Level 2**: Industries (uppercase, center-aligned, smaller font)  
- **Level 3**: Companies (with callout shape showing performance)

**Visual encoding:**  
- Size = Market capitalization  
- Color = 1-month performance (-10% to +10%)  

**Enhanced tooltips:**
- **Companies**: Show detailed financial metrics including price, P/E ratio, dividend yield, growth, etc.
- **Industries**: Display industry averages and aggregated statistics
- **Sectors**: Present sector-wide metrics and performance indicators

Use the filters to focus on specific sectors, industries, or performance ranges.
""")