'use strict';
const fs = require('fs');

const RETRY_DELAYS_MS = [50, 100, 200];

function syncSleep(ms) {
  const end = Date.now() + ms;
  while (Date.now() < end) { /* sync busy-wait, in-process only */ }
}

function writeAtomic(filePath, content) {
  const tmp = `${filePath}.${process.pid}.${Date.now()}.${Math.floor(Math.random() * 1e6)}.tmp`;
  fs.writeFileSync(tmp, content, 'utf-8');
  let lastErr;
  for (let i = 0; i <= RETRY_DELAYS_MS.length; i++) {
    try { fs.renameSync(tmp, filePath); return; }
    catch (e) {
      lastErr = e;
      if (e.code !== 'EPERM' && e.code !== 'EBUSY' && e.code !== 'EACCES') break;
      if (i < RETRY_DELAYS_MS.length) syncSleep(RETRY_DELAYS_MS[i]);
    }
  }
  try { fs.unlinkSync(tmp); } catch { /* tmp gone or already moved */ }
  throw lastErr;
}

function writeAtomicJson(filePath, obj) {
  writeAtomic(filePath, JSON.stringify(obj, null, 2));
}

module.exports = { writeAtomic, writeAtomicJson };
