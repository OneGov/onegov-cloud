# Foundation 6 Integration

The source files were copied out of a `node_modules` folder using the
[install instructions](https://get.foundation/sites/docs/installation.html).

The foundation javascript depedencies have to be transpiled with something other than duktape.
Duktape does not support `const`, `let` and [other language features](https://github.com/svaarala/duktape/issues/2179).
A more or less complete feature overview of the DUK engine can be found
[here](https://kangax.github.io/compat-table/es6/#duktape2_3).
So we decided to include pre-bundled javascript created with the foundation cli.

To update, use the provided command `onegov-foundation upgrade`.

## Adaptions from version 5.7

Here are some hints what must be changed:
https://github.com/foundation/foundation-sites/wiki/Upgrading-to-Foundation-6.2

