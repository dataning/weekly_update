// utils.js

// Simple helper functions for date parsing/formatting, etc.

export function parseDDMMYYYY(str) {
    const parts = str.split("/");
    if (parts.length !== 3) return null;
    const dd = parseInt(parts[0], 10);
    const mm = parseInt(parts[1], 10);
    const yyyy = parseInt(parts[2], 10);
    if (!dd || !mm || !yyyy) return null;
    const d = new Date(yyyy, mm - 1, dd);
    d.setHours(12, 0, 0, 0);
    return d;
}

export function formatDDMMYYYY(date) {
    const d = new Date(date);
    const dd = String(d.getDate()).padStart(2, "0");
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const yyyy = d.getFullYear();
    return dd + "/" + mm + "/" + yyyy;
}

export function getMonday(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(d.setDate(diff));
}

export function calcWorkingDays(start, end) {
    if (!start || !end) return 0;
    const s = new Date(start);
    const e = new Date(end);
    if (s > e) return 0;
    let count = 0;
    let d = new Date(s);
    while (d <= e) {
        const day = d.getDay();
        if (day >= 1 && day <= 5) {
            count++;
        }
        d.setDate(d.getDate() + 1);
    }
    return count;
}

export function truncateText(text, maxLength = 30) {
    if (text.length <= maxLength) return text;
    const front = Math.ceil(maxLength / 2);
    const back = Math.floor(maxLength / 2);
    return text.slice(0, front) + "..." + text.slice(text.length - back);
}