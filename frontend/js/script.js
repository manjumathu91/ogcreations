document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menuToggle");
  const navPanel = document.getElementById("navPanel");
  const navLinks = document.querySelectorAll(".nav-link, .btn-cta-nav");

  // Mobile navigation drawer
  const closeMenu = () => {
    if (!menuToggle || !navPanel) return;
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "Open navigation menu");
    navPanel.classList.remove("is-open");
  };

  menuToggle?.addEventListener("click", () => {
    const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
    menuToggle.setAttribute("aria-expanded", String(!isOpen));
    menuToggle.setAttribute("aria-label", isOpen ? "Open navigation menu" : "Close navigation menu");
    navPanel?.classList.toggle("is-open", !isOpen);
  });

  navLinks.forEach(link => link.addEventListener("click", closeMenu));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") closeMenu();
  });

  // Reveal sections as they enter the viewport
  const revealItems = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries, currentObserver) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          currentObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -35px 0px" });
    revealItems.forEach(item => observer.observe(item));
  } else {
    revealItems.forEach(item => item.classList.add("is-visible"));
  }

  // Portfolio category filter
  const filterButtons = document.querySelectorAll(".filter-btn");
  const projectCards = document.querySelectorAll(".project-card");
  filterButtons.forEach(button => {
    button.addEventListener("click", () => {
      const filter = button.dataset.filter;
      filterButtons.forEach(item => item.classList.toggle("active", item === button));
      projectCards.forEach(card => {
        const show = filter === "all" || card.dataset.category === filter;
        card.classList.toggle("is-hidden", !show);
      });
    });
  });

  // Contact form demo: compose an email (replace with Django API integration later)
  const contactForm = document.getElementById("contactForm");
  const formMessage = document.getElementById("formMessage");
  contactForm?.addEventListener("submit", event => {
    event.preventDefault();
    if (!contactForm.reportValidity()) return;
    const data = new FormData(contactForm);
    const subject = encodeURIComponent(`OG Creations enquiry — ${data.get("service")}`);
    const body = encodeURIComponent(
      `Name: ${data.get("name")}\nPhone: ${data.get("phone")}\nEmail: ${data.get("email")}\nService: ${data.get("service")}\n\nProject details:\n${data.get("details") || "Not provided"}`
    );
    if (formMessage) formMessage.textContent = "Opening your email app with the enquiry details…";
    window.location.href = `mailto:ogcreationsofficial@gmail.com?subject=${subject}&body=${body}`;
  });

  const year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
});
