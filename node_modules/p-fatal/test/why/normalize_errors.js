'use strict';

const absDirLib = require('absdir');
const readStdinNow = require('read-all-stdin-sync');

const repoPathResolve = absDirLib(module, '../../');
const repoPathAbs = repoPathResolve('.');

let tx = readStdinNow();

(function fix() {
  tx = tx.replace(/\s+$/, '');
  tx = tx.split(repoPathAbs).join('/…/path_to_repo/…');
}());

(function fix() {
  let lines = tx.split(/\n/);
  let ln;
  let prevLn;
  function s(r, w) { ln = ln.replace(r, w); }
  function m(r) { return ln.match(r); }

  const esmTranspileIntro = ('const __global__ = this;'
    + '(function (require, module, ');
  const esmTranspileDescr = '/* Crazy long ESM-transpiled code line */';
  const maxLineLen = 255;
  const crazyColumnPointer = '  […]  ^ (column pointer > ' + maxLineLen + ')';

  function enforceMaxLineLen() {
    if (ln.length <= maxLineLen) { return ln; }
    if (ln.startsWith(esmTranspileIntro)) { return esmTranspileDescr; }

    const t = ln.trim();
    if ((t === '^') && ln.endsWith('^')) { return crazyColumnPointer; }
    // However, for reeeeally far column pointers, node.js will not be able to
    // fully print that line, giving a line of just very many U+0020 space:
    if ((!t) && (prevLn === esmTranspileDescr)) { return crazyColumnPointer; }

    return ln.slice(0, maxLineLen) + '…';
  }

  lines = lines.map(function eachLine(curLn) {
    prevLn = ln;
    ln = curLn;
    ln = enforceMaxLineLen();
    if (m(/^\s*at /)) {
      s(/(?::[0-9]+){2}\)$/, ':…:…)');
      s(/^(\s*at (?:\S+ \u0028|))\/\S+\//g, '$1…/');
    }
    return ln;
  });

  tx = lines.join('\n');
}());

(function fix() {
  function s(r, w) { tx = tx.replace(r, w); }

  // Shorten the path in line 1 of node v16 error messages:
  const esmTranspileBlobRgx = /(^|\n)(\/\S+\.js:)\d+(\n[ -\uFFFF]*\n *\^\n)/;
  s(esmTranspileBlobRgx, function f(m, n, p, r) {
    let pathKept = p.split(/(?=\/)/).slice(-3).join('');
    if (pathKept.length < p.length) { pathKept = '/…' + pathKept; }
    return n + pathKept + '…' + r;
  });

  // In blocks of many "at" lines, cut off after the 3rd:
  s(/((?:\n\s*at [ -\uFFFF]+){3}\n\s*at )[ -\uFFFF]+(\n\s*at [ -\uFFFF]+)*/g,
    '$1…');
}());

console.log(tx);
