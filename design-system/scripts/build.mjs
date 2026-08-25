import { build } from 'esbuild';

await build({
  entryPoints: ['src/index.ts'],
  bundle: true,
  outfile: 'dist/index.js',
  format: 'esm',
  platform: 'browser',
  external: ['react', 'react-dom', 'react/jsx-runtime'],
  sourcemap: true,
});

await build({
  entryPoints: ['src/styles.css'],
  bundle: true,
  outfile: 'dist/styles.css',
});

console.log('Build complete: dist/index.js, dist/styles.css');
