import assert from 'node:assert/strict';
import {resolve} from 'node:path';
import test from 'node:test';

import {
    assertDependencyContract,
    getBundledPackagePaths,
    stripTrailingWhitespace,
    validateBundleDefinitions
} from '../build.mjs';


const sourceRoot = resolve('test-fixture/react_flow');
const assetRoot = resolve('test-fixture/assets');


test('generated assets have no trailing horizontal whitespace', () => {
    assert.equal(
        stripTrailingWhitespace('plain\nspace \ntab\t\n'),
        'plain\nspace\ntab\n'
    );
});


test('bundle definitions produce safe, feature-specific outputs', () => {
    const [definition] = validateBundleDefinitions([{
        entryPoint: 'src/entries/example.jsx',
        hasStyles: true,
        name: 'example-flow'
    }], sourceRoot, assetRoot);

    assert.equal(
        definition.entryPath,
        resolve(sourceRoot, 'src/entries/example.jsx')
    );
    assert.equal(
        definition.jsPath,
        resolve(assetRoot, 'js/example-flow.bundle.min.js')
    );
    assert.equal(
        definition.cssPath,
        resolve(assetRoot, 'css/example-flow.bundle.min.css')
    );
});


test('bundle definitions reject duplicates and paths outside the workspace', () => {
    assert.throws(
        () => validateBundleDefinitions([], sourceRoot, assetRoot),
        /At least one React Flow bundle/
    );
    assert.throws(() => validateBundleDefinitions([
        {entryPoint: 'one.jsx', hasStyles: false, name: 'duplicate'},
        {entryPoint: 'two.jsx', hasStyles: false, name: 'duplicate'}
    ], sourceRoot, assetRoot), /Duplicate React Flow bundle name/);
    assert.throws(() => validateBundleDefinitions([
        {entryPoint: '../outside.jsx', hasStyles: false, name: 'outside'}
    ], sourceRoot, assetRoot), /entryPoint must stay inside/);
    assert.throws(() => validateBundleDefinitions([
        {entryPoint: 'entry.jsx', hasStyles: false, name: '../outside'}
    ], sourceRoot, assetRoot), /Invalid React Flow bundle name/);
});


test('React runtime packages must be updated as a pair', () => {
    const packageJson = {
        dependencies: {'react': '19.2.8', 'react-dom': '20.0.0'},
        devDependencies: {},
        name: 'test-package',
        version: '1.0.0'
    };
    const lock = {
        lockfileVersion: 3,
        name: 'test-package',
        packages: {
            '': {
                dependencies: {'react': '19.2.8', 'react-dom': '20.0.0'},
                devDependencies: {}
            },
            'node_modules/react': {
                integrity: 'sha512-react',
                version: '19.2.8'
            },
            'node_modules/react-dom': {
                integrity: 'sha512-react-dom',
                version: '20.0.0'
            }
        },
        version: '1.0.0'
    };

    assert.throws(
        () => assertDependencyContract(packageJson, lock),
        /react and react-dom must be updated together/
    );
});


test('license packages come only from browser bundle inputs', () => {
    const commonInputs = {
        'node_modules/@xyflow/react/dist/esm/index.js': {},
        'node_modules/react/index.js': {},
        'src/entry.jsx': {}
    };
    const metafile = {inputs: commonInputs};

    const expected = ['node_modules/@xyflow/react', 'node_modules/react'];
    assert.deepEqual(getBundledPackagePaths(metafile), expected);
});
