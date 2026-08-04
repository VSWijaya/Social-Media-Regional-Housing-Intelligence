document.addEventListener("DOMContentLoaded", () => {
  const dashboard = document.getElementById("dashboard");
  const toggleButton = document.getElementById("sidebarToggle");

  const sidebarLinks = document.querySelectorAll(".sidebar-link");
  const topicButtons = document.querySelectorAll(".topic-button");

  const STORAGE_KEY = "sidebarCollapsed";

  // -----------------------------
  // Foldable sidebar
  // -----------------------------
  function saveSidebarState(collapsed) {
    try {
      localStorage.setItem(STORAGE_KEY, String(collapsed));
    } catch (error) {
      console.warn("Could not save sidebar state.", error);
    }
  }

  function loadSidebarState() {
    try {
      return localStorage.getItem(STORAGE_KEY) === "true";
    } catch (error) {
      console.warn("Could not load sidebar state.", error);
      return false;
    }
  }

  function updateSidebar(collapsed) {
    if (!dashboard || !toggleButton) {
      return;
    }

    dashboard.classList.toggle("sidebar-collapsed", collapsed);

    toggleButton.setAttribute("aria-expanded", String(!collapsed));
    toggleButton.setAttribute(
      "aria-label",
      collapsed ? "Expand sidebar" : "Collapse sidebar"
    );

    toggleButton.title = collapsed ? "Expand sidebar" : "Collapse sidebar";

    saveSidebarState(collapsed);
  }

  if (dashboard && toggleButton) {
    updateSidebar(loadSidebarState());

    toggleButton.addEventListener("click", () => {
      const isCollapsed = dashboard.classList.contains("sidebar-collapsed");

      updateSidebar(!isCollapsed);
    });
  }

  // -----------------------------
  // Highlight selected sidebar link
  // -----------------------------
  sidebarLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();

      sidebarLinks.forEach((item) => {
        item.classList.remove("active");
      });

      link.classList.add("active");
    });
  });

  // -----------------------------
  // Highlight selected topic button
  // -----------------------------
  topicButtons.forEach((button) => {
    button.addEventListener("click", () => {
      topicButtons.forEach((item) => {
        item.classList.remove("selected");
      });

      button.classList.add("selected");
    });
  });
});
