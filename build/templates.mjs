/* ==========================================================================
   OceanAstra — HTML templates
   Pure functions: (context) -> HTML string. No I/O happens here.
   Strings coming out of content/i18n/*.json are treated as HTML-ready
   fragments (they may contain entities such as &amp;), so they are inserted
   verbatim into markup and only quote-escaped when used in an attribute.
   ========================================================================== */

export const LOCALES = ['en', 'zh', 'ar'];
export const PAGES = ['home', 'solutions', 'about', 'support', 'contact', 'privacy', 'terms'];
const NAV_PAGES = ['home', 'solutions', 'about', 'support', 'contact'];

/* ------------------------------------------------------------- helpers -- */

const attr = (s) => String(s).replace(/"/g, '&quot;');

/** Locale root path, e.g. '/' for English, '/ar/' for Arabic. */
export function localeRoot(base, locale) {
  return locale === 'en' ? `${base}/` : `${base}/${locale}/`;
}

/** Absolute path to a page within a locale. */
export function pageUrl(base, locale, page) {
  const root = localeRoot(base, locale);
  return page === 'home' ? root : `${root}${page}/`;
}

/** Filesystem path (relative to the output root) for a page. */
export function pageFile(locale, page) {
  const dir = locale === 'en' ? '' : `${locale}/`;
  return page === 'home' ? `${dir}index.html` : `${dir}${page}/index.html`;
}

const mark = (id) => `<svg viewBox="0 0 40 40" aria-hidden="true" focusable="false">
      <defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#12557F"/><stop offset="1" stop-color="#04121F"/></linearGradient></defs>
      <rect width="40" height="40" rx="9" fill="url(#${id})"/>
      <path d="M6.5 26.4c3.4-3.4 6.8-3.4 10.2 0s6.8 3.4 10.2 0 6.8-3.4 10.2 0" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" opacity=".95"/>
      <path d="M6.5 32.2c3.4-3.4 6.8-3.4 10.2 0s6.8 3.4 10.2 0 6.8-3.4 10.2 0" fill="none" stroke="#4FC3D9" stroke-width="2.2" stroke-linecap="round" opacity=".75"/>
      <path d="M25.5 6.4c.55 4.3 1.35 5.1 5.6 5.65-4.25.55-5.05 1.35-5.6 5.65-.55-4.3-1.35-5.1-5.6-5.65 4.25-.55 5.05-1.35 5.6-5.65Z" fill="#4FC3D9"/>
    </svg>`;

const paragraphs = (arr) => (arr || []).map((p) => `<p>${p}</p>`).join('\n            ');

/* ---------------------------------------------------------------- head -- */

function head(ctx) {
  const { t, locale, page, company, base, all, noindex } = ctx;
  // The 404 page borrows the homepage's URL for its language links: it has no
  // canonical address of its own, and every locale must still be reachable.
  const linkPage = ctx.linkPage || page;
  const meta = t[page] || t.notFound;
  const canonical = company.siteUrl + pageUrl('', locale, linkPage);

  const discovery = noindex
    ? '  <meta name="robots" content="noindex">'
    : [
      `  <link rel="canonical" href="${attr(canonical)}">`,
      ...LOCALES.map((l) => {
        const href = company.siteUrl + pageUrl('', l, linkPage);
        return `  <link rel="alternate" hreflang="${all[l].meta.htmlLang}" href="${attr(href)}">`;
      }),
      `  <link rel="alternate" hreflang="x-default" href="${attr(company.siteUrl + pageUrl('', 'en', linkPage))}">`
    ].join('\n');

  const ld = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: company.brand,
    legalName: company.legalName.en,
    url: company.siteUrl,
    logo: `${company.siteUrl}/assets/img/favicon.svg`,
    foundingDate: company.founded,
    email: company.email.general,
    telephone: company.phone.display,
    address: {
      '@type': 'PostalAddress',
      streetAddress: company.address.en.lines[0],
      addressLocality: 'Dubai',
      addressCountry: 'AE'
    },
    contactPoint: [
      {
        '@type': 'ContactPoint',
        contactType: 'customer support',
        email: company.email.support,
        telephone: company.phone.display,
        availableLanguage: ['English', 'Arabic', 'Chinese']
      }
    ]
  };

  return `<!DOCTYPE html>
<html lang="${t.meta.htmlLang}" dir="${t.meta.dir}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${meta.title}</title>
  <meta name="description" content="${attr(meta.description)}">
${discovery}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="${attr(company.brand)}">
  <meta property="og:title" content="${attr(meta.title)}">
  <meta property="og:description" content="${attr(meta.description)}">
  <meta property="og:url" content="${attr(canonical)}">
  <meta name="theme-color" content="#04121f">
  <link rel="icon" href="${base}/assets/img/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="${base}/assets/css/site.css">
  <script>document.documentElement.className="js";</script>
  <script type="application/ld+json">${JSON.stringify(ld).replace(/</g, '\\u003c')}</script>
</head>`;
}

