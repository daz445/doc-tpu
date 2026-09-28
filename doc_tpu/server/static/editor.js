/* ═══════════════════════════════════════════════════════════
   doc-tpu: Редактор блоков (drag-and-drop, inline-edit)
   Session-aware: API через /api/ses-<id>/...
   ═══════════════════════════════════════════════════════════ */

let blocks = [];
let sortable = null;
let SESSION_ID = "";      // "ses-XXXX" — из URL
let diagramsMap = {};     // {idx: {png_base64}} — отредактированные диаграммы

// ── Определение сессии из URL ───────────────────────────────

function detectSession() {
    const m = window.location.pathname.match(/^\/ses-([a-f0-9]+)/);
    if (m) SESSION_ID = `ses-${m[1]}`;
}

// ── Загрузка блоков ──────────────────────────────────────

async function loadBlocks() {
    try {
        const [blocksResp, staticResp, diagramsResp] = await Promise.all([
            fetch(`/api/${SESSION_ID}/blocks`),
            fetch(`/api/${SESSION_ID}/static`),
            fetch(`/api/${SESSION_ID}/diagrams`),
        ]);

        if (!blocksResp.ok) throw new Error("Ошибка загрузки блоков");

        const data = await blocksResp.json();
        blocks = data.content?.body || [];

        const staticData = staticResp.ok ? await staticResp.json() : {};
        if (diagramsResp.ok) diagramsMap = await diagramsResp.json();

        renderCoverPage(staticData);
        renderBlocks();
        initSortable();
    } catch (e) {
        document.getElementById("blocks-container").innerHTML =
            `<div class="loading" style="color:red">Ошибка: ${e.message}</div>`;
    }
}

// ── Титульная страница ───────────────────────────────────

function renderCoverPage(data) {
    const cover = data.lab || {};
    const student = data.student || {};
    const teacher = data.teacher || {};

    setText("cover-school", "Инженерная школа информационных технологий и робототехники");
    setText("cover-program", "");
    setText("cover-department", "");
    setText("cover-title", cover.title || "");
    setText("cover-subtitle", cover.subtitle || "");
    setText("cover-discipline", cover.discipline ? `по дисциплине ${cover.discipline}` : "");
    setText("cover-variant", cover.variant ? `Вариант ${cover.variant}` : "");

    const sName = toInitials(student.full_name || "");
    const tName = toInitials(teacher.full_name || "");
    const tPos = teacher.position || "";

    const tableHTML = `
        <table>
            <tr>
                <td style="width:30%">Студент</td>
                <td style="width:30%"></td>
                <td style="width:40%; text-align:right">${sName}</td>
            </tr>
            <tr><td colspan="3" style="height:8px"></td></tr>
            <tr>
                <td>Преподаватель</td>
                <td>${tPos}</td>
                <td style="text-align:right">${tName}</td>
            </tr>
        </table>`;
    document.getElementById("cover-table").innerHTML = tableHTML;

    const year = new Date().getFullYear();
    setText("cover-footer", `Томск – ${year}`);
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function toInitials(name) {
    if (!name) return "";
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0];
    if (parts.length === 2) return `${parts[0]} ${parts[1][0]}.`;
    return `${parts[0]} ${parts[1][0]}.${parts[2][0]}.`;
}

// ── Рендер блоков ────────────────────────────────────────

function renderBlocks() {
    const container = document.getElementById("blocks-container");
    container.innerHTML = "";

    blocks.forEach((block, index) => {
        const el = createBlockElement(block, index);
        container.appendChild(el);
    });

    renderMermaidBlocks();
}

