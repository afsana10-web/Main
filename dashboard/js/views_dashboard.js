function simpleBarChart(entries, colorFn) {
  const max = Math.max(1, ...entries.map((e) => e.value));
  return `
    <div class="simple-bar-chart">
      ${entries.map((e) => `
        <div class="bar-col">
          <div class="bar-value">${e.value}</div>
          <div class="bar" style="height:${Math.max(4, (e.value / max) * 100)}%; background:${colorFn(e.label)}"></div>
          <div class="bar-label">${Utils.escapeHtml(e.label)}</div>
        </div>
      `).join("")}
    </div>
  `;
}

const STATUS_COLORS = {
  COMPLIANT: "#1e7b3c",
  PASS: "#1e7b3c",
  POTENTIAL_NON_COMPLIANCE: "#b7791f",
  NEEDS_OFFICER_VERIFICATION: "#1b5e9c",
  NEEDS_VERIFICATION: "#1b5e9c",
  PENDING: "#8695a8",
  PROCESSING: "#8695a8",
  FAILED: "#b00020",
  NOT_APPLICABLE: "#c7d0dd",
};

Views.dashboard = async function () {
  const stats = await API.dashboardStats();

  const node = Utils.el(`
    <div>
      <div class="disclaimer-banner">
        PARAKH provides preliminary, evidence-linked compliance screening. All potential findings require authorized officer verification before any enforcement action.
      </div>

      <div class="stat-grid">
        <div class="stat-card"><div class="value">${stats.total_inspections}</div><div class="label">Total Inspections</div></div>
        <div class="stat-card green"><div class="value">${stats.compliant}</div><div class="label">Compliant</div></div>
        <div class="stat-card amber"><div class="value">${stats.potential_issues}</div><div class="label">Potential Issues</div></div>
        <div class="stat-card blue"><div class="value">${stats.pending_verification}</div><div class="label">Pending Verification</div></div>
      </div>

      <div class="two-col">
        <div class="card">
          <h3>Inspections by Status</h3>
          ${simpleBarChart(
            Object.entries(stats.inspections_by_status).map(([label, value]) => ({ label: Utils.titleCase(label), value })),
            (label) => STATUS_COLORS[label.toUpperCase().replace(/ /g, "_")] || "#8695a8"
          )}
        </div>
        <div class="card">
          <h3>Potential Issues by Category</h3>
          ${Object.keys(stats.issues_by_category).length
            ? simpleBarChart(
                Object.entries(stats.issues_by_category).map(([label, value]) => ({ label, value })),
                () => "#b7791f"
              )
            : `<div class="empty-state">No potential issues recorded yet.</div>`}
        </div>
      </div>

      <div class="section-title">
        <h2>Recent Inspections</h2>
        <button class="btn btn-primary btn-sm" id="quick-new">+ Start New Inspection</button>
      </div>
      <div class="card table-wrap">
        <table>
          <thead><tr><th>Inspection ID</th><th>Product</th><th>Category</th><th>Date</th><th>Status</th><th></th></tr></thead>
          <tbody>
            ${stats.recent_inspections.length ? stats.recent_inspections.map((i) => `
              <tr>
                <td class="mono">${i.inspection_code}</td>
                <td>${Utils.escapeHtml(i.product_name)}</td>
                <td>${Utils.escapeHtml(i.category)}</td>
                <td>${Utils.fmtDate(i.inspection_date)}</td>
                <td>${Utils.statusBadge(i.status)}</td>
                <td><a href="#/inspection-detail/${i.id}">View &rarr;</a></td>
              </tr>
            `).join("") : `<tr><td colspan="6"><div class="empty-state">No inspections yet. Start your first inspection to see it here.</div></td></tr>`}
          </tbody>
        </table>
      </div>
    </div>
  `);

  node.querySelector("#quick-new").addEventListener("click", () => Router.go("new-inspection"));
  return node;
};