/* -------------------------------------------------------------- header -- */

function header(ctx) {
  const { t, locale, page, base, all } = ctx;
  const linkPage = ctx.linkPage || page;

  const links = NAV_PAGES.map((p) => {
    const current = p === page ? ' aria-current="page"' : '';
    return `<a href="${pageUrl(base, locale, p)}"${current}>${t.nav[p]}</a>`;
  }).join('\n        ');

  const langs = LOCALES.map((l) => {
    const current = l === locale ? ' aria-current="true"' : '';
    return `<a href="${pageUrl(base, l, linkPage)}" data-lang="${l}" hreflang="${all[l].meta.htmlLang}" lang="${all[l].meta.htmlLang}"${current}>${all[l].meta.label}</a>`;
  }).join('\n          ');

  return `<a class="skip-link" href="#main">${t.nav.skip}</a>
  <header class="site-header">
    <div class="wrap">
      <div class="header-inner">
        <a class="brand" href="${pageUrl(base, locale, 'home')}">
          ${mark('oa-header')}
          <span class="brand-name">OceanAstra</span>
        </a>
        <div class="header-spacer"></div>
        <button class="nav-toggle" type="button" id="nav-toggle" aria-expanded="false" aria-controls="primary-nav" aria-label="${attr(t.nav.menu)}">
          <svg class="icon-open" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
          <svg class="icon-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
        </button>
        <nav class="nav" id="primary-nav" data-open="false" aria-label="${attr(t.nav.menu)}">
        ${links}
          <div class="lang" role="group" aria-label="${attr(t.nav.language)}">
          ${langs}
          </div>
        </nav>
      </div>
    </div>
  </header>`;
}

/* -------------------------------------------------------------- footer -- */

function footer(ctx) {
  const { t, locale, base, company, buildYear } = ctx;
  const f = t.footer;
  const addr = company.address[locale];

  const solutionLinks = (t.solutions.sections || [])
    .map((s) => `<li><a href="${pageUrl(base, locale, 'solutions')}#${s.id}">${s.title}</a></li>`)
    .join('\n            ');

  const companyLinks = ['about', 'support', 'contact']
    .map((p) => `<li><a href="${pageUrl(base, locale, p)}">${t.nav[p]}</a></li>`)
    .join('\n            ');

  return `<footer class="site-footer">
    <div class="wrap">
      <div class="footer-grid">
        <div>
          <div class="footer-brand">${mark('oa-footer')}<span>OceanAstra</span></div>
          <p class="footer-tagline">${f.tagline}</p>
          <address class="footer-legal-name">
            <strong>${company.legalName[locale]}</strong>
            ${f.registered}<br>
            ${f.licenceLabel}: ${company.licence.number}
          </address>
        </div>
        <div>
          <h4>${f.solutionsHeading}</h4>
          <ul>
            ${solutionLinks}
          </ul>
        </div>
        <div>
          <h4>${f.companyHeading}</h4>
          <ul>
            ${companyLinks}
          </ul>
        </div>
        <div>
          <h4>${f.contactHeading}</h4>
          <address>
            <a href="mailto:${company.email.general}">${company.email.general}</a><br>
            <a href="tel:${company.phone.href}" dir="ltr">${company.phone.display}</a><br>
            ${addr.lines.join('<br>')}
          </address>
        </div>
      </div>
      <div class="footer-bottom">
        <span>&copy; <span data-year>${buildYear}</span> ${company.legalName[locale]} ${f.rights}</span>
        <span class="spacer"></span>
        <nav aria-label="${attr(f.legalHeading)}">
          <a href="${pageUrl(base, locale, 'privacy')}">${f.privacy}</a>
          <a href="${pageUrl(base, locale, 'terms')}">${f.terms}</a>
        </nav>
      </div>
    </div>
  </footer>`;
}

