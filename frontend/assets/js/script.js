

document.addEventListener("DOMContentLoaded", () => {
  "use strict";

  // =====================================================
  // 1. COMMON HELPERS
  // =====================================================

  const API = "/api/";

  const get = (id) => document.getElementById(id);

  async function fetchAPI(endpoint) {
    const response = await fetch(API + endpoint, {
      method: "GET",
      headers: {
        Accept: "application/json"
      }
    });

    if (!response.ok) {
      throw new Error(
        `${endpoint} API failed: ${response.status}`
      );
    }

    return response.json();
  }

  function setText(id, value) {
    const element = get(id);

    if (element && value !== null && value !== undefined && value !== "") {
      element.textContent = value;
    }
  }

  function safeUrl(value) {
    if (!value || typeof value !== "string") return "";

    const url = value.trim();

    if (
      url.startsWith("/") ||
      url.startsWith("#") ||
      url.startsWith("https://") ||
      url.startsWith("http://") ||
      url.startsWith("mailto:") ||
      url.startsWith("tel:")
    ) {
      return url;
    }

    return "";
  }

  function setLink(element, url, newTab = false) {
    if (!element) return;

    const validUrl = safeUrl(url);

    if (!validUrl) return;

    element.href = validUrl;

    if (newTab) {
      element.target = "_blank";
      element.rel = "noopener noreferrer";
    }
  }

  function setImage(element, url, alt = "") {
    if (!element) return;

    const validUrl = safeUrl(url);

    if (!validUrl) {
      element.removeAttribute("src");
      element.hidden = true;
      element.style.display = "none";
      return;
    }

    element.src = validUrl;
    element.alt = alt;
    element.hidden = false;
    element.style.display = "";

    element.onerror = () => {
      element.hidden = true;
      element.style.display = "none";
    };
  }

  function createElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) {
      element.className = className;
    }

    if (text !== undefined && text !== null) {
      element.textContent = text;
    }

    return element;
  }

  function normalizeCategory(value) {
    return String(value || "")
      .toLowerCase()
      .trim()
      .replace(/[_\s]+/g, "-");
  }

  function formatDate(value) {
    if (!value) return "";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleDateString("en-IN", {
      month: "short",
      year: "numeric"
    }).toUpperCase();
  }

  function openInNewTab(link, enabled) {
    if (enabled) {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
  }


  // =====================================================
  // 2. MOBILE MENU
  // =====================================================

  const mobileMenuToggle = get("mobile-menu");
  const navMenu = document.querySelector(".nav-menu");

  if (mobileMenuToggle && navMenu) {
    function toggleMenu() {
      navMenu.classList.toggle("active");
    }

    mobileMenuToggle.addEventListener("click", toggleMenu);

    mobileMenuToggle.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggleMenu();
      }
    });

    navMenu.addEventListener("click", (event) => {
      if (event.target.closest("a")) {
        navMenu.classList.remove("active");
      }
    });
  }


  // =====================================================
  // 3. SCROLL FADE-IN ANIMATION
  // =====================================================

  function initializeAnimations() {
    const fadeSections = document.querySelectorAll(
      ".fade-in-section"
    );

    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.15 }
      );

      fadeSections.forEach((section) => {
        observer.observe(section);
      });
    } else {
      fadeSections.forEach((section) => {
        section.classList.add("is-visible");
      });
    }
  }

  initializeAnimations();


  // =====================================================
  // 4. NAVIGATION API
  // GET /api/navigation/
  // =====================================================

  async function loadNavigation() {
    try {
      const data = await fetchAPI("navigation/");

      const navbar = data.navbar || {};
      const items = data.items || [];

      // Navbar brand
      setText(
        "navbar-brand-name",
        navbar.brand_text || "OG CREATIONS"
      );

      // Navbar logo
      const navbarLogo = get("navbar-logo");

      if (navbar.show_logo && navbar.logo) {
        setImage(navbarLogo, navbar.logo, "OG Creations Logo");
      } else if (navbarLogo) {
        navbarLogo.hidden = true;
        navbarLogo.style.display = "none";
      }

      // Navigation links
      const navList = get("navbar-links");

      if (navList && items.length > 0) {
        navList.replaceChildren();

        items.forEach((item) => {
          const li = createElement("li");
          const link = createElement("a", "", item.title);

          setLink(link, item.url);
          openInNewTab(link, item.open_in_new_tab);
          link.classList.add("nav-link");
          li.appendChild(link);

          if (item.children && item.children.length > 0) {
            const childList = createElement("ul");

            item.children.forEach((child) => {
              const childLi = createElement("li");
              const childLink = createElement("a", "", child.title);

              setLink(childLink, child.url);
              openInNewTab(childLink, child.open_in_new_tab);

              childLi.appendChild(childLink);
              childList.appendChild(childLi);
            });

            li.appendChild(childList);
          }

          navList.appendChild(li);
          
        });
        updateActiveNavLink();
      }

      // Navbar CTA
      const cta = navbar.cta || {};
      const ctaElement = get("navbar-cta");

      if (ctaElement && cta.enabled) {
        ctaElement.textContent = `${cta.text} →`;
        setLink(ctaElement, cta.url);
        openInNewTab(ctaElement, cta.open_in_new_tab);
        ctaElement.hidden = false;
      }

    } catch (error) {
      console.error("Navigation loading error:", error);
    }
  }

