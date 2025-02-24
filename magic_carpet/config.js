// config.js

export const CONFIG = {
    validDays: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    colors: {
        preset: [
            "#000000",
            "#CC3A0F",
            "#00573C",
            "#C80058",
            "#4A1589",
            "#654100",
            "#004B8C",
            "#1A3636",
            "#660066",
            "#003C4D",
        ],
        brand: {
            yellow: "#ffd700",
        },
    },
    views: {
        daily: { minOffset: -52, maxOffset: 52 },
        weekly: { minOffset: -13, maxOffset: 13 },
        monthly: { minOffset: -5, maxOffset: 5 },
    },
    dateFormat: {
        short: { day: "numeric", month: "numeric" },
        long: { month: "long", year: "numeric" },
    },
};

export function fixTaskItems(task) {
    if (!task.items) {
        task.items = [];
    } else if (!Array.isArray(task.items)) {
        if (typeof task.items === "string" && task.items.trim().length) {
            task.items = [task.items];
        } else {
            task.items = [];
        }
    }
    if (!task.status) {
        task.status = "Scoping";
    }
    return task;
}