/* ------------------------------------------------------------- shell ---- */

function shell(ctx, main) {
  return `${head(ctx)}
<body data-page="${ctx.page}">
  ${header(ctx)}
  <main id="main">
${main}
  </main>
  ${footer(ctx)}
  <script src="${ctx.base}/assets/js/site.js" defer></script>
</body>
</html>
`;
}

function ctaBand(cta, href) {
  return `    <section class="cta-band">
      <div class="wrap">
        <h2>${cta.heading}</h2>
        <p>${cta.body}</p>
        <a class="btn btn--primary" href="${href}">${cta.button}</a>
      </div>
    </section>`;
}

function pageHero(t, hero) {
  return `    <section class="hero hero--page">
      <div class="wrap">
        <p class="eyebrow">${hero.eyebrow}</p>
        <h1>${hero.heading}</h1>
        <p class="lede">${hero.lede}</p>
      </div>
    </section>`;
}

/* --------------------------------------------------------------- home --- */

function renderHome(ctx) {
  const { t, locale, base } = ctx;
  const h = t.home;

  const cards = h.pillars.items.map((item) => `          <article class="card" id="${item.id}">
            <div class="card-meta">
              <span class="card-number">${item.number}</span>
              ${item.badge ? `<span class="badge">${item.badge}</span>` : ''}
            </div>
            <h3><a href="${pageUrl(base, locale, 'solutions')}#${item.id}">${item.title}</a></h3>
            <p class="summary">${item.summary}</p>
            <ul class="card-points">
              ${item.points.map((p) => `<li>${p}</li>`).join('\n              ')}
            </ul>
          </article>`).join('\n');

  const steps = h.approach.items.map((s) => `          <article class="step">
            <p class="step-number">${s.step}</p>
            <h3>${s.title}</h3>
            <p>${s.body}</p>
          </article>`).join('\n');

  const main = `    <section class="hero">
      <div class="wrap">
        <p class="eyebrow">${h.hero.eyebrow}</p>
        <h1>${h.hero.heading}</h1>
        <p class="lede">${h.hero.lede}</p>
        <div class="hero-actions">
          <a class="btn btn--primary" href="${pageUrl(base, locale, 'solutions')}">${h.hero.primary}</a>
          <a class="btn btn--ghost" href="${pageUrl(base, locale, 'contact')}">${h.hero.secondary}</a>
        </div>
        <ul class="credentials">
          ${h.credentials.map((c) => `<li>${c}</li>`).join('\n          ')}
        </ul>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="section-head">
          <p class="eyebrow">${h.pillars.eyebrow}</p>
          <h2>${h.pillars.heading}</h2>
          <p class="lede">${h.pillars.lede}</p>
        </div>
        <div class="grid grid--3">
${cards}
        </div>
      </div>
    </section>

    <section class="section section--mist section--tight">
      <div class="wrap">
        <div class="section-head">
          <p class="eyebrow">${h.approach.eyebrow}</p>
          <h2>${h.approach.heading}</h2>
        </div>
        <div class="grid grid--4">
${steps}
        </div>
      </div>
    </section>

${ctaBand(h.cta, pageUrl(base, locale, 'contact'))}`;

  return shell(ctx, main);
}

/* ---------------------------------------------------------- solutions --- */

function renderSolutions(ctx) {
  const { t, locale, base } = ctx;
  const s = t.solutions;

  const details = s.sections.map((sec) => {
    const single = sec.groups.length === 1 ? ' detail-groups--single' : '';
    const groups = sec.groups.map((g) => `            <div class="group">
              <h3>${g.title}</h3>
              <ul>
                ${g.items.map((i) => `<li>${i}</li>`).join('\n                ')}
              </ul>
            </div>`).join('\n');

    return `        <article class="detail" id="${sec.id}">
          <div class="detail-head">
            <div class="card-meta">
              <span class="card-number">${sec.number}</span>
              ${sec.badge ? `<span class="badge">${sec.badge}</span>` : ''}
            </div>
            <h2>${sec.title}</h2>
            <p class="lede">${sec.lede}</p>
            ${paragraphs(sec.body)}
          </div>
          <div class="detail-groups${single}">
${groups}
          </div>
          ${sec.note ? `<p class="note">${sec.note}</p>` : ''}
        </article>`;
  }).join('\n\n');

  const main = `${pageHero(t, s.hero)}

    <section class="section">
      <div class="wrap">
${details}
      </div>
    </section>

${ctaBand(s.cta, pageUrl(base, locale, 'contact'))}`;

  return shell(ctx, main);
}

