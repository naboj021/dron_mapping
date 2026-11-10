"""Create a private offline HTML review page from a frame-extraction manifest.

No server, cloud requests, inferred georeferencing or material confirmation.
Annotations are drawn as editable normalized polygons on each image, and explicitly
exported to a local JSON file by the reviewer.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_HTML = r"""<!doctype html>
<html lang="sr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AZBEST MAPA | Lokalni pregled kadrova</title>
<style>
:root{font-family:system-ui,Segoe UI,sans-serif;color:#1b2733;background:#f1f3f6}
body{margin:0}header{background:#173047;color:#fff;padding:12px 20px}
header small{display:block;opacity:.84}main{display:grid;grid-template-columns:minmax(0,2fr) minmax(280px,1fr);gap:14px;padding:14px}
section{background:white;padding:12px;border-radius:10px;box-shadow:0 1px 5px #0001}
button,select,input,textarea{font:inherit}button{cursor:pointer;padding:7px 10px;margin:3px;border:1px solid #a9b8c6;border-radius:6px;background:#fff}
button.primary{background:#176e57;color:white;border-color:#176e57}
#viewer{width:100%;height:62vh;min-height:300px;max-height:750px;text-align:center;overflow:auto;background:#24313b;border-radius:6px}
#framebox{position:relative;display:inline-block;vertical-align:top;user-select:none;line-height:0}
#photo{display:block;max-width:none;max-height:none;pointer-events:none}
#overlay{position:absolute;inset:0;width:100%;height:100%;cursor:crosshair;touch-action:none}
#overlay polygon{fill:#ffb74d44;stroke:#ff9c1c;stroke-width:2;vector-effect:non-scaling-stroke;pointer-events:none}
#overlay polygon.selected{stroke:#10c4cc;stroke-width:3}
#overlay circle{fill:white;stroke:#087f82;stroke-width:2;vector-effect:non-scaling-stroke;cursor:grab;pointer-events:all}
#overlay circle:active{cursor:grabbing}
#overlay line.edge{stroke:transparent;stroke-width:16;vector-effect:non-scaling-stroke;pointer-events:stroke;cursor:move}

label{display:block;font-size:13px;margin-top:10px;font-weight:600}
input,textarea,select{width:100%;box-sizing:border-box;padding:7px;border:1px solid #afbcc6;border-radius:5px}
textarea{height:70px;resize:vertical}
#records{padding-left:20px;max-height:230px;overflow:auto}
#records li{margin-bottom:7px;overflow-wrap:anywhere}
.note{font-size:13px;color:#5d6570}
@media(max-width:850px){main{display:block}section{margin-bottom:12px}}
</style></head><body>
<header><strong>AZBEST MAPA — pregled kadrova (lokalno)</strong><small id="source"></small></header>
<main>
<section>
<div><button id="prev">← Prethodni</button><button id="next">Sledeći →</button><strong id="position"></strong></div>
<div><button id="zoomout" aria-label="Umanji fotografiju">−</button><input id="zoom" type="range" min="100" max="500" step="25" value="100" style="width:140px;vertical-align:middle" aria-label="Zum fotografije"><button id="zoomin" aria-label="Uvećaj fotografiju">+</button><button id="fit">Uklopi</button><span id="zoomvalue">100%</span></div>
<div id="viewer"><div id="framebox"><img id="photo" alt="Kadar iz DJI snimka"><svg id="overlay" viewBox="0 0 1000 1000" preserveAspectRatio="none"></svg></div></div>
<p class="note">Кликни редом на углове крова (најмање три), унеси податке па кликни „Сачувај област“. Зум користи контроле изнад слике; за померање увећане слике користи траке за померање. Одабери постојећу ознаку испод фотографије за измену темена или ивица.</p>
<hr>
<strong>Ознаке на овом кадру</strong><ol id="records"></ol>
</section>
<section>
<strong>Nova oznaka</strong>
<label>Положај дела објекта / крова</label><select id="orientation">
<option value="">Није одређено</option>
<option value="N">Север</option><option value="NE">Североисток</option>
<option value="E">Исток</option><option value="SE">Југоисток</option>
<option value="S">Југ</option><option value="SW">Југозапад</option>
<option value="W">Запад</option><option value="NW">Северозапад</option>
<option value="CENTRAL">Средишњи део</option>
</select>
<label>Opis oblasti</label><input id="label" placeholder="npr. dva krova gore levo / deo vrtića">
<label>Vizuelna kategorija</label><select id="category">
<option value="suspected_fibrecement">Sumnja na vlaknocementni pokrivač</option>
<option value="other_roof">Drugi tip krova</option>
<option value="kindergarten_area">Deo objekta vrtića</option>
<option value="replaced_roof_section">Zamenjeni deo krova — istorijska promena</option>
<option value="unknown">Neodređeno</option></select>
<label>Opis / napomena</label><textarea id="note" placeholder="Šta se vidi; šta treba proveriti?"></textarea>
<label>KML ID објекта (опционо, може се понављати за више кровова)</label><input id="kml" placeholder="Остави празно ако област није била у KML-у">
<div><button class="primary" id="save" disabled>Сачувај област</button><button id="cancel">Откажи цртање</button></div>
<hr>
<div id="saveStatus" role="status" style="font-weight:600;margin:8px 0">Провера локалног чувања…</div><button class="primary" id="export">Извези annotations JSON (резервна копија)</button>
<label>Настави рад: учитај раније извезен JSON</label><input type="file" id="import" accept=".json,application/json">
<p class="note">Када је страница отворена преко локалног http://127.0.0.1 сервера, свака измена се аутоматски чува у локални JSON на диску. На file:// страници нема аутоматског чувања: обавезно извези JSON. Ниједан податак се не шаље на интернет. Означени материјал није лабораторијски потврђен.</p>
</section></main>
<script>
"use strict";
const dataset=__DATA__;
let index=0, records=[], draft=[], selectedId=null, drag=null, counter=0, dirty=false, zoom=1;
const localMode=location.protocol==="http:"&&location.hostname==="127.0.0.1";
const reviewToken="__LOCAL_REVIEW_TOKEN__";
let saveQueue=Promise.resolve(), editVersion=0, savedVersion=0, loaded=false;
const byId=id=>document.getElementById(id);
byId("source").textContent=dataset.source_filename;
const overlay=byId("overlay"), img=byId("photo"), viewer=byId("viewer"), framebox=byId("framebox");
function fitDimensions(){
 if(!img.naturalWidth||!img.naturalHeight)return null;
 const scale=Math.min(viewer.clientWidth/img.naturalWidth,viewer.clientHeight/img.naturalHeight,1);
 return {w:img.naturalWidth*scale,h:img.naturalHeight*scale};
}
function updateZoom(keepCenter=true){
 const base=fitDimensions();if(!base)return;
 const cx=viewer.scrollLeft+viewer.clientWidth/2,cy=viewer.scrollTop+viewer.clientHeight/2;
 const oldWidth=framebox.offsetWidth||base.w,oldHeight=framebox.offsetHeight||base.h;
 const xRatio=cx/oldWidth,yRatio=cy/oldHeight;
 const w=base.w*zoom,h=base.h*zoom;
 framebox.style.width=w+"px";framebox.style.height=h+"px";
 img.style.width=w+"px";img.style.height=h+"px";
 byId("zoom").value=Math.round(zoom*100);
 byId("zoomvalue").textContent=Math.round(zoom*100)+"%";
 if(keepCenter){viewer.scrollLeft=xRatio*w-viewer.clientWidth/2;viewer.scrollTop=yRatio*h-viewer.clientHeight/2;}
 else{viewer.scrollLeft=0;viewer.scrollTop=0;}
}
img.addEventListener("load",()=>updateZoom(false));
window.addEventListener("resize",()=>updateZoom());
byId("zoom").oninput=e=>{zoom=Number(e.target.value)/100;updateZoom()};
byId("zoomin").onclick=()=>{zoom=Math.min(5,zoom+.25);updateZoom()};
byId("zoomout").onclick=()=>{zoom=Math.max(1,zoom-.25);updateZoom()};
byId("fit").onclick=()=>{zoom=1;updateZoom(false)};

const clamp=v=>Math.max(0,Math.min(1,v));
const active=()=>dataset.frames[index];
function status(message){byId("saveStatus").textContent=message}
function scheduleSave(){
 dirty=true;const revision=++editVersion;
 if(!localMode){status("Није аутоматски сачувано: извези JSON или отвори локални сервер.");return}
 const payload=JSON.stringify({schema_version:2,source_video:dataset.source_filename,
  review_type:"MANUAL_POLYGON_VISUAL_REVIEW",annotations:records});
 status("Чување у локални JSON…");
 saveQueue=saveQueue.catch(()=>{}).then(async()=>{
  const response=await fetch("/api/annotations",{
   method:"POST",headers:{"Content-Type":"application/json","X-Review-Token":reviewToken},
   body:payload
  });
  if(!response.ok)throw Error(await response.text());
  savedVersion=Math.max(savedVersion,revision);
  if(savedVersion===editVersion){dirty=false;status("Сачувано на диску ✓")}
 }).catch(err=>{status("ГРЕШКА чувања — извези JSON! "+err.message)});
}
async function loadSaved(){
 if(!localMode){loaded=true;status("file:// режим: нема аутоматског чувања — извези JSON.");render();return}
 try{
  const response=await fetch("/api/annotations",{headers:{"X-Review-Token":reviewToken}});
  if(!response.ok)throw Error(await response.text());
  const data=await response.json();
  if(data.source_video!==dataset.source_filename||!Array.isArray(data.annotations))throw Error("Неодговарајућа датотека");
  records=data.annotations;counter=records.length;savedVersion=editVersion;dirty=false;loaded=true;
  status("Локално чување укључено ✓ ("+records.length+" ознака учитано)");
 }catch(err){status("Не могу да учитам локалне ознаке: "+err.message+". Не почињи анотацију.");}
 finally{render()}
}
const coords=e=>{const b=overlay.getBoundingClientRect();return [clamp((e.clientX-b.left)/b.width),clamp((e.clientY-b.top)/b.height)]};
const polygonPoints=r=>r.points || (r.box?[[r.box.x,r.box.y],[r.box.x+r.box.w,r.box.y],[r.box.x+r.box.w,r.box.y+r.box.h],[r.box.x,r.box.y+r.box.h]]:[]);
const svg=(tag)=>document.createElementNS("http://www.w3.org/2000/svg",tag);
function draw(points,kind,owner){
 if(!points.length)return;
 if(points.length>=2){
  const p=svg("polygon");p.setAttribute("points",points.map(q=>(q[0]*1000)+","+(q[1]*1000)).join(" "));
  if(kind!=="saved")p.classList.add("selected");
  if(points.length===2){p.setAttribute("fill","none")}
  overlay.appendChild(p);
 }
 if(kind==="draft"||kind==="selected"){
  if(points.length>=2){
   const count=kind==="draft"?points.length-1:points.length;
   for(let i=0;i<count;i++){
    const a=points[i],b=points[(i+1)%points.length],line=svg("line");
    line.setAttribute("x1",a[0]*1000);line.setAttribute("y1",a[1]*1000);
    line.setAttribute("x2",b[0]*1000);line.setAttribute("y2",b[1]*1000);
    line.classList.add("edge");line.dataset.owner=owner;line.dataset.edge=i;
    overlay.appendChild(line);
   }
  }
  points.forEach((q,i)=>{
   const c=svg("circle");c.setAttribute("cx",q[0]*1000);c.setAttribute("cy",q[1]*1000);
   c.setAttribute("r",7);c.dataset.owner=owner;c.dataset.vertex=i;overlay.appendChild(c);
  });
 }
}
function render(){
 const f=active();const url=encodeURIComponent(f.filename);
 if(img.getAttribute("src")!==url)img.src=url;
 byId("position").textContent=(index+1)+"/"+dataset.frames.length+" — "+f.filename+" — "+f.requested_seek_seconds+" s";
 overlay.replaceChildren();
 const current=records.filter(r=>r.frame_filename===f.filename);
 for(const r of current)draw(polygonPoints(r),r.id===selectedId?"selected":"saved",r.id);
 if(draft.length)draw(draft,"draft","draft");
 const list=byId("records");list.replaceChildren();
 for(const r of current){
  const li=document.createElement("li");
  const choose=document.createElement("button");choose.textContent=(r.id===selectedId?"✓ ":"Измени: ")+(r.orientation?"["+r.orientation+"] ":"")+(r.description||r.visual_category)+(r.kml_reference?" · KML "+r.kml_reference:" · није у KML-у");
  choose.onclick=()=>{selectedId=selectedId===r.id?null:r.id;draft=[];render()};
  const del=document.createElement("button");del.textContent="Обриши";
  del.onclick=()=>{if(confirm("Обрисати ову ознаку?")){records=records.filter(x=>x.id!==r.id);scheduleSave();if(selectedId===r.id)selectedId=null;render()}};
  li.append(choose,del);list.appendChild(li);
 }
 byId("save").disabled=!loaded||draft.length<3;
}
function go(delta){
 if(draft.length&&!confirm("Одбацити незавршени полигон?"))return;
 draft=[];selectedId=null;zoom=1;index=Math.min(dataset.frames.length-1,Math.max(0,index+delta));render();
}
function orient(a,b,c){return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])}
function cross(a,b,c,d){
 const x=orient(a,b,c),y=orient(a,b,d),z=orient(c,d,a),w=orient(c,d,b);
 return x*y<0&&z*w<0;
}
function validPolygon(pts){
 if(pts.length<3)return false;
 const area=Math.abs(pts.reduce((v,p,i)=>{const q=pts[(i+1)%pts.length];return v+p[0]*q[1]-q[0]*p[1]},0)/2);
 if(area<.00002)return false;
 for(let i=0;i<pts.length;i++)for(let j=i+1;j<pts.length;j++){
  if(j===i+1||(i===0&&j===pts.length-1))continue;
  if(cross(pts[i],pts[(i+1)%pts.length],pts[j],pts[(j+1)%pts.length]))return false;
 }
 return true;
}
overlay.addEventListener("pointerdown",e=>{
 const t=e.target;
 if(t.dataset.edge!==undefined){
  const owner=t.dataset.owner,edge=Number(t.dataset.edge);
  const target=owner==="draft"?draft:polygonPoints(records.find(r=>r.id===owner)||{});
  if(edge>=target.length)return;
  drag={owner,edge,last:coords(e)};overlay.setPointerCapture(e.pointerId);e.preventDefault();return;
 }
 if(t.dataset.vertex!==undefined){
  const owner=t.dataset.owner,vertex=Number(t.dataset.vertex);
  const target=owner==="draft"?draft:polygonPoints(records.find(r=>r.id===owner)||{});
  if(vertex>=target.length)return;
  drag={owner,vertex};overlay.setPointerCapture(e.pointerId);e.preventDefault();return;
 }
 if(selectedId)selectedId=null;
 draft.push(coords(e));render();
});
overlay.addEventListener("pointermove",e=>{
 if(!drag)return;
 const p=coords(e);
 const record=drag.owner==="draft"?null:records.find(x=>x.id===drag.owner);
 const target=record?polygonPoints(record):draft;
 if(drag.edge!==undefined){
  const dx=p[0]-drag.last[0],dy=p[1]-drag.last[1];
  const i=drag.edge,j=(i+1)%target.length;
  const deltaX=Math.max(-Math.min(target[i][0],target[j][0]),Math.min(dx,1-Math.max(target[i][0],target[j][0])));
  const deltaY=Math.max(-Math.min(target[i][1],target[j][1]),Math.min(dy,1-Math.max(target[i][1],target[j][1])));
  target[i]=[target[i][0]+deltaX,target[i][1]+deltaY];
  target[j]=[target[j][0]+deltaX,target[j][1]+deltaY];
  drag.last=p;
 }else target[drag.vertex]=p;
 if(record){record.points=target;delete record.box;dirty=true;}
 render();
});
function endDrag(e){if(drag){const recordChange=drag.owner!=="draft";drag=null;if(overlay.hasPointerCapture(e.pointerId))overlay.releasePointerCapture(e.pointerId);if(recordChange)scheduleSave();render()}}
overlay.addEventListener("pointerup",endDrag);
overlay.addEventListener("pointercancel",endDrag);
byId("prev").onclick=()=>go(-1);
byId("next").onclick=()=>go(1);
byId("cancel").onclick=()=>{draft=[];selectedId=null;render()};
byId("save").onclick=()=>{
 if(!loaded){alert("Сачекај потврду учитавања локалних података.");return}
 if(!validPolygon(draft)){alert("Полигон није исправан. Потребна су бар три темена без самопресецања.");return;}
 const f=active();counter++;
 records.push({id:"a"+counter+"_"+Date.now(),source_video:dataset.source_filename,frame_filename:f.filename,
  requested_seek_seconds:f.requested_seek_seconds,points:draft.map(q=>q.slice()),
  image_width_px:img.naturalWidth,image_height_px:img.naturalHeight,
  description:byId("label").value.trim(),orientation:byId("orientation").value,visual_category:byId("category").value,note:byId("note").value.trim(),
  kml_reference:byId("kml").value.trim()||null,evidence_status:"MANUAL_VISUAL_REVIEW_NOT_LAB_CONFIRMED"});
 scheduleSave();draft=[];selectedId=null;byId("label").value="";byId("note").value="";byId("kml").value="";byId("orientation").selectedIndex=0;byId("category").selectedIndex=0;render();
};
byId("export").onclick=()=>{
 const payload={schema_version:2,source_video:dataset.source_filename,review_type:"MANUAL_POLYGON_VISUAL_REVIEW",annotations:records};
 const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:"application/json"}));
 const a=document.createElement("a");a.href=url;a.download="annotations_"+dataset.source_filename.replace(/\.mp4$/i,"")+".json";a.click();
 setTimeout(()=>URL.revokeObjectURL(url),1000);if(!localMode){dirty=false;status("JSON извезен; сачувај преузету датотеку.")}
};
byId("import").onchange=async e=>{
 const file=e.target.files[0];if(!file)return;
 try{
  const data=JSON.parse(await file.text());
  if(data.source_video!==dataset.source_filename||!Array.isArray(data.annotations))throw Error("Неодговарајући извор или формат");
  const names=new Set(dataset.frames.map(f=>f.filename));
  const converted=data.annotations.map((r,i)=>({...r,id:String(r.id||("import_"+i)),points:polygonPoints(r)}));
  if(converted.some(r=>!names.has(r.frame_filename)||r.points.length<3||r.points.some(p=>!Array.isArray(p)||p.length!==2||p.some(v=>!Number.isFinite(v)||v<0||v>1))||!validPolygon(r.points)))throw Error("Неисправне геометрије или називи");
  if((records.length||dirty)&&!confirm("Заменити текуће ознаке подацима из JSON-а?"))return;
  records=converted;counter=records.length;selectedId=null;draft=[];scheduleSave();render();
 }catch(err){alert("Увоз није успео: "+err.message)}
};
window.addEventListener("beforeunload",e=>{if(dirty){e.preventDefault();e.returnValue=""}});
loadSaved();
</script></body></html>"""


def build_review_page(folder: Path, output: Path | None = None) -> Path:
    folder = folder.resolve()
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = manifest.get("source_filename", "")
    frames = manifest.get("frames", [])
    if not source or not frames:
        raise ValueError("Expected a manifest with source_filename and extracted frames")
    clean_frames = []
    for frame in frames:
        name = frame.get("filename", "")
        if not name or Path(name).name != name or Path(name).suffix.lower() not in (".jpg", ".jpeg", ".png"):
            raise ValueError(f"Unsafe or invalid frame filename: {name!r}")
        if not (folder / name).is_file():
            raise FileNotFoundError(f"Missing extracted frame: {name}")
        clean_frames.append({
            "filename": name,
            "requested_seek_seconds": frame.get("requested_seek_seconds"),
        })
    data = json.dumps({"source_filename": source, "frames": clean_frames}, ensure_ascii=False)
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    markup = _HTML.replace("__DATA__", data)
    target = output or folder / "review.html"
    target = target.resolve()
    if target.parent != folder:
        raise ValueError("Review HTML must stay in the frame folder for relative image paths")
    target.write_text(markup, encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Build private HTML multi-roof annotation page")
    parser.add_argument("frames_dir", type=Path, help="Folder containing manifest.json and images")
    args = parser.parse_args()
    print(f"Created local review page: {build_review_page(args.frames_dir)}")


if __name__ == "__main__":
    main()
