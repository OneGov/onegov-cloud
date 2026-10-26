(function () {
    "use strict";

    var hoverQuery = window.matchMedia("(hover: hover) and (min-width: 768px)");

    function getDropdown(Dropdown, toggle) {
        var instance = Dropdown.getOrCreateInstance(toggle);

        // Bootstrap disables Popper inside .navbar, this re-enables it
        // so that auto-flip and boundary detection work for navbar dropdowns
        instance._inNavbar = false;

        return instance;
    }

    function initHoverDropdowns() {
        // Resolve the global at runtime, so the load order inside the bundle does not matter
        var Dropdown = window.bootstrap && window.bootstrap.Dropdown;

        if (!Dropdown) {
            return;
        }

        document.querySelectorAll(".dropdown, .dropend, .dropstart, .dropup").forEach(function (wrapper) {
            var toggle = wrapper.querySelector(":scope > [data-bs-toggle='dropdown']");

            if (!toggle) {
                return;
            }

            wrapper.addEventListener("mouseenter", function () {
                if (hoverQuery.matches) {
                    getDropdown(Dropdown, toggle).show();

                    // show() focuses the toggle, which is only wanted for keyboard usage
                    toggle.blur();
                }
            });

            wrapper.addEventListener("mouseleave", function () {
                if (hoverQuery.matches) {
                    getDropdown(Dropdown, toggle).hide();
                }
            });

            // Prevent Bootstrap's click toggle from closing the menu that hover just opened
            toggle.addEventListener("click", function (event) {
                if (hoverQuery.matches) {
                    event.stopPropagation();
                }
            });
        });
    }

    document.addEventListener("DOMContentLoaded", initHoverDropdowns);
})();