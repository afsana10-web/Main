Views.rules = async function (params, user) {
  if (user.role !== "ADMIN") {
    return Utils.el(`<div class="empty-state">Rule management is restricted to ADMIN users.</div>`);
  }

  const node = Utils.el(`
    <div>
      <div class="section-title">
        <h1>Rule Management</h1>
        <button class="btn btn-primary btn-sm" id="new-rule-btn">+ Add Rule</button>
      </div>
      <p style="color:var(--text-muted);">Compliance rules are configurable and versioned &mdash; they are never hard-coded into the screening logic.</p>
      <div id="rule-form-slot"></div>
      <div class="card table-wrap">
        <table>
          <thead><tr><th>Rule Code</th><th>Name</th><th>Category</th><th>Method</th><th>Version</th><th>Status</th><th>Updated</th><th></th></tr></thead>
          <tbody id="rule-rows"><tr><td colspan="8"><div class="empty-state">Loading...</div></td></tr></tbody>
        </table>
      </div>
    </div>
  `);

  async function loadRules() {
    const rules = await API.listRules();
    node.querySelector("#rule-rows").innerHTML = rules.map((r) => `
      <tr data-id="${r.id}">
        <td class="mono">${r.rule_code}</td>
        <td>${Utils.escapeHtml(r.rule_name)}</td>
        <td>${Utils.titleCase(r.category)}</td>
        <td>${r.validation_method}</td>
        <td class="mono">${r.version}</td>
        <td>${r.status === "ACTIVE" ? '<span class="badge badge-compliant">ACTIVE</span>' : '<span class="badge" style="background:#edf0f3;color:#5b6b80;">' + r.status + '</span>'}</td>
        <td>${Utils.fmtDate(r.updated_at)}</td>
        <td>
          <button class="btn btn-sm" data-role="edit">Edit</button>
          ${r.status === "ACTIVE" ? '<button class="btn btn-sm" data-role="deactivate">Deactivate</button>' : ""}
        </td>
      </tr>
    `).join("");

    node.querySelectorAll("[data-role=deactivate]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.closest("tr").dataset.id;
        if (!confirm("Deactivate this rule? Past inspections keep their recorded rule version.")) return;
        await API.deactivateRule(id);
        Utils.toast("Rule deactivated.", "success");
        loadRules();
      });
    });
    node.querySelectorAll("[data-role=edit]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.closest("tr").dataset.id;
        const rule = rules.find((r) => String(r.id) === id);
        showForm(rule);
      });
    });
  }

  function showForm(rule) {
    const isEdit = !!rule;
    const slot = node.querySelector("#rule-form-slot");
    slot.innerHTML = `
      <div class="card" style="margin-bottom:16px;">
        <h2>${isEdit ? "Edit Rule " + rule.rule_code : "New Rule"}</h2>
        <div class="field-row">
          <div class="field"><label>Rule Code</label><input type="text" id="rf-code" value="${isEdit ? rule.rule_code : ""}" ${isEdit ? "disabled" : ""} /></div>
          <div class="field"><label>Category (Declaration Field)</label><input type="text" id="rf-category" value="${isEdit ? rule.category : ""}" placeholder="e.g. MRP" /></div>
        </div>
        <div class="field"><label>Rule Name</label><input type="text" id="rf-name" value="${isEdit ? Utils.escapeHtml(rule.rule_name) : ""}" /></div>
        <div class="field-row">
          <div class="field">
            <label>Validation Method</label>
            <select id="rf-method">
              ${["REQUIRED_PRESENT", "REGEX_MATCH", "NUMERIC_RANGE", "NOT_APPLICABLE"].map((m) => `<option value="${m}" ${isEdit && rule.validation_method === m ? "selected" : ""}>${m}</option>`).join("")}
            </select>
          </div>
          <div class="field"><label>Version</label><input type="text" id="rf-version" value="${isEdit ? rule.version : "LMPC-2011-R1"}" /></div>
        </div>
        <div class="field"><label>Validation Params (JSON)</label><textarea id="rf-params">${isEdit ? Utils.escapeHtml(rule.validation_params || "{}") : "{}"}</textarea></div>
        <div class="field"><label>Reason Template</label><textarea id="rf-reason">${isEdit ? Utils.escapeHtml(rule.reason_template) : "Checked: {value}"}</textarea></div>
        <div class="field"><label>Legal Reference</label><input type="text" id="rf-legal" value="${isEdit ? Utils.escapeHtml(rule.legal_reference || "") : ""}" /></div>
        <button class="btn btn-primary btn-sm" id="rf-submit">${isEdit ? "Save Changes" : "Create Rule"}</button>
        <button class="btn btn-sm" id="rf-cancel">Cancel</button>
      </div>
    `;

    slot.querySelector("#rf-cancel").addEventListener("click", () => { slot.innerHTML = ""; });
    slot.querySelector("#rf-submit").addEventListener("click", async () => {
      const payload = {
        rule_name: slot.querySelector("#rf-name").value.trim(),
        category: slot.querySelector("#rf-category").value.trim(),
        validation_method: slot.querySelector("#rf-method").value,
        validation_params: slot.querySelector("#rf-params").value.trim(),
        reason_template: slot.querySelector("#rf-reason").value.trim(),
        version: slot.querySelector("#rf-version").value.trim(),
        legal_reference: slot.querySelector("#rf-legal").value.trim(),
      };
      try {
        if (isEdit) {
          await API.updateRule(rule.id, payload);
          Utils.toast("Rule updated.", "success");
        } else {
          payload.rule_code = slot.querySelector("#rf-code").value.trim();
          await API.createRule(payload);
          Utils.toast("Rule created.", "success");
        }
        slot.innerHTML = "";
        loadRules();
      } catch (e) {
        Utils.toast(e.message, "error");
      }
    });
  }

  node.querySelector("#new-rule-btn").addEventListener("click", () => showForm(null));

  await loadRules();
  return node;
};
