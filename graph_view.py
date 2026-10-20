"""Local SVG graph: no third-party JavaScript, CDNs or trackers."""
import json
import textwrap

from career_logic import materia_id, estado_materia, entorno_materia

COLORS = {"Aprobada": "#2ecc71", "Final": "#f5a04b", "Cursando": "#f1c40f",
          "Disponible": "#61b9ff", "Bloqueada": "#c1c7d0"}
LABELS = {"Final": "Final pendiente"}


def graph_data(plan, estados, foco=None):
    visible = entorno_materia(foco, plan)
    levels = {}
    def level(m, visiting=None):
        if m in levels:
            return levels[m]
        visiting = set() if visiting is None else visiting
        if m in visiting:
            raise ValueError("El plan contiene un ciclo de correlativas")
        parents = [p for p in plan[m]["correlativas"] if p in visible]
        levels[m] = max((level(p, visiting | {m}) + 1 for p in parents), default=0)
        return levels[m]
    rows, nodes = {}, []
    for m in plan:
        if m not in visible:
            continue
        column = level(m)
        row = rows.get(column, 0)
        rows[column] = row + 1
        state = estado_materia(m, plan, estados)
        nodes.append(dict(id=materia_id(m), name=m, state=LABELS.get(state, state),
                          color=COLORS[state], lines=textwrap.wrap(m, width=29),
                          credits=plan[m]["puntos"], requirements=plan[m]["correlativas"],
                          x=column*320+30, y=row*155+30))
    edges = [dict(source=materia_id(c), target=materia_id(m)) for m in plan if m in visible
             for c in plan[m]["correlativas"] if c in visible]
    return dict(nodes=nodes, edges=edges, focus=materia_id(foco) if foco else None)


def graph_html(plan, estados, foco=None):
    # Escape script terminators even if future plans contain imported names.
    payload = json.dumps(graph_data(plan, estados, foco), ensure_ascii=False).replace("<", "\\u003c")
    return TEMPLATE.replace("__GRAPH_DATA__", payload)


