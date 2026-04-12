(() => {
    "use strict";

    let totalPages = 0;
    let currentPage = 0;
    let currentZoom = 1.0;

    const canvas = document.getElementById("pdfCanvas");
    const ctx = canvas.getContext("2d");
    const loading = document.getElementById("loading");
    const pageInfo = document.getElementById("pageInfo");
    const zoomLevel = document.getElementById("zoomLevel");
    const textPanel = document.getElementById("textPanel");
    const textContent = document.getElementById("textContent");

    // --- Init ---
    async function init() {
        try {
            const res = await fetch(`/api/documents/${DOC_ID}`);
            if (!res.ok) throw new Error("Document not found");
            const data = await res.json();
            totalPages = data.pages;
            document.title = `DocView — ${data.filename}`;
            await renderPage(0);
        } catch (err) {
            loading.textContent = err.message;
        }
    }

    // --- Render ---
    async function renderPage(pageNum) {
        if (pageNum < 0 || pageNum >= totalPages) return;
        currentPage = pageNum;
        loading.style.display = "block";

        try {
            const res = await fetch(
                `/api/documents/${DOC_ID}/page/${pageNum}?zoom=${currentZoom}`
            );
            if (!res.ok) throw new Error("Render failed");

            const blob = await res.blob();
            const img = await createImageBitmap(blob);

            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);

            pageInfo.textContent = `${currentPage + 1} / ${totalPages}`;
            zoomLevel.textContent = `${Math.round(currentZoom * 100)}%`;
        } catch (err) {
            loading.textContent = err.message;
            return;
        }

        loading.style.display = "none";
    }

    // --- Navigation ---
    document.getElementById("prevBtn").addEventListener("click", () => {
        renderPage(currentPage - 1);
    });

    document.getElementById("nextBtn").addEventListener("click", () => {
        renderPage(currentPage + 1);
    });

    // --- Zoom ---
    document.getElementById("zoomIn").addEventListener("click", () => {
        currentZoom = Math.min(currentZoom + 0.25, 4.0);
        renderPage(currentPage);
    });

    document.getElementById("zoomOut").addEventListener("click", () => {
        currentZoom = Math.max(currentZoom - 0.25, 0.25);
        renderPage(currentPage);
    });

    document.getElementById("fitWidth").addEventListener("click", () => {
        const area = document.getElementById("viewerArea");
        const areaWidth = area.clientWidth - 48; // padding
        // Estimate: at zoom=1.0, image width ≈ page width at 150 DPI
        // Reset to 1.0, render, then compute scale from actual width
        currentZoom = 1.0;
        renderPage(currentPage).then(() => {
            if (canvas.width > 0) {
                currentZoom = Math.min(areaWidth / canvas.width, 4.0);
                currentZoom = Math.max(currentZoom, 0.25);
                renderPage(currentPage);
            }
        });
    });

    // --- Page operations ---
    document.getElementById("rotateBtn").addEventListener("click", async () => {
        try {
            const res = await fetch(`/api/documents/${DOC_ID}/rotate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ page: currentPage, angle: 90 }),
            });
            const data = await res.json();
            if (res.ok) {
                totalPages = data.pages;
                await renderPage(currentPage);
            }
        } catch (err) {
            alert("Rotate failed: " + err.message);
        }
    });

    document.getElementById("deleteBtn").addEventListener("click", async () => {
        if (totalPages <= 1) {
            alert("Cannot delete the last page");
            return;
        }
        if (!confirm(`Delete page ${currentPage + 1}?`)) return;

        try {
            const res = await fetch(`/api/documents/${DOC_ID}/delete-pages`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ pages: [currentPage] }),
            });
            const data = await res.json();
            if (res.ok) {
                totalPages = data.pages;
                if (currentPage >= totalPages) currentPage = totalPages - 1;
                await renderPage(currentPage);
            }
        } catch (err) {
            alert("Delete failed: " + err.message);
        }
    });

    // --- Text extraction ---
    document.getElementById("textBtn").addEventListener("click", async () => {
        textPanel.classList.toggle("open");
        if (!textPanel.classList.contains("open")) return;

        textContent.textContent = "Extracting...";
        try {
            const res = await fetch(`/api/documents/${DOC_ID}/text/${currentPage}`);
            const data = await res.json();
            textContent.textContent = data.text || "(No text found on this page)";
        } catch (err) {
            textContent.textContent = "Error: " + err.message;
        }
    });

    document.getElementById("closeTextBtn").addEventListener("click", () => {
        textPanel.classList.remove("open");
    });

    // --- Download ---
    document.getElementById("downloadBtn").addEventListener("click", () => {
        window.location.href = `/api/documents/${DOC_ID}/download`;
    });

    // --- Keyboard shortcuts ---
    document.addEventListener("keydown", (e) => {
        if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

        switch (e.key) {
            case "ArrowLeft":
            case "PageUp":
                e.preventDefault();
                renderPage(currentPage - 1);
                break;
            case "ArrowRight":
            case "PageDown":
                e.preventDefault();
                renderPage(currentPage + 1);
                break;
            case "+":
            case "=":
                e.preventDefault();
                currentZoom = Math.min(currentZoom + 0.25, 4.0);
                renderPage(currentPage);
                break;
            case "-":
                e.preventDefault();
                currentZoom = Math.max(currentZoom - 0.25, 0.25);
                renderPage(currentPage);
                break;
        }
    });

    init();
})();
