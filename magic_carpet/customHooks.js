// customHooks.js
import React, { useState, useEffect } from "react";

export function useDarkMode() {
    const [darkMode, setDarkMode] = useState(() => {
        const saved = localStorage.getItem("darkMode");
        return saved ? JSON.parse(saved) : false;
    });
    useEffect(() => {
        localStorage.setItem("darkMode", JSON.stringify(darkMode));
        document.body.classList.toggle("dark-mode", darkMode);
    }, [darkMode]);
    return [darkMode, setDarkMode];
}

export function useDebounce(value, delay) {
    const [debouncedValue, setDebouncedValue] = useState(value);
    useEffect(() => {
        const handler = setTimeout(() => setDebouncedValue(value), delay);
        return () => clearTimeout(handler);
    }, [value, delay]);
    return debouncedValue;
}