/* OceanAstra — progressive enhancement only.
   Every page is fully readable and navigable with JavaScript disabled. */
(function () {
  'use strict';

  var STORAGE_KEY = 'oceanastra:lang';

  /* ---------------------------------------------------------- mobile nav -- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('primary-nav');

  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.getAttribute('data-open') === 'true';
      nav.setAttribute('data-open', String(!open));
      toggle.setAttribute('aria-expanded', String(!open));
    });

    // Close the menu when the viewport grows past the mobile breakpoint.
    window.addEventListener('resize', function () {
      if (window.innerWidth > 940 && nav.getAttribute('data-open') === 'true') {
        nav.setAttribute('data-open', 'false');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ------------------------------------------------- language preference -- */
  // Remember an explicit language choice. Stored on the device only — it is
  // never transmitted, which is what the privacy policy states.
  function store(value) {
    try { window.localStorage.setItem(STORAGE_KEY, value); } catch (e) { /* private mode */ }
  }
  function read() {
    try { return window.localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
  }

  Array.prototype.forEach.call(document.querySelectorAll('[data-lang]'), function (link) {
    link.addEventListener('click', function () {
      store(link.getAttribute('data-lang'));
    });
  });

  // Apply a remembered preference on the English homepage only, and only for a
  // visitor arriving from outside the site. Deep links, in-site navigation and
  // first-time visitors are never redirected — an unknown visitor always sees
  // the English site exactly as published.
  var root = document.body.getAttribute('data-page') === 'home' &&
             document.documentElement.getAttribute('lang') === 'en';

  if (root) {
    var preferred = read();
    var sameOrigin = document.referrer &&
                     document.referrer.indexOf(window.location.origin) === 0;

    if (preferred && preferred !== 'en' && !sameOrigin) {
      var target = document.querySelector('[data-lang="' + preferred + '"]');
      if (target) { window.location.replace(target.getAttribute('href')); }
    }
  }

  /* ------------------------------------------------------- current year -- */
  Array.prototype.forEach.call(document.querySelectorAll('[data-year]'), function (el) {
    el.textContent = String(new Date().getFullYear());
  });
})();