// Active Navbar Link on Scroll
function updateActiveNavLink() {
  const navLinks = document.querySelectorAll(
    "#navbar-links a.nav-link"
  );

  const sections = document.querySelectorAll(
    "section[id]"
  );

  let currentSection = "";

  sections.forEach((section) => {
    const rect = section.getBoundingClientRect();

    if (rect.top <= 150 && rect.bottom > 150) {
      currentSection = section.id;
    }
  });

  navLinks.forEach((link) => {
    link.classList.remove("active");

    const href = link.getAttribute("href");

    if (href && href.startsWith("#") &&
        href.substring(1) === currentSection) {
      link.classList.add("active");
    }
  });
}

// Scroll and page load
window.addEventListener("scroll", updateActiveNavLink);
window.addEventListener("load", updateActiveNavLink);
  // =====================================================
  // 5. SITE SETTINGS API
  // GET /api/settings/
  // =====================================================

  async function loadSettings() {
    try {
      const data = await fetchAPI("settings/");
            // Floating Phone Button
      const phoneButton = get("floating-phone");

      if (phoneButton && data.phone) {
        const phoneNumber = String(data.phone).replace(/[^\d+]/g, "");
        phoneButton.href = `tel:${phoneNumber}`;
        phoneButton.style.display = "flex";
      } else if (phoneButton) {
        phoneButton.style.display = "none";
      }

      // Floating WhatsApp Button
const whatsappButton = get("floating-whatsapp");

if (whatsappButton) {
    whatsappButton.style.display = "flex";

    if (data.whatsapp_enabled && data.whatsapp_url) {
        whatsappButton.href = data.whatsapp_url;
        whatsappButton.target = "_blank";
        whatsappButton.rel = "noopener noreferrer";
    } else {
        console.warn("WhatsApp settings are missing");
    }
}
      
      setText(
        "navbar-tagline",
        data.tagline || "CONCEPT TO CREATION"
      );

      // Site name
      if (data.site_name) {
        document.title = `${data.site_name} | ${data.tagline || "Concept to Creation"}`;
      }

      // Favicon
      if (data.favicon) {
        let favicon = document.querySelector(
          'link[rel="icon"]'
        );

        if (!favicon) {
          favicon = document.createElement("link");
          favicon.rel = "icon";
          document.head.appendChild(favicon);
        }

        favicon.href = safeUrl(data.favicon);
      }

      // Theme colors
      const root = document.documentElement;

      if (data.background_color) {
        root.style.setProperty(
          "--background-color",
          data.background_color
        );
      }

      if (data.primary_color) {
        root.style.setProperty(
          "--primary-color",
          data.primary_color
        );
      }

      if (data.accent_color) {
        root.style.setProperty(
          "--accent-color",
          data.accent_color
        );
      }

      if (data.secondary_color) {
        root.style.setProperty(
          "--secondary-color",
          data.secondary_color
        );
      }

      if (data.text_color) {
        root.style.setProperty(
          "--text-color",
          data.text_color
        );
      }

    } catch (error) {
      console.error("Settings loading error:", error);
    }
  }


  // =====================================================
  // 6. HERO API
  // GET /api/hero/
  // =====================================================

  async function loadHero() {
    try {
      const data = await fetchAPI("hero/");

      if (!data || Object.keys(data).length === 0) {
        return;
      }

      setText("hero-heading", data.heading);
      setText("hero-subheading", data.subheading);
      setText("hero-description", data.description);

      // Hero background image
      const heroSection = document.querySelector(
        "[data-hero-section]"
      );

      if (heroSection && data.hero_image) {
        const imageUrl = safeUrl(data.hero_image);

        if (imageUrl) {
          heroSection.style.backgroundImage =
            `url("${imageUrl.replace(/"/g, "%22")}")`;
        }
      }

      // Primary button
      const primaryButton = get("hero-primary-button");

      if (primaryButton) {
        if (data.primary_button_text) {
          primaryButton.textContent =
            `${data.primary_button_text} →`;
        }

        setLink(
          primaryButton,
          data.primary_button_url
        );
      }

      // Secondary button
      const secondaryButton = get("hero-secondary-button");

      if (secondaryButton) {
        if (data.secondary_button_text) {
          secondaryButton.textContent =
            data.secondary_button_text;
        }

        setLink(
          secondaryButton,
          data.secondary_button_url
        );
      }

    } catch (error) {
      console.error("Hero loading error:", error);
    }
  }


  // =====================================================
  // 7. STUDIO API
  // GET /api/studio/
  // =====================================================

  async function loadStudio() {
    try {
      const data = await fetchAPI("studio/");

      if (!Array.isArray(data) || data.length === 0) {
        return;
      }

      const studio = data[0];

      setText("studio-heading", studio.title);
      setText("studio-description", studio.description);

      // Main image
      const mainImage = get("studio-image-main");

      setImage(
        mainImage,
        studio.image,
        studio.title || "OG Creations Studio"
      );

      // Additional images
      const images = studio.additional_images || [];

      const image1 = get("studio-image-secondary-1");
      const image2 = get("studio-image-secondary-2");

      setImage(
        image1,
        images[0] && images[0].url,
        images[0] && images[0].alt_text || "Studio image"
      );

      setImage(
        image2,
        images[1] && images[1].url,
        images[1] && images[1].alt_text || "Production image"
      );

    } catch (error) {
      console.error("Studio loading error:", error);
    }
  }


  // =====================================================
  // 8. SERVICES API
  // GET /api/services/
  // =====================================================

  async function loadServices() {
  try {
    const data = await fetchAPI("services/");
    if (!Array.isArray(data) || !data.length) return;

    const grid = get("services-grid");
    if (!grid) return;

    grid.replaceChildren();

    data.forEach((service, index) => {
      const card = createElement("div", "service-card");
      const imageBox = createElement("div", "card-img-box");

      const images = [
        service.image,
        ...(service.additional_images || []).map(item => item.url)
      ].filter(Boolean);

      images.forEach((src, imageIndex) => {
        const image = createElement("img");
        image.loading = "lazy";
        setImage(image, src, service.title || "Service");
        if (imageIndex > 0) image.classList.add("service-extra-image");
        imageBox.appendChild(image);
      });

      imageBox.appendChild(
        createElement("div", "card-number", String(index + 1).padStart(2, "0"))
      );

      const content = createElement("div", "card-content");
      content.appendChild(createElement("h3", "", service.title));
      content.appendChild(
        createElement("p", "", service.short_description || service.description || "")
      );

      card.appendChild(imageBox);
      card.appendChild(content);
      grid.appendChild(card);
    });

  } catch (error) {
    console.error("Services loading error:", error);
  }
}
  
  // =====================================================
  // 9. FEATURED PROJECTS API
  // GET /api/portfolio/?featured=true
  // =====================================================

  async function loadProjects() {
    try {
      const data = await fetchAPI("portfolio/?featured=true");

      if (!Array.isArray(data) || data.length === 0) {
        return;
      }

      const grid = get("projects-grid");

      if (!grid) return;

      grid.replaceChildren();

      data.forEach((project, index) => {
        const category = normalizeCategory(project.category);

        const card = createElement(
          "div",
          index % 2 === 0
            ? "project-card large-card"
            : "project-card small-card"
        );

        card.dataset.category = category;

        const imageBox = createElement(
          "div",
          "project-img-box"
        );

       const projectImages = [
  project.thumbnail,
  ...(project.gallery_images || []).map(item => item.url)
].filter(Boolean);

projectImages.forEach((src, imageIndex) => {
  const image = createElement("img");
  image.loading = "lazy";

  setImage(
    image,
    src,
    project.title || "Portfolio project"
  );

  if (imageIndex > 0) {
    image.classList.add("project-extra-image");
  }

  imageBox.appendChild(image);
});
        

        // Video button
        if (project.video_url) {
          const videoUrl = safeUrl(project.video_url);

          if (videoUrl) {
            const videoButton = createElement(
              "a",
              "play-video-btn"
            );

            videoButton.href = videoUrl;
            videoButton.target = "_blank";
            videoButton.rel = "noopener noreferrer";
            videoButton.setAttribute(
              "aria-label",
              "Watch project video"
            );

            const svg = document.createElementNS(
              "http://www.w3.org/2000/svg",
              "svg"
            );

            svg.setAttribute("width", "24");
            svg.setAttribute("height", "24");
            svg.setAttribute("viewBox", "0 0 24 24");
            svg.setAttribute("fill", "none");

            const polygon = document.createElementNS(
              "http://www.w3.org/2000/svg",
              "polygon"
            );

            polygon.setAttribute(
              "points",
              "5,3 19,12 5,21"
            );

            polygon.setAttribute("fill", "#1F2937");

            svg.appendChild(polygon);
            videoButton.appendChild(svg);

            imageBox.appendChild(videoButton);
          }
        }

        const overlay = createElement(
          "div",
          "project-overlay-info"
        );

        overlay.appendChild(
          createElement(
            "span",
            "proj-cat",
            String(project.category || "").replace(/[_-]/g, " ").toUpperCase()
          )
        );

        overlay.appendChild(
          createElement(
            "h3",
            "proj-title",
            project.title
          )
        );

        imageBox.appendChild(overlay);
        card.appendChild(imageBox);

        grid.appendChild(card);
      });

      initializeProjectFilters();

    } catch (error) {
      console.error("Projects loading error:", error);
    }
  }


  // =====================================================
  // 10. PROJECT FILTER
  // =====================================================

  function initializeProjectFilters() {
    const filterLinks = document.querySelectorAll(
      ".projects-filter-nav .filter-link"
    );

    filterLinks.forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();

        filterLinks.forEach((item) => {
          item.classList.remove("active");
        });

        link.classList.add("active");

        const selectedCategory = normalizeCategory(
          link.dataset.filter
        );

        const cards = document.querySelectorAll(
          ".projects-grid .project-card"
        );

        cards.forEach((card) => {
          const cardCategory = normalizeCategory(
            card.dataset.category
          );

          card.style.display =
            selectedCategory === "all" ||
            cardCategory === selectedCategory
              ? ""
              : "none";
        });
      });
    });
  }

  initializeProjectFilters();


  // =====================================================
  // 11. BTS GALLERY API
  // GET /api/gallery/
  // =====================================================

  
  
