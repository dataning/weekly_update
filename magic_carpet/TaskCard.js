// TaskCard.js

import React, { useState, useEffect, useRef } from "react";
import MarkdownEditor from "./MarkdownEditor.js";
import { truncateText, calcWorkingDays, formatDDMMYYYY } from "./utils.js";
import { CONFIG } from "./config.js";
import {
    updateTaskInDB,
    deleteTaskFromDB,
} from "./db.js";

export default function TaskCard({
    task,
    day,
    columnDate,
    onUpdate,
    onDelete,
    onReorder,
    forceCollapse,
    searchTerm,
}) {
    const [expanded, setExpanded] = useState(true);
    const [editTask, setEditTask] = useState({ ...task });
    const fileInputRef = useRef(null);
    const colorInputRef = useRef(null);
    const [editTagsCollapsed, setEditTagsCollapsed] = useState(false);
    const [editUsersCollapsed, setEditUsersCollapsed] = useState(false);
    const [editExpirationCollapsed, setEditExpirationCollapsed] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    useEffect(() => {
        setEditTask({ ...task });
    }, [task]);

    useEffect(() => {
        setExpanded(false);
    }, [forceCollapse]);

    const isHighlight = searchTerm
        ? editTask.title.toLowerCase().includes(searchTerm.toLowerCase())
        : false;

    function computeExpirationProgress() {
        if (!editTask.expirationDate) return 0;
        const today = new Date();
        let remaining = calcWorkingDays(today, editTask.expirationDate);
        if (remaining >= 10) return 0;
        if (remaining <= 0) return 100;
        return Math.round(((10 - remaining) / 10) * 100);
    }

    const progressValue = computeExpirationProgress();
    const remainingDays = editTask.expirationDate
        ? calcWorkingDays(new Date(), editTask.expirationDate)
        : 0;

    const handleSave = () => {
        onUpdate(editTask);
        updateTaskInDB(editTask);
        setExpanded(false);
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setEditTask((prev) => ({ ...prev, [name]: value }));
    };

    const handleMarkdownChange = (newMarkdown) => {
        setEditTask((prev) => ({ ...prev, items: [newMarkdown] }));
    };

    const handleTagsInput = (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            const val = e.target.value.trim();
            if (!val) return;
            const chip = { id: "_" + Math.random().toString(36).substr(2, 9), text: val };
            setEditTask((prev) => ({
                ...prev,
                tags: prev.tags ? [...prev.tags, chip] : [chip],
            }));
            e.target.value = "";
        }
    };

    const handleUsersInput = (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            const val = e.target.value.trim();
            if (!val) return;
            const chip = { id: "_" + Math.random().toString(36).substr(2, 9), name: val };
            setEditTask((prev) => ({
                ...prev,
                users: prev.users ? [...prev.users, chip] : [chip],
            }));
            e.target.value = "";
        }
    };

    const handleUrlsInput = (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            const val = e.target.value.trim();
            if (!val) return;
            const chip = { id: "_" + Math.random().toString(36).substr(2, 9), url: val };
            setEditTask((prev) => ({
                ...prev,
                urls: prev.urls ? [...prev.urls, chip] : [chip],
            }));
            e.target.value = "";
        }
    };

    const triggerFileSelect = () => fileInputRef.current.click();
    const handleFileChange = (e) => {
        const files = Array.from(e.target.files).map((f) => f.name);
        setEditTask((prev) => ({
            ...prev,
            attachments: prev.attachments ? [...prev.attachments, ...files] : files,
        }));
    };

    const removeAttachment = (fname) => {
        setEditTask((prev) => ({
            ...prev,
            attachments: prev.attachments.filter((x) => x !== fname),
        }));
    };

    const triggerColorSelect = () => colorInputRef.current.click();

    const handleColorChange = (e) => {
        const val = e.target.value;
        setEditTask((prev) => {
            const updated = { ...prev, color: val };
            onUpdate(updated);
            updateTaskInDB(updated);
            return updated;
        });
    };

    const handleColorSelect = (col) => {
        setEditTask((prev) => {
            const updated = { ...prev, color: col };
            onUpdate(updated);
            updateTaskInDB(updated);
            return updated;
        });
    };

    const handleMoveNextDay = () => {
        const dayIndex = CONFIG.validDays.indexOf(day);
        if (day === "aggregated" || dayIndex < 0) return;
        if (dayIndex === CONFIG.validDays.length - 1) {
            alert("No next day in this week!");
            return;
        }
        const nextDay = CONFIG.validDays[dayIndex + 1];
        onReorder(task.id, null, nextDay);
    };

    const updateCollapsedTags = (value) => {
        const vals = value.split(",").map((v) => v.trim()).filter(Boolean);
        const newTags = vals.map((v) => ({
            id: "_" + Math.random().toString(36).substr(2, 9),
            text: v,
        }));
        const updated = { ...editTask, tags: newTags };
        setEditTask(updated);
        onUpdate(updated);
        updateTaskInDB(updated);
        setEditTagsCollapsed(false);
    };

    const updateCollapsedUsers = (value) => {
        const vals = value.split(",").map((v) => v.trim()).filter(Boolean);
        const newUsers = vals.map((v) => ({
            id: "_" + Math.random().toString(36).substr(2, 9),
            name: v,
        }));
        const updated = { ...editTask, users: newUsers };
        setEditTask(updated);
        onUpdate(updated);
        updateTaskInDB(updated);
        setEditUsersCollapsed(false);
    };

    const updateCollapsedExpiration = (value) => {
        const newDateVal = value ? new Date(value) : null;
        if (newDateVal) newDateVal.setHours(12, 0, 0, 0);
        const updated = { ...editTask, expirationDate: newDateVal };
        setEditTask(updated);
        onUpdate(updated);
        updateTaskInDB(updated);
        setEditExpirationCollapsed(false);
    };

    const toggleExpanded = () => setExpanded((prev) => !prev);

    const handleDelete = () => {
        setIsDeleting(true);
        setTimeout(() => {
            onDelete(task.id);
            deleteTaskFromDB(task.id);
        }, 300);
    };

    return (
        <div
            className={`task ${isHighlight ? "highlight" : ""}`}
            style={{ backgroundColor: editTask.color || "#000" }}
            draggable
            onDragStart={(e) => {
                e.dataTransfer.setData("taskId", task.id);
                e.dataTransfer.setData("sourceDay", day);
                e.currentTarget.style.opacity = "0.8";
                e.currentTarget.style.transform = "scale(1.05)";
                e.currentTarget.style.zIndex = 100;
            }}
            onDragEnd={(e) => {
                e.currentTarget.style.opacity = "1";
                e.currentTarget.style.transform = "scale(1)";
                e.currentTarget.style.zIndex = 1;
            }}
            onDragOver={(e) => e.preventDefault()}
            // (CHANGE 1) -- Removed "sourceDay === day &&" check to allow dropping into a different column.
            onDrop={(e) => {
                e.preventDefault();
                e.stopPropagation();
                const sourceTaskId = e.dataTransfer.getData("taskId");
                if (sourceTaskId && sourceTaskId !== task.id) {
                    onReorder(sourceTaskId, task.id, day);
                }
            }}
        >
            <div className="task-controls">
                <button className="delete-task" onClick={handleDelete} title="Delete Task">
                    <i className="fa-solid fa-trash"></i>
                </button>
                <button
                    className="collapse-toggle"
                    onClick={() => setExpanded(!expanded)}
                    title="Collapse/Expand Task"
                >
                    {expanded ? (
                        <i className="fa-solid fa-minus"></i>
                    ) : (
                        <i className="fa-solid fa-plus"></i>
                    )}
                </button>
            </div>
            <div className="task-header">
                <input
                    type="text"
                    name="title"
                    value={editTask.title}
                    onChange={handleChange}
                    onBlur={!expanded ? handleSave : undefined}
                    onDoubleClick={(e) => e.target.select()}
                    onKeyDown={(e) => {
                        if (e.key === "Enter") {
                            handleSave();
                            e.preventDefault();
                        }
                    }}
                    className="task-title"
                />
                {!expanded && (
                    <div className="collapsed-content">
                        <hr className="collapsed-divider" />

                        {/* Collapsed Tags */}
                        <div
                            className="collapsed-row tags-row"
                            onClick={() => setEditTagsCollapsed(true)}
                            title="Click to edit tags"
                        >
                            <span className="row-label">Tags:</span>
                            <div className="editable-area">
                                {editTagsCollapsed ? (
                                    <input
                                        type="text"
                                        defaultValue={editTask.tags?.map((x) => x.text).join(", ")}
                                        autoFocus
                                        onBlur={(e) => updateCollapsedTags(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter") {
                                                e.preventDefault();
                                                updateCollapsedTags(e.target.value);
                                            }
                                        }}
                                    />
                                ) : editTask.tags?.length ? (
                                    editTask.tags.map((tg) => (
                                        <span key={tg.id} className="chip" title={tg.text}>
                                            {tg.text}
                                        </span>
                                    ))
                                ) : (
                                    <span style={{ opacity: 0.6 }}>None</span>
                                )}
                            </div>
                        </div>

                        {/* Collapsed Users */}
                        <div
                            className="collapsed-row users-row"
                            onClick={() => setEditUsersCollapsed(true)}
                            title="Click to edit users"
                        >
                            <span className="row-label">Users:</span>
                            <div className="editable-area">
                                {editUsersCollapsed ? (
                                    <input
                                        type="text"
                                        defaultValue={editTask.users?.map((u) => u.name).join(", ")}
                                        autoFocus
                                        onBlur={(e) => updateCollapsedUsers(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter") {
                                                e.preventDefault();
                                                updateCollapsedUsers(e.target.value);
                                            }
                                        }}
                                    />
                                ) : editTask.users && editTask.users.length > 0 ? (
                                    <>
                                        {editTask.users.slice(0, 4).map((u) => (
                                            <span key={u.id} className="chip" title={u.name}>
                                                {u.name}
                                            </span>
                                        ))}
                                        {editTask.users.length > 4 && (
                                            <span
                                                className="chip"
                                                title={editTask.users.map((u) => u.name).join(", ")}
                                            >
                                                +{editTask.users.length - 4}
                                            </span>
                                        )}
                                    </>
                                ) : (
                                    <span style={{ opacity: 0.6 }}>None</span>
                                )}
                            </div>
                        </div>

                        {/* Collapsed Color */}
                        <div className="collapsed-row">
                            <span className="row-label">Color:</span>
                            <div className="editable-area">
                                <div className="color-palette">
                                    {CONFIG.colors.preset.map((col, idx) => (
                                        <div
                                            key={idx}
                                            className="color-swatch"
                                            style={{
                                                backgroundColor: col,
                                                border:
                                                    editTask.color === col
                                                        ? "2px solid #4a90e2"
                                                        : "none",
                                            }}
                                            onClick={() => handleColorSelect(col)}
                                        ></div>
                                    ))}
                                    <button
                                        className="color-btn"
                                        onClick={triggerColorSelect}
                                        title="Custom Color"
                                    >
                                        <i
                                            className="fa-solid fa-eye-dropper"
                                            style={{ fontSize: "0.8em" }}
                                        ></i>
                                    </button>
                                    <input
                                        type="color"
                                        ref={colorInputRef}
                                        className="hidden-color"
                                        value={editTask.color || "#000000"}
                                        onInput={handleColorChange}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Collapsed Status */}
                        <div className="collapsed-row" title="Click to change status">
                            <span className="row-label">Status:</span>
                            <div className="editable-area">
                                <select
                                    name="status"
                                    value={editTask.status}
                                    onChange={(e) => {
                                        const newStatus = e.target.value;
                                        setEditTask((prev) => {
                                            const updated = { ...prev, status: newStatus };
                                            onUpdate(updated);
                                            updateTaskInDB(updated);
                                            return updated;
                                        });
                                    }}
                                    className="status-dropdown"
                                >
                                    <option value="Scoping">Scoping</option>
                                    <option value="In Progress">In Progress</option>
                                    <option value="Completed">Completed</option>
                                    <option value="Pending">Pending</option>
                                </select>
                            </div>
                        </div>

                        {/* Collapsed Expiration */}
                        <div className="collapsed-row" title="Click to edit expiration date">
                            <span className="row-label">Expires:</span>
                            <div className="editable-area">
                                {editTask.expirationDate && !editExpirationCollapsed ? (
                                    <span onClick={() => setEditExpirationCollapsed(true)}>
                                        {formatDDMMYYYY(editTask.expirationDate)}
                                    </span>
                                ) : (
                                    <input
                                        type="date"
                                        className="expiration-date-input"
                                        value={
                                            editTask.expirationDate
                                                ? new Date(editTask.expirationDate)
                                                    .toISOString()
                                                    .substring(0, 10)
                                                : ""
                                        }
                                        autoFocus
                                        onChange={(e) => {
                                            const val = e.target.value
                                                ? new Date(e.target.value)
                                                : null;
                                            if (val) val.setHours(12, 0, 0, 0);
                                            setEditTask((prev) => ({ ...prev, expirationDate: val }));
                                        }}
                                        onBlur={(e) => updateCollapsedExpiration(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter") {
                                                e.preventDefault();
                                                updateCollapsedExpiration(e.target.value);
                                            }
                                        }}
                                    />
                                )}
                            </div>
                        </div>

                        {/* New Signal Bar */}
                        {editTask.expirationDate && (
                            <div
                                className="signal-bar-container"
                                title={`${remainingDays} working days left`}
                            >
                                {Array.from({ length: 20 }).map((_, i) => (
                                    <div
                                        key={i}
                                        className="signal-cell"
                                        style={{
                                            backgroundColor:
                                                i >= 20 - remainingDays ? "#32CD32" : "#fff",
                                        }}
                                    ></div>
                                ))}
                            </div>
                        )}

                        {/* Collapsed URLs/Attachments */}
                        <div className="collapsed-row">
                            <span className="row-label">Files:</span>
                            <div className="editable-area" style={{ position: "relative" }}>
                                {editTask.urls?.length > 0 && (
                                    <div
                                        style={{
                                            position: "relative",
                                            display: "inline-block",
                                            marginRight: "6px",
                                        }}
                                    >
                                        <i className="fa-solid fa-link" title="URL(s) present"></i>
                                        <span className="count-badge">
                                            {editTask.urls.length}
                                        </span>
                                    </div>
                                )}
                                {editTask.attachments?.length > 0 && (
                                    <div
                                        style={{
                                            position: "relative",
                                            display: "inline-block",
                                        }}
                                    >
                                        <i
                                            className="fa-solid fa-paperclip"
                                            title="Attachment(s) present"
                                        ></i>
                                        <span className="count-badge">
                                            {editTask.attachments.length}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
            {expanded && (
                <div className="task-body">
                    <div>
                        <label>Items:</label>
                        <MarkdownEditor initialMarkdown={editTask.items} onChange={handleMarkdownChange} />
                    </div>
                    <div>
                        <label>Color:</label>
                        <div className="color-palette">
                            {CONFIG.colors.preset.map((col, idx) => (
                                <div
                                    key={idx}
                                    className="color-swatch"
                                    style={{
                                        backgroundColor: col,
                                        border:
                                            editTask.color === col ? "2px solid #4a90e2" : "none",
                                    }}
                                    onClick={() => handleColorSelect(col)}
                                ></div>
                            ))}
                            <button
                                className="color-btn"
                                onClick={triggerColorSelect}
                                title="Custom Color"
                            >
                                <i
                                    className="fa-solid fa-eye-dropper"
                                    style={{ fontSize: "0.8em" }}
                                ></i>
                            </button>
                            <input
                                type="color"
                                ref={colorInputRef}
                                className="hidden-color"
                                value={editTask.color || "#000000"}
                                onInput={handleColorChange}
                            />
                        </div>
                    </div>
                    <hr />
                    <div className="status-row" style={{ marginTop: "10px" }}>
                        <label>Status:</label>
                        <select
                            className="status-dropdown expanded-status-select"
                            name="status"
                            value={editTask.status}
                            onChange={(e) => {
                                const newStatus = e.target.value;
                                setEditTask((prev) => {
                                    const updated = { ...prev, status: newStatus };
                                    onUpdate(updated);
                                    updateTaskInDB(updated);
                                    return updated;
                                });
                            }}
                        >
                            <option value="Scoping">Scoping</option>
                            <option value="In Progress">In Progress</option>
                            <option value="Completed">Completed</option>
                            <option value="Pending">Pending</option>
                        </select>
                    </div>
                    <hr />
                    <div className="inline-row">
                        <label>Tag(s):</label>
                        <div className="chip-container">
                            {editTask.tags?.map((tg) => (
                                <div
                                    key={tg.id}
                                    className="chip"
                                    title="Click to remove"
                                    onClick={() =>
                                        setEditTask((prev) => ({
                                            ...prev,
                                            tags: prev.tags.filter((x) => x.id !== tg.id),
                                        }))
                                    }
                                >
                                    {tg.text} &times;
                                </div>
                            ))}
                        </div>
                        <input
                            type="text"
                            className="input-modern"
                            onKeyDown={handleTagsInput}
                            placeholder="Press Enter to add tag"
                        />
                    </div>
                    <div className="inline-row">
                        <label>User(s):</label>
                        <div className="chip-container">
                            {editTask.users?.map((u) => (
                                <div
                                    key={u.id}
                                    className="chip"
                                    title={u.name}
                                    onClick={() =>
                                        setEditTask((prev) => ({
                                            ...prev,
                                            users: prev.users.filter((x) => x.id !== u.id),
                                        }))
                                    }
                                >
                                    {u.name} &times;
                                </div>
                            ))}
                        </div>
                        <input
                            type="text"
                            className="input-modern"
                            onKeyDown={handleUsersInput}
                            placeholder="Press Enter to add user"
                        />
                    </div>
                    <div>
                        <label>URL(s):</label>
                        <div className="chip-container">
                            {editTask.urls?.map((chip) => (
                                <div
                                    key={chip.id}
                                    className="chip"
                                    title="Click to remove"
                                    onClick={() =>
                                        setEditTask((prev) => ({
                                            ...prev,
                                            urls: prev.urls.filter((x) => x.id !== chip.id),
                                        }))
                                    }
                                >
                                    {truncateText(chip.url, 30)} &times;
                                </div>
                            ))}
                        </div>
                        <input
                            type="text"
                            className="input-modern"
                            onKeyDown={handleUrlsInput}
                            placeholder="Press Enter to add URL"
                        />
                    </div>
                    <div>
                        <label>Expiration Date:</label>
                        <input
                            type="date"
                            name="expirationDate"
                            className="expiration-date-input"
                            value={
                                editTask.expirationDate
                                    ? new Date(editTask.expirationDate).toISOString().substring(0, 10)
                                    : ""
                            }
                            onChange={(e) => {
                                const val = e.target.value ? new Date(e.target.value) : null;
                                if (val) val.setHours(12, 0, 0, 0);
                                setEditTask((prev) => ({ ...prev, expirationDate: val }));
                            }}
                        />
                        {editTask.expirationDate && (
                            <div style={{ marginTop: "5px", fontSize: "0.9em" }}>
                                <strong>{remainingDays}</strong> working days left
                            </div>
                        )}
                    </div>
                    {editTask.expirationDate && (
                        <div style={{ marginTop: "8px" }}>
                            <div className="expiration-progress-bar-container">
                                <div
                                    className="elapsed-progress"
                                    style={{ width: progressValue + "%" }}
                                ></div>
                                <div
                                    className="remaining-progress"
                                    style={{
                                        width: (100 - progressValue) + "%",
                                        left: progressValue + "%",
                                    }}
                                ></div>
                                <i
                                    className="fa-solid fa-van-shuttle bus-icon"
                                    style={{ left: progressValue + "%" }}
                                ></i>
                            </div>
                        </div>
                    )}
                    <div>
                        <hr />
                        <label>Attachments:</label>
                        <button className="attach-button" onClick={triggerFileSelect}>
                            <i className="fa-solid fa-paperclip"></i> Browse File
                        </button>
                        <input
                            type="file"
                            ref={fileInputRef}
                            className="hidden-file"
                            multiple
                            onChange={handleFileChange}
                        />
                        <br />
                        {editTask.attachments?.length > 0 && (
                            <div className="chip-container">
                                {editTask.attachments.map((f, idx) => (
                                    <div
                                        key={idx}
                                        className="chip"
                                        title="Click to remove"
                                        onClick={() => removeAttachment(f)}
                                    >
                                        {truncateText(f, 30)} &times;
                                    </div>
                                ))}
                            </div>
                        )}
                        <hr />
                    </div>
                    <div style={{ marginTop: "10px", display: "flex", gap: "5px" }}>
                        <button className="btn save-btn" onClick={handleSave}>
                            Save
                        </button>
                        <button
                            className="btn move-next-day"
                            onClick={handleMoveNextDay}
                            title="Move to next date column"
                        >
                            <i className="fa-solid fa-arrow-right"></i>
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}