// eslint-disable-next-line spaced-comment
/*jslint indent: 2, maxlen: 80, continue: false, unparam: false, node: true */
'use strict';
/* eslint-disable no-var, one-var, one-var-declaration-per-line */

function pfatal(origErr, origPr) {
  var e = pfatal.ensureTruthy(origErr);
  try {
    e.promise = origPr;
  } catch (ignore) {
    // We tried. Propagating this error would mask the original one,
    // which is probably more important.
  }
  pfatal.addCauseStack(e);
  setImmediate(function rethrowNow() { throw e; });
}


pfatal.ensureTruthy = function ensureTruthy(orig) {
  var e = orig;
  if (e) { return e; }
  try {
    e = '"' + String(e) + '"';
  } catch (c) {
    e = 'something that cannot even be stringified.';
  }
  e = new Error('unhandledRejection is not an object: ' + e);
  e.origFalseyError = orig;
  return e;
};


pfatal.addCauseStack = function addCauseStack(e) {
  var c = e, s;
  while (c) {
    c = (c.jse_cause || c.cause || false);
    s = (c.stack || s);
  }
  if (!s) { return; }
  e.stack = (String(e.stack).replace(/\s+$/, '')
    + '\n----- original .cause stack -----\n' + s);
};


process.on('unhandledRejection', pfatal);

module.exports = pfatal;
