document.addEventListener('DOMContentLoaded', function() {
    if (document.body.classList.contains('framed')) {
      const urlParams = new URLSearchParams(window.location.search);

      // Store params in sessionStorage for persistence across pages
      for (const [key, value] of urlParams.entries()) {
        sessionStorage.setItem(key, value);
      }

      // Add click listeners to all links
      document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function(e) {
          // Don't modify external links
          if (link.hostname === window.location.hostname) {
            e.preventDefault();

            // Create URL object from the link's href
            const url = new URL(link.href);

            // Append stored parameters
            for (let i = 0; i < sessionStorage.length; i++) {
              const key = sessionStorage.key(i);
              // Only add if the parameter isn't already present
              if (!url.searchParams.has(key)) {
                url.searchParams.append(key, sessionStorage.getItem(key));
              }
            }

            // Navigate to the new URL with parameters
            window.location.href = url.toString();
          }
        });
      });
    }
  });