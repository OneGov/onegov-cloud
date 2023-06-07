const sentry_dsn = document.documentElement.dataset.sentryDsn;
const sentry_release = document.documentElement.dataset.version;

if (sentry_dsn) {
    Sentry.init({
        dsn: sentry_dsn,
        release: sentry_release,
        environment: "javascript",
        ignoreUrls: [/\/(gtm|ga|analytics)\.js/i],
        shouldSendCallback: function(data) {
            var crumbs = (data.breadcrumbs && data.breadcrumbs.values || []);
            var errors = (data.exception.values && data.exception.values || []);

            if (crumbs.length > 0 && errors.length > 0) {

                // if the last occurrence in the breadcrumbs is an XHR error
                // and the error itself is by intercooler we can ignore it
                // as we would see the error in the backend and we will
                // have informed the user in the frontend
                if (crumbs[crumbs.length - 1].category === 'xhr') {
                    if ((errors[errors.length - 1].value || {}).namespace === 'ic') {
                        return false;
                    }
                }
            }

            return true;
        }
    });
}