/* -------------------------------------------------------------- about --- */

function renderAbout(ctx) {
  const { t, locale, base, company } = ctx;
  const a = t.about;
  const L = a.facts.labels;
  const V = a.facts.values;
  const addr = company.address[locale];

  const principles = a.principles.items.map((p) => `          <article class="card">
            <h3>${p.title}</h3>
            <p class="summary">${p.body}</p>
          </article>`).join('\n');

  const rows = [
    [L.legalName, company.legalName[locale]],
    [L.tradeName, company.brand],
    [L.type, V.type],
    [L.jurisdiction, V.jurisdiction],
    [L.licence, company.licence.number],
    [L.authority, company.licence.authority[locale]],
    [L.registerNumber, company.licence.registerNumber],
    [L.chamberNumber, company.licence.chamberNumber],
    [L.founded, company.founded],
    [L.address, addr.full],
    [L.email, `<a href="mailto:${company.email.general}">${company.email.general}</a>`],
    [L.phone, `<span dir="ltr"><a href="tel:${company.phone.href}">${company.phone.display}</a></span>`],
    [L.website, `<a href="${company.siteUrl}">${company.domain}</a>`]
  ].map(([dt, dd]) => `          <div class="fact"><dt>${dt}</dt><dd>${dd}</dd></div>`).join('\n');

  const main = `${pageHero(t, a.hero)}

    <section class="section">
      <div class="wrap">
        <div class="section-head">
          <h2>${a.story.heading}</h2>
        </div>
        <div class="prose">
            ${paragraphs(a.story.paragraphs)}
        </div>
      </div>
    </section>

    <section class="section section--mist section--tight">
      <div class="wrap">
        <div class="section-head">
          <h2>${a.principles.heading}</h2>
        </div>
        <div class="grid grid--2">
${principles}
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="section-head">
          <h2>${a.facts.heading}</h2>
          <p class="lede">${a.facts.lede}</p>
        </div>
        <dl class="facts">
${rows}
        </dl>
      </div>
    </section>

${ctaBand(a.cta, pageUrl(base, locale, 'contact'))}`;

  return shell(ctx, main);
}

/* ------------------------------------------------------------ support --- */

function renderSupport(ctx) {
  const { t, base, locale, company } = ctx;
  const s = t.support;

  const hrefs = [`mailto:${company.email.support}`, `tel:${company.phone.href}`, null];
  const labels = [company.email.support, company.phone.display, null];

  const channels = s.channels.items.map((c, i) => `          <article class="contact-card">
            <h3>${c.title}</h3>
            <p>${c.body}</p>
            ${hrefs[i] ? `<a class="contact-link" href="${hrefs[i]}"${i === 1 ? ' dir="ltr"' : ''}>${labels[i]}</a>` : ''}
          </article>`).join('\n');

  const expectations = s.expectations.items.map((e) => `          <article class="step">
            <h3>${e.title}</h3>
            <p>${e.body}</p>
          </article>`).join('\n');

  const main = `${pageHero(t, s.hero)}

    <section class="section">
      <div class="wrap">
        <div class="section-head">
          <h2>${s.channels.heading}</h2>
        </div>
        <div class="grid grid--3">
${channels}
        </div>
      </div>
    </section>

    <section class="section section--mist section--tight">
      <div class="wrap">
        <div class="section-head">
          <h2>${s.expectations.heading}</h2>
        </div>
        <div class="grid grid--4">
${expectations}
        </div>
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        <div class="prose">
          <h2>${s.apps.heading}</h2>
          <p>${s.apps.body}</p>
          <p class="note">${t.common.hours}: ${company.hours[locale]}</p>
        </div>
      </div>
    </section>

${ctaBand(s.cta, `mailto:${company.email.support}`)}`;

  return shell(ctx, main);
}

/* ------------------------------------------------------------ contact --- */