TEMPLATE = r'''<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;background:#0b0d11;color:#e0e0e0;font:14px monospace}
.controls{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
button{background:#1a1c23;color:#f1c40f;border:1px solid #737d8f;border-radius:6px;padding:10px 12px;min-height:44px;cursor:pointer;font:inherit}
button:hover{background:#34301b}button:focus-visible,svg:focus-visible{outline:3px solid #f1c40f;outline-offset:2px}
svg{display:block;width:100%;height:440px;background:#10151e;border:1px solid #536077;border-radius:8px;touch-action:none;cursor:grab}
svg:active{cursor:grabbing}.node{cursor:pointer}.node:focus{outline:none}.node:focus rect{stroke:#fff;stroke-width:4}
.node.selected rect{stroke:#f1c40f;stroke-width:4;filter:drop-shadow(0 0 5px #f1c40f66)}
#detail{padding:10px 12px;line-height:1.5;background:#1a1c23;border-left:3px solid #f1c40f;min-height:68px;margin-top:10px;white-space:pre-line}
.hint{color:#bbc5d6;font-size:13px;line-height:1.5;margin:8px 0}
@media(max-width:640px){svg{height:360px}button{flex:1;font-size:13px}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.node.selected rect{filter:none}}
</style></head><body>
<div class="controls" role="group" aria-label="Controles del mapa">
<button id="in" aria-label="Acercar mapa">＋ Acercar</button><button id="out" aria-label="Alejar mapa">− Alejar</button>
<button id="center">◎ Centrar selección</button><button id="reset">↺ Ver todo</button></div>
<p class="hint" id="help">Seleccioná una materia para ver sus requisitos. Arrastrá para mover; usá los botones o pellizcá para zoom. Teclado: flechas, +, − y Home. La lista de Planificar ofrece la misma información.</p>
<svg id="map" viewBox="0 0 1000 540" tabindex="0" role="group" aria-label="Mapa de correlatividades" aria-describedby="help">
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#8093b3"/></marker></defs>
<g id="world"></g></svg><div id="detail" role="status" aria-live="polite">Elegí una materia.</div>
<script>
(()=>{'use strict';const data=__GRAPH_DATA__, svg=document.getElementById('map'),world=document.getElementById('world');
const NS='http://www.w3.org/2000/svg',index=new Map(data.nodes.map(n=>[n.id,n]));let zoom=1,px=0,py=0,selected=data.focus,vw=1000,vh=540;
function el(tag,attrs,text){const e=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text!==undefined)e.textContent=text;return e}
function draw(){world.setAttribute('transform',`translate(${px},${py}) scale(${zoom})`)}
function scale(factor,cx=vw/2,cy=vh/2){const next=Math.max(.08,Math.min(3,zoom*factor));px=cx-(cx-px)*next/zoom;py=cy-(cy-py)*next/zoom;zoom=next;draw()}
function fit(){const width=Math.max(...data.nodes.map(n=>n.x+260),1),height=Math.max(...data.nodes.map(n=>n.y+125),1);zoom=Math.min((vw-32)/width,(vh-32)/height,1.15);px=(vw-width*zoom)/2;py=(vh-height*zoom)/2;draw()}
function center(){const n=index.get(selected);if(!n){fit();return}zoom=Math.min(1.3,(vw-24)/260);px=vw/2-(n.x+130)*zoom;py=vh/2-(n.y+62)*zoom;draw()}
function select(id){selected=id;world.querySelectorAll('.node').forEach(e=>e.classList.toggle('selected',e.getAttribute('data-id')===id));const n=index.get(id);document.getElementById('detail').textContent=`${n.name} · ${n.state} · ${n.credits} créditos\nRequiere: ${n.requirements.join(', ')||'Sin correlativas'}`}
for(const edge of data.edges){const a=index.get(edge.source),b=index.get(edge.target);const x1=a.x+260,y1=a.y+62,x2=b.x,y2=b.y+62;world.append(el('path',{d:`M${x1},${y1} C${x1+32},${y1} ${x2-32},${y2} ${x2},${y2}`,fill:'none',stroke:'#8093b3','stroke-width':2,'marker-end':'url(#arrow)'}))}
for(const n of data.nodes){const g=el('g',{'class':'node','data-id':n.id,tabindex:0,role:'button','aria-label':`${n.name}. ${n.state}. ${n.credits} créditos`,transform:`translate(${n.x},${n.y})`});g.append(el('rect',{width:260,height:125,rx:8,fill:'#1a2432',stroke:n.color,'stroke-width':2}));n.lines.forEach((line,i)=>g.append(el('text',{x:12,y:23+i*18,fill:'#f2f5fa','font-size':14},line)));g.append(el('text',{x:12,y:110,fill:n.color,'font-size':13},`${n.state} · ${n.credits} cr.`));g.addEventListener('click',()=>select(n.id));g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();select(n.id)}});world.append(g)}
document.getElementById('in').onclick=()=>scale(1.3);document.getElementById('out').onclick=()=>scale(1/1.3);document.getElementById('center').onclick=center;document.getElementById('reset').onclick=fit;
svg.addEventListener('keydown',e=>{if(e.target!==svg)return;const moves={ArrowLeft:[50,0],ArrowRight:[-50,0],ArrowUp:[0,50],ArrowDown:[0,-50]};if(moves[e.key]){e.preventDefault();px+=moves[e.key][0];py+=moves[e.key][1];draw()}else if(['+','=','-','Home'].includes(e.key)){e.preventDefault();if(e.key==='Home')fit();else scale(e.key==='-'?1/1.3:1.3)}});
const pointers=new Map();let previousDistance=null;
const point=e=>{const r=svg.getBoundingClientRect();return{x:(e.clientX-r.left)*vw/r.width,y:(e.clientY-r.top)*vh/r.height}};
svg.addEventListener('pointerdown',e=>{if(e.target.closest('.node'))return;svg.setPointerCapture(e.pointerId);pointers.set(e.pointerId,point(e));previousDistance=null});
svg.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;const old=pointers.get(e.pointerId),p=point(e);pointers.set(e.pointerId,p);if(pointers.size===1){px+=p.x-old.x;py+=p.y-old.y;draw()}else if(pointers.size===2){const [a,b]=[...pointers.values()],distance=Math.hypot(a.x-b.x,a.y-b.y);if(previousDistance)scale(distance/previousDistance,(a.x+b.x)/2,(a.y+b.y)/2);previousDistance=distance}});
for(const event of ['pointerup','pointercancel','lostpointercapture'])svg.addEventListener(event,e=>{pointers.delete(e.pointerId);previousDistance=null});
function resize(){const r=svg.getBoundingClientRect();vw=r.width;vh=r.height;svg.setAttribute('viewBox',`0 0 ${vw} ${vh}`);if(vw<640&&selected)center();else fit()}
new ResizeObserver(resize).observe(svg);resize();if(selected)select(selected);
})();</script></body></html>'''
