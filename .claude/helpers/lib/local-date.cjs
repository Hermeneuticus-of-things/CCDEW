'use strict';
/**
 * Timezone-aware date helpers — replaces UTC-based toISOString().slice(0,10)
 * which silently rolled "today" 2-4h before midnight for non-UTC users.
 *
 * Uses local-time YYYY-MM-DD / YYYY-MM via Intl.DateTimeFormat (no Date math).
 */

function todayLocal(d) {
  const dt = d || new Date();
  // en-CA produces "YYYY-MM-DD" format directly — works on any TZ.
  return dt.toLocaleDateString('en-CA');
}

function monthLocal(d) {
  return todayLocal(d).slice(0, 7);
}

function tzOffsetMinutes(d) {
  return -(d || new Date()).getTimezoneOffset();
}

function isoLocal(d) {
  // YYYY-MM-DDTHH:MM:SS+OFFSET (local), useful for log timestamps.
  const dt = d || new Date();
  const pad = n => String(n).padStart(2, '0');
  const off = tzOffsetMinutes(dt);
  const sign = off >= 0 ? '+' : '-';
  const oh = pad(Math.floor(Math.abs(off) / 60));
  const om = pad(Math.abs(off) % 60);
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}${sign}${oh}:${om}`;
}

module.exports = { todayLocal, monthLocal, tzOffsetMinutes, isoLocal };
