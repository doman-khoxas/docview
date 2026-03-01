#!/bin/bash
# -*- coding: utf-8, tab-width: 2 -*-


function why () {
  export LANG{,UAGE}=en_US.UTF-8  # make error messages search engine-friendly
  local SELFPATH="$(readlink -m "$BASH_SOURCE"/..)"
  cd -- "$SELFPATH" || return $?
  rm -- tmp.*.{early,late}.*-*.{raw,log} 2>/dev/null

  local NODEJS="$(which node{js,} 2>/dev/null | grep -m 1 -Pe '^/')"

  local ENV_TYPE='dev'
  if [ -n "$CI" ]; then
    [ -z "$GITHUB_WORKSPACE" ] || ENV_TYPE='github-ci'
  fi

  local TESTNAME='"why" test'
  local MODULES=(
    perish
    p-fatal
    )
  local STAGE= MOD= ERR_CNT=0
  for MOD in "${MODULES[@]}"; do
    for STAGE in early late; do
      test_why "$STAGE" "$MOD"
    done
  done

  [ "$ERR_CNT" == 0 ] || return 4$(
    echo "-ERR $TESTNAME failed $ERR_CNT tests." >&2)
  echo "+OK $TESTNAME passed"
}


function test_why () {
  local RQR_WHEN="$1"; shift
  local PKG_NAME="$1"; shift
  local RQR_NAME="$PKG_NAME"
  case "$PKG_NAME" in
    p-fatal ) RQR_NAME='../../fatal.js';;
  esac
  export REQUIRE_LATE=
  export REQUIRE_EARLY=
  export REQUIRE_"${RQR_WHEN^^}"="$RQR_NAME"

  local LOG_EXP="expect.$ENV_TYPE/$PKG_NAME.$RQR_WHEN.log"
  local LOG_ACT="tmp.$PKG_NAME.$RQR_WHEN.$(date +%y%m%d-%H%M%S)-$$.log"
  local LOG_RAW="${LOG_ACT%.*}.raw"

  "$NODEJS" -r esm why.js &>"$LOG_RAW" || true
  <"$LOG_RAW" "$NODEJS" normalize_errors.js >"$LOG_ACT"
  if diff -sU 9002 -- "$LOG_EXP" "$LOG_ACT"; then
    rm -- "$LOG_ACT" "$LOG_RAW"
    return 0
  fi

  if [ -n "$GITHUB_STEP_SUMMARY" ]; then
    ( echo

      echo "### [why] $PKG_NAME.$RQR_WHEN.raw (albeit cut)"
      echo '```text'
      cut --bytes=1-500 -- "$LOG_RAW" | nl -ba
      echo '```'
      echo

      echo "### [why] $PKG_NAME.$RQR_WHEN.normalized.actual.log"
      echo '```text'
      cut --bytes=1-500 -- "$LOG_ACT" | nl -ba
      echo '```'
      echo
    ) >>"$GITHUB_STEP_SUMMARY"
  fi

  echo
  echo "-ERR $TESTNAME failed for $LOG_EXP" >&2
  (( ERR_CNT += 1 ))
}










[ "$1" == --lib ] && return 0; why "$@"; exit $?
