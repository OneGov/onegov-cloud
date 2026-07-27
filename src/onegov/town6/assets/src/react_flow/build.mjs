import {readFile, readdir, writeFile} from 'node:fs/promises';
import {
    basename,
    dirname,
    isAbsolute,
    relative,
    resolve,
    sep
} from 'node:path';
import {fileURLToPath} from 'node:url';

import {build} from 'esbuild';

import {bundles} from './bundles.mjs';


const sourceDirectory = dirname(fileURLToPath(import.meta.url));
const assetDirectory = resolve(sourceDirectory, '../..');
const versionPattern = (
    /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/
);
const compareText = (left, right) => left < right ? -1 : left > right ? 1 : 0;


export const stripTrailingWhitespace = text => (
    text.replace(/[ \t]+$/gm, '')
);


const isWithin = (parent, child) => {
    const path = relative(parent, child);
    return path !== '..' && !path.startsWith(`..${sep}`) && !isAbsolute(path);
};


export function validateBundleDefinitions(
    definitions,
    sourceRoot = sourceDirectory,
    assetRoot = assetDirectory
) {
    if (!Array.isArray(definitions) || definitions.length === 0) {
        throw new Error('At least one React Flow bundle is required');
    }
    const names = new Set();

    return definitions.map((definition) => {
        if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(definition.name)) {
            throw new Error(
                `Invalid React Flow bundle name: ${definition.name}`
            );
        }
        if (names.has(definition.name)) {
            throw new Error(
                `Duplicate React Flow bundle name: ${definition.name}`
            );
        }
        names.add(definition.name);

        if (typeof definition.entryPoint !== 'string') {
            throw new Error(`${definition.name} needs an entryPoint`);
        }
        if (typeof definition.hasStyles !== 'boolean') {
            throw new Error(`${definition.name} must declare hasStyles`);
        }
        const entryPath = resolve(sourceRoot, definition.entryPoint);
        if (!isWithin(sourceRoot, entryPath) || entryPath === sourceRoot) {
            throw new Error(
                `${definition.name} entryPoint must stay inside ${sourceRoot}`
            );
        }

        const stem = `${definition.name}.bundle.min`;
        const jsPath = resolve(assetRoot, 'js', `${stem}.js`);
        const cssPath = resolve(assetRoot, 'css', `${stem}.css`);
        const licensePath = `${jsPath}.LEGAL.txt`;
        if (![jsPath, cssPath, licensePath].every(
            path => isWithin(assetRoot, path)
        )) {
            throw new Error(`${definition.name} output escapes ${assetRoot}`);
        }

        return {
            ...definition,
            cssPath,
            entryPath,
            jsPath,
            licensePath
        };
    });
}


export function assertDependencyContract(packageJson, lock) {
    if (lock.lockfileVersion !== 3 || !lock.packages?.['']) {
        throw new Error('A package-lock v3 file is required');
    }
    if (lock.name !== packageJson.name || lock.version !== packageJson.version) {
        throw new Error('package.json and package-lock.json metadata differ');
    }

    const dependencies = {
        ...packageJson.dependencies,
        ...packageJson.devDependencies
    };
    const lockedRoot = {
        ...lock.packages[''].dependencies,
        ...lock.packages[''].devDependencies
    };

    Object.entries(dependencies).forEach(([name, version]) => {
        const installed = lock.packages[`node_modules/${name}`];
        if (!versionPattern.test(version)) {
            throw new Error(`${name} must use an exact semantic version`);
        }
        if (
            lockedRoot[name] !== version ||
            installed?.version !== version ||
            !installed.integrity?.startsWith('sha512-')
        ) {
            throw new Error(`${name} is not exactly and integrity locked`);
        }
    });
    if (
        !packageJson.dependencies.react ||
        packageJson.dependencies.react !== packageJson.dependencies['react-dom']
    ) {
        throw new Error('react and react-dom must be updated together');
    }
}


const packagePathForInput = (inputPath) => {
    const parts = inputPath.replaceAll('\\', '/').split('/');
    let packageEnd = -1;

    parts.forEach((part, index) => {
        if (part !== 'node_modules' || index + 1 >= parts.length) {
            return;
        }
        packageEnd = index + (parts[index + 1].startsWith('@') ? 3 : 2);
    });

    if (packageEnd < 0) {
        return null;
    }
    const firstNodeModules = parts.indexOf('node_modules');
    return parts.slice(firstNodeModules, packageEnd).join('/');
};


export function getBundledPackagePaths(metafile) {
    return [...new Set(
        Object.keys(metafile.inputs)
            .map(packagePathForInput)
            .filter(Boolean)
    )].sort(compareText);
}


const parseJson = async path => JSON.parse(await readFile(path, 'utf8'));


