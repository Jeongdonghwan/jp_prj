// 견적 위젯
(function () {
  const est = document.getElementById('est');
  if (!est) return;
  const d = est.dataset, sel = n => est.querySelector(`[name=${n}]`);
  const out = document.getElementById('est-total'), save = document.getElementById('est-save'), cta = document.getElementById('est-cta');
  const fmt = n => n.toLocaleString();
  function calc() {
    const air = sel('airport').value, trip = +sel('trip').value, people = sel('people').value;
    const base = +d[air] * trip, off = trip === 2 ? Math.round(base * +d.off) : 0, total = base - off;
    const big = people === '15';
    out.textContent = big ? d.ask : fmt(total) + d.won;
    save.hidden = big || !off;
    save.querySelector('span').textContent = fmt(off) + d.won;
    const msg = d.msg.replace('{airport}', sel('airport').selectedOptions[0].text)
      .replace('{trip}', sel('trip').selectedOptions[0].text)
      .replace('{people}', sel('people').selectedOptions[0].text)
      .replace('{total}', big ? '-' : fmt(total));
    // LINE 공식계정 링크에 텍스트 프리필 (https://line.me/R/oaMessage/@id/?text) — 일반 링크면 원래 URL 유지
    const m = d.line.match(/@[\w.-]+/);
    cta.href = m ? `https://line.me/R/oaMessage/${m[0]}/?${encodeURIComponent(msg)}` : d.line;
  }
  est.addEventListener('change', calc); calc();
})();

// 갤러리 탭 + 라이트박스
(function () {
  const gal = document.getElementById('gal'); if (!gal) return;
  const items = [...gal.querySelectorAll('a')];
  document.querySelectorAll('.tabs button').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.tabs button').forEach(x => x.classList.toggle('on', x === b));
    items.forEach(a => a.hidden = b.dataset.f !== 'all' && a.dataset.cat !== b.dataset.f);
  }));
  const lb = document.getElementById('lb'), img = lb.querySelector('img'), cap = lb.querySelector('figcaption');
  let cur = 0;
  const visible = () => items.filter(a => !a.hidden);
  function show(i) {
    const v = visible(); cur = (i + v.length) % v.length;
    img.src = v[cur].href; img.alt = cap.textContent = v[cur].dataset.cap; lb.hidden = false;
    document.body.style.overflow = 'hidden';
  }
  const close = () => { lb.hidden = true; document.body.style.overflow = ''; };
  items.forEach(a => a.addEventListener('click', e => { e.preventDefault(); show(visible().indexOf(a)); }));
  lb.querySelector('.lb-x').onclick = close;
  lb.querySelector('.lb-p').onclick = () => show(cur - 1);
  lb.querySelector('.lb-n').onclick = () => show(cur + 1);
  lb.addEventListener('click', e => { if (e.target === lb) close(); });
  document.addEventListener('keydown', e => {
    if (lb.hidden) return;
    if (e.key === 'Escape') close(); else if (e.key === 'ArrowLeft') show(cur - 1); else if (e.key === 'ArrowRight') show(cur + 1);
  });
})();

// 모바일 메뉴: 링크 클릭 시 닫기
document.querySelectorAll('.nav a').forEach(a => a.addEventListener('click', () => document.body.classList.remove('nav-open')));
