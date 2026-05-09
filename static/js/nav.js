    (function () {
        const toggler = document.getElementById('navToggler');
        const navEl   = document.getElementById('navbarNav');

        function openMenu() {
            navEl.classList.add('nav-open');
            toggler.setAttribute('aria-expanded', 'true');
        }

        function closeMenu() {
            navEl.classList.remove('nav-open');
            toggler.setAttribute('aria-expanded', 'false');
        }

        function isOpen() {
            return navEl.classList.contains('nav-open');
        }

        /* Toggle po kliknięciu hamburgera */
        toggler.addEventListener('click', function (e) {
            e.stopPropagation();
            isOpen() ? closeMenu() : openMenu();
        });

        /* Zamknij po kliknięciu poza menu */
        document.addEventListener('click', function (e) {
            if (isOpen() && !navEl.contains(e.target) && !toggler.contains(e.target)) {
                closeMenu();
            }
        });

        /* Zamknij po naciśnięciu Escape */
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && isOpen()) {
                closeMenu();
                toggler.focus();
            }
        });

        /* Zamknij po kliknięciu linku w menu (nawigacja na mobile) */
        navEl.querySelectorAll('.nav-link').forEach(function (link) {
            link.addEventListener('click', closeMenu);
        });
    })();