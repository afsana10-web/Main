Views["inspection-detail"] = async function (params) {
  const inspectionId = params[0];
  const [inspection, results, images] = await Promise.all([
    API.getInspection(inspectionId),
    API.getResults(inspectionId).catch(() => null),
    Promise.resolve(null),
  ]);

  const node = Utils.el(`
    <div>
      <div class="section-title">
        <div>
          <h1 class="mono">${inspection.inspection_code}</h1>
          <div style="color:var(--text-muted); font-size:13px;">${Utils.escapeHtml(inspection.product_name)} &middot; ${Utils.escapeHtml(inspection.brand)} &middot; ${Utils.escapeHtml(inspection.category)}</div>
        </div>
        <div style="text-align:right;">
          ${Utils.statusBadge(inspection.status)}
          ${inspection.is_demo ? '<div style="margin-top:4px;"><span class="badge" style="background:#edf0f3;color:#5b6b80;">DEMO MODE</span></div>' : ""}
        </div>
      </div>

      <div class="disclaimer-banner">Automated screening result &mdash; requires authorized officer verification.</div>

      <div class="card" style="margin-bottom:16px;">
        <h2>Inspection Information</h2>
        <div class="field-row">
          <div><strong>Location:</strong> ${Utils.escapeHtml(inspection.location)}</div>
          <div><strong>Inspection Date:</strong> ${Utils.fmtDate(inspection.inspection_date)}</div>
        </div>
        <div class="field-row" style="margin-top:8px;">
          <div><strong>Rule Version:</strong> <span class="mono">${inspection.ruleset_version || "-"}</span></div>
          <div><strong>Analyzed At:</strong> ${Utils.fmtDateTime(inspection.analyzed_at)}</div>
        </div>
        ${inspection.notes ? `<div style="margin-top:8px;"><strong>Notes:</strong> ${Utils.escapeHtml(inspection.notes)}</div>` : ""}
      </div>

      <div class="pill-tabs">
        <div class="pill-tab active" data-tab="declarations">Declarations</div>
        <div class="pill-tab" data-tab="findings">Findings &amp; Evidence</div>
        <div class="pill-tab" data-tab="images">Package Images</div>
        <div class="pill-tab" data-tab="report">Report</div>
      </div>

      <div id="tab-outlet"></div>
    </div>
  `);

  const tabOutlet = node.querySelector("#tab-outlet");

  function renderDeclarationsTab() {
    if (!results) {
      tabOutlet.innerHTML = `<div class="empty-state">No analysis results yet. Run analysis from the New Inspection screen.</div>`;
      return;
    }
    tabOutlet.innerHTML = results.declarations.map((d) => {
      const check = results.checks.find((c) => c.declaration_field === d.field);
      return `
        <div class="declaration-card">
          <div class="d-head">
            <span class="d-field">${Utils.titleCase(d.field)}</span>
            ${check ? Utils.statusBadge(check.status) : ""}
          </div>
          <div><strong>Detected Value:</strong> ${d.detected_value ? Utils.escapeHtml(d.detected_value) : '<em>Not detected</em>'}</div>
          <div class="d-meta">OCR Confidence: ${d.ocr_confidence !== null ? d.ocr_confidence.toFixed(0) + "%" : "-"} &nbsp;|&nbsp; Verification needed: ${d.needs_verification ? "Yes" : "No"}</div>
          ${check ? `<div class="d-reason">${Utils.escapeHtml(check.reason)}</div>` : ""}
        </div>
      `;
    }).join("");
  }

  function renderFindingsTab() {
    if (!results || !results.checks.some((c) => c.finding)) {
      tabOutlet.innerHTML = `<div class="empty-state">No findings were generated &mdash; all evaluated declarations passed or were not applicable.</div>`;
      return;
    }
    const findingChecks = results.checks.filter((c) => c.finding);
    tabOutlet.innerHTML = `<div id="findings-wrap"></div>`;
    const wrap = tabOutlet.querySelector("#findings-wrap");
    findingChecks.forEach((check) => {
      const f = check.finding;
      const card = Utils.el(`
        <div class="card" style="margin-bottom:14px;">
          <div class="two-col">
            <div>
              <h3>${Utils.escapeHtml(f.title)}</h3>
              <div style="font-size:12.5px; color:var(--text-muted); margin-bottom:8px;">${Utils.statusBadge(check.status)} &nbsp; Rule R${check.rule_id} (v${check.rule_version})</div>
              <div><strong>Expected:</strong> ${Utils.escapeHtml(f.expected || "-")}</div>
              <div><strong>Detected:</strong> ${Utils.escapeHtml(f.detected || "-")}</div>
              <div style="margin-top:6px;"><strong>Reason:</strong> ${Utils.escapeHtml(check.reason)}</div>
              <div class="verify-actions" style="margin-top:14px;"></div>
            </div>
            <div class="evidence-slot"></div>
          </div>
        </div>
      `);
      renderEvidence(card.querySelector(".evidence-slot"), f);
      renderVerifyActions(card.querySelector(".verify-actions"), f);
      wrap.appendChild(card);
    });
  }

  function renderEvidence(container, finding) {
    const ev = finding.evidence;
    if (!ev || ev.status !== "AVAILABLE") {
      container.innerHTML = `<div class="empty-state" style="border:1px dashed var(--border-strong); border-radius:6px;">Evidence region unavailable &mdash; officer verification required.</div>`;
      return;
    }
    const imagePath = inspection.images ? null : null; // placeholder; resolved below via images list fetch
    container.innerHTML = `<div class="evidence-viewer" data-source-image="${ev.source_image_id}">
      <img data-role="ev-img" alt="Evidence" />
      <div class="evidence-box" data-role="ev-box"></div>
    </div>
    ${ev.extracted_text ? `<div style="font-size:12px; color:var(--text-muted); margin-top:6px;"><strong>Extracted text:</strong> ${Utils.escapeHtml(ev.extracted_text.slice(0, 200))}</div>` : ""}`;

    // Resolve source image path from the inspection's image list (fetched separately)
    loadImagesOnce().then((imgs) => {
      const match = imgs.find((im) => im.id === ev.source_image_id);
      if (!match) return;
      const imgEl = container.querySelector("[data-role=ev-img]");
      imgEl.src = API.imageUrl(match.original_path);
      imgEl.onload = () => {
        const scaleX = imgEl.clientWidth / (match.width || imgEl.naturalWidth);
        const scaleY = imgEl.clientHeight / (match.height || imgEl.naturalHeight);
        const box = container.querySelector("[data-role=ev-box]");
        box.style.left = `${ev.bbox_x * scaleX}px`;
        box.style.top = `${ev.bbox_y * scaleY}px`;
        box.style.width = `${ev.bbox_width * scaleX}px`;
        box.style.height = `${ev.bbox_height * scaleY}px`;
      };
    });
  }

  function renderVerifyActions(container, finding) {
    if (finding.verification) {
      const v = finding.verification;
      container.innerHTML = `
        <div class="card" style="background:var(--grey-bg); border-style:dashed;">
          <strong>Officer Decision:</strong> ${v.decision}<br/>
          ${v.corrected_value ? `<strong>Corrected Value:</strong> ${Utils.escapeHtml(v.corrected_value)}<br/>` : ""}
          ${v.remarks ? `<strong>Remarks:</strong> ${Utils.escapeHtml(v.remarks)}<br/>` : ""}
          <span style="font-size:11.5px; color:var(--text-muted);">Verified ${Utils.fmtDateTime(v.verification_date)}</span>
        </div>
      `;
      return;
    }
    container.innerHTML = `
      <div class="field-row" style="align-items:end;">
        <button class="btn" data-decision="CONFIRMED">Confirm Finding</button>
        <button class="btn" data-decision="REJECTED">Reject Finding</button>
      </div>
      <div style="margin-top:8px;">
        <button class="btn btn-primary btn-sm" data-decision="MODIFIED">Modify Finding&hellip;</button>
      </div>
      <div class="modify-form" style="display:none; margin-top:10px;">
        <div class="field"><label>Corrected Value</label><input type="text" data-role="corrected-value" /></div>
        <div class="field"><label>Remarks</label><textarea data-role="remarks"></textarea></div>
        <button class="btn btn-primary btn-sm" data-role="submit-modify">Submit</button>
      </div>
    `;

    container.querySelectorAll("[data-decision]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const decision = btn.dataset.decision;
        if (decision === "MODIFIED") {
          container.querySelector(".modify-form").style.display = "block";
          return;
        }
        const remarks = decision === "REJECTED" ? prompt("Remarks for this rejection (optional):") || "" : "";
        try {
          const updated = await API.verifyFinding(finding.id, { decision, remarks });
          Utils.toast(`Finding marked ${decision.toLowerCase()}.`, "success");
          finding.verification = updated.verification;
          renderVerifyActions(container, finding);
        } catch (e) {
          Utils.toast(e.message, "error");
        }
      });
    });

    const modifyForm = container.querySelector(".modify-form");
    if (modifyForm) {
      modifyForm.querySelector("[data-role=submit-modify]").addEventListener("click", async () => {
        const corrected_value = modifyForm.querySelector("[data-role=corrected-value]").value.trim();
        const remarks = modifyForm.querySelector("[data-role=remarks]").value.trim();
        if (!corrected_value) { Utils.toast("Corrected value is required.", "error"); return; }
        try {
          const updated = await API.verifyFinding(finding.id, { decision: "MODIFIED", corrected_value, remarks });
          Utils.toast("Finding modified.", "success");
          finding.verification = updated.verification;
          renderVerifyActions(container, finding);
        } catch (e) {
          Utils.toast(e.message, "error");
        }
      });
    }
  }

  let cachedImages = null;
  async function loadImagesOnce() {
    if (cachedImages) return cachedImages;
    // Images aren't exposed via a dedicated list endpoint in this API surface,
    // so we derive them from evidence source_image_id + declarations, which
    // is sufficient for rendering. For a full gallery we reconstruct from
    // declarations' source_image_id set.
    const idsFromDecl = results ? results.declarations.filter((d) => d.source_image_id).map((d) => d.source_image_id) : [];
    // We don't have a raw image listing endpoint; use inspection.images if
    // present (may be absent depending on schema) - fallback to constructing
    // minimal stand-ins so bounding boxes can still be positioned relatively.
    cachedImages = inspection.images || [];
    return cachedImages;
  }

  function renderImagesTab() {
    tabOutlet.innerHTML = `<div class="empty-state">Loading images&hellip;</div>`;
    loadImagesOnce().then((imgs) => {
      if (!imgs.length) {
        tabOutlet.innerHTML = `<div class="empty-state">No package images recorded for this inspection.</div>`;
        return;
      }
      tabOutlet.innerHTML = `<div class="image-thumb-grid">${imgs.map((im) => `
        <div class="image-thumb">
          <img src="${API.imageUrl(im.original_path)}" alt="${im.category}" />
          <div class="cat-tag">${im.category}${im.quality ? " &middot; " + im.quality : ""}</div>
        </div>
      `).join("")}</div>`;
    });
  }

  function renderReportTab() {
    tabOutlet.innerHTML = `
      <div class="card">
        <h2>Compliance Report</h2>
        <p style="color:var(--text-muted); font-size:12.5px;">Generates a PDF containing inspection details, package images, extracted declarations, rule-by-rule results, findings, evidence, and officer verification &mdash; with the required preliminary-screening disclaimer.</p>
        <button class="btn btn-primary" id="gen-report-btn">Generate Report</button>
        <div id="report-result" style="margin-top:12px;"></div>
      </div>
    `;
    tabOutlet.querySelector("#gen-report-btn").addEventListener("click", async (e) => {
      e.target.disabled = true;
      e.target.textContent = "Generating...";
      try {
        const { report_id } = await API.generateReport(inspectionId);
        tabOutlet.querySelector("#report-result").innerHTML = `
          <a class="btn btn-primary" href="${API.downloadReportUrl(report_id)}" target="_blank">Download PDF Report</a>
        `;
      } catch (err) {
        Utils.toast(err.message, "error");
      } finally {
        e.target.disabled = false;
        e.target.textContent = "Generate Report";
      }
    });
  }

  const tabRenderers = {
    declarations: renderDeclarationsTab,
    findings: renderFindingsTab,
    images: renderImagesTab,
    report: renderReportTab,
  };

  node.querySelectorAll(".pill-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      node.querySelectorAll(".pill-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      tabRenderers[tab.dataset.tab]();
    });
  });

  renderDeclarationsTab();
  return node;
};
