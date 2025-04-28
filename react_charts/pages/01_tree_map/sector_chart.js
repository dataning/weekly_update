// sector_chart.js
// Jinja2 will inject `categories` (array of sector names) and `values` (array of avg perf)

Highcharts.chart('container', {
    chart: {
        type: 'item'
    },

    title: {
        text: 'Average Performance by Sector'
    },

    subtitle: {
        text: 'S&P 500 Sectors, as of latest trading day'
    },

    legend: {
        labelFormat: '{name} <span style="opacity: 0.4">{y}</span>'
    },

    series: [{
        name: 'Sectors',
        keys: ['name', 'y', 'color', 'label'],
        data: (function(){
            // build data array: [name, y, color, label]
            const cats = {{ categories }};
            const vals = {{ values }};
            const palette = [
                '#2ecc71','#3498db','#9b59b6','#f1c40f',
                '#e67e22','#e74c3c','#1abc9c','#34495e'
            ];
            return cats.map((cat,i)=>[
                cat,
                vals[i],
                palette[i % palette.length],
                cat.slice(0,3).toUpperCase()
            ]);
        })(),
        dataLabels: {
            enabled: true,
            format: '{point.label}',
            style: {
                textOutline: '3px contrast'
            }
        },

        // Circular options
        center: ['50%', '75%'],
        size: '90%',
        startAngle: -100,
        endAngle: 100
    }],

    responsive: {
        rules: [{
            condition: { maxWidth: 600 },
            chartOptions: {
                series: [{
                    dataLabels: { distance: -20 }
                }]
            }
        }]
    },

    exporting: { enabled: true },
    credits: { enabled: false }
});