Views.inspections = async function () {
  const node = Utils.el(`
    <div>
      <h1>Inspections</h1>
      <div class="filters-bar">
        <div class="field"><label>Search</label><input type="search" id="filt-search" placeholder="Product, brand, or inspection ID" /></div>
        <div class="field">
          <label>Status</label>
          <select id="filt-status">
            <option value="">All</option>
            <option value="COMPLIANT">Compliant</option>
            <option value="POTENTIAL_NON_COMPLIANCE">Potential Non-Compliance</option>
            <option value="NEEDS_OFFICER_VERIFICATION">Needs Verification</option>
            <option value="PENDING">Pending</option>
            <option value="PROCESSING">Processing</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
        <div class="field"><label>Category</label><input type="text" id="filt-category" placeholder="e.g. Food" /></div>
        <button class="btn" id="filt-apply">Apply</button>
      </div>
      <div class="card table-wrap">
        <table>
          <thead><tr><th>Inspection ID</th><th>Product</th><th>Category</th><th>Date</th><th>Status</th><th></th></tr></thead>
          <tbody id="insp-rows"><tr><td colspan="6"><div class="empty-state">Loading...</div></td></tr></tbody>
        </table>
      </div>
    </div>
  `);

  async function load() {
    const rowsEl = node.querySelector("#insp-rows");
    const params = {
      search: node.querySelector("#filt-search").value.trim(),
      status: node.querySelector("#filt-status").value,
      category: node.querySelector("#filt-category").value.trim(),
    };
    try {
      const items = await API.listInspections(params);
      rowsEl.innerHTML = items.length ? items.map((i) => `
        <tr>
          <td class="mono">${i.inspection_code}</td>
          <td>${Utils.escapeHtml(i.product_name)}</td>
          <td>${Utils.escapeHtml(i.category)}</td>
          <td>${Utils.fmtDate(i.inspection_date)}</td>
          <td>${Utils.statusBadge(i.status)}</td>
          <td><a href="#/inspection-detail/${i.id}">View &rarr;</a></td>
        </tr>
      `).join("") : `<tr><td colspan="6"><div class="empty-state">No inspections match these filters.</div></td></tr>`;
    } catch (e) {
      rowsEl.innerHTML = `<tr><td colspan="6"><div class="empty-state">Failed to load inspections: ${Utils.escapeHtml(e.message)}</div></td></tr>`;
    }
  }

  node.querySelector("#filt-apply").addEventListener("click", load);
  node.querySelector("#filt-search").addEventListener("keydown", (e) => { if (e.key === "Enter") load(); });
  load();

  return node;
};
