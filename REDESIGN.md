# Handcrafted Marketplace frontend

The existing Django application now uses a shared cream, terracotta, blush, sage, and mocha design system. Templates remain connected to the existing SQLite database and custom user model. No model changes or migrations were made, and the original database was not seeded or reset.

## Preview

From the project directory in PowerShell:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001 --no-color
```

Open http://127.0.0.1:8001/ . Port 8001 avoids the unrelated Django server already running on port 8000 at implementation time. Stop the server with Ctrl+C. For a new environment, create a virtual environment and install `requirements.txt` first.

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

Tests create a separate temporary database and temporary media directory; they do not add example listings to the real database.

## Changed files and pages

- `static/css/style.css`: reusable design tokens, typography, cards, forms, layouts, accessible focus styles, responsive breakpoints, and reduced-motion support.
- `static/js/site.js`: image gallery, quantity controls, seller registration field visibility, navigation states, image fallback, and mobile search panel.
- `static/images/`: original botanical-style SVG placeholders and an AI-generated decorative still-life photograph.
- `templates/base.html`, all existing page templates, and new `templates/partials/`: shared navigation, footer, alerts, product/category/seller cards, status badges, forms, pagination, seller sidebar, and order summaries.
- New templates: `checkout.html`, `register.html`, `makers.html`, `about.html`, and `for_sellers.html`.
- `handcrafted_app/views.py`: database-backed homepage and related products, catalog sorting/filtering/pagination, dashboard counts, checkout summary, image validation, quantity support, and informational pages.
- `handcrafted_app/forms.py`: shipping inputs saved into the existing order shipping-address field.
- `handcrafted_app/context_processors.py` and project `settings.py`: shared categories and cart count.
- `handcrafted_app/urls.py`: preserves existing URL names and adds the Makers, About, and For Sellers pages.
- `handcrafted_app/tests.py`: flow, rendering, authorization, filtering, checkout rollback, upload, and custom-request coverage.

Redesigned pages include the homepage, catalog/categories, product details, cart, checkout, login, registration, public shop, seller dashboard, product add/edit, shop editing, order history, buyer custom requests, seller requests, request creation, and request management.

## Preserved behavior

Buyer/seller roles, shop ownership restrictions, multiple product images, server-side stock checks, transactional order creation, cart removal and quantities, seller product deactivation, administrator-managed order statuses, approved custom-order eligibility, request statuses, and proposed prices remain connected to the existing backend. Accepting a custom request never creates an order.

## Existing limitations

- The database has five categories but currently no seller shops, products, or product images. Empty states are intentional. Create real seller accounts and upload your photographs to populate the marketplace.
- The shop model supports a logo but has no cover-image field. Public shop covers use botanical decoration. Adding an uploadable cover would require a model field and migration, which this redesign avoids.
- Custom orders need both administrator approval and the existing custom-order flag enabled in Django admin.
- Shipping has no cost calculation, and checkout collects no online payment. Both are clearly disclosed.
- No review, wishlist, social media, newsletter, or contact-message controls are displayed without working backend support or configured links.
- Bootstrap and fonts load from their existing/public CDN providers and need an internet connection.

## Decorative image provenance

`static/images/handmade-still-life.png` was generated with the built-in ImageGen tool. It is decorative, not a seller listing or claim about merchandise.

Prompt: Original editorial still-life photograph of artisan materials: cream and muted blush wool yarn, wooden crochet tools, an ivory ceramic vase with dried botanical stems and daisies, linen, and light oak. Warm natural window light, refined adult boutique atmosphere, cream with muted sage and terracotta accents, portrait framing, real material textures. No people, toys, hearts, illustrations, text, brands, logos, or watermarks. Intended for an arch-cropped homepage hero and authentication panels.
