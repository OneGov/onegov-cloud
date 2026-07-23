# OneGov BlockNote bundle

This package builds the browser assets used by OneGov's `HtmlField`. The
dependency versions are intentionally exact so that rebuilding a release is
reproducible.

```console
npm ci
npm run build
```

The generated JavaScript, stylesheet, and license notice are written to the
parent `assets/js` and `assets/css` directories and are committed with the
application assets.

## Updating BlockNote

Treat `node_modules` and the generated bundles as immutable build inputs and
outputs. Never patch a dependency in `node_modules` or edit a generated bundle
by hand. OneGov-specific behaviour belongs in `blocknote-editor.jsx`, its
stylesheet, or the build script.

1. Change the exact versions in `package.json`. Keep all `@blocknote/*`
   packages on the same version.
2. Run `npm install --package-lock-only` to update the lock file.
3. Run `npm ci && npm run lint && npm run build && npm run check`.
4. Commit `package.json`, `package-lock.json`, and all three generated assets.

The build validates exact versions and integrity hashes. It also applies a
narrow, in-memory CSP compatibility transform to two Lodash modules while
bundling; the installed package files remain untouched. If an upstream update
changes those modules, the build fails instead of silently applying a partial
patch.
