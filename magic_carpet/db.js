// db.js
// Dexie setup, plus withRetry helper, plus methods to add/update/delete tasks.

import Dexie from "dexie";
import { CONFIG, fixTaskItems } from "./config.js";

const db = new Dexie("TaskTrackerDB");

db.version(1).stores({
    tasks: "id, title, items, tags, users, color, urls, attachments, dateAssigned, dateModified, day, expirationDate",
});

db.version(2)
    .stores({
        tasks: "id, title, items, tags, users, color, urls, attachments, dateAssigned, dateModified, day, expirationDate, status",
    })
    .upgrade(async (tx) => {
        const allTasks = await tx.tasks.toArray();
        for (const t of allTasks) {
            if (!t.status) {
                t.status = "Scoping";
            }
            await tx.tasks.put(t);
        }
    });

export { db };

export async function withRetry(operation, maxAttempts = 3) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await operation();
        } catch (error) {
            if (attempt === maxAttempts) throw error;
            await new Promise((res) => setTimeout(res, 1000 * attempt));
        }
    }
}

export async function updateTaskInDB(task) {
    return withRetry(async () => {
        if (!CONFIG.validDays.includes(task.day)) {
            await db.tasks.delete(task.id);
            return;
        }
        fixTaskItems(task);
        task.dateModified = new Date();
        await db.tasks.put(task);
    });
}

export async function deleteTaskFromDB(id) {
    return withRetry(async () => {
        await db.tasks.delete(id);
    });
}

export async function addTaskToDB(task) {
    return withRetry(async () => {
        if (!CONFIG.validDays.includes(task.day)) return;
        fixTaskItems(task);
        task.dateModified = new Date();
        await db.tasks.add(task);
    });
}