// exportCSVHelper.js
import { db } from "./db.js";

export async function exportDexieToCSV() {
    try {
        const tasks = await db.tasks.toArray();
        if (!tasks.length) {
            alert("No tasks in DB to export.");
            return;
        }
        tasks.sort(
            (a, b) =>
                new Date(b.dateModified) - new Date(a.dateModified) ||
                new Date(b.dateAssigned) - new Date(a.dateAssigned)
        );
        const header = [
            "id",
            "title",
            "items",
            "tags",
            "users",
            "urls",
            "attachments",
            "Date Assigned",
            "Date Modified",
            "Expiration Date",
            "color",
            "status",
        ];
        const csvRows = [header.join(",")];
        for (const t of tasks) {
            const itemsStr = Array.isArray(t.items)
                ? t.items.join(" | ")
                : String(t.items ?? "");
            const row = [
                t.id,
                `"${t.title}"`,
                `"${itemsStr}"`,
                `"${t.tags?.map((ch) => ch.text).join(" | ")}"`,
                `"${t.users?.map((u) => u.name).join(" | ")}"`,
                `"${t.urls?.map((u) => u.url).join(" | ")}"`,
                `"${t.attachments?.join(" | ")}"`,
                t.dateAssigned
                    ? new Date(t.dateAssigned).toLocaleDateString(undefined, {
                        day: "numeric",
                        month: "numeric",
                        year: "numeric",
                    })
                    : "",
                t.dateModified ? new Date(t.dateModified).toLocaleDateString() : "",
                t.expirationDate ? new Date(t.expirationDate).toLocaleDateString() : "",
                t.color || "",
                t.status || "",
            ];
            csvRows.push(row.join(","));
        }
        const csvString = csvRows.join("\n");
        const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", "tasks_export.csv");
        link.click();
    } catch (err) {
        console.error("Error exporting Dexie to CSV:", err);
    }
}