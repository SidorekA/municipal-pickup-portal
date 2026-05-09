/* static/js/nav.js
 * Obsługa hamburger menu — zastępuje Bootstrap collapse własnym togglem,
 * żeby animacje CSS (swing-in/out) działały płynnie w obu kierunkach.
 */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        const toggler = document.getElementById('navToggler');
        const navEl   = document.getElementById('navbarNav');

        if (!toggler || !navEl) return;

        let closeHandler = null;

        function isOpen() {
            return navEl.classList.contains('nav-open');
        }

        function openMenu() {
            if (closeHandler) {
                navEl.removeEventListener('animationend', closeHandler);
                closeHandler = null;
            }
            navEl.classList.remove('nav-closing');
            navEl.classList.add('nav-open');
            toggler.setAttribute('aria-expanded', 'true');
        }

        function closeMenu() {
            if (!isOpen()) return;

            toggler.setAttribute('aria-expanded', 'false');
            navEl.classList.add('nav-closing');

            closeHandler = function () {
                navEl.classList.remove('nav-open', 'nav-closing');
                navEl.removeEventListener('animationend', closeHandler);
                closeHandler = null;
            };
            navEl.addEventListener('animationend', closeHandler);
        }

        toggler.addEventListener('click', function (e) {
            e.stopPropagation();
            isOpen() ? closeMenu() : openMenu();
        });

        document.addEventListener('click', function (e) {
            if (isOpen() && !navEl.contains(e.target) && !toggler.contains(e.target)) {
                closeMenu();
            }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && isOpen()) {
                closeMenu();
                toggler.focus();
            }
        });

        navEl.querySelectorAll('.nav-link').forEach(function (link) {
            link.addEventListener('click', closeMenu);
        });
    });
})();