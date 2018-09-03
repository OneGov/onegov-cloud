#!/bin/sh
cd quill
npm install
bundle install
npm run build

cp dist/quill.js ../onegov/quill/assets/js
cp dist/quill.snow.css ../onegov/quill/assets/css
