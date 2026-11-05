# OG Creations — Frontend

A responsive standalone frontend built with HTML5, CSS3 and Vanilla JavaScript.

## Folder structure
- `index.html` — page content and sections
- `css/style.css` — brand styles, responsive layout, transitions and animations
- `js/script.js` — mobile navigation, reveal-on-scroll, portfolio filters and demo contact form
- `assets/images/` — place approved local images here
- `assets/icons/` — place additional icons here

## Run locally
1. Extract the ZIP.
2. Open the folder in VS Code.
3. Open `index.html` in a browser, or use the VS Code Live Server extension.

## Included
- Sticky responsive navigation and animated mobile menu
- Hero banner with reveal animation and moving ticker
- About, services, portfolio, BTS gallery, process, upcoming project and contact sections
- Inline SVG service icons and hover effects
- Portfolio category filters
- Scroll reveal effects using IntersectionObserver
- WhatsApp click-to-chat and telephone/email links
- Responsive desktop, tablet and mobile layouts
- Reduced-motion accessibility support

## Important integration notes
- The contact form currently opens the visitor's email application using `mailto:`. It does **not** save leads to a database.
- Replace the sample Unsplash image URLs with the approved OG Creations assets from the project owner.
- Connect the contact form and dynamic content to the Django backend API before production.
- Confirm the contact number, email, address, project names and all copy with the project owner before launch.
- The page is based on the supplied project brief and brand colours; it has not been verified pixel-for-pixel against the Figma file.
