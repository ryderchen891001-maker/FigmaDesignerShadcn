import json, collections, os

SP = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(f"{SP}/english-schools.json"))

BANDS = ["0–5 km", "5–10 km", "10–15 km", "15–20 km"]
cnt = collections.Counter(r["band"] for r in rows)
dist_cnt = collections.Counter(f'{r["city"]}{r["district"]}' for r in rows)
districts = [d for d, _ in dist_cnt.most_common()]

data = [{
    "b": BANDS.index(r["band"]),
    "d": r["distance_km"],
    "n": r["name"],
    "a": r["address"],
    "p": r["phone"],
    "w": r["website"],
    "r": r["rating"] if r["rating"] != "" else None,
    "c": r["reviews"] if r["reviews"] != "" else None,
    "t": r["type"],
    "g": f'{r["city"]}{r["district"]}',
    "m": r["maps"],
    "x": r["status"] != "OPERATIONAL",
} for r in rows]

HTML = """<title>楊梅英語補習班名錄</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700&family=Noto+Sans+TC:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --paper:#f2f4f1; --surface:#ffffff; --surface-2:#e9ece7; --raised:#fbfcfa;
  --ink:#15201e; --ink-2:#55625d; --ink-3:#7d8a84;
  --line:#d7dcd4; --line-strong:#bcc4ba;
  --accent:#0b5c50; --accent-ink:#ffffff; --accent-soft:#e2ede8;
  --b1:#0b5c50; --b2:#35806c; --b3:#6f9f88; --b4:#a6bdaf;
  --warn:#8a5a12; --warn-soft:#f6ecd8;
  --focus:#0b5c50;
  --serif:"Noto Serif TC",Georgia,"Songti TC",serif;
  --sans:"Noto Sans TC",-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Menlo,monospace;
}
:root:not([data-theme="light"]){@media (prefers-color-scheme:dark){
  --paper:#111614; --surface:#191f1d; --surface-2:#222a27; --raised:#1e2523;
  --ink:#e7ece9; --ink-2:#9daaa4; --ink-3:#7a8781;
  --line:#2c3733; --line-strong:#3d4a45;
  --accent:#63c4ae; --accent-ink:#0c1a17; --accent-soft:#1b322c;
  --b1:#79d4bd; --b2:#55ae97; --b3:#3f8874; --b4:#4c6b60;
  --warn:#d9ad63; --warn-soft:#2b2417;
  --focus:#63c4ae;
}}
:root[data-theme="dark"]{
  --paper:#111614; --surface:#191f1d; --surface-2:#222a27; --raised:#1e2523;
  --ink:#e7ece9; --ink-2:#9daaa4; --ink-3:#7a8781;
  --line:#2c3733; --line-strong:#3d4a45;
  --accent:#63c4ae; --accent-ink:#0c1a17; --accent-soft:#1b322c;
  --b1:#79d4bd; --b2:#55ae97; --b3:#3f8874; --b4:#4c6b60;
  --warn:#d9ad63; --warn-soft:#2b2417;
  --focus:#63c4ae;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:32px 20px 80px}
a{color:var(--accent)}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{
  outline:2px solid var(--focus);outline-offset:2px;border-radius:3px}

/* ---- masthead ---- */
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--ink-3);margin:0 0 10px}
h1{font-family:var(--serif);font-weight:700;font-size:clamp(28px,4.4vw,42px);
  line-height:1.15;letter-spacing:.01em;margin:0;text-wrap:balance}
.lede{color:var(--ink-2);max-width:60ch;margin:12px 0 0;font-size:15px}
.origin{display:flex;flex-wrap:wrap;gap:8px 22px;margin-top:18px;
  padding-top:16px;border-top:1px solid var(--line)}
.origin div{display:flex;flex-direction:column;gap:2px}
.origin dt{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--ink-3)}
.origin dd{margin:0;font-size:14px;font-variant-numeric:tabular-nums}
.origin dd.mono{font-family:var(--mono);font-size:13px}

/* ---- caveat ---- */
.note{margin:22px 0 0;padding:12px 14px;background:var(--warn-soft);
  border-left:3px solid var(--warn);border-radius:0 4px 4px 0;
  font-size:13.5px;color:var(--ink-2);line-height:1.55}
.note b{color:var(--ink);font-weight:500}

/* ---- band filter ---- */
.bands{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:10px;margin:28px 0 0;padding:0;list-style:none}
.band-btn{display:flex;flex-direction:column;align-items:flex-start;gap:4px;
  width:100%;padding:12px 14px 12px 13px;background:var(--surface);
  border:1px solid var(--line);border-left:4px solid var(--bc,var(--line-strong));
  border-radius:4px;cursor:pointer;font-family:inherit;text-align:left;
  color:var(--ink);transition:border-color .12s,background .12s}
.band-btn:hover{background:var(--raised);border-color:var(--line-strong)}
.band-btn[aria-pressed="true"]{background:var(--accent-soft);
  border-color:var(--accent);border-left-color:var(--bc,var(--accent))}
.band-btn .k{font-family:var(--mono);font-size:12px;letter-spacing:.06em;
  color:var(--ink-2)}
.band-btn .v{font-family:var(--serif);font-size:26px;font-weight:700;
  line-height:1;font-variant-numeric:tabular-nums}
.band-btn .v small{font-family:var(--sans);font-size:12px;font-weight:400;
  color:var(--ink-3);margin-left:4px}

/* ---- controls ---- */
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;
  margin:20px 0 0;padding:14px;background:var(--surface-2);border-radius:4px}
.field{display:flex;align-items:center;gap:7px}
.field label{font-family:var(--mono);font-size:10.5px;letter-spacing:.11em;
  text-transform:uppercase;color:var(--ink-3);white-space:nowrap}
input[type=search],select{font-family:inherit;font-size:14px;color:var(--ink);
  background:var(--surface);border:1px solid var(--line-strong);
  border-radius:4px;padding:7px 9px}
input[type=search]{min-width:210px}
.chk{display:flex;align-items:center;gap:6px;font-size:13.5px;color:var(--ink-2);
  cursor:pointer;user-select:none}
.chk input{accent-color:var(--accent);width:15px;height:15px}
.count{margin-left:auto;font-family:var(--mono);font-size:12.5px;color:var(--ink-2);
  font-variant-numeric:tabular-nums}

/* ---- table ---- */
.tablewrap{margin-top:18px;overflow-x:auto;border:1px solid var(--line);
  border-radius:4px;background:var(--surface)}
table{width:100%;border-collapse:collapse;font-size:14px}
thead th{position:sticky;top:0;z-index:2;background:var(--surface-2);
  font-family:var(--mono);font-size:10.5px;letter-spacing:.11em;
  text-transform:uppercase;color:var(--ink-2);font-weight:500;
  text-align:left;padding:10px 12px;border-bottom:1px solid var(--line-strong);
  white-space:nowrap}
thead th.num{text-align:right}
tbody tr{border-bottom:1px solid var(--line)}
tbody tr:last-child{border-bottom:0}
tbody tr:hover{background:var(--raised)}
td{padding:11px 12px;vertical-align:top}
tr.grouphead td{background:var(--surface-2);padding:8px 12px;
  border-top:1px solid var(--line-strong);border-bottom:1px solid var(--line-strong)}
tr.grouphead span{font-family:var(--mono);font-size:11px;letter-spacing:.13em;
  text-transform:uppercase;color:var(--ink-2);display:inline-flex;
  align-items:center;gap:8px}
tr.grouphead i{width:22px;height:3px;border-radius:2px;background:var(--bc);
  display:inline-block}
td.dist{font-family:var(--mono);font-variant-numeric:tabular-nums;
  text-align:right;white-space:nowrap;color:var(--ink);font-weight:500;
  border-left:4px solid var(--bc);padding-left:10px}
td.dist small{display:block;font-size:10.5px;color:var(--ink-3);font-weight:400}
.nm{font-weight:500;line-height:1.4;display:block;max-width:44ch}
.tag{display:inline-block;margin-top:4px;font-family:var(--mono);font-size:10px;
  letter-spacing:.08em;color:var(--ink-3);border:1px solid var(--line);
  border-radius:99px;padding:1px 7px}
.tag.closed{color:var(--warn);border-color:var(--warn)}
td.addr{color:var(--ink-2);max-width:30ch;font-size:13.5px}
td.tel a{font-family:var(--mono);font-size:13.5px;white-space:nowrap;
  text-decoration:none;border-bottom:1px solid var(--accent-soft)}
td.tel a:hover{border-bottom-color:var(--accent)}
td.web a{font-size:13px;text-decoration:none;border-bottom:1px solid var(--accent-soft)}
td.web a:hover{border-bottom-color:var(--accent)}
.dash{color:var(--ink-3)}
td.rate{font-family:var(--mono);font-variant-numeric:tabular-nums;
  white-space:nowrap;font-size:13px}
td.rate b{font-weight:500}
td.rate small{color:var(--ink-3)}
.empty{padding:48px 16px;text-align:center;color:var(--ink-2)}

footer{margin-top:34px;padding-top:18px;border-top:1px solid var(--line);
  font-size:12.5px;color:var(--ink-3);line-height:1.7;max-width:74ch}
footer code{font-family:var(--mono);font-size:11.5px;background:var(--surface-2);
  padding:1px 5px;border-radius:3px;color:var(--ink-2)}

@media (max-width:760px){
  .wrap{padding:22px 14px 60px}
  thead{display:none}
  table,tbody,tr,td{display:block;width:100%}
  tbody tr{padding:12px 12px 12px 0;border-bottom:1px solid var(--line)}
  td{padding:2px 12px;border:0}
  td.dist{text-align:left;border-left:4px solid var(--bc);padding:2px 12px 2px 10px}
  td.dist small{display:inline;margin-left:6px}
  tr.grouphead{padding:0}
  tr.grouphead td{padding:8px 12px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<div class="wrap">
  <p class="eyebrow">Google Maps Places API · 擷取於 2026-09-09</p>
  <h1>楊梅英語補習班名錄</h1>
  <p class="lede">以桃園市楊梅區永平路為圓心，半徑 20 公里內的英文／美語補習班，依直線距離分為四級。每筆均含立案或招牌名稱、地址、聯絡電話與官方網站（若有登錄）。</p>

  <dl class="origin">
    <div><dt>圓心</dt><dd>桃園市楊梅區永平路</dd></div>
    <div><dt>座標</dt><dd class="mono">24.920261, 121.178141</dd></div>
    <div><dt>半徑</dt><dd>20 km（直線距離）</dd></div>
    <div><dt>筆數</dt><dd>__TOTAL__ 家</dd></div>
    <div><dt>行政區</dt><dd>__NDIST__ 個</dd></div>
  </dl>

  <p class="note"><b>覆蓋率說明：</b>Places API 每次呼叫最多回傳 20 筆，掃描用的 85 個網格中有 36 格已達上限，代表中壢、桃園、八德等密集區域仍有遺漏；楊梅市區本身有 7 格達上限。這份名單是可靠的第一輪普查，不是完整戶籍。名稱不含「美語／英語／英文／語文」等字樣的純升學文理班未納入。</p>

  <ul class="bands" id="bands"></ul>

  <div class="controls">
    <div class="field">
      <label for="q">搜尋</label>
      <input type="search" id="q" placeholder="名稱、地址或路名…" autocomplete="off">
    </div>
    <div class="field">
      <label for="dist">行政區</label>
      <select id="dist"><option value="">全部</option>__DISTOPTS__</select>
    </div>
    <div class="field">
      <label for="sort">排序</label>
      <select id="sort">
        <option value="d">距離（近→遠）</option>
        <option value="r">評分（高→低）</option>
        <option value="c">評論數（多→少）</option>
      </select>
    </div>
    <label class="chk"><input type="checkbox" id="onlyweb">只看有官網</label>
    <label class="chk"><input type="checkbox" id="onlytel">只看有電話</label>
    <span class="count" id="count"></span>
  </div>

  <div class="tablewrap">
    <table>
      <thead><tr>
        <th class="num">距離</th><th>名稱</th><th>地址</th>
        <th>電話</th><th>官網</th><th>評分</th>
      </tr></thead>
      <tbody id="tb"></tbody>
    </table>
  </div>

  <footer>
    資料來源為 Google Maps Places API (New) <code>places:searchNearby</code>，以六角網格覆蓋 20 公里圓域、每格半徑 2.8 公里，類型限定 <code>school</code> 與 <code>child_care_agency</code>，並排除主類型為公立中小學與大學者。距離以 haversine 公式計算圓心到各點的直線距離，非行車距離。評分與評論數為擷取當下的 Google 使用者評價。撥打前建議先確認營業狀態——補習班異動頻繁。
  </footer>
</div>

<script>
const BANDS=["0–5 km","5–10 km","10–15 km","15–20 km"];
const BC=["var(--b1)","var(--b2)","var(--b3)","var(--b4)"];
const COUNTS=__COUNTS__;
const DATA=__DATA__;
const state={band:null,q:"",dist:"",web:false,tel:false,sort:"d"};

const bandsEl=document.getElementById("bands");
const mk=(i,label,n)=>{
  const li=document.createElement("li");
  const b=document.createElement("button");
  b.className="band-btn";b.type="button";
  b.style.setProperty("--bc", i===null?"var(--accent)":BC[i]);
  b.setAttribute("aria-pressed", String(state.band===i));
  b.innerHTML='<span class="k">'+label+'</span><span class="v">'+n+'<small>家</small></span>';
  b.addEventListener("click",()=>{state.band = state.band===i ? null : i; render();});
  li.appendChild(b);bandsEl.appendChild(li);
  return b;
};
mk(null,"全部",DATA.length);
BANDS.forEach((lb,i)=>mk(i,lb,COUNTS[i]));

const tb=document.getElementById("tb"), countEl=document.getElementById("count");
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const host=u=>{try{return new URL(u).hostname.replace(/^www\\./,"")}catch(e){return "連結"}};

function render(){
  [...bandsEl.querySelectorAll(".band-btn")].forEach((b,idx)=>
    b.setAttribute("aria-pressed", String(state.band === (idx===0?null:idx-1))));
  const q=state.q.trim().toLowerCase();
  let rows=DATA.filter(r=>
    (state.band===null||r.b===state.band) &&
    (!state.dist||r.g===state.dist) &&
    (!state.web||r.w) && (!state.tel||r.p) &&
    (!q||(r.n+" "+r.a).toLowerCase().includes(q)));
  if(state.sort==="d") rows.sort((a,b)=>a.d-b.d);
  if(state.sort==="r") rows.sort((a,b)=>(b.r??-1)-(a.r??-1)||(b.c??0)-(a.c??0));
  if(state.sort==="c") rows.sort((a,b)=>(b.c??0)-(a.c??0));

  countEl.textContent=rows.length+" / "+DATA.length+" 家";
  if(!rows.length){tb.innerHTML='<tr><td colspan="6" class="empty">沒有符合條件的補習班。放寬篩選條件再試一次。</td></tr>';return;}

  let html="",last=null;
  const grouped = state.sort==="d";
  for(const r of rows){
    if(grouped && r.b!==last){
      last=r.b;
      html+='<tr class="grouphead" style="--bc:'+BC[r.b]+'"><td colspan="6">'
          +'<span><i></i>'+BANDS[r.b]+'　'+rows.filter(x=>x.b===r.b).length+' 家</span></td></tr>';
    }
    html+='<tr>'
      +'<td class="dist" style="--bc:'+BC[r.b]+'">'+r.d.toFixed(2)+'<small>km</small></td>'
      +'<td><span class="nm">'+esc(r.n)+'</span>'
        +(r.t?'<span class="tag">'+esc(r.t)+'</span>':'')
        +(r.x?'<span class="tag closed">已歇業／暫停</span>':'')+'</td>'
      +'<td class="addr">'+esc(r.a)+'</td>'
      +'<td class="tel">'+(r.p?'<a href="tel:'+esc(r.p.replace(/\\s/g,""))+'">'+esc(r.p)+'</a>':'<span class="dash">—</span>')+'</td>'
      +'<td class="web">'+(r.w?'<a href="'+esc(r.w)+'" target="_blank" rel="noopener">'+esc(host(r.w))+'</a>':'<span class="dash">—</span>')+'</td>'
      +'<td class="rate">'+(r.r?'<b>'+r.r.toFixed(1)+'</b> <small>('+(r.c??0)+')</small>':'<span class="dash">—</span>')+'</td>'
      +'</tr>';
  }
  tb.innerHTML=html;
}
document.getElementById("q").addEventListener("input",e=>{state.q=e.target.value;render()});
document.getElementById("dist").addEventListener("change",e=>{state.dist=e.target.value;render()});
document.getElementById("sort").addEventListener("change",e=>{state.sort=e.target.value;render()});
document.getElementById("onlyweb").addEventListener("change",e=>{state.web=e.target.checked;render()});
document.getElementById("onlytel").addEventListener("change",e=>{state.tel=e.target.checked;render()});
render();
</script>
"""

opts = "".join(f'<option value="{d}">{d}（{dist_cnt[d]}）</option>' for d in districts)
HTML = (HTML
        .replace("__TOTAL__", str(len(rows)))
        .replace("__NDIST__", str(len(districts)))
        .replace("__DISTOPTS__", opts)
        .replace("__COUNTS__", json.dumps([cnt[b] for b in BANDS]))
        .replace("__DATA__", json.dumps(data, ensure_ascii=False)))

open(f"{SP}/yangmei-english-schools.html", "w").write(HTML)
print("wrote", len(HTML), "bytes;", len(rows), "rows;", len(districts), "districts")
