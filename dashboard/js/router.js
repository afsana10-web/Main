const Router = (() => {
  const routes = {};
  let currentUser = null;

  function register(name, handler) {
    routes[name] = handler;
  }

  function parseHash() {
    const hash = window.location.hash.replace(/^#\/?/, "");
    const [name, ...rest] = hash.split("/");
    return { name: name || "dashboard", params: rest };
  }

  function go(name, ...params) {
    window.location.hash = "#/" + [name, ...params].filter(Boolean).join("/");
  }

  async function renderShell() {
    const shell = document.getElementById("app");
    if (!API.getToken()) {
      shell.innerHTML = "";
      shell.appendChild(Views.login());
      return;
    }
    if (!currentUser) {
      try {
        currentUser = await API.me();
      } catch (e) {
        shell.innerHTML = "";
        shell.appendChild(Views.login());
        return;
      }
    }

    const { name, params } = parseHash();
    shell.innerHTML = "";
    const wrapper = Utils.el(`
      <div class="shell">
        <nav class="sidebar">
          <div class="brand">
            <div class="name">PARAKH</div>
            <div class="tagline">Scan. Analyse. Verify.</div>
          </div>
          <div class="nav-group">
            ${navItem("dashboard", "Dashboard", name)}
            ${navItem("new-inspection", "New Inspection", name)}
            ${navItem("inspections", "Inspections", name)}
            ${navItem("reports", "Reports", name)}
            ${currentUser.role === "ADMIN" ? navItem("rules", "Rules", name) : ""}
            ${currentUser.role === "ADMIN" ? navItem("users", "Users", name) : ""}
            ${navItem("settings", "Settings", name)}
          </div>
          <div class="sidebar-footer">
            OCR Engine: Tesseract<br/>
            Rule Engine: configurable<br/>
            v0.1.0 prototype
          </div>
        </nav>
        <div class="main">
          <div class="topbar">
            <div></div>
            <div class="officer">
              <div><strong>${Utils.escapeHtml(currentUser.full_name)}</strong> <span class="logout-link"><a href="#" id="logout-link">Log out</a></span></div>
              <div>${Utils.escapeHtml(currentUser.officer_id)} &middot; <span class="role-badge">${currentUser.role}</span></div>
            </div>
          </div>
          <div id="view-outlet"></div>
        </div>
      </div>
    `);
    shell.appendChild(wrapper);
    wrapper.querySelector("#logout-link").addEventListener("click", (e) => {
      e.preventDefault();
      API.clearToken();
      currentUser = null;
      go("login");
    });

    const outlet = wrapper.querySelector("#view-outlet");
    const handler = routes[name] || routes["dashboard"];
    try {
      const viewNode = await handler(params, currentUser);
      outlet.appendChild(viewNode);
    } catch (e) {
      outlet.appendChild(Utils.el(`<div class="card">Error loading view: ${Utils.escapeHtml(e.message)}</div>`));
    }
  }

  function navItem(route, label, current) {
    return `<div class="nav-item ${current === route ? "active" : ""}" data-route="${route}">${label}</div>`;
  }

  function bindNavClicks() {
    document.addEventListener("click", (e) => {
      const item = e.target.closest(".nav-item");
      if (item) go(item.dataset.route);
    });
  }

  function invalidateUser() {
    currentUser = null;
  }

  function init() {
    bindNavClicks();
    window.addEventListener("hashchange", renderShell);
    renderShell();
  }

  return { register, go, init, renderShell, invalidateUser, get currentUser() { return currentUser; } };
})();
