// QuickAddModal.js
import React, { useState, useRef, useEffect } from "react";
import { CONFIG } from "./config.js";

export default function QuickAddModal({
    isOpen,
    onClose,
    onAddTask,
    defaultDay,
}) {
    const backdropRef = useRef(null);
    const [title, setTitle] = useState("");
    const [day, setDay] = useState(defaultDay || "Monday");
    const [details, setDetails] = useState("");

    useEffect(() => {
        if (isOpen) {
            setTitle("");
            setDetails("");
            if (defaultDay) {
                setDay(defaultDay);
            }
        }
    }, [isOpen, defaultDay]);

    const handleBackdropClick = (e) => {
        if (e.target === backdropRef.current) {
            onClose();
        }
    };

    const handleSubmit = () => {
        // 'details' currently unused in code (but you'd store it if needed).
        onAddTask(day, title || "New Task", details);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="quick-add-backdrop" ref={backdropRef} onClick={handleBackdropClick}>
            <div className="quick-add-modal">
                <button className="quick-add-close" onClick={onClose}>
                    &times;
                </button>
                <h2>Quick Add Task</h2>
                <label>Title:</label>
                <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Task title"
                    style={{ marginBottom: "8px" }}
                />
                <label>Day:</label>
                <select
                    value={day}
                    onChange={(e) => setDay(e.target.value)}
                    style={{ marginBottom: "8px" }}
                >
                    {CONFIG.validDays.map((d) => (
                        <option key={d} value={d}>
                            {d}
                        </option>
                    ))}
                </select>
                <label>Details (optional):</label>
                <textarea
                    value={details}
                    onChange={(e) => setDetails(e.target.value)}
                    placeholder="Any quick notes..."
                    style={{ marginBottom: "8px" }}
                />
                <button onClick={handleSubmit} className="btn save-btn">
                    Create
                </button>
            </div>
        </div>
    );
}