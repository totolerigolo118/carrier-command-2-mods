// ================================================================ dessin (carte marine : hachures et encre, couleurs du radar tactique)
function teamOfIsland(id,t){let team=0;if(!R)return team;R.T.forEach(s=>{if(s.tick<=t){const x=s.tiles.find(q=>q.id===id);if(x)team=x.team;}});return team;}
function makeEnv(w){const ww=maxX-minX,hh=maxZ-minZ,S=Math.min(W/ww,H/hh),ox=(W-ww*S)/2,oy=(H-hh*S)/2;return {W,H,S,w,hits:[],P:(x,z)=>[ox+(x-minX)*S,oy+(maxZ-z)*S]};}
const CYAN='rgba(61,242,255,',PALE='rgba(159,232,240,';
let hatch=null;
function hatchPattern(c){if(hatch)return hatch;const p=document.createElement('canvas');p.width=p.height=7;const q=p.getContext('2d');q.strokeStyle='rgba(95,225,210,.42)';q.lineWidth=1;q.beginPath();q.moveTo(0,7);q.lineTo(7,0);q.moveTo(-1,1);q.lineTo(1,-1);q.moveTo(6,8);q.lineTo(8,6);q.stroke();hatch=c.createPattern(p,'repeat');return hatch;}
function halo(c,tx,x,y,col,lw){c.lineJoin='round';c.strokeStyle='rgba(4,8,10,.92)';c.lineWidth=lw||4;c.strokeText(tx,x,y);c.fillStyle=col;c.fillText(tx,x,y);}
function gridLines(c,e,step,stroke){
  c.strokeStyle=stroke;c.lineWidth=1;c.beginPath();
  for(let x=Math.ceil(minX/step)*step;x<maxX;x+=step){const a=e.P(x,minZ),b=e.P(x,maxZ);c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);}
  for(let z=Math.ceil(minZ/step)*step;z<maxZ;z+=step){const a=e.P(minX,z),b=e.P(maxX,z);c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);}
  c.stroke();
}
function frameChart(c,e){        // cadre double, graduation alternée au km, repères tous les 10 km
  const a=3,b=9;
  c.strokeStyle=CYAN+'.8)';c.lineWidth=1.2;c.strokeRect(a+.5,a+.5,e.W-2*a-1,e.H-2*a-1);
  c.strokeStyle=CYAN+'.4)';c.lineWidth=.8;c.strokeRect(b+.5,b+.5,e.W-2*b-1,e.H-2*b-1);
  c.fillStyle=CYAN+'.6)';
  for(let x=Math.floor(minX/1000)*1000;x<maxX;x+=1000){if(Math.abs(Math.round(x/1000))%2)continue;
    const x0=Math.max(e.P(x,0)[0],b),x1=Math.min(e.P(x+1000,0)[0],e.W-b);if(x1<=x0)continue;
    c.fillRect(x0,a+1,x1-x0,b-a-1);c.fillRect(x0,e.H-b,x1-x0,b-a-1);}
  for(let z=Math.floor(minZ/1000)*1000;z<maxZ;z+=1000){if(Math.abs(Math.round(z/1000))%2)continue;
    const y0=Math.max(e.P(0,z+1000)[1],b),y1=Math.min(e.P(0,z)[1],e.H-b);if(y1<=y0)continue;
    c.fillRect(a+1,y0,b-a-1,y1-y0);c.fillRect(e.W-b,y0,b-a-1,y1-y0);}
  c.fillStyle=PALE+'.85)';c.font=SERIF(11);c.textBaseline='top';
  for(let x=Math.ceil(minX/10000)*10000;x<maxX;x+=10000){const p=e.P(x,0);c.fillText(String(x/1000),p[0]+3,b+3);}
  c.textBaseline='alphabetic';
  for(let z=Math.ceil(minZ/10000)*10000;z<maxZ;z+=10000){const p=e.P(0,z);c.fillText(String(z/1000),b+4,p[1]-3);}
}
function echelle(c,e){           // barre d'échelle : 5 km en tronçons de 1 km
  const x0=24,y0=e.H-26,seg=1000*e.S;c.lineWidth=1;c.strokeStyle=CYAN+'.85)';
  for(let k=0;k<5;k++){c.fillStyle=k%2?'#04080a':CYAN+'.85)';c.fillRect(x0+k*seg,y0,seg,5);c.strokeRect(x0+k*seg+.5,y0+.5,seg,5);}
  c.fillStyle=PALE+'.9)';c.font=SERIF(11);c.textAlign='center';c.fillText('0',x0,y0-4);c.fillText('5 km',x0+5*seg,y0-4);c.textAlign='left';
}
function rose(c,e){              // rose des vents
  const x=e.W-48,y=e.H-54,r=21;c.save();c.translate(x,y);c.strokeStyle=CYAN+'.8)';c.fillStyle=CYAN+'.8)';c.lineWidth=1;
  c.beginPath();c.arc(0,0,r,0,6.2832);c.stroke();c.globalAlpha=.5;c.beginPath();c.arc(0,0,r*.62,0,6.2832);c.stroke();c.globalAlpha=1;
  for(let k=0;k<16;k++){const a=k*Math.PI/8,l=k%4===0?r+7:k%2===0?r+4:r+2;c.beginPath();c.moveTo(Math.sin(a)*r,-Math.cos(a)*r);c.lineTo(Math.sin(a)*l,-Math.cos(a)*l);c.stroke();}
  c.beginPath();c.moveTo(0,-r-2);c.lineTo(5,0);c.lineTo(0,r+2);c.lineTo(-5,0);c.closePath();c.fill();
  c.beginPath();c.moveTo(-r-2,0);c.lineTo(0,4);c.lineTo(r+2,0);c.lineTo(0,-4);c.closePath();c.stroke();
  c.font=SERIF(12,'italic bold');c.textAlign='center';c.fillText('N',0,-r-11);c.restore();
}
function drawStatic(c,e){
  const g=c.createRadialGradient(e.W/2,e.H/2,e.W*.05,e.W/2,e.H/2,e.H*.8);g.addColorStop(0,'#0d1c20');g.addColorStop(1,'#04080a');c.fillStyle=g;c.fillRect(0,0,e.W,e.H);
  gridLines(c,e,1000,'rgba(61,242,200,.045)');gridLines(c,e,5000,'rgba(61,242,200,.15)');
  frameChart(c,e);echelle(c,e);rose(c,e);
}
function drawIslands(c,e,t){     // les îles dépendent du temps (propriétaire) : dessinées à chaque image
  if(!flt.isl)return;
  const pat=hatchPattern(c);
  ISL.forEach(i=>{const team=teamOfIsland(i.id,t),rgb=RGB[team];
    [1.5,1.25].forEach((s,j)=>{coast(c,e,i,s);c.strokeStyle='rgba(95,225,210,'+(0.20+j*0.10)+')';c.lineWidth=.8;c.setLineDash([1.5,4]);c.stroke();c.setLineDash([]);});   // lignes de sonde
    coast(c,e,i,1);c.fillStyle='rgba(8,34,36,.88)';c.fill();c.fillStyle=pat;c.fill();c.fillStyle=rgba(rgb,.10);c.fill();                                          // terre hachurée
    c.strokeStyle=rgba(mix([95,225,210],rgb,0.75),.95);c.lineWidth=1.6;c.stroke();
    const [x,y]=e.P(i.x,i.z),Rr=i.half*0.85*e.S;c.font=SERIF(12,'italic bold');c.textAlign='center';halo(c,'Île '+i.id,x,y+Rr*1.05+12,COL[team]);c.textAlign='left';});
}
function routes(c,e){
  if(flt.route){
    e.w.carriers.forEach(u=>{const [x,y]=e.P(u.x,u.z);c.setLineDash([3,5]);c.lineWidth=1;c.font=SERIF(10);c.textAlign='center';   // anneaux de distance (radar)
      [5000,10000,15000,20000].forEach(r=>{c.strokeStyle=CYAN+'.16)';c.beginPath();c.arc(x,y,r*e.S,0,6.2832);c.stroke();c.fillStyle=PALE+'.5)';c.fillText(r/1000+' km',x,y-r*e.S-3);});c.setLineDash([]);c.textAlign='left';});
    [1,2].forEach(t=>{const pts=e.w.wakes[t];if(!pts)return;                                                                  // route du porte-avions : trait mixte
      c.strokeStyle=COL[t];c.lineWidth=1.5;c.globalAlpha=.85;c.setLineDash([6,3]);c.beginPath();pts.forEach((p,k)=>{const q=e.P(p[0],p[1]);k?c.lineTo(q[0],q[1]):c.moveTo(q[0],q[1]);});c.stroke();c.setLineDash([]);
      const s0=e.P(pts[0][0],pts[0][1]);c.globalAlpha=1;c.lineWidth=1.2;c.beginPath();c.arc(s0[0],s0[1],4.5,0,6.2832);c.stroke();});
  }
}
function flights(c,e){if(!flt.air)return;c.lineWidth=1.2;c.setLineDash([1.5,3]);e.w.ftr.forEach(t=>{c.strokeStyle=COL[t.team];c.globalAlpha=.7;c.beginPath();t.pts.forEach((p,k)=>{const q=e.P(p[0],p[1]);k?c.lineTo(q[0],q[1]):c.moveTo(q[0],q[1]);});c.stroke();});c.setLineDash([]);c.globalAlpha=1;}
function units(c,e){
  const order=u=>CATOF(u.def)==='air'?3:CATOF(u.def)==='sea'?1:0;
  const aBord=u=>e.w.carriers.some(cv=>cv.team===u.team&&Math.hypot(cv.x-u.x,cv.z-u.z)<120);   // sur le pont du porte-avions : on ne dessine que le porte-avions
  e.w.units.slice().sort((a,b)=>order(a)-order(b)).forEach(u=>{if(!vis(u)||!ICON[u.def]||aBord(u))return;const k=CATOF(u.def),[x,y]=e.P(u.x,u.z),n=ICON[u.def],sz=0.55*(SIZE[u.def]||14)*(u.team===0&&k==='land'?0.85:1);
    icon(c,n,x,y,sz,sz*(IMG[n].height/IMG[n].width),u.yaw||0,COL[u.team],0);
    e.hits.push({x,y,r:Math.max(5,sz/2),t:(NAME[u.def]||('Type '+u.def))+' · '+TNAME[u.team],col:COL[u.team]});});
  e.w.carriers.forEach(u=>{const [x,y]=e.P(u.x,u.z),right=x>e.W*.7;c.strokeStyle=COL[u.team];c.globalAlpha=.55;c.lineWidth=1;c.setLineDash([2,3]);c.beginPath();c.arc(x,y,16,0,6.2832);c.stroke();c.setLineDash([]);c.globalAlpha=1;
    icon(c,'carrier',x,y,12,24,u.yaw,COL[u.team],0);
    c.font=SERIF(12,'italic bold');c.textAlign=right?'right':'left';halo(c,ONLY===null?'PA '+u.team:'Porte-avions',x+(right?-21:21),y+4,COL[u.team]);c.textAlign='left';
    e.hits.push({x,y,r:14,t:'Porte-avions · '+TNAME[u.team],col:COL[u.team]});});
}
/*MISSILES*/
function render(now){
  if(!W)return;
  const w=R?frameAt(R,T):{units:[],ftr:[],carriers:[],wakes:{},ticks:{},mis:[],imp:[],past:[],all:[]},e=makeEnv(w);
  if(dirty){const c=stat.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);c.textAlign='left';c.lineCap='round';c.setLineDash([]);drawStatic(c,e);dirty=false;}
  const m=cv.getContext('2d');m.setTransform(1,0,0,1,0,0);m.globalCompositeOperation='source-over';m.globalAlpha=1;m.shadowBlur=0;m.drawImage(stat,0,0);
  m.setTransform(dpr,0,0,dpr,0,0);m.textAlign='left';m.lineCap='round';m.setLineDash([]);
  if(R){drawIslands(m,e,T);routes(m,e);flights(m,e);units(m,e);missiles(m,e);}
  else{m.fillStyle=PALE+'.9)';m.font=SERIF(14);m.textAlign='center';m.fillText('Charge un enregistrement',W/2,H/2-8);m.fillText('ou clique sur une partie ou sur Démo',W/2,H/2+14);m.textAlign='left';}
  if(hover){let best=null,bd=1e9;e.hits.forEach(h=>{const d=Math.hypot(h.x-hover.x,h.y-hover.y);if(d<h.r+4&&d<bd){bd=d;best=h;}});
    if(best){m.font=SERIF(12);const w2=m.measureText(best.t).width+14;let bx=best.x+14,by=best.y-11;if(bx+w2>W-4)bx=best.x-14-w2;m.fillStyle='rgba(5,12,14,.95)';m.fillRect(bx,by,w2,21);m.strokeStyle=best.col;m.lineWidth=1;m.strokeRect(bx+.5,by+.5,w2-1,20);m.fillStyle='#d8fbff';m.fillText(best.t,bx+7,by+14);}}
  if(R)updateUI(w);
}
function buildMarks(){           // repères d'événements sur la barre de temps (seulement les équipes affichées)
  if(!R)return;const bar=$('bar');bar.querySelectorAll('u').forEach(u=>u.remove());
  R.events.forEach(ev=>{if(!teamOk(ev.team))return;const u=document.createElement('u');u.style.left=((ev.tick-R.t0)/Math.max(1,R.t1-R.t0)*100)+'%';u.style.background=COL[ev.team];bar.appendChild(u);});
}
function parties(){              // parties intégrées à la page (facultatif) : un bouton chacune, la marquée « auto » se charge seule
  const el=$('parties');document.querySelectorAll('script[data-partie]').forEach(s=>{const b=document.createElement('button');b.textContent=s.dataset.partie;b.onclick=()=>loadText(s.dataset.partie,s.textContent);el.appendChild(b);});
  const a=document.querySelector('script[data-auto]');if(a)loadText(a.dataset.partie,a.textContent);
}
