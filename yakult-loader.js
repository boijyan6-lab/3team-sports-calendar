/* Overlay only confirmed Yakult games; never erase unrelated entries. */
(async function () {
  try {
    const r = await fetch('fixtures_yakult.json?ts=' + Date.now(), {cache:'no-store'});
    if (!r.ok) return;
    const entries = await r.json();
    if (!Array.isArray(entries)) return;
    for (const e of entries) {
      if (!e || e.team !== 'yakult' || !/^\d{4}-\d{2}-\d{2}$/.test(e.date) ||
          !/^\d{2}:\d{2}$/.test(e.time) || !e.opp || !['H','A'].includes(e.ha)) continue;
      const matches = initial.filter(x => x.team === 'yakult' && x.date === e.date &&
                                            x.opp === e.opp && x.ha === e.ha);
      if (matches.length) {
        for (const target of matches) Object.assign(target, e);
      } else if (!initial.some(x => x.team === 'yakult' && x.date === e.date)) {
        initial.push({...e});
      }
    }
    initial.sort((a,b) => a.date.localeCompare(b.date) || (a.time||'').localeCompare(b.time||''));
    render();
  } catch (err) {
    console.warn('Yakult fixture overlay unavailable:', err);
  }
})();
