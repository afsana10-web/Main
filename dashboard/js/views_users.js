Views.users = async function (params, currentUser) {
  if (currentUser.role !== "ADMIN") {
    return Utils.el(`<div class="empty-state">User management is restricted to ADMIN users.</div>`);
  }

  const node = Utils.el(`
    <div>
      <div class="section-title">
        <h1>User Management</h1>
        <button class="btn btn-primary btn-sm" id="new-user-btn">+ Add User</button>
      </div>
      <div id="user-form-slot"></div>
      <div class="card table-wrap">
        <table>
          <thead><tr><th>Name</th><th>Officer ID</th><th>Role</th><th>Status</th><th>Last Login</th><th></th></tr></thead>
          <tbody id="user-rows"><tr><td colspan="6"><div class="empty-state">Loading...</div></td></tr></tbody>
        </table>
      </div>
    </div>
  `);

  async function loadUsers() {
    const users = await API.listUsers();
    node.querySelector("#user-rows").innerHTML = users.map((u) => `
      <tr data-id="${u.id}">
        <td>${Utils.escapeHtml(u.full_name)}</td>
        <td class="mono">${u.officer_id}</td>
        <td>${u.role}</td>
        <td>${u.is_active ? '<span class="badge badge-compliant">ACTIVE</span>' : '<span class="badge badge-failed">INACTIVE</span>'}</td>
        <td>-</td>
        <td>
          <button class="btn btn-sm" data-role="toggle">${u.is_active ? "Deactivate" : "Activate"}</button>
        </td>
      </tr>
    `).join("");

    node.querySelectorAll("[data-role=toggle]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.closest("tr").dataset.id;
        const user = users.find((u) => String(u.id) === id);
        if (user.is_active) {
          await API.deactivateUser(id);
        } else {
          await API.updateUser(id, { is_active: true });
        }
        Utils.toast("User updated.", "success");
        loadUsers();
      });
    });
  }

  node.querySelector("#new-user-btn").addEventListener("click", () => {
    const slot = node.querySelector("#user-form-slot");
    slot.innerHTML = `
      <div class="card" style="margin-bottom:16px;">
        <h2>New User</h2>
        <div class="field-row">
          <div class="field"><label>Full Name</label><input type="text" id="uf-name" /></div>
          <div class="field"><label>Officer ID</label><input type="text" id="uf-officer-id" /></div>
        </div>
        <div class="field-row">
          <div class="field"><label>Email</label><input type="email" id="uf-email" /></div>
          <div class="field"><label>Role</label>
            <select id="uf-role"><option value="OFFICER">OFFICER</option><option value="ADMIN">ADMIN</option></select>
          </div>
        </div>
        <div class="field"><label>Temporary Password</label><input type="text" id="uf-password" /></div>
        <button class="btn btn-primary btn-sm" id="uf-submit">Create User</button>
        <button class="btn btn-sm" id="uf-cancel">Cancel</button>
      </div>
    `;
    slot.querySelector("#uf-cancel").addEventListener("click", () => { slot.innerHTML = ""; });
    slot.querySelector("#uf-submit").addEventListener("click", async () => {
      try {
        await API.createUser({
          full_name: slot.querySelector("#uf-name").value.trim(),
          officer_id: slot.querySelector("#uf-officer-id").value.trim(),
          email: slot.querySelector("#uf-email").value.trim(),
          role: slot.querySelector("#uf-role").value,
          password: slot.querySelector("#uf-password").value,
        });
        Utils.toast("User created.", "success");
        slot.innerHTML = "";
        loadUsers();
      } catch (e) {
        Utils.toast(e.message, "error");
      }
    });
  });

  await loadUsers();
  return node;
};
