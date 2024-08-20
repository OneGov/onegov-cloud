import * as child_process from "child_process";
import * as esbuild from "esbuild";
import * as fs from "fs";
import { parseArgs } from "node:util";

const cliOptions = {
    dev: { type: "boolean" },
};

const args = parseArgs({ options: cliOptions, tokens: true });
const isDev = args.values.dev || false;

const buildConfig = {
    entryPoints: ["index.js"],
    bundle: true,
    minify: true,
    outfile: "../../js/tiptap.bundle.min.js"
};

await esbuild
    .build(buildConfig)
    .then(() => console.log(`⚡ Done building ${release}`))
    .catch(() => process.exit(1));

if (isDev) {
    /* dev: watch files for changes and reload */
    let ctx = await esbuild.context(buildConfig);
    await ctx.watch();
}
