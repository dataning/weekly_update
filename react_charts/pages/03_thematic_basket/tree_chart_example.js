// Updated chart.js for theme-first hierarchy

const renderChart = data => {
  // Log data to check formatting
  console.log('Rendering with theme-first hierarchy:', data);
  
  Highcharts.chart('container', {
    chart: {
      backgroundColor: '#252931',
      spacing: [10, 10, 0, 10],
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
      colorKey: 'value',
      nodeSizeBy: 'leaf',
      dataLabels: {
        enabled: false,
        allowOverlap: true,
        style: { fontSize: '0.9em', textOutline: 'none' }
      },
      levels: [
        {
          // Level 1: Themes
          level: 1,
          borderWidth: 3,
          dataLabels: {
            enabled: true,
            headers: true,
            align: 'left',
            padding: 3,
            style: {
              fontWeight: 'bold',
              fontSize: '0.75em',
              textTransform: 'uppercase',
              color: 'white'
            }
          }
        },
        {
          // Level 2: Benchmarks
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
          // Level 3: Baskets
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
      text: 'Investment Themes and Benchmarks',
      align: 'left',
      style: { color: 'white' }
    },

    subtitle: {
      text: 'Click to drill down. Size = Allocation, Color = Performance',
      align: 'left',
      style: { color: 'silver' }
    },

    tooltip: {
      followPointer: true,
      outside: true,
      formatter: function() {
        const full = this.point.custom.fullName;
        const level = this.point.node.level;
        const perf = this.point.custom.performance || '';
        
        // Customize tooltip based on level
        if (level === 1) {
          return `<span style="font-size:0.9em">Theme: ${full}</span>`;
        } else if (level === 2) {
          return `<span style="font-size:0.9em">Benchmark: ${full}</span>`;
        } else {
          return `<span style="font-size:0.9em">${full}</span><br/>
                  <b>Performance:</b> ${perf}`;
        }
      }
    },

    colorAxis: {
      minColor: '#f73539',
      maxColor: '#2ecc59',
      stops: [
        [0,   '#f73539'],   // deep red
        [0.475, '#414555'], // gray appears only right around the middle
        [0.525, '#414555'],
        [1,   '#2ecc59']    // deep green
      ],
      min: -10,
      max: 10,
      gridLineWidth: 0,
      labels: {
        overflow: 'allow',
        format: '{value}%',
        style: { color: 'white' }
      },

      legend: {
        align: 'center',
        layout: 'horizontal',
        verticalAlign: 'bottom',
        floating: true,
        y: -40,
        margin: 0,
        symbolHeight: 12
      }
    },

    exporting: {
      sourceWidth: 1200,
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

// Modified event handler for the new hierarchy
Highcharts.addEvent(Highcharts.Series, 'drawDataLabels', function () {
  if (this.type === 'treemap') {
    this.points.forEach(pt => {
      // For benchmark level (now level 2)
      if (pt.node.level === 2 && Number.isFinite(pt.value)) {
        // Calculate average performance for the benchmark
        const total = pt.node.children.reduce((sum, c) => sum + (c.point.value || 0), 0);
        const count = pt.node.children.length || 1;
        const avgPerf = total / count;
        
        // Use avgPerf to color the benchmark node
        pt.dlOptions.backgroundColor = this.colorAxis.toColor(avgPerf);
      }
      
      // For basket level (still level 3)
      if (pt.node.level === 3 && pt.shapeArgs) {
        // Adjust font size based on area
        const area = pt.shapeArgs.width * pt.shapeArgs.height;
        pt.dlOptions.style.fontSize = Math.min(32, 7 + Math.round(area * 0.0008)) + 'px';
        
        // Ensure color value is set
        if (pt.colorValue === undefined && pt.value !== undefined) {
          pt.colorValue = pt.value;
        }
      }
    });
  }
});