$(document).ready(function() {
    var $offcanvas = $('#offCanvasMainMenu');
    var $body = $offcanvas.find('.offcanvas-body');

    if ($body.length && $body.find('.drilldown-menu').length) {

        var toggleToMenu = new Map();
        var menuToParentMenu = new Map();

        $body.find('ul.drilldown-menu').each(function() {
            var $menu = $(this);
            var $parentLi = $menu.parent().closest('li');
            var $parentMenu = $parentLi.length ? $parentLi.closest('ul.drilldown-menu') : $();
            menuToParentMenu.set($menu[0], $parentMenu.length ? $parentMenu[0] : null);

            var $item = $menu.prev('.drilldown-item');
            var $toggle = $item.children('.drilldown-toggle');
            if ($toggle.length) {
                toggleToMenu.set($toggle[0], $menu[0]);
            }
        });

        menuToParentMenu.forEach(function (_parentMenu, menu) {
            $body.append(menu);
        });

        $body.on('click', '[data-bs-toggle="drilldown"], [data-bs-toggle="drilldown-back"]', function (event) {
            var $target = $(event.target);
            var $forward = $target.closest('[data-bs-toggle="drilldown"]');
            var $back = $target.closest('[data-bs-toggle="drilldown-back"]');

            if ($forward.length) {
                event.preventDefault();
                var targetMenu = toggleToMenu.get($forward[0]);
                var $currentMenu = $body.find('.drilldown-menu.is-current');
                if (!targetMenu || !$currentMenu.length) { return; }

                $currentMenu.removeClass('is-current').addClass('is-prev');
                $(targetMenu).removeClass('is-prev').addClass('is-current');
            }

            if ($back.length) {
                event.preventDefault();
                var $currentMenu2 = $body.find('.drilldown-menu.is-current');
                var parentMenu = menuToParentMenu.get($currentMenu2[0]);
                if (!parentMenu) { return; }

                $currentMenu2.removeClass('is-current');
                $(parentMenu).removeClass('is-prev').addClass('is-current');

                titleStack.pop();
            }
        });

        $offcanvas.on('hidden.bs.offcanvas', function() {
            $body.find('ul.drilldown-menu').removeClass('is-current is-prev');
            $body.find('ul.drilldown-menu').first().addClass('is-current');
            titleStack.length = 1;
        });
    }
});
