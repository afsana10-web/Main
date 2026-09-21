Router.register("login", Views.login);
Router.register("dashboard", Views.dashboard);
Router.register("new-inspection", Views["new-inspection"]);
Router.register("inspections", Views.inspections);
Router.register("inspection-detail", Views["inspection-detail"]);
Router.register("reports", Views.reports);
Router.register("rules", Views.rules);
Router.register("users", Views.users);
Router.register("settings", Views.settings);

document.addEventListener("DOMContentLoaded", () => Router.init());
