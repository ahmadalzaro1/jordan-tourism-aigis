import { copyFile, mkdir } from 'node:fs/promises';
const publicDir = new URL('../public/', import.meta.url);
await mkdir(publicDir, {recursive: true});
await copyFile(new URL('../node_modules/maplibre-gl/dist/maplibre-gl-worker.mjs', import.meta.url), new URL('maplibre-gl-worker.mjs', publicDir));
