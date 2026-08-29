// Frontend Interactions for QR Contact System

document.addEventListener("DOMContentLoaded", () => {
    // 1. Client-Side Search Filtering for the Tag Table
    const searchInput = document.getElementById("tagSearch");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase().strip();
            const rows = document.querySelectorAll(".tag-row");
            rows.forEach((row) => {
                const tagId = row.dataset.tagId.toLowerCase();
                const name = (row.dataset.name || "").toLowerCase();
                if (tagId.includes(query) || name.includes(query)) {
                    row.classList.remove("hidden");
                } else {
                    row.classList.add("hidden");
                }
            });
        });
    }

    // String strip utility for JS
    if (!String.prototype.strip) {
        String.prototype.strip = function () {
            return this.trim();
        };
    }

    // 2. Clipboard Copy with Visual Toast Feedback
    const copyButtons = document.querySelectorAll(".copy-link-btn");
    copyButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const url = btn.dataset.url;
            navigator.clipboard.writeText(url).then(() => {
                // Show a brief success tooltip or toast
                const originalText = btn.innerHTML;
                btn.innerHTML = `<svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>`;
                btn.classList.add("bg-emerald-950/30", "border-emerald-500/50");
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.classList.remove("bg-emerald-950/30", "border-emerald-500/50");
                }, 1500);
            }).catch(err => {
                console.error("Failed to copy URL: ", err);
            });
        });
    });

    // 3. Live QR Code Preview & Customization Handler
    const customizerForm = document.getElementById("qrCustomizerForm");
    const previewImg = document.getElementById("qrPreviewImage");
    const previewSpinner = document.getElementById("previewSpinner");
    const downloadBtn = document.getElementById("downloadQrBtn");
    
    // We update the preview dynamically when inputs change
    if (customizerForm && previewImg) {
        const updatePreview = async () => {
            // Show loading spinner
            if (previewSpinner) previewSpinner.classList.remove("hidden");
            
            const formData = new FormData(customizerForm);
            
            try {
                // POST form details to preview API which supports colors & files
                const response = await fetch("/api/qr/preview", {
                    method: "POST",
                    body: formData
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const oldUrl = previewImg.src;
                    
                    // Revoke old object URL to prevent memory leaks
                    if (oldUrl.startsWith("blob:")) {
                        URL.revokeObjectURL(oldUrl);
                    }
                    
                    const newUrl = URL.createObjectURL(blob);
                    previewImg.src = newUrl;
                } else {
                    console.error("Failed to fetch QR preview");
                }
            } catch (err) {
                console.error("Error loading QR preview:", err);
            } finally {
                if (previewSpinner) previewSpinner.classList.add("hidden");
            }
        };

        // Attach event listeners to all fields
        const interactiveFields = customizerForm.querySelectorAll("input:not([type='file']), select");
        interactiveFields.forEach((field) => {
            field.addEventListener("change", updatePreview);
            if (field.tagName === "INPUT" && field.type === "color") {
                // Instantly update on drag
                field.addEventListener("input", updatePreview);
            }
        });

        // For logo files, we update on file change
        const fileInput = document.getElementById("logoUpload");
        if (fileInput) {
            fileInput.addEventListener("change", () => {
                // Display file name in UI if needed
                const fileLabel = document.getElementById("logoFileName");
                if (fileLabel) {
                    fileLabel.textContent = fileInput.files.length > 0 ? fileInput.files[0].name : "No file chosen";
                }
                updatePreview();
            });
        }

        // Initialize preview on page load
        updatePreview();

        // 4. Download handler for single QR
        if (downloadBtn) {
            downloadBtn.addEventListener("click", (e) => {
                e.preventDefault();
                const tagSelect = document.getElementById("tagSelect");
                if (!tagSelect || !tagSelect.value) return;
                
                const tagId = tagSelect.value;
                const fgColor = encodeURIComponent(document.getElementById("fgColor").value);
                const bgColor = encodeURIComponent(document.getElementById("bgColor").value);
                const ecc = document.getElementById("eccLevel").value;
                
                // Construct a URL for direct browser download
                // Note: file downloads with logo uploads require posting the form.
                // If there's a logo, we submit the form directly to the download endpoint.
                if (fileInput && fileInput.files.length > 0) {
                    customizerForm.action = "/api/qr/download";
                    customizerForm.method = "POST";
                    customizerForm.submit();
                } else {
                    // Standard GET request for download without logo
                    window.location.href = `/api/qr/download-simple?tag_id=${tagId}&fg_color=${fgColor}&bg_color=${bgColor}&ecc=${ecc}`;
                }
            });
        }
    }

    // 5. Autoselect Tag in Customizer on clicking table row action
    const configureButtons = document.querySelectorAll(".configure-tag-btn");
    configureButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const tagId = btn.dataset.tagId;
            const tagSelect = document.getElementById("tagSelect");
            if (tagSelect) {
                tagSelect.value = tagId;
                // Dispatch change event to update preview
                tagSelect.dispatchEvent(new Event("change"));
                
                // Scroll customizer into view on mobile
                const customizerSection = document.getElementById("customizerSection");
                if (customizerSection) {
                    customizerSection.scrollIntoView({ behavior: "smooth" });
                }
            }
        });
    });
});