function createBlockElement(block, index) {
    const div = document.createElement("div");
    div.className = `block block-${block.type}`;
    div.dataset.index = index;
    div.dataset.type = block.type;

    const controls = document.createElement("div");
    controls.className = "block-controls";
    controls.innerHTML = `
        <button class="drag-handle" title="Перетащить">☰</button>
        <button class="btn-delete" title="Удалить" onclick="deleteBlock(${index})">🗑</button>
    `;
    div.appendChild(controls);

    const content = document.createElement("div");
    content.className = `block-content block-${block.type}`;

    switch (block.type) {
        case "heading":
            content.className += ` block-heading-${block.level || 1}`;
            content.innerHTML = `<div class="block-editable" contenteditable="true"
                data-field="text">${escapeHtml(block.text || "")}</div>`;
            break;

        case "paragraph":
            content.className += " block-paragraph";
            if (block.elements) {
                content.innerHTML = `<div class="block-editable" contenteditable="true"
                    data-field="elements">${elementsToHtml(block.elements)}</div>`;
            } else {
                content.innerHTML = `<div class="block-editable" contenteditable="true"
                    data-field="text">${escapeHtml(block.text || "")}</div>`;
            }
            break;

        case "list":
            content.className += " block-list";
            const tag = block.list_type === "numbered" ? "ol" : "ul";
            const items = (block.items || []).map((item, i) =>
                `<li><div class="block-editable" contenteditable="true"
                    data-field="item" data-item-index="${i}">${escapeHtml(item)}</div></li>`
            ).join("");
            content.innerHTML = `<${tag}>${items}</${tag}>`;
            break;

        case "table":
            content.className += " block-table";
            content.innerHTML = renderTable(block);
            break;

        case "code":
            content.className += " block-code";
            content.innerHTML = `<div class="block-editable" contenteditable="true"
                data-field="text" style="white-space:pre">${escapeHtml(block.text || "")}</div>`;
            break;

        case "mermaid":
            content.className += " block-mermaid";
            content.dataset.blockIndex = index;
            content.onclick = () => openDiagramEditor(index);
            // Номер диаграммы среди mermaid-блоков
            let mermaidNum = 0;
            for (let k = 0; k < index; k++) {
                if (blocks[k] && blocks[k].type === "mermaid") mermaidNum++;
            }
            // Если есть отредактированная версия (PNG из Excalidraw) — показываем её
            const edited = diagramsMap[String(mermaidNum)];
            const inner = edited && edited.png_base64
                ? `<img src="data:image/png;base64,${edited.png_base64}" alt="Диаграмма (отредактировано)" style="max-width:100%">`
                : `<pre class="mermaid">${escapeHtml(block.code || "")}</pre>`;
            content.innerHTML = `
                <div class="mermaid-label">📊 Диаграмма — кликните для редактирования${edited ? " ✏️" : ""}</div>
                <div class="mermaid-render" data-mermaid-index="${index}">${inner}</div>`;
            break;

        case "quote":
            content.className += " block-quote";
            content.innerHTML = `<div class="block-editable" contenteditable="true"
                data-field="text">${escapeHtml(block.text || "")}</div>`;
            break;

        case "separator":
            content.className += " block-separator";
            content.innerHTML = "<hr>";
            break;

        case "image":
            content.className += " block-image";
            const src = block.source || "";
            const alt = block.alt_text || "";
            content.innerHTML = `<img src="${escapeHtml(src)}" alt="${escapeHtml(alt)}">`;
            if (block.caption) {
                content.innerHTML += `<div class="caption">${escapeHtml(block.caption)}</div>`;
            }
            break;

        default:
            content.innerHTML = `<pre>${escapeHtml(JSON.stringify(block, null, 2))}</pre>`;
    }

    div.appendChild(content);

    div.addEventListener("focusout", (e) => {
        if (e.target.classList.contains("block-editable")) {
            updateBlockFromEdit(index, e.target);
        }
    });

    return div;
}

function renderTable(block) {
    const rows = block.content || [];
    if (rows.length === 0) return "<p>Пустая таблица</p>";

    let html = "<table>";
    rows.forEach((row, ri) => {
        html += "<tr>";
        row.forEach(cell => {
            const tag = ri === 0 ? "th" : "td";
            let text = "";
            if (cell.elements) {
                text = cell.elements.map(el => {
                    let t = escapeHtml(el.text || "");
                    if (el.bold) t = `<strong>${t}</strong>`;
                    return t;
                }).join("");
            } else {
                text = escapeHtml(String(cell));
            }
            html += `<${tag}>${text}</${tag}>`;
        });
        html += "</tr>";
    });
    html += "</table>";

    if (block.caption) {
        html += `<div class="caption">${escapeHtml(block.caption)}</div>`;
    }
    return html;
}

// ── Mermaid рендер ───────────────────────────────────────

