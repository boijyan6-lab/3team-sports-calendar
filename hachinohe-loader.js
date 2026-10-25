/* Hachinohe confirmed fixtures overlay. Existing schedule remains available if fetch fails. */
(async function () {
  try {
    const response = await fetch('fixtures_hachinohe.json?ts=' + Date.now(), {cache: 'no-store'});
    if (!response.ok) throw new Error('Hachinohe data unavailable');
    const entries = await response.json();
    if (!Array.isArray(entries) || entries.length === 0) return;
    const valid = entries.filter(e =>
      e && e.team === 'hachinohe' && /^\d{4}-\d{2}-\d{2}$/.test(e.date) &&
      typeof e.opp === 'string' && e.opp && typeof e.comp === 'string'
    );
    if (!valid.length) return;
    const updatedDates = new Set(valid.map(e => e.date));
    // For dates with confirmed official fixtures, remove stale static entries.
    initial = initial.filter(e => e.team !== 'hachinohe' || !updatedDates.has(e.date));
    const seen = new Set();
    for (const e of valid) {
      const key = [e.date, e.opp, e.comp].join('|');
      if (seen.has(key)) continue;
      seen.add(key);
      initial.push({...e, conditional: false, dateEnd: undefined, note: undefined});
    }
    initial.sort((a,b) => a.date.localeCompare(b.date) || (a.time || '').localeCompare(b.time || ''));
    render();
  } catch (error) {
    console.warn('Hachinohe automatic fixtures could not be loaded:', error);
  }
})();
