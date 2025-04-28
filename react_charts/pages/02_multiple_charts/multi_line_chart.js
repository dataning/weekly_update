// 1. Load and parse the injected approval data
const chartData = JSON.parse(
    document.getElementById('data').textContent
  );
  
  // 2. Create a chart container for each president
  const container = document.getElementById('chartsContainer');
  chartData.forEach(({ id }) => {
    const div = document.createElement('div');
    div.id = id;
    div.style.minWidth = '300px';
    container.appendChild(div);
  });
  
  // 3. Store chart instances for synchronized interactions
  const charts = [];
  
  // Sync hover state across all charts
  function syncHover(event) {
    const index = event.target.x;
    charts.forEach(chart => {
      const [appPoint, disPoint] = [
        chart.series[0].points[index],
        chart.series[1].points[index]
      ];
      chart.tooltip.refresh([appPoint, disPoint]);
    });
  }
  
  // Hide all tooltips on mouse out
  function syncMouseOut() {
    charts.forEach(chart => chart.tooltip.hide());
  }
  
  // 4. Initialize charts when DOM is ready
  function initCharts() {
    chartData.forEach(president => {
      const { id, name, years, approval, disapproval, range } = president;
  
      const chart = Highcharts.chart(id, {
        exporting: { enabled: false },
        title: {
          useHTML: true,
          text: `<div>${name}</div>
                 <div style="font-size:12px;color:#666;">${years}</div>`
        },
        xAxis: {
          categories: ['0', '1', '2', '3', '4'],
          gridLineWidth: 1
        },
        yAxis: {
          title: { text: 'Rating (%)' },
          min: 20,
          max: 80,
          gridLineWidth: 1
        },
        tooltip: {
          shared: true,
          crosshairs: true,
          useHTML: true,
          formatter: function() {
            const ap = this.points.find(p => p.series.name === 'Approval').y;
            const dis = this.points.find(p => p.series.name === 'Disapproval').y;
            const diff = ap - dis;
            const label = diff > 0 ? `Approval +${diff}%` : `Disapproval +${-diff}%`;
            const color = diff > 0 ? '#059669' : '#EC4899';
            return `
              <div style="font-family:sans-serif;">
                <div style="font-size:0.9em;color:#666;">Year ${this.x}</div>
                <div><span style="color:#059669">●</span> Approval: <b>${ap}%</b></div>
                <div><span style="color:#EC4899">●</span> Disapproval: <b>${dis}%</b></div>
                <div style="padding-top:8px;border-top:1px solid #eee;">
                  <span style="color:${color};font-weight:500">${label}</span>
                </div>
              </div>`;
          }
        },
        plotOptions: {
          series: {
            states: { inactive: { opacity: 1 } },
            point: {
              events: {
                mouseOver: syncHover,
                mouseOut: syncMouseOut
              }
            }
          },
          spline: {
            tension: 0.4,
            marker: { enabled: false }
          },
          areasplinerange: {
            enableMouseTracking: false,
            fillOpacity: 0.1,
            lineWidth: 0
          }
        },
        series: [
          { name: 'Approval', type: 'spline', data: approval, zIndex: 2 },
          { name: 'Disapproval', type: 'spline', data: disapproval, zIndex: 2 },
          { name: 'Range', type: 'areasplinerange', data: range, showInLegend: false, zIndex: 1 }
        ],
        credits: { enabled: false }
      });
      charts.push(chart);
    });
  
    // 5. Export all charts to a single image
    document
      .getElementById('export-button')
      .addEventListener('click', handleExport);
  }
  
  document.addEventListener('DOMContentLoaded', initCharts);
  
  // Helper: format and trigger canvas export
  function handleExport() {
    html2canvas(
      document.getElementById('export-container'),
      { backgroundColor: '#fff', scale: 2 }
    ).then(canvas => {
      const link = document.createElement('a');
      link.download = 'presidential_approval_charts.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
    });
  }
  