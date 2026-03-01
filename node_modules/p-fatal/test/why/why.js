'use strict';
/* eslint-disable import/no-dynamic-require */

if (process.env.REQUIRE_EARLY) { require(process.env.REQUIRE_EARLY); }

const errorWatchdog = require('./configurable-error-logger.js');

if (process.env.REQUIRE_LATE) { require(process.env.REQUIRE_LATE); }

errorWatchdog.install({
  errorLogTarget: (process.env.appcfg_errlog || 'default.error.log'),
});

(async function failWhale() { throw new Error('Fail whale failed. :-('); }());
