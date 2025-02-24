// TaskBoard.js
import React, { useState, useRef, useEffect, useImperativeHandle, forwardRef } from "react";
import { CONFIG, fixTaskItems } from "./config.js";
import { db, addTaskToDB, updateTaskInDB } from "./db.js";
import { getMonday, calcWorkingDays, truncateText } from "./utils.js";
import TaskCard from "./TaskCard.js";

function computeDate(dayLabel, offset, baseMonday) {
    const dayIndex = CONFIG.validDays.indexOf(dayLabel);
    const newDate = new Date(baseMonday);
    newDate.setDate(newDate.getDate() + offset * 7 + dayIndex);
    newDate.setHours(12, 0, 0, 0);
    return newDate;
}

const TaskBoard = forwardRef(function TaskBoard(
    { viewMode, offset, setOffset, setViewMode, searchTerm, filterTag, filterUser, filterExpiration },
    ref
) {
    const [forceCollapse, setForceCollapse] = useState(0);
    const [tasksByWeek, setTasksByWeek] = useState({});

    const baseMonday = getMonday(new Date());
    const emptyBoard = {
        Monday: [],
        Tuesday: [],
        Wednesday: [],
        Thursday: [],
        Friday: [],
    };

    const groupTasksByWeek = (fetchedTasks) => {
        const board = {};
        for (const t of fetchedTasks) {
            if (!CONFIG.validDays.includes(t.day)) continue;
            const diffWeeks = Math.floor(
                (new Date(t.dateAssigned) - baseMonday) / (7 * 24 * 3600 * 1000)
            );
            if (!board[diffWeeks]) {
                board[diffWeeks] = JSON.parse(JSON.stringify(emptyBoard));
            }
            board[diffWeeks][t.day].push(t);
        }
        return board;
    };

    useEffect(() => {
        const fetchTasks = async () => {
            try {
                const fetchedTasks = await db.tasks.toArray();
                fetchedTasks.forEach((tk) => fixTaskItems(tk));
                const board = groupTasksByWeek(fetchedTasks);
                setTasksByWeek(board);
            } catch (err) {
                console.error("Error fetching tasks:", err);
            }
        };
        fetchTasks();
    }, []);

    useEffect(() => {
        setForceCollapse(Date.now());
    }, [viewMode]);

    let columns = [];
    if (viewMode === "daily") {
        const weeklyTasks = tasksByWeek[offset] || emptyBoard;
        columns = CONFIG.validDays.map((lbl) => ({
            label: lbl,
            tasks: weeklyTasks[lbl] || [],
            date: computeDate(lbl, offset, baseMonday).toLocaleDateString(undefined, {
                day: "numeric",
                month: "numeric",
            }),
            columnDate: new Date(computeDate(lbl, offset, baseMonday)),
        }));
    } else if (viewMode === "weekly") {
        // Modified approach: Month-based
        const currentDate = new Date();
        const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
        let firstMonday = getMonday(firstDayOfMonth);
        if (firstMonday.getMonth() !== firstDayOfMonth.getMonth()) {
            firstMonday = new Date(firstMonday.getTime() + 7 * 24 * 3600 * 1000);
        }
        for (let i = 0; i < 4; i++) {
            const weekStart = new Date(firstMonday.getTime() + i * 7 * 24 * 3600 * 1000);
            const weekStartTime = weekStart.getTime();
            const weekEndTime = weekStartTime + 7 * 24 * 3600 * 1000;
            const allTasks = [];
            for (const wk in tasksByWeek) {
                for (const d in tasksByWeek[wk]) {
                    allTasks.push(...tasksByWeek[wk][d]);
                }
            }
            const tasksInWeek = allTasks.filter((t) => {
                const dateAssigned = new Date(t.dateAssigned);
                return dateAssigned.getTime() >= weekStartTime && dateAssigned.getTime() < weekEndTime;
            });
            columns.push({
                label: `Week ${i + 1}`,
                tasks: tasksInWeek,
                date: weekStart.toLocaleDateString(),
            });
        }
    } else if (viewMode === "monthly") {
        // Modified approach: Quarter-based from January
        const baseMonth = new Date(new Date().getFullYear(), 0, 1);
        for (let i = 0; i < 3; i++) {
            const monthDate = new Date(baseMonth.getFullYear(), baseMonth.getMonth() + i, 1);
            const monthStart = monthDate.getTime();
            const nextMonth = new Date(
                monthDate.getFullYear(),
                monthDate.getMonth() + 1,
                1
            ).getTime();
            const allTasks = [];
            for (const wk in tasksByWeek) {
                for (const d in tasksByWeek[wk]) {
                    allTasks.push(...tasksByWeek[wk][d]);
                }
            }
            const tasksInMonth = allTasks.filter((t) => {
                const dateAssigned = new Date(t.dateAssigned);
                return dateAssigned.getTime() >= monthStart && dateAssigned.getTime() < nextMonth;
            });
            columns.push({
                label: `Month ${i + 1}`,
                tasks: tasksInMonth,
                date: monthDate.toLocaleDateString("default", {
                    month: "long",
                    year: "numeric",
                }),
            });
        }
    }

    const matchesFilters = (t) => {
        if (filterTag) {
            const hasTag = t.tags?.some(
                (x) => x.text.toLowerCase() === filterTag.toLowerCase()
            );
            if (!hasTag) return false;
        }
        if (filterUser) {
            const lowerUser = filterUser.toLowerCase();
            const hasUser = t.users?.some((u) => u.name.toLowerCase() === lowerUser);
            if (!hasUser) return false;
        }
        if (filterExpiration) {
            if (filterExpiration === "overdue") {
                if (!t.expirationDate) return false;
                const now = new Date();
                if (new Date(t.expirationDate) >= now) return false;
            }
            if (filterExpiration === "none") {
                if (t.expirationDate) return false;
            }
        }
        return true;
    };

    columns = columns.map((col) => {
        const filteredTasks = col.tasks.filter((tk) => matchesFilters(tk));
        return { ...col, tasks: filteredTasks, columnDate: col.columnDate };
    });

    const updateTask = (t) => {
        setTasksByWeek((prev) => {
            for (const wk in prev) {
                for (const d in prev[wk]) {
                    prev[wk][d] = prev[wk][d].map((x) => (x.id === t.id ? t : x));
                }
            }
            return { ...prev };
        });
    };

    const deleteTask = (id) => {
        setTasksByWeek((prev) => {
            for (const wk in prev) {
                for (const d in prev[wk]) {
                    prev[wk][d] = prev[wk][d].filter((x) => x.id !== id);
                }
            }
            return { ...prev };
        });
    };

    const addTask = (dayLabel, weekIndex = offset, newTitle = "New Task") => {
        const dateObj = computeDate(dayLabel, weekIndex, baseMonday);
        const newTask = {
            id: "_" + Math.random().toString(36).substr(2, 9),
            title: newTitle,
            items: [],
            color: "#000000",
            tags: [],
            users: [],
            urls: [],
            attachments: [],
            day: dayLabel,
            dateAssigned: dateObj,
            expirationDate: null,
            status: "Scoping",
            isNew: true,
        };
        setTasksByWeek((prev) => {
            const boardCopy = prev[weekIndex] || JSON.parse(JSON.stringify(emptyBoard));
            boardCopy[dayLabel] = [...boardCopy[dayLabel], newTask];
            return { ...prev, [weekIndex]: boardCopy };
        });
        addTaskToDB(newTask);
    };

    const reorderTask = (sourceTaskId, targetTaskId = null, newDay = null) => {
        setTasksByWeek((prev) => {
            let foundWeekIndex = null;
            let foundDay = null;
            for (const wk in prev) {
                for (const d in prev[wk]) {
                    if (prev[wk][d].some((tt) => tt.id === sourceTaskId)) {
                        foundWeekIndex = Number(wk);
                        foundDay = d;
                        break;
                    }
                }
                if (foundWeekIndex !== null) break;
            }
            if (foundWeekIndex === null || !foundDay) return prev;

            const boardCopy = prev[foundWeekIndex] || JSON.parse(JSON.stringify(emptyBoard));
            const tasksInDay = [...boardCopy[foundDay]];
            const idx = tasksInDay.findIndex((x) => x.id === sourceTaskId);
            if (idx === -1) return prev;

            const [movedTask] = tasksInDay.splice(idx, 1);
            boardCopy[foundDay] = tasksInDay;

            if (newDay && newDay !== foundDay) {
                movedTask.day = newDay;
                if (viewMode === "daily") {
                    movedTask.dateAssigned = computeDate(newDay, offset, baseMonday);
                }
            }

            let insertDay = newDay && newDay !== foundDay ? newDay : foundDay;
            let tasksTargetArr = [...boardCopy[insertDay]];

            if (targetTaskId) {
                const tgtIdx = tasksTargetArr.findIndex((x) => x.id === targetTaskId);
                if (tgtIdx === -1) tasksTargetArr.push(movedTask);
                else tasksTargetArr.splice(tgtIdx, 0, movedTask);
            } else {
                tasksTargetArr.push(movedTask);
            }

            boardCopy[insertDay] = tasksTargetArr;
            updateTaskInDB(movedTask);
            return { ...prev, [foundWeekIndex]: boardCopy };
        });
    };

    const handleDropInZone = (e, targetTaskId, day) => {
        e.preventDefault();
        const sourceTaskId = e.dataTransfer.getData("taskId");
        if (sourceTaskId && sourceTaskId !== targetTaskId) {
            reorderTask(sourceTaskId, targetTaskId, day);
        }
    };

    useImperativeHandle(ref, () => ({
        performSearch: (query) => {
            const q = query.toLowerCase();
            for (const wk in tasksByWeek) {
                for (const d in tasksByWeek[wk]) {
                    if (tasksByWeek[wk][d].some((tt) => tt.title.toLowerCase().includes(q))) {
                        setOffset(Number(wk));
                        setViewMode("daily");
                        return;
                    }
                }
            }
            alert("No task found with that search query.");
        },
        addTask,
    }));

    return (
        <div className="board">
            {columns.map((col, idx) => (
                <div
                    key={idx}
                    className="column"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                        e.currentTarget.classList.remove("drop-zone-highlight");
                        handleDropInZone(e, null, col.label);
                    }}
                    onDragEnter={(e) => e.currentTarget.classList.add("drop-zone-highlight")}
                    onDragLeave={(e) => e.currentTarget.classList.remove("drop-zone-highlight")}
                >
                    <h3>
                        {col.label}
                        {col.date && (
                            <div className="date-label" style={{ fontSize: "0.8em" }}>
                                {col.date}
                            </div>
                        )}
                        {viewMode === "daily" && (
                            <button className="add-task-btn" onClick={() => addTask(col.label)}>
                                <i className="fa-solid fa-plus"></i>
                            </button>
                        )}
                    </h3>
                    {/* Drop zone at the top of column */}
                    <div
                        className="drop-zone"
                        onDragOver={(e) => e.preventDefault()}
                        onDragEnter={(e) => e.currentTarget.classList.add("drop-zone-highlight")}
                        onDragLeave={(e) => e.currentTarget.classList.remove("drop-zone-highlight")}
                        onDrop={(e) => {
                            e.currentTarget.classList.remove("drop-zone-highlight");
                            handleDropInZone(e, col.tasks[0] ? col.tasks[0].id : null, col.label);
                        }}
                    ></div>
                    {col.tasks.map((tk, index) => (
                        <React.Fragment key={tk.id + "_" + forceCollapse}>
                            <TaskCard
                                task={tk}
                                day={viewMode === "daily" ? col.label : "aggregated"}
                                columnDate={col.columnDate}
                                onUpdate={updateTask}
                                onDelete={deleteTask}
                                onReorder={reorderTask}
                                forceCollapse={forceCollapse}
                                searchTerm={searchTerm}
                            />
                            <div
                                className="drop-zone"
                                onDragOver={(e) => e.preventDefault()}
                                onDragEnter={(e) => e.currentTarget.classList.add("drop-zone-highlight")}
                                onDragLeave={(e) => e.currentTarget.classList.remove("drop-zone-highlight")}
                                onDrop={(e) => {
                                    e.currentTarget.classList.remove("drop-zone-highlight");
                                    handleDropInZone(
                                        e,
                                        col.tasks[index + 1] ? col.tasks[index + 1].id : null,
                                        col.label
                                    );
                                }}
                            ></div>
                        </React.Fragment>
                    ))}
                </div>
            ))}
        </div>
    );
});

export default TaskBoard;