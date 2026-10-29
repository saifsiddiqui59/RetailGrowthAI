'use strict';
// Server-side, no-network bridge to the vendored MIT creative director.
const director = require('./director');
const MAX_INPUT = 320000;
let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  raw += chunk;
  if (raw.length > MAX_INPUT) {
    process.stderr.write('Feature2 creative input too large\n');
    process.exit(2);
  }
});
process.stdin.on('end', () => {
  try {
    const input = JSON.parse(raw);
    let output;
    switch (process.argv[2]) {
      case 'prompt': output = director.directorPrompt(input.request); break;
      case 'compile': output = director.compile(input.request, input.candidate, input.options || {}); break;
      case 'revise': output = director.revise(input.request, input.previous, input.candidate, input.notes); break;
      default: throw new Error('Unsupported read-only creative operation');
    }
    process.stdout.write(JSON.stringify(output) + '\n');
  } catch (error) {
    process.stderr.write('Feature2 creative validation failed: ' + error.message + '\n');
    process.exitCode = 2;
  }
});
