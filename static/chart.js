(() => {
  const source = document.getElementById('weight-data');
  const svg = document.getElementById('weight-chart');
  if (!source || !svg) return;
  const data = JSON.parse(source.textContent);
  const ns = 'http://www.w3.org/2000/svg';
  const draw = (tag, attrs, text) => { const el = document.createElementNS(ns, tag); Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k,v)); if (text !== undefined) el.textContent = text; svg.appendChild(el); return el; };
  const values = data.map(d => d.weight), low = Math.min(...values)-1, high = Math.max(...values)+1;
  const dates = data.map(d => Date.parse(d.date)), first = dates[0], span = dates[dates.length-1]-first;
  const x = i => span ? 52+(dates[i]-first)/span*618 : 361;
  const y = v => 195-(v-low)/(high-low)*170;
  for (let i=0;i<5;i++) { const v=low+(high-low)*i/4; draw('line',{x1:52,x2:670,y1:y(v),y2:y(v),stroke:'#e8ede9'}); draw('text',{x:42,y:y(v)+4,'text-anchor':'end',fill:'#7b8981','font-size':11},v.toFixed(1)); }
  draw('polyline',{points:data.map((d,i)=>`${x(i)},${y(d.weight)}`).join(' '),fill:'none',stroke:'#287455','stroke-width':3,'stroke-linejoin':'round'});
  data.forEach((d,i)=>{const c=draw('circle',{cx:x(i),cy:y(d.weight),r:4,fill:'#287455'}); const title=document.createElementNS(ns,'title'); title.textContent=`${d.date} : ${d.weight} kg`; c.appendChild(title);});
  [...new Set([0, Math.floor((data.length-1)/2), data.length-1])].forEach(i=>draw('text',{x:x(i),y:225,'text-anchor':'middle',fill:'#7b8981','font-size':11},new Date(dates[i]).toLocaleDateString('fr-FR',{day:'numeric',month:'short',timeZone:'UTC'})));
})();
