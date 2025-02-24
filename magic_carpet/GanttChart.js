// GanttChart.js
import React from "react";
import { formatMMDD } from "./SummaryView.js";

// A simple Gantt chart that marks date ranges in orange.

export default function GanttChart({ tasks, onClose, filterTag }) {
    // Build rows: one row per (task, tag).
    const rows = [];
    tasks.forEach((task) => {
        if (task.tags && task.tags.length > 0) {
            task.tags.forEach((tag) => {
                if (!filterTag || tag.text.toLowerCase().includes(filterTag.toLowerCase())) {
                    rows.push({
                        tag: tag.text,
                        title: task.title,
                        start: task.dateAssigned ? new Date(task.dateAssigned) : null,
                        end: task.expirationDate
                            ? new Date(task.expirationDate)
                            : task.dateAssigned
                                ? new Date(task.dateAssigned)
                                : null,
                    });
                }
            });
        }
    });

    if (rows.length === 0) {
        return <div style={{ marginTop: "20px" }}>No data for Gantt Chart</div>;
    }

    // Determine overall date range
    const minDate = new Date(Math.min(...rows.map((r) => r.start.getTime())));
    const maxDate = new Date(Math.max(...rows.map((r) => r.end.getTime())));
    const dateColumns = [];
    let d = new Date(minDate);
    while (d <= maxDate) {
        dateColumns.push(new Date(d));
        d.setDate(d.getDate() + 1);
    }

    return (
        <div style={{ marginTop: "20px", border: "1px solid", padding: "10px" }}>
            <button onClick={onClose} style={{ float: "right" }}>
                Close
            </button>
            <h3>Gantt Chart View</h3>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                    <tr>
                        <th style={{ border: "1px solid", padding: "5px" }}>Tag</th>
                        <th style={{ border: "1px solid", padding: "5px" }}>Title</th>
                        {dateColumns.map((date, index) => (
                            <th key={index} style={{ border: "1px solid", padding: "5px" }}>
                                {formatMMDD(date)}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row, index) => (
                        <tr key={index}>
                            <td style={{ border: "1px solid", padding: "5px" }}>{row.tag}</td>
                            <td style={{ border: "1px solid", padding: "5px" }}>{row.title}</td>
                            {dateColumns.map((date, idx) => {
                                const inRange =
                                    row.start && row.end && date >= row.start && date <= row.end;
                                return (
                                    <td
                                        key={idx}
                                        style={{
                                            border: "1px solid",
                                            padding: "5px",
                                            backgroundColor: inRange ? "orange" : "transparent",
                                        }}
                                    ></td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}