async function loadGallery() {
  try {
    const data = await fetchAPI("gallery/");

    if (!Array.isArray(data) || data.length === 0) {
      return;
    }

    const grid = get("bts-grid");
    if (!grid) return;

    grid.replaceChildren();

    data.forEach((item) => {
      const galleryImages = [
        item.image,
        ...(item.additional_images || []).map(img => img.url)
      ].filter(Boolean);

      galleryImages.forEach((src, index) => {
        const card = createElement("div", "bts-card");

        const imageBox = createElement("div", "bts-img-box");

        const image = createElement("img");
        image.loading = "lazy";

        setImage(
          image,
          src,
          item.title || "Behind the scenes"
        );

        imageBox.appendChild(image);

        const caption = createElement("div", "bts-caption");

        caption.appendChild(
          createElement(
            "p",
            "",
            item.title || "BEHIND THE SCENES"
          )
        );

        if (item.description && index === 0) {
          caption.appendChild(
            createElement(
              "span",
              "bts-subtext",
              item.description
            )
          );
        }

        card.appendChild(imageBox);
        card.appendChild(caption);

        grid.appendChild(card);
      });
    });

  } catch (error) {
    console.error("Gallery loading error:", error);
  }
}

  // =====================================================
  // 12. PRODUCTION PROCESS API
  // GET /api/process/
  // =====================================================

  async function loadProcess() {
    try {
      const data = await fetchAPI("process/");

      if (!Array.isArray(data) || data.length === 0) {
        return;
      }

      const grid = get("process-grid");

      if (!grid) return;

      grid.replaceChildren();

      data.forEach((stage) => {
        const card = createElement(
          "div",
          "process-card"
        );

        const iconBox = createElement(
          "div",
          "icon-box"
        );

        if (stage.icon_image) {
          const iconImage = createElement("img");

          setImage(
            iconImage,
            stage.icon_image,
            stage.title || "Process icon"
          );

          iconImage.style.maxWidth = "28px";
          iconImage.style.maxHeight = "28px";

          iconBox.appendChild(iconImage);
        } else if (stage.icon) {
          iconBox.textContent = stage.icon;
        } else {
          iconBox.textContent = "✦";
        }

        card.appendChild(iconBox);

        card.appendChild(
          createElement(
            "span",
            "step-num",
            String(stage.step_number || "").padStart(2, "0")
          )
        );

        card.appendChild(
          createElement(
            "h3",
            "step-title",
            stage.title
          )
        );

        card.appendChild(
          createElement(
            "p",
            "step-desc",
            stage.description
          )
        );

        grid.appendChild(card);
      });

    } catch (error) {
      console.error("Process loading error:", error);
    }
  }


  // =====================================================
  // 13. UPCOMING PROJECTS API
  // GET /api/upcoming/
  // =====================================================

  async function loadUpcoming() {
    try {
      const data = await fetchAPI("upcoming/");

      if (!Array.isArray(data) || data.length === 0) {
        return;
      }

      const container = get("upcoming-container");

      if (!container) return;

      container.replaceChildren();

      data.forEach((project) => {
        const card = createElement(
          "div",
          "upcoming-card"
        );

        const info = createElement(
          "div",
          "upcoming-info-side"
        );

        info.appendChild(
          createElement(
            "span",
            "upcoming-label",
            "UPCOMING —"
          )
        );

        info.appendChild(
          createElement(
            "h3",
            "proj-name",
            project.title
          )
        );

        info.appendChild(
          createElement(
            "p",
            "proj-tagline",
            project.description || ""
          )
        );

        const meta = createElement(
          "div",
          "upcoming-meta"
        );

        if (project.release_date) {
          meta.appendChild(
            createElement(
              "span",
              "release-date",
              formatDate(project.release_date)
            )
          );
        }

        meta.appendChild(
          createElement(
            "span",
            "release-status",
            project.status_display || project.status || "COMING SOON"
          )
        );

        info.appendChild(meta);

        const imageSide = createElement(
          "div",
          "upcoming-img-side"
        );

        const image = createElement("img");
        image.loading = "lazy";

        setImage(
          image,
          project.poster,
          project.title || "Upcoming project"
        );

        imageSide.appendChild(image);

        card.appendChild(info);
        card.appendChild(imageSide);

        container.appendChild(card);
      });

    } catch (error) {
      console.error("Upcoming projects loading error:", error);
    }
  }


  // =====================================================
  // 14. FOOTER API
  // GET /api/footer/
  // =====================================================

  async function loadFooter() {
    try {
      const data = await fetchAPI("footer/");

      // Footer brand
      setText(
        "footer-brand-name",
        data.site_name || "OG CREATIONS"
      );

      setText(
        "footer-description",
        data.description ||
          "Film and creative production, from concept to creation."
      );

      // Footer logo
      setImage(
        get("footer-logo"),
        data.logo,
        "OG Creations Logo"
      );

      // Copyright
      setText(
        "footer-copyright",
        data.copyright ||
          `© ${new Date().getFullYear()} ${data.site_name || "OG Creations"}. All rights reserved.`
      );

      // Social links
      const socialContainer = get(
        "footer-social-links"
      );

      if (socialContainer) {
        socialContainer.replaceChildren();

        (data.social || []).forEach((item) => {
          const url = safeUrl(item.url);

          if (!url) return;

          const link = createElement(
            "a",
            "social-icon",
            item.label || item.platform
          );

          link.href = url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          link.setAttribute(
            "aria-label",
            item.label || item.platform
          );

          socialContainer.appendChild(link);
        });
      }

      // Footer navigation
      const navContainer = get(
        "footer-navigation"
      );

      if (navContainer && Array.isArray(data.groups)) {
        // Footer groups are separate from main navigation.
        // The navigation API supplies the main navigation links.
      }

      // Footer services
      const servicesContainer = get(
        "footer-services"
      );

      if (servicesContainer) {
        const services = await fetchAPI("services/");

        if (Array.isArray(services) && services.length > 0) {
          servicesContainer.replaceChildren();

          services.forEach((service) => {
            const li = createElement("li");
            const link = createElement(
              "a",
              "",
              service.title
            );

            link.href = "#services";

            li.appendChild(link);
            servicesContainer.appendChild(li);
          });
        }
      }

      // Footer contact
      if (data.contact) {
        const contact = data.contact;

        setText(
          "footer-phone",
          contact.phone || ""
        );

        setText(
          "footer-email",
          contact.email || ""
        );

        setText(
          "footer-address",
          contact.address || ""
        );
      }

      // Footer link groups
      if (navContainer && Array.isArray(data.groups) &&
          data.groups.length > 0) {
        const footerLinksColumn = navContainer.closest(
          ".footer-links-col"
        );

        if (footerLinksColumn) {
          const heading = footerLinksColumn.querySelector("h4");

          if (heading) heading.textContent = "NAVIGATE";

          navContainer.replaceChildren();

          data.groups.forEach((group) => {
            (group.links || []).forEach((item) => {
              const li = createElement("li");
              const link = createElement("a", "", item.title);

              setLink(link, item.url);
              openInNewTab(link, item.open_in_new_tab);

              li.appendChild(link);
              navContainer.appendChild(li);
            });
          });
        }
      }

      
      

    } catch (error) {
      console.error("Footer loading error:", error);
    }
  }


  // =====================================================
  // 15. LOCATION API
  // GET /api/location/
  // =====================================================

  async function loadLocation() {
    try {
      const data = await fetchAPI("location/");

      setText(
        "contact-phone",
        data.phone || ""
      );

      setText(
        "contact-email",
        data.email || ""
      );

      setText(
        "contact-address",
        data.full_address || data.address || ""
      );

      // Footer contact
      setText(
        "footer-phone",
        data.phone || ""
      );

      setText(
        "footer-email",
        data.email || ""
      );

      setText(
        "footer-address",
        data.full_address || data.address || ""
      );

      // Map link
      const mapLink = get("contact-map-link");

      if (mapLink) {
        const mapUrl = data.maps_url || data.directions_url;

        if (mapUrl) {
          setLink(mapLink, mapUrl, true);
          mapLink.hidden = false;
        }
      }

    } catch (error) {
      console.error("Location loading error:", error);
    }
  }


  // =====================================================
  // 16. ENQUIRY FORM
  // POST /api/leads/
  // =====================================================

  const projectForm = get("project-form");

  if (projectForm) {
    projectForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const fullName = projectForm.querySelector(
        '[name="full_name"]'
      );

      const phone = projectForm.querySelector(
        '[name="phone_number"]'
      );

      const email = projectForm.querySelector(
        '[name="email"]'
      );

      const service = projectForm.querySelector(
        '[name="service_required"]'
      );

      const details = projectForm.querySelector(
        '[name="project_details"]'
      );

      const messageBox = get("form-messages");

      const submitButton = projectForm.querySelector(
        'button[type="submit"]'
      );

      function showFormMessage(message, type = "error") {
        if (messageBox) {
          messageBox.replaceChildren();

          const alert = createElement(
            "div",
            `alert alert-${type}`,
            message
          );

          messageBox.appendChild(alert);
        } else {
          window.alert(message);
        }
      }

      // Required fields check
      if (
        !fullName ||
        !phone ||
        !email ||
        !service ||
        !details
      ) {
        showFormMessage(
          "Please check the enquiry form fields."
        );
        return;
      }

      const fields = [
        fullName,
        phone,
        email,
        service,
        details
      ];

      fields.forEach((field) => {
        field.style.borderColor = "";
      });

      if (
        !fullName.value.trim() ||
        !phone.value.trim() ||
        !email.value.trim() ||
        !service.value ||
        !details.value.trim()
      ) {
        showFormMessage(
          "Please fill out all required fields."
        );
        return;
      }

      // Phone validation
      const phoneRegex = /^[0-9+()\-\s.]{10,30}$/;

      if (!phoneRegex.test(phone.value.trim())) {
        phone.style.borderColor = "#8D2236";

        showFormMessage(
          "Please enter a valid phone number."
        );

        return;
      }

      // Email validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      if (!emailRegex.test(email.value.trim())) {
        email.style.borderColor = "#8D2236";

        showFormMessage(
          "Please enter a valid email address."
        );

        return;
      }

      const originalButtonText = submitButton
        ? submitButton.textContent
        : "";

      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = "SENDING...";
      }

      try {
        const response = await fetch(API + "leads/", {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
          },

          body: JSON.stringify({
            lead_type: "project",
            name: fullName.value.trim(),
            phone: phone.value.trim(),
            email: email.value.trim(),
            project_type: service.value,
            message: details.value.trim(),
            preferred_contact: "phone"
          })
        });

        const result = await response.json();

        if (!response.ok) {
          let errorMessage =
            "Unable to submit your enquiry. Please try again.";

          const errors = result.errors || result;

          if (errors && typeof errors === "object") {
            const messages = [];

            Object.entries(errors).forEach(([key, value]) => {
              if (Array.isArray(value)) {
                messages.push(
                  `${key}: ${value.join(", ")}`
                );
              } else if (typeof value === "string") {
                messages.push(`${key}: ${value}`);
              }
            });

            if (messages.length > 0) {
              errorMessage = messages.join("\n");
            }
          }

          showFormMessage(errorMessage);
          return;
        }

        showFormMessage(
          result.message ||
          "Thank you! Your enquiry has been received.",
          "success"
        );

        projectForm.reset();

      } catch (error) {
        console.error("Enquiry submission error:", error);

        showFormMessage(
          "Unable to connect to the server. Please try again."
        );

      } finally {
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = originalButtonText;
        }
      }
    });
  }


  // =====================================================
  // 17. LOAD ALL BACKEND CONTENT
  // =====================================================

  async function initializeWebsite() {
    await Promise.allSettled([
      loadSettings(),
      loadNavigation(),
      loadHero(),
      loadStudio(),
      loadServices(),
      loadProjects(),
      loadGallery(),
      loadProcess(),
      loadUpcoming(),
      loadFooter(),
      loadLocation()
    ]);

    console.log("OG Creations website initialization completed.");
  }

  initializeWebsite();


  // =====================================================
  // 18. AUTO-DISMISS ALERT MESSAGES
  // =====================================================

  const alertBoxes = document.querySelectorAll(
    ".form-messages .alert"
  );

  if (alertBoxes.length > 0) {
    setTimeout(() => {
      alertBoxes.forEach((alert) => {
        alert.style.transition =
          "opacity 0.5s ease, transform 0.5s ease";

        alert.style.opacity = "0";
        alert.style.transform = "translateY(-10px)";

        setTimeout(() => alert.remove(), 500);
      });
    }, 5000);
  }
