import {readFile, readdir, writeFile} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

import {build} from 'esbuild';


const sourceDirectory = dirname(fileURLToPath(import.meta.url));
const assetDirectory = resolve(sourceDirectory, '../..');
const jsPath = resolve(assetDirectory, 'js/blocknote.bundle.min.js');
const cssPath = resolve(assetDirectory, 'css/blocknote.bundle.min.css');
const licensePath = `${jsPath}.LEGAL.txt`;
const checkOnly = process.argv.includes('--check');
const versionPattern = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/;


// The two modular Lodash packages used by BlockNote XL AI contain a legacy
// global-object fallback based on Function('return this'). Browsers supported
// by this bundle always provide globalThis, so replace only that fallback and
// keep the generated editor compatible with a CSP that omits unsafe-eval.
const cspSafeLodash = {
  name: 'csp-safe-lodash-global',
  setup(context) {
    context.onLoad({filter: /node_modules\/lodash\.(?:isequal|merge)\/index\.js$/}, async args => {
      const source = await readFile(args.path, 'utf8');
      const safeSource = source.replace(
        "Function('return this')()",
        'globalThis',
      );
      if (safeSource === source) {
        throw new Error(`Expected Lodash global fallback in ${args.path}`);
      }
      return {contents: safeSource, loader: 'js'};
    });
  },
};


const parseJson = async path => JSON.parse(await readFile(path, 'utf8'));


const packageJson = await parseJson(resolve(sourceDirectory, 'package.json'));
const lock = await parseJson(resolve(sourceDirectory, 'package-lock.json'));
const directDependencies = packageJson.dependencies;
const blocknoteVersion = directDependencies['@blocknote/core'];


const assertDependencyContract = () => {
  if (!versionPattern.test(blocknoteVersion)) {
    throw new Error('BlockNote must use an exact semantic version');
  }

  const blocknotePackages = [
    '@blocknote/core',
    '@blocknote/react',
    '@blocknote/mantine',
    '@blocknote/xl-ai',
  ];
  blocknotePackages.forEach(name => {
    if (directDependencies[name] !== blocknoteVersion) {
      throw new Error('All BlockNote packages must use the same exact version');
    }
  });

  Object.entries({...directDependencies, ...packageJson.devDependencies})
    .forEach(([name, version]) => {
      if (!versionPattern.test(version)) {
        throw new Error(`${name} must use an exact semantic version`);
      }

      const rootVersion = {
        ...lock.packages[''].dependencies,
        ...lock.packages[''].devDependencies,
      }[name];
      const locked = lock.packages[`node_modules/${name}`];
      if (
        rootVersion !== version ||
        locked?.version !== version ||
        !locked.integrity?.startsWith('sha512-')
      ) {
        throw new Error(`${name} is not exactly and integrity locked`);
      }
    });
};


const renderLicense = async () => {
  const sections = [];
  const seen = new Set();
  const packages = Object.entries(lock.packages)
    .filter(([path, metadata]) => path && metadata.version)
    .sort((left, right) => left[0].localeCompare(right[0]));

  for (const [packagePath, metadata] of packages) {
    const directory = resolve(sourceDirectory, packagePath);
    let installed;
    try {
      installed = await parseJson(resolve(directory, 'package.json'));
    } catch (error) {
      if (error.code === 'ENOENT' && metadata.optional) {
        continue;
      }
      throw error;
    }
    const identity = `${installed.name}@${installed.version}`;

    if (seen.has(identity)) {
      continue;
    }
    seen.add(identity);

    const filenames = (await readdir(directory, {withFileTypes: true}))
      .filter(entry => (
        entry.isFile() && /^(?:licen[cs]e|copying|notice)(?:\.|$)/i.test(entry.name)
      ))
      .map(entry => entry.name)
      .sort((left, right) => left.localeCompare(right));
    const texts = await Promise.all(filenames.map(async filename => (
      `----- ${filename} -----\n${(
        await readFile(resolve(directory, filename), 'utf8')
      ).trimEnd()}`
    )));

    sections.push(
      `===== ${identity} (${installed.license || metadata.license || 'unknown'}) =====\n\n` +
      (texts.length ? texts.join('\n\n') : 'No license file was included in the npm package.'),
    );
  }

  return `GENERATED FILE - DO NOT EDIT

This notice accompanies OneGov's generated BlockNote browser bundle.
BlockNote ${blocknoteVersion} core packages are licensed under MPL-2.0.
BlockNote XL AI is distributed under its GPL-3.0 license option. The
corresponding upstream and third-party source archives are identified by exact
versions, registry URLs, and sha512 integrity hashes in the adjacent
package-lock.json.
The OneGov adapter and reproducible build recipe are in this source tree under
src/onegov/org/assets/src/blocknote. Run "npm ci && npm run build" there to
recreate the distributed JavaScript and CSS from those sources.

${sections.join('\n\n')}
`;
};


const renderArtifacts = async () => {
  const banner = `/*! BlockNote ${blocknoteVersion} bundled for OneGov; ` +
    'MPL-2.0/GPL-3.0 and third-party licenses: ' +
    'blocknote.bundle.min.js.LEGAL.txt */';
  const result = await build({
    absWorkingDir: sourceDirectory,
    banner: {js: banner},
    bundle: true,
    conditions: ['style'],
    entryPoints: ['blocknote-editor.jsx'],
    format: 'iife',
    legalComments: 'none',
    loader: {
      '.woff': 'dataurl',
      '.woff2': 'dataurl',
    },
    minify: true,
    outfile: jsPath,
    platform: 'browser',
    plugins: [cspSafeLodash],
    sourcemap: false,
    target: ['es2020'],
    write: false,
  });

  const javascript = result.outputFiles.find(file => file.path.endsWith('.js'));
  const stylesheet = result.outputFiles.find(file => file.path.endsWith('.css'));
  if (!javascript || !stylesheet || result.outputFiles.length !== 2) {
    throw new Error('Expected one JavaScript and one CSS BlockNote artifact');
  }

  const source = new TextDecoder().decode(javascript.contents);
  if (/\b(?:Function|eval)\s*\(/.test(source)) {
    throw new Error('The BlockNote browser bundle must not require unsafe-eval');
  }

  return {
    js: javascript.contents,
    css: stylesheet.contents,
    license: new TextEncoder().encode(await renderLicense()),
  };
};


const assertCommitted = async (path, expected) => {
  const actual = await readFile(path);
  if (!actual.equals(Buffer.from(expected))) {
    throw new Error(`Committed BlockNote artifact is stale: ${path}`);
  }
};


assertDependencyContract();
const artifacts = await renderArtifacts();

if (checkOnly) {
  await Promise.all([
    assertCommitted(jsPath, artifacts.js),
    assertCommitted(cssPath, artifacts.css),
    assertCommitted(licensePath, artifacts.license),
  ]);
} else {
  await Promise.all([
    writeFile(jsPath, artifacts.js),
    writeFile(cssPath, artifacts.css),
    writeFile(licensePath, artifacts.license),
  ]);
}