function renderContact(ctx) {
  const { t, locale, company } = ctx;
  const c = t.contact;
  const addr = company.address[locale];

  const cards = [
    [c.cards.general, company.email.general],
    [c.cards.support, company.email.support]
  ].map(([card, mail]) => `          <article class="contact-card">
            <h3>${card.title}</h3>
            <p>${card.body}</p>
            <a class="contact-link" href="mailto:${mail}">${mail}</a>
          </article>`).join('\n');

  const main = `${pageHero(t, c.hero)}

    <section class="section">
      <div class="wrap">
        <div class="grid grid--2">
${cards}
        </div>
        <p class="note" style="margin-block-start:32px;">${c.note}</p>
      </div>
    </section>

    <section class="section section--tight section--mist">
      <div class="wrap">
        <div class="section-head">
          <h2>${c.office.heading}</h2>
        </div>
        <div class="office">
          <div class="office-item">
            <h4>${t.common.address}</h4>
            <address>${addr.lines.join('<br>')}</address>
            ${company.mapUrl ? `<p><a href="${company.mapUrl}" target="_blank" rel="noopener">${t.common.viewOnMap}</a></p>` : ''}
          </div>
          <div class="office-item">
            <h4>${t.common.phone}</h4>
            <p><a href="tel:${company.phone.href}" dir="ltr">${company.phone.display}</a></p>
          </div>
          <div class="office-item">
            <h4>${t.common.email}</h4>
            <p><a href="mailto:${company.email.general}">${company.email.general}</a></p>
          </div>
          <div class="office-item">
            <h4>${t.common.hours}</h4>
            <p>${company.hours[locale]}</p>
          </div>
        </div>
        <p class="note" style="margin-block-start:24px;">${c.office.note}</p>
      </div>
    </section>`;

  return shell(ctx, main);
}

/* -------------------------------------------------------------- legal --- */

function renderLegal(ctx) {
  const { t, page, locale, company } = ctx;
  const d = t[page];

  const sections = d.sections.map((s) => {
    const parts = [`          <h2>${s.heading}</h2>`];
    if (s.paragraphs) parts.push(`          ${paragraphs(s.paragraphs)}`);
    if (s.list) {
      parts.push(`          <ul>\n            ${s.list.map((i) => `<li>${i}</li>`).join('\n            ')}\n          </ul>`);
    }
    if (s.after) parts.push(`          ${paragraphs(s.after)}`);
    return parts.join('\n');
  }).join('\n\n');

  const addr = company.address[locale];

  const main = `    <section class="hero hero--page">
      <div class="wrap">
        <h1>${d.heading}</h1>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="prose">
          <p class="updated">${t.common.lastUpdated}: ${d.updated}</p>
          <p class="intro">${d.intro}</p>

${sections}

          <div class="office" style="margin-block-start:44px;">
            <div class="office-item">
              <h4>${t.about.facts.labels.legalName}</h4>
              <address>${company.legalName[locale]}<br>${addr.full}</address>
            </div>
            <div class="office-item">
              <h4>${t.common.email}</h4>
              <p><a href="mailto:${company.email.general}">${company.email.general}</a></p>
            </div>
            <div class="office-item">
              <h4>${t.common.phone}</h4>
              <p><a href="tel:${company.phone.href}" dir="ltr">${company.phone.display}</a></p>
            </div>
          </div>
        </div>
      </div>
    </section>`;

  return shell(ctx, main);
}

/* ---------------------------------------------------------------- 404 --- */

export function render404(ctx) {
  const { t, locale, base } = ctx;
  const n = t.notFound;
  const main = `    <div class="wrap">
      <div class="error-page">
        <h1>${n.heading}</h1>
        <p>${n.lede}</p>
        <a class="btn btn--dark" href="${pageUrl(base, locale, 'home')}">${n.button}</a>
      </div>
    </div>`;
  return shell({ ...ctx, page: 'notFound', linkPage: 'home', noindex: true }, main);
}

/* ------------------------------------------------------------ dispatch -- */

const RENDERERS = {
  home: renderHome,
  solutions: renderSolutions,
  about: renderAbout,
  support: renderSupport,
  contact: renderContact,
  privacy: renderLegal,
  terms: renderLegal
};

export function renderPage(ctx) {
  const renderer = RENDERERS[ctx.page];
  if (!renderer) throw new Error(`No renderer for page "${ctx.page}"`);
  return renderer(ctx);
}
