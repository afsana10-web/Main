Views.settings = async function (params, currentUser) {
  return Utils.el(`
    <div>
      <h1>Settings</h1>
      <div class="card" style="margin-bottom:16px; max-width:520px;">
        <h2>Profile</h2>
        <div><strong>Name:</strong> ${Utils.escapeHtml(currentUser.full_name)}</div>
        <div><strong>Officer ID:</strong> ${Utils.escapeHtml(currentUser.officer_id)}</div>
        <div><strong>Role:</strong> ${currentUser.role}</div>
      </div>
      <div class="card" style="max-width:520px;">
        <h2>About PARAKH</h2>
        <p>PARAKH is an inspection-assistance and preliminary compliance-screening system for Legal Metrology (Packaged Commodities) Rules, 2011. It identifies potential non-compliance and evidence for an authorized officer to verify &mdash; it does not make a final legal judgment.</p>
        <div><strong>App Version:</strong> 0.1.0 (prototype)</div>
        <div><strong>OCR Engine:</strong> Tesseract OCR</div>
        <div><strong>Rule Engine Version:</strong> configurable (see Rules)</div>
        <div><strong>API Base:</strong> <span class="mono">${API.BASE_URL}</span></div>
      </div>
    </div>
  `);
};
