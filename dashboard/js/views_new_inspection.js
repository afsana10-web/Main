Views["new-inspection"] = async function () {
  let stagedFiles = []; // { file, category }

  const node = Utils.el(`
    <div>
      <h1>New Inspection</h1>
      <p style="color:var(--text-muted); margin-bottom:18px;">Capture or upload package images, then run the PARAKH screening pipeline.</p>

      <div class="card" style="margin-bottom:18px;">
        <h2>Product Details</h2>
        <div class="field-row">
          <div class="field"><label>Product Name</label><input type="text" id="f-product" required /></div>
          <div class="field"><label>Brand</label><input type="text" id="f-brand" required /></div>
        </div>
        <div class="field-row">
          <div class="field"><label>Product Category</label><input type="text" id="f-category" placeholder="e.g. Food - Snacks" required /></div>
          <div class="field"><label>Inspection Location</label><input type="text" id="f-location" required /></div>
        </div>
        <div class="field"><label>Notes</label><textarea id="f-notes" placeholder="Optional notes about the inspection context"></textarea></div>
      </div>

      <div class="card" style="margin-bottom:18px;">
        <h2>Package Images</h2>
        <p style="color:var(--text-muted); font-size:12.5px;">Add photos of each visible side of the package. Categorize each image (front, back, side, top, bottom, other).</p>
        <div class="upload-drop" id="upload-drop">
          <input type="file" id="file-input" accept="image/jpeg,image/png,image/webp" multiple style="display:none" />
          <button type="button" class="btn" id="choose-files-btn">Choose Images</button>
          <div style="font-size:12px; margin-top:6px;">JPEG, PNG or WEBP. Camera capture also works on mobile browsers.</div>
        </div>
        <div id="staged-list" style="margin-top:14px;"></div>
      </div>

      <div id="inspection-actions">
        <button class="btn btn-primary" id="start-analysis-btn">START ANALYSIS</button>
      </div>

      <div id="processing-panel" style="display:none; margin-top:18px;"></div>
    </div>
  `);

  const stagedList = node.querySelector("#staged-list");
  const fileInput = node.querySelector("#file-input");

  node.querySelector("#choose-files-btn").addEventListener("click", () => fileInput.click());

  function renderStaged() {
    stagedList.innerHTML = stagedFiles.map((sf, idx) => `
      <div class="upload-row" data-idx="${idx}">
        <select data-role="category">
          ${["FRONT", "BACK", "SIDE", "TOP", "BOTTOM", "OTHER"].map((c) => `<option value="${c}" ${sf.category === c ? "selected" : ""}>${c}</option>`).join("")}
        </select>
        <div class="fname">${Utils.escapeHtml(sf.file.name)}</div>
        <button type="button" class="btn btn-sm" data-role="remove">Remove</button>
      </div>
    `).join("") || `<div class="empty-state" style="padding:16px;">No images added yet.</div>`;

    stagedList.querySelectorAll(".upload-row").forEach((row) => {
      const idx = Number(row.dataset.idx);
      row.querySelector("[data-role=category]").addEventListener("change", (e) => { stagedFiles[idx].category = e.target.value; });
      row.querySelector("[data-role=remove]").addEventListener("click", () => { stagedFiles.splice(idx, 1); renderStaged(); });
    });
  }

  fileInput.addEventListener("change", () => {
    Array.from(fileInput.files).forEach((file) => stagedFiles.push({ file, category: "FRONT" }));
    fileInput.value = "";
    renderStaged();
  });

  renderStaged();

  node.querySelector("#start-analysis-btn").addEventListener("click", async () => {
    const product_name = node.querySelector("#f-product").value.trim();
    const brand = node.querySelector("#f-brand").value.trim();
    const category = node.querySelector("#f-category").value.trim();
    const location = node.querySelector("#f-location").value.trim();
    const notes = node.querySelector("#f-notes").value.trim();

    if (!product_name || !brand || !category || !location) {
      Utils.toast("Please fill in all required product details.", "error");
      return;
    }
    if (stagedFiles.length === 0) {
      Utils.toast("Please add at least one package image.", "error");
      return;
    }

    const actionsBox = node.querySelector("#inspection-actions");
    const panel = node.querySelector("#processing-panel");
    actionsBox.innerHTML = `<button class="btn btn-primary" disabled>Processing...</button>`;
    panel.style.display = "block";

    const stages = [
      "Images Received", "Image Preprocessing", "OCR & Text Extraction",
      "Declaration Identification", "Rule-Based Validation", "Evidence Generation", "Preparing Results",
    ];
    let stageIdx = 0;
    function renderStages() {
      panel.innerHTML = `
        <div class="card">
          <h3>Analysis in Progress</h3>
          <ul style="list-style:none; padding:0; margin:10px 0 0 0; font-size:13px;">
            ${stages.map((s, i) => `<li style="padding:4px 0; color:${i <= stageIdx ? "var(--text)" : "var(--text-faint)"}">${i < stageIdx ? "&#10003;" : (i === stageIdx ? "&rarr;" : "&#9675;")} ${s}</li>`).join("")}
          </ul>
        </div>
      `;
    }
    renderStages();
    const tick = setInterval(() => {
      if (stageIdx < stages.length - 1) { stageIdx++; renderStages(); }
    }, 900);

    try {
      const inspection = await API.createInspection({ product_name, brand, category, location, notes });
      const formData = new FormData();
      stagedFiles.forEach((sf) => {
        formData.append("files", sf.file);
        formData.append("categories", sf.category);
      });
      await API.uploadImages(inspection.id, formData);
      stageIdx = 2;
      renderStages();
      const analyzed = await API.analyzeInspection(inspection.id);
      clearInterval(tick);
      stageIdx = stages.length - 1;
      renderStages();
      Utils.toast("Analysis complete.", "success");
      setTimeout(() => Router.go("inspection-detail", analyzed.id), 500);
    } catch (err) {
      clearInterval(tick);
      Utils.toast(err.message || "Analysis failed", "error");
      actionsBox.innerHTML = `<button class="btn btn-primary" id="start-analysis-btn-retry">START ANALYSIS</button>`;
      panel.style.display = "none";
    }
  });

  return node;
};
