// SummaryView.js
import React, { useState } from "react";
import { db } from "./db.js";
import { fixTaskItems } from "./config.js";
import { formatDDMMYYYY } from "./utils.js";
import GanttChart from "./GanttChart.js";

// A helper to format date as "mm-dd" for table columns in Gantt.
export function formatMMDD(date) {
    const d = new Date(date);
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return mm + "-" + dd;
}

export default function SummaryView({ allUsers }) {
    const [apiKey, setApiKey] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");
    const [tagFilter, setTagFilter] = useState("");
    const [userFilter, setUserFilter] = useState("");
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [promptText, setPromptText] = useState("");
    const [copied, setCopied] = useState(false);
    const [showAuthFields, setShowAuthFields] = useState(false);
    const [showGantt, setShowGantt] = useState(false);

    const fetchTasksForSummary = async () => {
        try {
            let tasks = await db.tasks.toArray();
            tasks.forEach((tk) => fixTaskItems(tk));
            tasks = tasks.filter((t) => t.day && t.day.length && t.day !== "");

            if (startDate) {
                const sd = new Date(startDate);
                sd.setHours(12, 0, 0, 0);
                tasks = tasks.filter((t) => new Date(t.dateAssigned) >= sd);
            }
            if (endDate) {
                const ed = new Date(endDate);
                ed.setHours(12, 0, 0, 0);
                tasks = tasks.filter((t) => new Date(t.dateAssigned) <= ed);
            }

            if (tagFilter.trim()) {
                tasks = tasks.filter((t) =>
                    t.tags?.some((x) => x.text.toLowerCase().includes(tagFilter.toLowerCase()))
                );
            }
            if (userFilter.trim()) {
                tasks = tasks.filter((t) =>
                    t.users?.some((u) => u.name.toLowerCase().includes(userFilter.toLowerCase()))
                );
            }
            setResults(tasks);
            return tasks;
        } catch (err) {
            console.error(err);
        }
    };

    const generatePrompt = async (existingTasks) => {
        try {
            const tasksToUse = existingTasks ? existingTasks : await fetchTasksForSummary();
            const tableEntries = tasksToUse
                .map(
                    (t) =>
                        `- Title: ${t.title}; Items: ${Array.isArray(t.items) ? t.items.join(", ") : ""
                        }; Tags: ${t.tags?.length
                            ? t.tags.map((x) => x.text).join(", ")
                            : "None"
                        }; Users: ${t.users?.length
                            ? t.users.map((u) => u.name).join(", ")
                            : "None"
                        }; URLs: ${t.urls?.length
                            ? t.urls.map((u) => u.url).join(", ")
                            : "None"
                        };`
                )
                .join("\n");

            const refinedPromptPrefix = `You are a professional business solution consultant. I will provide you with a set of table entries (Title, Items, Tags, Users, URLs). Your job is to:

1. Summarize the table in concise bullet points.
2. Group similar tasks or notes if they share the same Tags or Users.
3. If an entry is missing Items, Tags, Users, or URLs, write "None" for that field.
4. End with a short concluding statement (1–2 sentences) highlighting any patterns or important insights.

Make sure the final output contains:
- Bullet points listing each entry, in a consistent format (e.g., “**Title**: … | **Items**: … | **Tags**: … | **Users**: … | **URLs**: …”).
- No extra commentary beyond this summary.
- A final sentence or two as a conclusion.

Use only the data provided; do not make up additional facts.

Here is the [FILTERED TABLE] data:
`;

            const fullPrompt = refinedPromptPrefix + tableEntries;
            setPromptText(fullPrompt);
        } catch (err) {
            console.error(err);
            setError("Error generating prompt. Please try again.");
        }
    };

    const handlePullData = async () => {
        setLoading(true);
        setError("");
        try {
            const tasks = await fetchTasksForSummary();
            await generatePrompt(tasks);
            if (tasks && tasks.length > 0) {
                setShowGantt(true);
            } else {
                setShowGantt(false);
            }
        } catch (err) {
            console.error(err);
            setError("Error during pull data.");
        } finally {
            setLoading(false);
        }
    };

    const generateSummary = async () => {
        setLoading(true);
        setError("");
        try {
            const tasks = await fetchTasksForSummary();
            const prompt = tasks
                .map(
                    (t) =>
                        `Task Title: ${t.title}\nItems: ${Array.isArray(t.items) ? t.items.join(", ") : ""
                        }\nTags: ${t.tags?.map((x) => x.text).join(", ")}\nUsers: ${t.users
                            ?.map((u) => u.name)
                            .join(", ")}\n`
                )
                .join("\n");
            const response = await fetch("https://api.openai.com/v1/engines/davinci/completions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${apiKey}`,
                },
                body: JSON.stringify({
                    prompt: `Generate a summary for the following tasks:\n${prompt}\nSummary:`,
                    max_tokens: 150,
                    temperature: 0.7,
                }),
            });
            if (!response.ok) {
                throw new Error("API request failed");
            }
            const data = await response.json();
            const summaryText = data.choices[0].text.trim();
            setResults((prev) =>
                prev.map((task) => ({ ...task, summary: summaryText }))
            );
        } catch (err) {
            console.error(err);
            setError("Error generating summary. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const copyPromptToClipboard = () => {
        if (!promptText) return;
        navigator.clipboard.writeText(promptText);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
    };

    return (
        <div className="summary-container">
            <h2>Summary Configuration Panel</h2>
            <button
                className="summary-btn"
                onClick={() => setShowAuthFields(!showAuthFields)}
                style={{ marginBottom: "10px" }}
            >
                {showAuthFields ? "Hide Auth Settings" : "Show Auth Settings"}
            </button>
            {showAuthFields && (
                <div style={{ marginBottom: "15px" }}>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
                        <div style={{ flex: "1 1 200px" }}>
                            <label>API Key:</label>
                            <input
                                type="text"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="Enter API key"
                                className="summary-input"
                            />
                        </div>
                        <div style={{ flex: "1 1 200px" }}>
                            <label>Email Address:</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="Enter email"
                                className="summary-input"
                            />
                        </div>
                        <div style={{ flex: "1 1 200px" }}>
                            <label>Password:</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter password"
                                className="summary-input"
                            />
                        </div>
                    </div>
                </div>
            )}

            <div
                style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "10px",
                    justifyContent: "center",
                    marginTop: "10px",
                }}
            >
                <div style={{ flex: "1 1 200px" }}>
                    <label>Start Date:</label>
                    <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="summary-input"
                    />
                </div>
                <div style={{ flex: "1 1 200px" }}>
                    <label>End Date:</label>
                    <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="summary-input"
                    />
                </div>
                <div style={{ flex: "1 1 200px" }}>
                    <label>Filter by Tag:</label>
                    <input
                        type="text"
                        value={tagFilter}
                        onChange={(e) => setTagFilter(e.target.value)}
                        placeholder="Enter tag text"
                        className="summary-input"
                    />
                </div>
                <div style={{ flex: "1 1 200px" }}>
                    <label>Filter by User:</label>
                    <select
                        value={userFilter}
                        onChange={(e) => setUserFilter(e.target.value)}
                        className="summary-input"
                    >
                        <option value="">Filter User</option>
                        {allUsers.map((u) => (
                            <option key={u} value={u}>
                                {u.charAt(0).toUpperCase() + u.slice(1)}
                            </option>
                        ))}
                    </select>
                </div>
            </div>
            <div style={{ marginTop: "10px", display: "flex", gap: "10px" }}>
                <button className="summary-btn" onClick={handlePullData} disabled={loading}>
                    Pull Data
                </button>
                <button className="summary-btn" onClick={generateSummary} disabled={loading}>
                    {loading ? "Generating..." : "Generate Summary 🚧 Feature in Development!"}
                </button>
            </div>

            {error && <p style={{ color: "red" }}>{error}</p>}
            {results.length > 0 && (
                <div style={{ marginTop: "20px", overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead>
                            <tr>
                                <th style={{ border: "1px solid", padding: "5px" }}>Title</th>
                                <th style={{ border: "1px solid", padding: "5px" }}>Items</th>
                                <th style={{ border: "1px solid", padding: "5px" }}>Tags</th>
                                <th style={{ border: "1px solid", padding: "5px" }}>Users</th>
                                <th style={{ border: "1px solid", padding: "5px" }}>URLs</th>
                                <th style={{ border: "1px solid", padding: "5px" }}>Start Date</th>
                                <th style={{ border: "1px solid", padding: "5px" }}>End Date</th>
                                <th style={{ border: "1px solid", padding: "5px" }}>Summary</th>
                            </tr>
                        </thead>
                        <tbody>
                            {results.map((t) => {
                                const itemsJoined = Array.isArray(t.items)
                                    ? t.items.join(" | ")
                                    : String(t.items ?? "");
                                return (
                                    <tr key={t.id}>
                                        <td style={{ border: "1px solid", padding: "5px" }}>{t.title}</td>
                                        <td style={{ border: "1px solid", padding: "5px" }}>{itemsJoined}</td>
                                        <td style={{ border: "1px solid", padding: "5px" }}>
                                            {t.tags?.map((x) => x.text).join(" | ")}
                                        </td>
                                        <td style={{ border: "1px solid", padding: "5px" }}>
                                            {t.users?.map((u) => u.name).join(" | ")}
                                        </td>
                                        <td style={{ border: "1px solid", padding: "5px" }}>
                                            {t.urls?.map((u) => u.url).join(" | ")}
                                        </td>
                                        <td style={{ border: "1px solid", padding: "5px" }}>
                                            {t.dateAssigned ? formatMMDD(t.dateAssigned) : ""}
                                        </td>
                                        <td style={{ border: "1px solid", padding: "5px" }}>
                                            {t.expirationDate ? formatMMDD(t.expirationDate) : ""}
                                        </td>
                                        <td style={{ border: "1px solid", padding: "5px" }}>
                                            {t.summary || "N/A"}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}

            {promptText && (
                <div style={{ marginTop: "20px" }}>
                    <label>Generated Prompt:</label>
                    <textarea
                        readOnly
                        className="generated-prompt-textarea"
                        value={promptText}
                    />
                    <button className="summary-btn" onClick={copyPromptToClipboard} style={{ marginTop: "10px" }}>
                        {copied ? "Copied" : "Copy"}
                    </button>
                </div>
            )}
            {showGantt && (
                <GanttChart tasks={results} onClose={() => setShowGantt(false)} filterTag={tagFilter} />
            )}
        </div>
    );
}