// =========================================
// 19. PUBLIC AI CHAT ASSISTANT
// =========================================

{
    const aiButton = document.getElementById("floating-ai");
    const chatWindow = document.getElementById("ai-chat-window");
    const closeButton = document.getElementById("ai-chat-close");
    const chatForm = document.getElementById("ai-chat-form");
    const chatInput = document.getElementById("ai-chat-input");
    const sendButton = document.getElementById("ai-chat-send");
    const messagesBox = document.getElementById("ai-chat-messages");

    let aiAvailable = false;

    function getAISessionId() {
        let sessionId = sessionStorage.getItem("og_creations_ai_session_id");

        if (!sessionId) {
            if (window.crypto && window.crypto.randomUUID) {
                sessionId = window.crypto.randomUUID().replace(/-/g, "");
            } else {
                sessionId = Date.now().toString(36) +
                    Math.random().toString(36).substring(2) +
                    Math.random().toString(36).substring(2);
            }

            sessionStorage.setItem("og_creations_ai_session_id", sessionId);
        }

        return sessionId;
    }

    function addAIMessage(message, type = "assistant") {
        const messageElement = document.createElement("div");

        messageElement.className =
            type === "user"
                ? "ai-message user-message"
                : "ai-message assistant-message";

        // Safe text rendering: API response is not treated as HTML.
        messageElement.textContent = message;

        messagesBox.appendChild(messageElement);
        messagesBox.scrollTop = messagesBox.scrollHeight;

        return messageElement;
    }

    async function checkAIStatus() {
        try {
            const response = await fetch(`${API}ai/status/`, {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                }
            });

            if (!response.ok) {
                throw new Error("AI status request failed");
            }

            const data = await response.json();

            aiAvailable = data.available === true;

            if (data.welcome_message && messagesBox.children.length === 1) {
                messagesBox.children[0].textContent = data.welcome_message;
            }

        } catch (error) {
            console.error("AI status error:", error);
            aiAvailable = false;
        }
    }

    if (aiButton && chatWindow && closeButton &&
        chatForm && chatInput && sendButton && messagesBox) {

        aiButton.addEventListener("click", () => {
            chatWindow.hidden = !chatWindow.hidden;

            if (!chatWindow.hidden) {
                chatInput.focus();
            }
        });

        closeButton.addEventListener("click", () => {
            chatWindow.hidden = true;
        });

        chatForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const message = chatInput.value.trim();

            if (!message || sendButton.disabled) {
                return;
            }

            addAIMessage(message, "user");
            chatInput.value = "";
            sendButton.disabled = true;
            sendButton.textContent = "Sending...";

            const loadingMessage = addAIMessage("Thinking...");

            try {
                const response = await fetch(`${API}ai/chat/`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: getAISessionId()
                    })
                });

                const data = await response.json();

                loadingMessage.remove();

                if (!response.ok) {
                    throw new Error(
                        data.detail ||
                        data.error ||
                        "Unable to get a response. Please try again."
                    );
                }

                const reply =
                    data.reply ||
                    data.response ||
                    data.answer ||
                    data.message;

                addAIMessage(
                    typeof reply === "string"
                        ? reply
                        : "I couldn't understand the response. Please try again."
                );

            } catch (error) {
                loadingMessage.remove();

                console.error("Public AI chat error:", error);

                addAIMessage(
                    error.message || "Sorry, something went wrong. Please try again."
                );

            } finally {
                sendButton.disabled = false;
                sendButton.textContent = "Send";
                chatInput.focus();
            }
        });

        checkAIStatus();
    }
}
});
