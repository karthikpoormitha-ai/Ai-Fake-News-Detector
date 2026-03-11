const c = document.getElementById("particles");
const ctx = c.getContext("2d");
let w, h, p = [];

function resize() {
  w = c.width = window.innerWidth;
  h = c.height = window.innerHeight;
}
window.onresize = resize; resize();

for (let i=0;i<80;i++) p.push({x:Math.random()*w,y:Math.random()*h,vx:(Math.random()-0.5),vy:(Math.random()-0.5)});

function draw() {
  ctx.clearRect(0,0,w,h);
  ctx.fillStyle = "rgba(0,255,255,0.7)";
  p.forEach(pt=>{
    pt.x+=pt.vx; pt.y+=pt.vy;
    if(pt.x<0||pt.x>w) pt.vx*=-1;
    if(pt.y<0||pt.y>h) pt.vy*=-1;
    ctx.beginPath(); ctx.arc(pt.x,pt.y,2,0,Math.PI*2); ctx.fill();
  });
  requestAnimationFrame(draw);
}
draw();
