/* ═══════════════════════════════════════════════════════════
   doc-tpu: Экспорт и сохранение
   ═══════════════════════════════════════════════════════════ */

// ── Сохранить блоки → content.md ─────────────────────────

document.getElementById("btn-save").addEventListener("click", async () => {
    try {
        const resp = await fetch("/api/blocks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(blocks),
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Ошибка сохранения");
        }

        showToast("✅ content.md сохранён", "success");
    } catch (e) {
        showToast(`❌ ${e.message}`, "error");
    }
});

// ── Экспорт в .docx ──────────────────────────────────────

document.getElementById("btn-export").addEventListener("click", async () => {
    try {
        // Сначала сохраняем
        await fetch("/api/blocks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(blocks),
        });

        // Затем экспортируем
        const resp = await fetch("/api/export/docx");
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Ошибка экспорта");
        }

        // Скачиваем файл
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "report.docx";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showToast("✅ report.docx скачан", "success");
    } catch (e) {
        showToast(`❌ ${e.message}`, "error");
    }
});

// ── Горячие клавиши ──────────────────────────────────────

document.addEventListener("keydown", (e) => {
    // Ctrl+S — сохранить
    if (e.ctrlKey && e.key === "s") {
        e.preventDefault();
        document.getElementById("btn-save").click();
    }
    // Ctrl+E — экспорт
    if (e.ctrlKey && e.key === "e") {
        e.preventDefault();
        document.getElementById("btn-export").click();
    }
});