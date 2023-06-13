const sentry_dsn = document.documentElement.dataset.sentryDsn;
const sentry_release = document.documentElement.dataset.version;

if (sentry_dsn) {
    Sentry.init({
        dsn: sentry_dsn,
        release: sentry_release,
        environment: "javascript"
    });
}
