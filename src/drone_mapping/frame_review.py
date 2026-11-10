"""Create a private offline HTML review page from a frame-extraction manifest.

No server, cloud requests, inferred georeferencing or material confirmation.
Annotations are drawn as normalized rectangles on each image, and explicitly
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
#framebox{position:relative;width:100%;user-select:none;touch-action:none;background:#24313b}
#photo{display:block;width:100%;height:auto;pointer-events:none}
#overlay{position:absolute;inset:0;width:100%;height:100%;cursor:crosshair;touch-action:none}
#overlay rect{fill:#ffb74d55;stroke:#ff9c1c;stroke-width:3;vector-effect:non-scaling-stroke;pointer-events:none}
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
<div id="framebox"><img id="photo" alt="Kadar iz DJI snimka"><svg id="overlay" viewBox="0 0 1000 1000" preserveAspectRatio="none"></svg></div>
<p class="note">Prevuci mišem pravougaonik oko pojedinačnog krova ili dela objekta. Jedan kadar može imati više oznaka. Način prikaza nije georeferenciranje.</p>
</section>
<section>
<strong>Nova oznaka</strong>
<label>Opis oblasti</label><input id="label" placeholder="npr. dva krova gore levo / deo vrtića">
<label>Vizuelna kategorija</label><select id="category">
<option value="suspected_fibrecement">Sumnja na vlaknocementni pokrivač</option>
<option value="other_roof">Drugi tip krova</option>
<option value="kindergarten_area">Deo objekta vrtića</option>
<option value="replaced_roof_section">Zamenjeni deo krova — istorijska promena</option>
<option value="unknown">Neodređeno</option></select>
<label>Opis / napomena</label><textarea id="note" placeholder="Šta se vidi; šta treba proveriti?"></textarea>
<label>KML oznaka (opciono, ručna veza)</label><input id="kml" placeholder="ID placemarka ili originalni naziv">
<div><button class="primary" id="save" disabled>Sačuvaj исцртану област</button><button id="cancel">Откажи цртање</button></div>
<hr>
<strong>Ознаке на овом кадру</strong><ol id="records"></ol>
<hr>
<button class="primary" id="export">Извези annotations JSON</button>
<label>Настави рад: учитај раније извезен JSON</label><input type="file" id="import" accept=".json,application/json">
<p class="note">Промене нису аутоматски сачуване. Извези JSON пре затварања. Снимци и ознаке остају локални; ништа се не шаље на сервер. Све визуелне процене су без лабораторијске потврде.</p>
</section></main>
<script>
"use strict";
const dataset=__DATA__;
let index=0, records=[], start=null, draft=null, counter=0;
const byId=id=>document.getElementById(id);
byId("source").textContent=dataset.source_filename;
const box=byId("overlay"), img=byId("photo");
function clamp(v){return Math.min(1,Math.max(0,v))}
function point(e){const b=box.getBoundingClientRect();return [clamp((e.clientX-b.left)/b.width),clamp((e.clientY-b.top)/b.height)]}
function rect(a,b){return {x:Math.min(a[0],b[0]),y:Math.min(a[1],b[1]),w:Math.abs(a[0]-b[0]),h:Math.abs(a[1]-b[1])}}
function drawShape(r,kind){const n=document.createElementNS("http://www.w3.org/2000/svg","rect");n.setAttribute("x",r.x*1000);n.setAttribute("y",r.y*1000);n.setAttribute("width",r.w*1000);n.setAttribute("height",r.h*1000);if(kind==="draft"){n.setAttribute("stroke","#35f3ee")}box.appendChild(n)}
function active(){return dataset.frames[index]}
function render(){
 const f=active();const url=encodeURIComponent(f.filename);if(img.getAttribute("src")!==url)img.src=url;byId("position").textContent=(index+1)+"/"+dataset.frames.length+" — "+f.filename+" — "+f.requested_seek_seconds+" s";
 box.replaceChildren();
 const current=records.filter(r=>r.frame_filename===f.filename);
 for(const r of current)drawShape(r.box,"saved");
 if(draft)drawShape(draft,"draft");
 const list=byId("records");list.replaceChildren();
 for(const r of current){
  const li=document.createElement("li");li.appendChild(document.createTextNode(r.description+" ["+r.visual_category+"] "));
  const del=document.createElement("button");del.textContent="Обриши";del.onclick=()=>{records=records.filter(x=>x.id!==r.id);render()};li.appendChild(del);list.appendChild(li);
 }
 byId("save").disabled=!draft;
}
box.addEventListener("pointerdown",e=>{start=point(e);draft=null;box.setPointerCapture(e.pointerId)});
box.addEventListener("pointermove",e=>{if(!start)return;draft=rect(start,point(e));render()});
box.addEventListener("pointerup",e=>{if(!start)return;draft=rect(start,point(e));start=null;if(draft.w<.006||draft.h<.006)draft=null;render()});
function go(delta){start=null;draft=null;index=Math.min(dataset.frames.length-1,Math.max(0,index+delta));render()}
byId("prev").onclick=()=>go(-1);byId("next").onclick=()=>go(1);
byId("cancel").onclick=()=>{start=null;draft=null;render()};
byId("save").onclick=()=>{
 if(!draft)return;
 const f=active();counter++;
 records.push({id:"a"+counter,source_video:dataset.source_filename,frame_filename:f.filename,requested_seek_seconds:f.requested_seek_seconds,
  box:draft,image_width_px:img.naturalWidth,image_height_px:img.naturalHeight,
  description:byId("label").value.trim(),visual_category:byId("category").value,note:byId("note").value.trim(),
  kml_reference:byId("kml").value.trim()||null,evidence_status:"MANUAL_VISUAL_REVIEW_NOT_LAB_CONFIRMED"});
 draft=null;byId("label").value="";byId("note").value="";byId("kml").value="";render();
};
byId("export").onclick=()=>{
 const payload={schema_version:1,source_video:dataset.source_filename,review_type:"MANUAL_RECTANGLE_VISUAL_REVIEW",annotations:records};
 const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:"application/json"}));
 const a=document.createElement("a");a.href=url;a.download="annotations_"+dataset.source_filename.replace(/\.mp4$/i,"")+".json";a.click();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
};
byId("import").onchange=async e=>{
 const file=e.target.files[0];if(!file)return;
 try{const data=JSON.parse(await file.text());
 if(data.source_video!==dataset.source_filename||!Array.isArray(data.annotations))throw Error("Neodgovarajući izvor ili format");
 const names=new Set(dataset.frames.map(f=>f.filename));
 if(data.annotations.some(r=>!names.has(r.frame_filename)||!r.box||!["x","y","w","h"].every(k=>Number.isFinite(r.box[k])&&r.box[k]>=0&&r.box[k]<=1)||r.box.x+r.box.w>1.000001||r.box.y+r.box.h>1.000001))throw Error("Neispravne geometrije ili nazivi");
 if(records.length&&!confirm("Zameniti trenutne oznake podacima iz JSON-a?"))return;
 records=data.annotations;counter=records.length;render();
 }catch(err){alert("Uvoz nije uspeo: "+err.message)}
};
window.addEventListener("beforeunload",e=>{if(records.length){e.preventDefault();e.returnValue=""}});
render();
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
