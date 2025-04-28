// chart.js

const renderChart = data => {
    Highcharts.chart('container', {
      chart: {
        backgroundColor: '#252931',
        spacing:       [10, 10, 0, 10],   // top, right, bottom, left
        spacingBottom: 0,
      },
  
      credits: { enabled: false },
  
      series: [{
        name: 'All',
        type: 'treemap',
        layoutAlgorithm: 'squarified',
        allowDrillToNode: true,
        animationLimit: 1000,
        borderColor: '#252931',
        color: '#252931',
        opacity: 0.01,
        nodeSizeBy: 'leaf',
        dataLabels: {
          enabled: false,
          allowOverlap: true,
          style: { fontSize: '0.9em', textOutline: 'none' }
        },
        levels: [
          {
            level: 1,
            borderWidth: 3,
            dataLabels: {
              enabled: true,
              headers: true,
              align: 'left',
              padding: 3,
              style: {
                fontWeight: 'bold',
                fontSize: '0.7em',
                textTransform: 'uppercase',
                color: 'white'
              }
            }
          },
          {
            level: 2,
            groupPadding: 1,
            dataLabels: {
              enabled: true,
              headers: true,
              align: 'center',
              shape: 'callout',
              backgroundColor: 'gray',
              borderWidth: 1,
              borderColor: '#252931',
              padding: 0,
              style: {
                color: 'white',
                fontSize: '0.6em',
                textTransform: 'uppercase'
              }
            }
          },
          {
            level: 3,
            dataLabels: {
              enabled: true,
              align: 'center',
              format: '{point.name}<br><span style="font-size:0.7em">{point.custom.performance}</span>',
              style: { color: 'white' }
            }
          }
        ],
        data
      }],
  
      title: {
        text: 'S&P 500 Companies (As of T‑1)',
        align: 'left',
        style: { color: 'white' }
      },
  
      subtitle: {
        text: 'Click to drill down. Size = Market Cap, Color = Performance',
        align: 'left',
        style: { color: 'silver' }
      },
  
      tooltip: {
        followPointer: true,
        outside: true,
        formatter: function() {
          const full = this.point.custom.fullName;
          const cap  = (this.point.value / 1e9).toFixed(1);
          const perf = this.point.custom.performance
                     ? '<br/><b>Performance:</b> ' + this.point.custom.performance
                     : '';
          return `<span style="font-size:0.9em">${full}</span><br/>
                  <b>Market Cap:</b> USD ${cap} bln${perf}`;
        }
      },
  
      colorAxis: {
        minColor: '#f73539',
        maxColor: '#2ecc59',
        stops:    [[0,'#f73539'],[0.5,'#414555'],[1,'#2ecc59']],
        min:     -10,
        max:      10,
        gridLineWidth: 0,
        labels: {
          overflow: 'allow',
          format: '{value}%',
          style: { color: 'white' }
        },
  
        // FLOAT the legend right at the bottom and overlap it
        legend: {
          align:         'center',
          layout:        'horizontal',
          verticalAlign: 'bottom',
          floating:      true,
          y:             -40,      // <— tweak this “upward” until the gap disappears
          margin:        0,
          symbolHeight:  12
        }
      },
  
      exporting: {
        sourceWidth:  1200,
        sourceHeight: 800,
        buttons: {
          fullscreen: {
            text: 'Fullscreen',
            onclick: function() { this.fullscreen.toggle(); }
          },
          contextButton: {
            menuItems: ['downloadPNG','downloadJPEG','downloadPDF','downloadSVG'],
            text: 'Export'
          }
        }
      },
  
      navigation: {
        buttonOptions: {
          theme: {
            fill: '#252931',
            style: { color: 'silver', whiteSpace: 'nowrap' },
            states: {
              hover: { fill: '#333', style: { color: 'white' } }
            }
          },
          symbolStroke: 'silver',
          useHTML: true
        }
      }
    });
  };
  
  // dynamic header‐color & font‐size plugin (unchanged)
  Highcharts.addEvent(Highcharts.Series, 'drawDataLabels', function () {
    if (this.type === 'treemap') {
      this.points.forEach(pt => {
        if (pt.node.level === 2 && Number.isFinite(pt.value)) {
          const total = pt.node.children.reduce((sum, c) => sum + (c.point.value || 0), 0);
          const perf  = 100 * (pt.value - total) / (total || 1);
          pt.dlOptions.backgroundColor = this.colorAxis.toColor(perf);
        }
        if (pt.node.level === 3 && pt.shapeArgs) {
          const area = pt.shapeArgs.width * pt.shapeArgs.height;
          pt.dlOptions.style.fontSize = Math.min(32, 7 + Math.round(area * 0.0008)) + 'px';
        }
      });
    }
  });