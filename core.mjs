export const MAX_AGE = 90 * 60 * 1000;
export const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const safeURL = value => { try { const u = new URL(value); return u.protocol === 'https:' ? u.href : '#'; } catch { return '#'; } };
export const number = (v, digits = 0) => v == null || !Number.isFinite(Number(v)) ? '—' : Number(v).toLocaleString('en-US', { maximumFractionDigits: digits });
export function ageMs(iso, now = Date.now()) { const t = Date.parse(iso); return Number.isFinite(t) ? now - t : Infinity; }
export function freshness(feed, now = Date.now(), threshold = MAX_AGE) {
  if (!feed?.ok || feed.data == null) return 'unavailable';
  if (feed.lastFailure) return 'cached';
  const age = ageMs(feed.observedAt || feed.fetchedAt, now);
  if (age < -5 * 60000) return 'clock mismatch';
  return age > threshold ? 'stale' : 'updated';
}
export function vesselGroup(ship) {
  const type = String(ship.ship_category || '').toLowerCase();
  if (/tanker|vlcc|lng|lpg/.test(type)) return 'tanker';
  if (/cargo|bulk|container/.test(type)) return 'cargo';
  if (/passenger|ferry/.test(type)) return 'passenger';
  return 'other';
}
export function validPosition(ship) {
  return typeof ship.latitude === 'number' && typeof ship.longitude === 'number' &&
    Number.isFinite(ship.latitude) && Number.isFinite(ship.longitude) &&
    ship.latitude >= 20 && ship.latitude <= 32 && ship.longitude >= 44 && ship.longitude <= 65;
}
export function filterShips(ships, {query = '', type = 'all', zone = 'all', watch = false, watched = []} = {}) {
  const q = query.toLowerCase().trim();
  return ships.filter(s => (!q || [s.name, s.mmsi, s.destination, s.flag].some(v => String(v ?? '').toLowerCase().includes(q))) &&
    (type === 'all' || vesselGroup(s) === type) && (zone === 'all' || s.zone === zone) &&
    (!watch || watched.includes(String(s.mmsi))));
}
export function aggregateDays(rows) {
  const days = new Map();
  for (const row of rows) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(row.day) || !['inbound', 'outbound'].includes(row.direction)) continue;
    const item = days.get(row.day) || {day: row.day, inbound: 0, outbound: 0};
    item[row.direction] += Number.isFinite(Number(row.count)) ? Math.max(0, Number(row.count)) : 0;
    days.set(row.day, item);
  }
  return [...days.values()].sort((a, b) => a.day.localeCompare(b.day));
}
export function csvCell(value) {
  let s = String(value ?? '');
  if (/^[\s]*[=+\-@]/.test(s)) s = "'" + s;
  return '"' + s.replace(/"/g, '""') + '"';
}
export function csv(headers, rows) { return [headers, ...rows].map(r => r.map(csvCell).join(',')).join('\r\n'); }
