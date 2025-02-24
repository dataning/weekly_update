// DexieModal.js
import React, { useRef } from "react";

export default function DexieModal({ tasks, onClose }) {
    const backdropRef = useRef(null);

    const handleBackdropClick = (e) => {
        if (e.target === backdropRef.current) {
            onClose();
        }
    };

    const isDarkMode = document.body.classList.contains("dark-mode");

    return (
        <div
            ref={backdropRef}
            style={{
                position: "fixed",
                top: 0,
                left: 0,
                width: "100vw",
                height: "100vh",
                backgroundColor: "rgba(0,0,0,0.5)",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                zIndex: 1000,
            }}
            onClick={handleBackdropClick}
        >
            <div
                className="dexie-modal-container"
                style={{
                    backgroundColor: isDarkMode ? "#333" : "#fff",
                    padding: "20px",
                    maxHeight: "80%",
                    overflowY: "auto",
                    borderRadius: "6px",
                }}
            >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <h2 style={{ color: isDarkMode ? "#fff" : "#000" }}>Dexie Task Table</h2>
                    <button
                        onClick={onClose}
                        style={{
                            background: "none",
                            border: "none",
                            fontSize: "1.5em",
                            cursor: "pointer",
                            color: isDarkMode ? "#fff" : "#000",
                        }}
                    >
                        ×
                    </button>
                </div>
                <table style={{ borderCollapse: "collapse", width: "100%", tableLayout: "fixed" }}>
                    <thead>
                        <tr>
                            {[
                                "ID",
                                "Title",
                                "Items",
                                "Tags",
                                "Users",
                                "URLs",
                                "Attachments",
                                "Date Assigned",
                                "Date Modified",
                                "Expiration Date",
                                "Color",
                                "Status",
                            ].map((h) => (
                                <th
                                    key={h}
                                    style={{ border: "1px solid", padding: "5px", textAlign: "left" }}
                                >
                                    {h}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {tasks.map((t) => {
                            const displayItems = Array.isArray(t.items)
                                ? t.items.join(" | ")
                                : String(t.items ?? "");
                            return (
                                <tr key={t.id}>
                                    <td style={{ border: "1px solid", padding: "5px" }}>{t.id}</td>
                                    <td style={{ border: "1px solid", padding: "5px" }}>{t.title}</td>
                                    <td style={{ border: "1px solid", padding: "5px" }}>{displayItems}</td>
                                    <td style={{ border: "1px solid", padding: "5px" }}>
                                        {t.tags?.map((ch) => ch.text).join(" | ")}
                                    </td>
                                    <td style={{ border: "1px solid", padding: "5px" }}>
                                        {t.users?.map((u) => u.name).join(" | ")}
                                    </td>
                                    <td style={{ border: "1px solid", padding: "5px" }}>
                                        {t.urls?.map((u) => u.url).join(" | ")}
                                    </td>
                                    <td style={{ border: "1px solid", padding: "5px" }}>
                                        {t.attachments?.join(" | ")}
                                    </td>
                                    <td style={{ border: "1px solid", padding: "5px" }}>
                                        {t.dateAssigned
                                            ? new Date(t.dateAssigned).toLocaleDateString(undefined, {
                                                day: "numeric",
                                                month: "numeric",
                                                year: "numeric",
                                            })
                                            : ""}
                                    </td>
                                    <td style={{ border: "1px solid", padding: "5px" }}>
                                        {t.dateModified ? new Date(t.dateModified).toLocaleDateString() : ""}
                                    </td>
                                    <td style={{ border: "1px solid", padding: "5px" }}>
                                        {t.expirationDate ? new Date(t.expirationDate).toLocaleDateString() : ""}
                                    </td>
                                    <td style={{ border: "1px solid", padding: "5px" }}>{t.color}</td>
                                    <td style={{ border: "1px solid", padding: "5px" }}>{t.status}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}