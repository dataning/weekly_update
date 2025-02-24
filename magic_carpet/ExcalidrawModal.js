// ExcalidrawModal.js
import React, { useRef } from "react";

export default function ExcalidrawModal({ onClose }) {
    const backdropRef = useRef(null);

    const handleBackdropClick = (e) => {
        if (e.target === backdropRef.current) {
            onClose();
        }
    };

    const isDarkMode = document.body.classList.contains("dark-mode");

    return (
        <div className="excalidraw-backdrop" ref={backdropRef} onClick={handleBackdropClick}>
            <div className="excalidraw-modal-content">
                <button
                    onClick={onClose}
                    style={{
                        position: "absolute",
                        top: "10px",
                        right: "10px",
                        background: "none",
                        border: "none",
                        fontSize: "1.5em",
                        cursor: "pointer",
                        color: isDarkMode ? "#fff" : "#000",
                        zIndex: 999,
                    }}
                >
                    ×
                </button>
                <h2 style={{ margin: "10px", textAlign: "center" }}>Excalidraw Drawing Board</h2>
                <iframe
                    src="https://excalidraw.com?embed=1"
                    title="Excalidraw"
                    style={{ width: "100%", height: "calc(100% - 60px)", border: "none" }}
                />
            </div>
        </div>
    );
}