// grid_lite_example.js

(function(){
  // Allow <input checked> if ever needed
  Grid.AST.allowedTags.push('input');
  Grid.AST.allowedAttributes.push('checked');

  const brightGreen = '#28a745';
  const brightRed   = '#dc3545';

  function initGrid(dataTable) {
    const baseConfig = {
      dataTable: { columns: dataTable },
      rendering: {
        rows: { virtualization: false }
      },
      credits: { enabled: false },  // disable built‑in credits
      columnDefaults: {
        cells: {
          formatter: function() {
            const val = this.value;
            const id  = this.column.id;
            if (val == null || typeof val !== 'number') {
              return val;
            }
            if (id === 'Performance') {
              const pct   = val.toFixed(2) + '%';
              const color = val > 0
                ? brightGreen
                : (val < 0 ? brightRed : 'inherit');
              return `<span style="color:${color}; font-weight:600">${pct}</span>`;
            }
            if (['Previous_Close', 'Latest_Price', 'Market Cap'].includes(id)) {
              return val.toFixed(2);
            }
            return val;
          }
        },
        sorting: { sortable: true }
      },
      columns: [
        { id: 'Performance',    sorting: { sortable: true, order: 'desc' } },
        { id: 'Previous_Close', sorting: { sortable: true } },
        { id: 'Latest_Price',   sorting: { sortable: true } },
        { id: 'Market Cap',      sorting: { sortable: true } }
      ]
    };

    // Merge only caption/description if you want text,
    // here we keep defaults, no theme overrides.
    const merged = Highcharts.merge(baseConfig, {
      // captions could go here if desired
    });

    Grid.grid('table_3', merged);
  }

  // expose it globally
  window.initGrid = initGrid;
})();