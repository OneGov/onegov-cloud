# Foundation 6 Integration

The source files were copied out of a `node_modules` folder using the 
[install instructions](https://get.foundation/sites/docs/installation.html), specifically

    npm install foundation-sites
    foundation new --framework sites --template zurb
    
To update, use the provided command `onegov-foundation upgrade`.

    
## External dependencies

We need Babel to transpile Typescript and ES. The app.js as a single file is bundled using webpack.
duktape does not support `const`, `let` and [other language features](https://github.com/svaarala/duktape/issues/2179).
A more or less complete feature overview of the DUK engine can be found 
[here](https://kangax.github.io/compat-table/es6/#duktape2_3)

## Adaptions from version 5.7

Here are some hints what must be changed:
https://github.com/foundation/foundation-sites/wiki/Upgrading-to-Foundation-6.2


## Implications using webpack

- In fact, we do just need a minified version all the js there is for foundation, so it would be possible to evade
the node/webpack dependency.
- It would be a big bundle containing all foundation javascript.
- How we update foundation then? It gets messy to update the sourc files already copying them from the node_modules.

## ES9 Guidelines

- For ES6, best use the `import`-Syntax which is the built-in modules implementation of ES6 in contrast with
the `require` directive from RequireJS. This would come with a static module structure 
([read about ES6 modules](https://2ality.com/2014/09/es6-modules-final.html)). 