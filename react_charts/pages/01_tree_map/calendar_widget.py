# calendar_widget.py

"""
This module provides an HTML snippet that displays the given trading day in a
calendar-style widget.
"""

def render_calendar(trading_day: str) -> str:
    """
    Returns an HTML snippet (with embedded CSS/JS) that displays
    the provided trading day as a calendar widget.

    :param trading_day: ISO date string (YYYY-MM-DD) of the trading day
    :return: HTML string
    """
    # We use margin: 0 auto 20px to center the fixed-width widget
    return f"""
    <style>
      .calendar {{
        width: 120px;
        border: 1px solid #ccc;
        border-radius: 4px;
        text-align: center;
        font-family: sans-serif;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin: 0 auto 20px;
      }}
      .calendar-header {{
        background: #3498db;
        color: #fff;
        padding: 6px 0;
        font-size: 14px;
        text-transform: uppercase;
      }}
      .calendar-day {{
        font-size: 48px;
        padding: 10px 0;
        line-height: 1;
        color: #333;
      }}
      .calendar-year {{
        font-size: 12px;
        color: #777;
        padding-bottom: 6px;
      }}
    </style>
    <div class="calendar" id="t-calendar">
      <div class="calendar-header" id="cal-month"></div>
      <div class="calendar-day" id="cal-day"></div>
      <div class="calendar-year" id="cal-year"></div>
    </div>
    <script>
      const td = new Date("{trading_day}T00:00:00");
      const mn = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
      document.getElementById('cal-month').textContent = mn[td.getMonth()];
      document.getElementById('cal-day').textContent   = String(td.getDate()).padStart(2,'0');
      document.getElementById('cal-year').textContent  = td.getFullYear();
    </script>
    """