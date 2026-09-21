Views.reports = async function () {
  const node = Utils.el(`
    <div>
      <h1>Reports</h1>
      <p style="color:var(--text-muted);">Generate and download PDF compliance reports for any inspection.</p>
      <div class="card table-wrap">
        <table>
          <thead><tr><th>Inspection ID</th><th>Product</th><th>Status</th><th>Date</th><th></th></tr></thead>
          <tbody id="rep-rows"><tr><td colspan="5"><div class="empty-state">Loading...</div></td></tr></tbody>
        </table>
      </div>
    </div>
  `);

  const items = await API.listInspections();
  const rowsEl = node.querySelector("#rep-rows");
  rowsEl.innerHTML = items.length ? items.map((i) => `
    <tr data-id="${i.id}">
      <td class="mono">${i.inspection_code}</td>
      <td>${Utils.escapeHtml(i.product_name)}</td>
      <td>${Utils.statusBadge(i.status)}</td>
      <td>${Utils.fmtDate(i.inspection_date)}</td>
      <td><button class="btn btn-sm" data-role="gen">Generate &amp; Download</button></td>
    </tr>
  `).join("") : `<tr><td colspan="5"><div class="empty-state">No inspections available yet.</div></td></tr>`;

  rowsEl.querySelectorAll("[data-role=gen]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.closest("tr").dataset.id;
      btn.disabled = true;
      btn.textContent = "Generating...";
      try {
        const { report_id } = await API.generateReport(id);
        window.open(API.downloadReportUrl(report_id), "_blank");
      } catch (e) {
        Utils.toast(e.message, "error");
      } finally {
        btn.disabled = false;
        btn.textContent = "Generate & Download";
      }
    });
  });

  return node;
};