export async function renderLicenseNotice({
    bundleName,
    lock,
    packagePaths,
    sourceRoot = sourceDirectory
}) {
    const sections = [];
    const seen = new Set();

    for (const packagePath of packagePaths) {
        const metadata = lock.packages[packagePath];
        if (!metadata) {
            throw new Error(
                `Bundled package is missing from lockfile: ${packagePath}`
            );
        }
        const directory = resolve(sourceRoot, packagePath);
        const installed = await parseJson(resolve(directory, 'package.json'));
        const identity = `${installed.name}@${installed.version}`;
        if (seen.has(identity)) {
            continue;
        }
        seen.add(identity);

        const filenames = (await readdir(directory, {withFileTypes: true}))
            .filter(entry => (
                entry.isFile() &&
                /^(?:licen[cs]e|copying|notice)(?:\.|$)/i.test(entry.name)
            ))
            .map(entry => entry.name)
            .sort(compareText);
        const texts = await Promise.all(filenames.map(async filename => (
            `----- ${filename} -----\n${(
                await readFile(resolve(directory, filename), 'utf8')
            ).trimEnd()}`
        )));

        sections.push(
            `===== ${identity} (${installed.license ||
                metadata.license || 'unknown'}) =====\n\n` +
            (texts.length ? texts.join('\n\n') :
                'No license file was included in the npm package.')
        );
    }

    return `GENERATED FILE - DO NOT EDIT

This notice accompanies OneGov's generated ${bundleName} React Flow browser
bundle. It contains notices only for packages included in that bundle. Exact
direct versions, registry URLs, and sha512 integrity hashes are recorded in the
source package-lock.json.

The reusable adapters, feature entry points, and reproducible build recipe are
under src/onegov/town6/assets/src/react_flow. Run "npm ci && npm run build"
there to recreate the distributed JavaScript, CSS, and license notice.

${sections.join('\n\n')}
`;
}


const renderBundle = async (definition, lock) => {
    const result = await build({
        absWorkingDir: sourceDirectory,
        banner: {
            js: `/*! OneGov React Flow bundle: ${definition.name}; ` +
                `licenses: ${basename(definition.licensePath)} */`
        },
        bundle: true,
        define: {
            'process.env.NODE_ENV': '"production"'
        },
        entryPoints: [definition.entryPath],
        format: 'iife',
        jsx: 'automatic',
        legalComments: 'none',
        metafile: true,
        minify: true,
        outfile: definition.jsPath,
        platform: 'browser',
        sourcemap: false,
        target: ['es2019'],
        write: false
    });
    const javascript = result.outputFiles.find(
        file => file.path.endsWith('.js')
    );
    const stylesheet = result.outputFiles.find(
        file => file.path.endsWith('.css')
    );
    if (!javascript || Boolean(stylesheet) !== definition.hasStyles) {
        throw new Error(
            `${definition.name} did not produce its declared JavaScript/CSS`
        );
    }

    const packagePaths = getBundledPackagePaths(result.metafile);
    const license = await renderLicenseNotice({
        bundleName: definition.name,
        lock,
        packagePaths
    });
    const encoder = new TextEncoder();
    const decoder = new TextDecoder();

    return [
        {
            contents: encoder.encode(stripTrailingWhitespace(
                decoder.decode(javascript.contents)
            )),
            path: definition.jsPath
        },
        ...(stylesheet ? [{
            contents: stylesheet.contents,
            path: definition.cssPath
        }] : []),
        {contents: encoder.encode(license), path: definition.licensePath}
    ];
};


const assertCommitted = async ({contents, path}) => {
    const actual = await readFile(path);
    if (!actual.equals(Buffer.from(contents))) {
        throw new Error(
            `Committed React Flow asset is stale: ${path}\n` +
            `Run npm run build in ${sourceDirectory}`
        );
    }
};


async function main() {
    const packageJson = await parseJson(resolve(sourceDirectory, 'package.json'));
    const lock = await parseJson(resolve(sourceDirectory, 'package-lock.json'));
    const definitions = validateBundleDefinitions(bundles);
    assertDependencyContract(packageJson, lock);

    const artifacts = (await Promise.all(definitions.map(
        definition => renderBundle(definition, lock)
    ))).flat();

    if (process.argv.includes('--validate')) {
        console.log(`Validated ${definitions.length} React Flow bundle(s)`);
        return;
    }
    if (process.argv.includes('--check')) {
        await Promise.all(artifacts.map(assertCommitted));
        console.log(`Verified ${artifacts.length} committed React Flow assets`);
        return;
    }

    await Promise.all(artifacts.map(({contents, path}) => (
        writeFile(path, contents)
    )));
    artifacts.forEach(({path}) => console.log(`Wrote ${path}`));
}


if (
    process.argv[1] &&
    resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
    await main();
}
