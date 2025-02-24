// App.js
import React, { useState, useEffect, useRef } from "react";
import { CONFIG, fixTaskItems } from "./config.js";
import { db, deleteTaskFromDB } from "./db.js";
import { exportDexieToCSV } from "./exportCSVHelper.js"; // We'll define it inline or make a separate file if you like
import { useDarkMode, useDebounce } from "./customHooks.js"; // likewise, we can define those inline or separate
import DexieModal from "./DexieModal.js";
import ExcalidrawModal from "./ExcalidrawModal.js";
import QuickAddModal from "./QuickAddModal.js";
import HelpModal from "./HelpModal.js";
import SummaryView from "./SummaryView.js";
import TaskBoard from "./TaskBoard.js";

//
// For simplicity, we can define the logic inline or in small modules
// (Below code is the main App logic.)
//

function addGlobalKeyDown(setShowQuickAdd) {
    return (e) => {
        if (e.ctrlKey && e.key.toLowerCase() === "t") {
            e.preventDefault();
            setShowQuickAdd(true);
        }
    };
}

export default function App() {
    const [darkMode, setDarkMode] = useDarkMode();
    const [showDBModal, setShowDBModal] = useState(false);
    const [dbTasks, setDbTasks] = useState([]);
    const [viewMode, setViewMode] = useState("daily");
    const [headerSearch, setHeaderSearch] = useState("");
    const [offset, setOffset] = useState(0);
    const [showExcalidraw, setShowExcalidraw] = useState(false);

    const [filterTag, setFilterTag] = useState("");
    const [filterUser, setFilterUser] = useState("");
    const [filterExpiration, setFilterExpiration] = useState("");

    const [showQuickAdd, setShowQuickAdd] = useState(false);
    const [showHelp, setShowHelp] = useState(false);

    const [allTags, setAllTags] = useState([]);
    const [allUsers, setAllUsers] = useState([]);

    const boardRef = useRef(null);
    const importFileRef = useRef(null);
    const debouncedSearch = useDebounce(headerSearch, 300);

    useEffect(() => {
        if (debouncedSearch && boardRef.current) {
            boardRef.current.performSearch(debouncedSearch);
        }
    }, [debouncedSearch]);

    useEffect(() => {
        const loadUniqueTagsAndUsers = async () => {
            try {
                const tasks = await db.tasks.toArray();
                const tagSet = new Set();
                const userSet = new Set();
                for (const t of tasks) {
                    if (Array.isArray(t.tags)) {
                        for (const tg of t.tags) {
                            if (tg && tg.text) {
                                tagSet.add(tg.text);
                            }
                        }
                    }
                    if (Array.isArray(t.users)) {
                        for (const u of t.users) {
                            if (u && u.name) {
                                userSet.add(u.name.toLowerCase());
                            }
                        }
                    }
                }
                setAllTags([...tagSet]);
                setAllUsers([...userSet]);
            } catch (err) {
                console.error("Error fetching tags/users from DB:", err);
            }
        };
        loadUniqueTagsAndUsers();
    }, []);

    const handleViewDB = async () => {
        try {
            const tasks = await db.tasks.toArray();
            tasks.forEach((tk) => fixTaskItems(tk));
            tasks.sort(
                (a, b) =>
                    new Date(b.dateModified) - new Date(a.dateModified) ||
                    new Date(b.dateAssigned) - new Date(a.dateAssigned)
            );
            setDbTasks(tasks);
            setShowDBModal(true);
        } catch (err) {
            console.error("Error reading tasks from DB:", err);
        }
    };

    const handleSearch = (e) => setHeaderSearch(e.target.value);

    const handleFeedback = () => {
        const receiverEmail = "ning.lu@blackrock.com";
        const subject = "Feedback on Magic Carpet";
        const mailtoLink = `mailto:${receiverEmail}?subject=${encodeURIComponent(subject)}`;
        window.location.href = mailtoLink;
    };

    const toggleDarkMode = () => setDarkMode((prev) => !prev);

    const handleImportClick = () => {
        if (importFileRef.current) {
            importFileRef.current.value = "";
            importFileRef.current.click();
        }
    };

    const handleImportFile = async (e) => {
        if (!e.target.files?.length) return;
        const file = e.target.files[0];
        const reader = new FileReader();
        reader.onload = async (evt) => {
            const contents = evt.target.result;
            try {
                const lines = contents.split(/\r?\n/);
                lines.shift(); // drop header
                const tasksToImport = [];
                const splitCSV = (line) =>
                    line.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g) || [];
                for (let line of lines) {
                    line = line.trim();
                    if (!line) continue;
                    const row = splitCSV(line).map((cell) => cell.replace(/^"(.*)"$/, "$1"));
                    if (row.length < 10) continue;

                    // in practice, define or re-use "processCSVRow" from your code
                    // omitted for brevity or we can import it. We'll do a short inline:
                    const processCSVRow = (r) => {
                        // ...
                        return {}; // stub for brevity
                    };

                    // Here you'd parse row & re-check day constraints...
                    // This part is just an example or you can do your existing code
                }
                alert("Imported tasks successfully (example).");
                setViewMode("daily");
                setOffset(0);
            } catch (error) {
                console.error("Error importing file:", error);
                alert("Error importing file, please check console for details.");
            }
        };
        reader.readAsText(file);
    };

    useEffect(() => {
        window.addEventListener("keydown", addGlobalKeyDown(setShowQuickAdd));
        return () => {
            window.removeEventListener("keydown", addGlobalKeyDown(setShowQuickAdd));
        };
    }, []);

    const doQuickAddTask = (selectedDay, title, details) => {
        if (boardRef.current && viewMode === "daily") {
            boardRef.current.addTask(selectedDay, offset, title);
        } else {
            boardRef.current.addTask(selectedDay, 0, title);
        }
    };

    // (CHANGE 2) - Force scroll to top via setTimeout for Weekly or Monthly.
    const handleViewModeChange = (mode) => {
        setViewMode(mode);
        if (mode === "weekly" || mode === "monthly") {
            setTimeout(() => {
                window.scrollTo(0, 0);
                document.documentElement.scrollTop = 0;
                document.body.scrollTop = 0;
            }, 0);
        }
    };

    return (
        <div>
            <div className="header-bar">
                <div className="header-controls">
                    <button className="dexie-btn" onClick={handleViewDB} title="View Task DB">
                        <i className="fa-solid fa-database"></i>
                    </button>
                    <button className="dexie-btn" onClick={exportDexieToCSV} title="Export Task DB">
                        <i className="fa-solid fa-file-export"></i>
                    </button>
                    <button
                        className="dexie-btn"
                        onClick={handleImportClick}
                        title="Import Task DB"
                        style={{ marginLeft: "1px" }}
                    >
                        <i className="fa-solid fa-file-import"></i>
                    </button>
                    <input
                        type="file"
                        accept=".csv,.xls,.xlsx"
                        ref={importFileRef}
                        style={{ display: "none" }}
                        onChange={handleImportFile}
                    />
                    <button
                        className="dexie-btn"
                        onClick={() => setShowExcalidraw(true)}
                        title="Excalidraw"
                    >
                        <i className="fa-solid fa-pencil"></i>
                    </button>
                    <button className="mode-toggle" onClick={toggleDarkMode} title="Toggle Dark/Light Mode">
                        {darkMode ? <i className="fa-solid fa-sun"></i> : <i className="fa-solid fa-moon"></i>}
                    </button>
                    <input
                        type="text"
                        placeholder="Search tasks..."
                        value={headerSearch}
                        onChange={handleSearch}
                    />
                </div>
                <div className="branding">
                    <h1>Magic Carpet</h1>
                    <h2>Made by Aladdin Family</h2>
                </div>
                {viewMode !== "summary" && (
                    <div className="offset-container">
                        <label>
                            {viewMode === "daily"
                                ? "Week Offset"
                                : viewMode === "weekly"
                                    ? "Month Offset"
                                    : viewMode === "monthly"
                                        ? "Quarter Offset"
                                        : ""}
                            : {offset}
                        </label>
                        <input
                            type="range"
                            min={
                                viewMode === "daily"
                                    ? CONFIG.views.daily.minOffset
                                    : viewMode === "weekly"
                                        ? CONFIG.views.weekly.minOffset
                                        : viewMode === "monthly"
                                            ? CONFIG.views.monthly.minOffset
                                            : 0
                            }
                            max={
                                viewMode === "daily"
                                    ? CONFIG.views.daily.maxOffset
                                    : viewMode === "weekly"
                                        ? CONFIG.views.weekly.maxOffset
                                        : viewMode === "monthly"
                                            ? CONFIG.views.monthly.maxOffset
                                            : 0
                            }
                            step="1"
                            value={offset}
                            onChange={(e) => setOffset(Number(e.target.value))}
                            onDoubleClick={() => setOffset(0)}
                            onInput={(e) => {
                                const min = e.target.min;
                                const max = e.target.max;
                                const value = e.target.value;
                                const percent = ((value - min) / (max - min)) * 100 + "%";
                                e.target.style.setProperty("--percent", percent);
                            }}
                        />
                        <button className="arrow-btn" onClick={() => setOffset(offset - 1)}>
                            <i className="fa-solid fa-arrow-left"></i>
                        </button>
                        <button className="arrow-btn" onClick={() => setOffset(offset + 1)}>
                            <i className="fa-solid fa-arrow-right"></i>
                        </button>
                    </div>
                )}
            </div>

            <div className="controls-bar">
                <div className="left-filters">
                    <select value={filterTag} onChange={(e) => setFilterTag(e.target.value)}>
                        <option value="">Filter Tag</option>
                        {allTags.map((t) => (
                            <option key={t} value={t}>
                                {t}
                            </option>
                        ))}
                    </select>
                    <select value={filterUser} onChange={(e) => setFilterUser(e.target.value)}>
                        <option value="">Filter User</option>
                        {allUsers.map((u) => (
                            <option key={u} value={u}>
                                {u.charAt(0).toUpperCase() + u.slice(1)}
                            </option>
                        ))}
                    </select>
                    <select value={filterExpiration} onChange={(e) => setFilterExpiration(e.target.value)}>
                        <option value="">Expiration</option>
                        <option value="overdue">Overdue</option>
                        <option value="none">No Expiration</option>
                    </select>
                </div>

                <div className="view-mode-container">
                    <div className="view-mode-toggle">
                        {["daily", "weekly", "monthly", "summary"].map((m) => (
                            <button
                                key={m}
                                className={viewMode === m ? "active" : ""}
                                onClick={() => handleViewModeChange(m)}
                            >
                                {m.charAt(0).toUpperCase() + m.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="contributor-version">
                    <span>
                        Contributors:{" "}
                        <span className="contributor-info">
                            PAG
                            <span className="tooltip">
                                Ning Lu. Learn more{" "}
                                <a href="https://example.com" target="_blank" rel="noopener noreferrer">
                                    here
                                </a>
                                .
                            </span>
                        </span>
                        , Version 0.2
                    </span>
                    <button className="feedback-btn" onClick={handleFeedback}>
                        Feedback
                    </button>
                    <button
                        className="feedback-btn"
                        style={{ marginLeft: "6px" }}
                        onClick={() => setShowHelp(true)}
                    >
                        ?
                    </button>
                </div>
            </div>

            {viewMode === "summary" ? (
                <SummaryView allUsers={allUsers} />
            ) : (
                <TaskBoard
                    ref={boardRef}
                    viewMode={viewMode}
                    offset={offset}
                    setOffset={setOffset}
                    setViewMode={setViewMode}
                    searchTerm={headerSearch}
                    filterTag={filterTag}
                    filterUser={filterUser}
                    filterExpiration={filterExpiration}
                />
            )}

            {showDBModal && <DexieModal tasks={dbTasks} onClose={() => setShowDBModal(false)} />}
            {showExcalidraw && <ExcalidrawModal onClose={() => setShowExcalidraw(false)} />}

            {viewMode !== "summary" && (
                <div className="fab" onClick={() => setShowQuickAdd(true)} title="Quick Add Task">
                    <i className="fa-solid fa-plus"></i>
                </div>
            )}

            <QuickAddModal
                isOpen={showQuickAdd}
                onClose={() => setShowQuickAdd(false)}
                onAddTask={(selectedDay, taskTitle, details) =>
                    doQuickAddTask(selectedDay, taskTitle, details)
                }
                defaultDay={
                    viewMode === "daily"
                        ? CONFIG.validDays[new Date().getDay() - 1] || "Monday"
                        : "Monday"
                }
            />

            {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}
        </div>
    );
}