// HelpModal.js
import React, { useRef } from "react";

export default function HelpModal({ onClose }) {
    const backdropRef = useRef(null);

    const handleBackdropClick = (e) => {
        if (e.target === backdropRef.current) {
            onClose();
        }
    };

    return (
        <div className="help-backdrop" ref={backdropRef} onClick={handleBackdropClick}>
            <div className="help-modal">
                <button className="help-close-btn" onClick={onClose}>
                    &times;
                </button>
                <h2>Help & Documentation</h2>
                <p>Here are some usage instructions, keyboard shortcuts, and FAQs:</p>
                <ul>
                    <li><strong>Ctrl + T:</strong> Open Quick Add Task modal.</li>
                    <li><strong>Drag & Drop:</strong> Reorder tasks or move them between days.</li>
                    <li><strong>Click + or "Add Task":</strong> Create a new task in that column.</li>
                    <li><strong>Search Bar:</strong> Type to quickly locate tasks by title.</li>
                    <li><strong>Advanced Filters:</strong> Filter tasks by tags, users, or expiration status.</li>
                    <li><strong>Dark Mode:</strong> Toggle the moon/sun icon.</li>
                    <li><strong>Summary View:</strong> Provides a specialized summary or prompt generation.</li>
                </ul>
                <p><strong>FAQs:</strong></p>
                <ul>
                    <li><em>How do I attach files?</em> Use the "Browse File" button in the expanded task view.</li>
                    <li><em>Can I edit columns?</em> Columns are fixed to Monday–Friday.</li>
                </ul>
            </div>
        </div>
    );
}