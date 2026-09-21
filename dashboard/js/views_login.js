const Views = {};

Views.login = function () {
  const node = Utils.el(`
    <div class="login-screen">
      <div class="login-card">
        <div class="brand-mark">PARAKH</div>
        <div class="brand-sub">Scan. Analyse. Verify. &mdash; Legal Metrology Compliance Screening</div>
        <div id="login-error" style="display:none" class="login-error"></div>
        <form id="login-form">
          <div class="field">
            <label>Officer ID / Email</label>
            <input type="text" id="login-officer-id" required autocomplete="username" />
          </div>
          <div class="field">
            <label>Password</label>
            <div style="position:relative">
              <input type="password" id="login-password" required autocomplete="current-password" style="padding-right:60px" />
              <button type="button" id="toggle-pw" class="btn btn-sm" style="position:absolute; right:4px; top:4px; padding:4px 8px;">Show</button>
            </div>
          </div>
          <button type="submit" class="btn btn-primary" style="width:100%; justify-content:center;" id="login-submit">Log In</button>
        </form>
        <div class="demo-creds">
          Demo credentials &mdash; Admin: ADMIN001 / Admin@123 &nbsp;|&nbsp; Officer: OFF1001 / Officer@123
        </div>
      </div>
    </div>
  `);

  const form = node.querySelector("#login-form");
  const errorBox = node.querySelector("#login-error");
  const submitBtn = node.querySelector("#login-submit");
  const pwInput = node.querySelector("#login-password");

  node.querySelector("#toggle-pw").addEventListener("click", (e) => {
    pwInput.type = pwInput.type === "password" ? "text" : "password";
    e.target.textContent = pwInput.type === "password" ? "Show" : "Hide";
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorBox.style.display = "none";
    submitBtn.disabled = true;
    submitBtn.textContent = "Logging in...";
    try {
      const officerId = node.querySelector("#login-officer-id").value.trim();
      const password = pwInput.value;
      const { access_token } = await API.login(officerId, password);
      API.setToken(access_token);
      Router.invalidateUser();
      Router.go("dashboard");
      Router.renderShell();
    } catch (err) {
      errorBox.textContent = err.message || "Login failed";
      errorBox.style.display = "block";
      submitBtn.disabled = false;
      submitBtn.textContent = "Log In";
    }
  });

  return node;
};