function renderMermaidBlocks() {
    if (typeof mermaid !== "undefined") {
        mermaid.initialize({ startOnLoad: false, theme: "default" });
        document.querySelectorAll(".mermaid-render .mermaid").forEach(async (el) => {
            try {
                const code = el.textContent;
                const id = `m-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
                const { svg } = await mermaid.render(id, code);
                el.innerHTML = svg;
            } catch (e) {
                el.innerHTML = `<p style="color:red">Ошибка mermaid: ${e.message}</p>`;
            }
        });
    }
}

// ── Drag-and-drop (SortableJS) ───────────────────────────

function initSortable() {
    const container = document.getElementById("blocks-container");
    if (sortable) sortable.destroy();

    sortable = new Sortable(container, {
        handle: ".drag-handle",
        animation: 200,
        ghostClass: "dragging",
        onEnd: (evt) => {
            const [moved] = blocks.splice(evt.oldIndex, 1);
            blocks.splice(evt.newIndex, 0, moved);
            renderBlocks();
            initSortable();
        },
    });
}

// ── Редактирование блоков ────────────────────────────────

function updateBlockFromEdit(blockIndex, el) {
    const field = el.dataset.field;
    const block = blocks[blockIndex];
    if (!block) return;

    const text = el.innerText.trim();

    if (field === "text") {
        block.text = text;
    } else if (field === "item") {
        const itemIndex = parseInt(el.dataset.itemIndex);
        if (block.items) block.items[itemIndex] = text;
    } else if (field === "elements") {
        block.text = text;
        delete block.elements;
    }
}

// ── Удаление блока ───────────────────────────────────────

function deleteBlock(index) {
    if (confirm("Удалить этот блок?")) {
        blocks.splice(index, 1);
        renderBlocks();
        initSortable();
    }
}

// ── Добавление блока ─────────────────────────────────────

function openAddModal() {
    document.getElementById("modal-add").style.display = "flex";
}

function closeModal() {
    document.getElementById("modal-add").style.display = "none";
}

document.getElementById("btn-add-block").addEventListener("click", openAddModal);

document.querySelectorAll(".type-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        addBlock(btn.dataset.type);
        closeModal();
    });
});

function addBlock(type) {
    const newBlock = { type };

    switch (type) {
        case "paragraph":
            newBlock.text = "Новый абзац...";
            break;
        case "heading":
            newBlock.level = 1;
            newBlock.text = "Новый заголовок";
            break;
        case "list":
            newBlock.list_type = "bulleted";
            newBlock.items = ["Пункт 1", "Пункт 2"];
            break;
        case "table":
            newBlock.content = [
                [{elements: [{type: "text", text: "Заголовок", bold: true}]},
                 {elements: [{type: "text", text: "Значение", bold: true}]}],
                [{elements: [{type: "text", text: "Данные"}]},
                 {elements: [{type: "text", text: "0"}]}],
            ];
            break;
        case "code":
            newBlock.text = "// код";
            newBlock.language = "";
            break;
        case "mermaid":
            newBlock.code = "graph TD\n    A[Начало] --> B[Конец]";
            break;
        case "quote":
            newBlock.text = "Цитата...";
            break;
        case "separator":
            break;
    }

    blocks.push(newBlock);
    renderBlocks();
    initSortable();
}

// ── Редактор диаграмм ────────────────────────────────────

function openDiagramEditor(blockIndex) {
    // Ищем mermaid-блок: blockIndex — индекс блока, но нумерация
    // диаграмм ведётся только по mermaid-блокам
    let mermaidIdx = 0;
    for (let i = 0; i < blocks.length; i++) {
        if (blocks[i].type === "mermaid") {
            if (i === parseInt(blockIndex)) {
                // Открываем в новой вкладке: /ses-XXXX/diagram/N
                window.open(`/ses-${SESSION_ID.slice(4)}/diagram/${mermaidIdx}`, "_blank");
                return;
            }
            mermaidIdx++;
        }
    }
}

// ── Утилиты ──────────────────────────────────────────────

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function elementsToHtml(elements) {
    return elements.map(el => {
        let t = escapeHtml(el.text || "");
        if (el.bold) t = `<strong>${t}</strong>`;
        if (el.italic) t = `<em>${t}</em>`;
        return t;
    }).join("");
}

function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.style.display = "block";
    setTimeout(() => { toast.style.display = "none"; }, 3000);
}

// ── Инициализация ────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    detectSession();
    loadBlocks();
});
