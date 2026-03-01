'use strict';

require('../fatal.js');

const hasOwn = Function.call.bind(Object.prototype.hasOwnProperty);

const stockNonErrors = {
  'undef': undefined,
  '0bj': Object.create(null),
};

let nonError = process.env.NON_ERR;
nonError = (hasOwn(stockNonErrors, nonError)
  ? stockNonErrors[nonError]
  : JSON.parse(nonError));

(async function dare() { throw nonError; }());
