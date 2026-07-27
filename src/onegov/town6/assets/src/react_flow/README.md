# React Flow assets

This private npm workspace builds the self-contained React Flow views used by
Town6. Each view is emitted as its own classic JavaScript bundle and optional
stylesheet. React is bundled intentionally: OneGov's shared browser widgets use
React 15, while React Flow requires a modern React runtime.

## Structure

- `bundles.mjs` is the explicit build manifest.
- `src/core` contains small, optional adapters for ELK layout, full-viewport PNG
  export, React mounting, and JSON loading.
- `src/entries` contains one browser entry point per generated bundle.
- `src/views` contains feature behavior and styling. URL-tree logic belongs to
  the information-architecture view, not to the shared adapters.

To add a view, create its feature source and entry point, then add one object to
`bundles.mjs`. The generic build writes `<name>.bundle.min.js`, the optional CSS
file, and an adjacent legal notice into the Town6 asset directories. A view pays
only for the adapters and npm packages its entry point imports.

## Build and verify

Use the Node major configured in CI and the npm release in `packageManager`:

```sh
npm ci
npm run build
npm run verify
```

`npm run verify` validates every manifest entry, runs the build-contract tests,
checks the installed dependency tree, and byte-compares every generated asset.
Legal notices are derived from esbuild's bundle metadata, so build-only and
platform-specific packages cannot make the output differ between macOS and
Linux.

## Dependency updates

Direct dependencies use exact versions and `package-lock.json` records integrity
hashes. Dependabot checks this workspace monthly. Its pull requests intentionally
leave `npm run check` failing until a maintainer reviews the release notes and
commits regenerated assets.

For a reviewed manual update:

```sh
npm run deps:outdated
npm install --save-exact <package>@<version>
npm ci
npm run build
npm run verify
```

Update `react` and `react-dom` together. For React Flow major releases, follow
the [official migration guide](https://reactflow.dev/learn/troubleshooting/migrate-to-v12)
and verify the layout, MiniMap, fit-to-view behavior, CSS selectors, and PNG
export in the browser. Treat ELK `0.x` minor updates as migration-level changes
and recheck both layout directions.

`html-to-image` stays pinned at `1.11.11` and is excluded from Dependabot because
the [official React Flow image example](https://reactflow.dev/examples/misc/download-image)
warns that later versions currently break exports. Remove that exception only
after the warning is gone and the browser export regression test passes.
