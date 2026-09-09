import json, os, collections, statistics as st

SP = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(f"{SP}/english-schools-scale.json"))

BANDS = ["0–5 km", "5–10 km", "10–15 km", "15–20 km"]
cnt = collections.Counter(r["band"] for r in rows)
dist_cnt = collections.Counter(f'{r["city"]}{r["district"]}' for r in rows)
districts = [d for d, _ in dist_cnt.most_common()]

n_reg = sum(1 for r in rows if r["reg_name"])
n_scale = sum(1 for r in rows if r["classrooms"])
areas = [r["building_m2"] for r in rows if r["building_m2"]]
crooms = [r["classrooms"] for r in rows if r["classrooms"]]
teach = [r["n_teachers"] for r in rows if r["n_teachers"]]

data = [{
    "b": BANDS.index(r["band"]),
    "d": r["distance_km"],
    "n": r["name"],
    "rn": r["reg_name"],
    "a": r["address"],
    "p": r["phone"],
    "w": r["website"],
    "r": r["rating"] if r["rating"] != "" else None,
    "c": r["reviews"] if r["reviews"] != "" else None,
    "g": f'{r["city"]}{r["district"]}',
    "sz": r["size_tier"],
    "rm": r["classrooms"] or None,
    "m2": r["building_m2"] or None,
    "te": r["n_teachers"] or None,
    "cl": r["n_classes"] or None,
    "cap": r["approved_capacity"] or None,
    "cen": r["approved_capacity_en"] or None,
    "lic": (r["licensed_on"] or "")[:4],
    "x": r["status"] != "OPERATIONAL",
} for r in rows]

HTML = r"""<title>楊梅英語補習班名錄</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700&family=Noto+Sans+TC:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --paper:#f2f4f1; --surface:#ffffff; --surface-2:#e9ece7; --raised:#fbfcfa;
  --ink:#15201e; --ink-2:#55625d; --ink-3:#7d8a84;
  --line:#d7dcd4; --line-strong:#bcc4ba;
  --accent:#0b5c50; --accent-soft:#e2ede8;
  --b1:#0b5c50; --b2:#35806c; --b3:#6f9f88; --b4:#a6bdaf;
  --lg:#8a4b12; --lg-bg:#f7ecdd; --md:#1f5f7a; --md-bg:#e2eef4; --sm:#5a655f; --sm-bg:#e9ece7;
  --warn:#8a5a12; --warn-soft:#f6ecd8; --focus:#0b5c50;
  --serif:"Noto Serif TC",Georgia,"Songti TC",serif;
  --sans:"Noto Sans TC",-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Menlo,monospace;
}
:root:not([data-theme="light"]){@media (prefers-color-scheme:dark){
  --paper:#111614; --surface:#191f1d; --surface-2:#222a27; --raised:#1e2523;
  --ink:#e7ece9; --ink-2:#9daaa4; --ink-3:#7a8781;
  --line:#2c3733; --line-strong:#3d4a45;
  --accent:#63c4ae; --accent-soft:#1b322c;
  --b1:#79d4bd; --b2:#55ae97; --b3:#3f8874; --b4:#4c6b60;
  --lg:#e0a765; --lg-bg:#2e2417; --md:#7cc0dd; --md-bg:#172a33; --sm:#93a09a; --sm-bg:#242c29;
  --warn:#d9ad63; --warn-soft:#2b2417; --focus:#63c4ae;
}}
:root[data-theme="dark"]{
  --paper:#111614; --surface:#191f1d; --surface-2:#222a27; --raised:#1e2523;
  --ink:#e7ece9; --ink-2:#9daaa4; --ink-3:#7a8781;
  --line:#2c3733; --line-strong:#3d4a45;
  --accent:#63c4ae; --accent-soft:#1b322c;
  --b1:#79d4bd; --b2:#55ae97; --b3:#3f8874; --b4:#4c6b60;
  --lg:#e0a765; --lg-bg:#2e2417; --md:#7cc0dd; --md-bg:#172a33; --sm:#93a09a; --sm-bg:#242c29;
  --warn:#d9ad63; --warn-soft:#2b2417; --focus:#63c4ae;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1320px;margin:0 auto;padding:32px 20px 80px}
a{color:var(--accent)}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{
  outline:2px solid var(--focus);outline-offset:2px;border-radius:3px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--ink-3);margin:0 0 10px}
h1{font-family:var(--serif);font-weight:700;font-size:clamp(28px,4.4vw,42px);
  line-height:1.15;margin:0;text-wrap:balance}
.lede{color:var(--ink-2);max-width:62ch;margin:12px 0 0}
.origin{display:flex;flex-wrap:wrap;gap:10px 26px;margin-top:18px;
  padding-top:16px;border-top:1px solid var(--line)}
.origin div{display:flex;flex-direction:column;gap:2px}
.origin dt{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--ink-3)}
.origin dd{margin:0;font-size:14px;font-variant-numeric:tabular-nums}
.origin dd.mono{font-family:var(--mono);font-size:13px}
.note{margin:22px 0 0;padding:12px 14px;background:var(--warn-soft);
  border-left:3px solid var(--warn);border-radius:0 4px 4px 0;
  font-size:13.5px;color:var(--ink-2);line-height:1.6}
.note b{color:var(--ink);font-weight:500}
.note+.note{margin-top:10px}
.bands{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:10px;margin:28px 0 0;padding:0;list-style:none}
.band-btn{display:flex;flex-direction:column;align-items:flex-start;gap:4px;width:100%;
  padding:12px 14px 12px 13px;background:var(--surface);border:1px solid var(--line);
  border-left:4px solid var(--bc,var(--line-strong));border-radius:4px;cursor:pointer;
  font-family:inherit;text-align:left;color:var(--ink);transition:border-color .12s,background .12s}
.band-btn:hover{background:var(--raised);border-color:var(--line-strong)}
.band-btn[aria-pressed="true"]{background:var(--accent-soft);border-color:var(--accent)}
.band-btn .k{font-family:var(--mono);font-size:12px;letter-spacing:.06em;color:var(--ink-2)}
.band-btn .v{font-family:var(--serif);font-size:26px;font-weight:700;line-height:1;
  font-variant-numeric:tabular-nums}
.band-btn .v small{font-family:var(--sans);font-size:12px;font-weight:400;
  color:var(--ink-3);margin-left:4px}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:20px 0 0;
  padding:14px;background:var(--surface-2);border-radius:4px}
.field{display:flex;align-items:center;gap:7px}
.field label{font-family:var(--mono);font-size:10.5px;letter-spacing:.11em;
  text-transform:uppercase;color:var(--ink-3);white-space:nowrap}
input[type=search],select{font-family:inherit;font-size:14px;color:var(--ink);
  background:var(--surface);border:1px solid var(--line-strong);border-radius:4px;padding:7px 9px}
input[type=search]{min-width:190px}
.chk{display:flex;align-items:center;gap:6px;font-size:13.5px;color:var(--ink-2);
  cursor:pointer;user-select:none}
.chk input{accent-color:var(--accent);width:15px;height:15px}
.count{margin-left:auto;font-family:var(--mono);font-size:12.5px;color:var(--ink-2);
  font-variant-numeric:tabular-nums}
.tablewrap{margin-top:18px;overflow-x:auto;border:1px solid var(--line);
  border-radius:4px;background:var(--surface)}
table{width:100%;border-collapse:collapse;font-size:14px}
thead th{position:sticky;top:0;z-index:2;background:var(--surface-2);
  font-family:var(--mono);font-size:10.5px;letter-spacing:.11em;text-transform:uppercase;
  color:var(--ink-2);font-weight:500;text-align:left;padding:10px 12px;
  border-bottom:1px solid var(--line-strong);white-space:nowrap}
thead th.num{text-align:right}
tbody tr{border-bottom:1px solid var(--line)}
tbody tr:last-child{border-bottom:0}
tbody tr:hover{background:var(--raised)}
td{padding:11px 12px;vertical-align:top}
tr.grouphead td{background:var(--surface-2);padding:8px 12px;
  border-top:1px solid var(--line-strong);border-bottom:1px solid var(--line-strong)}
tr.grouphead span{font-family:var(--mono);font-size:11px;letter-spacing:.13em;
  text-transform:uppercase;color:var(--ink-2);display:inline-flex;align-items:center;gap:8px}
tr.grouphead i{width:22px;height:3px;border-radius:2px;background:var(--bc);display:inline-block}
td.dist{font-family:var(--mono);font-variant-numeric:tabular-nums;text-align:right;
  white-space:nowrap;font-weight:500;border-left:4px solid var(--bc);padding-left:10px}
td.dist small{display:block;font-size:10.5px;color:var(--ink-3);font-weight:400}
.nm{font-weight:500;line-height:1.4;display:block;max-width:40ch}
.reg{display:block;margin-top:3px;font-size:12px;color:var(--ink-3);max-width:40ch;line-height:1.4}
.reg::before{content:"立案　";font-family:var(--mono);font-size:10px;letter-spacing:.08em}
.pill{display:inline-block;font-family:var(--mono);font-size:10.5px;font-weight:500;
  letter-spacing:.06em;padding:2px 8px;border-radius:3px;white-space:nowrap}
.pill.大型{color:var(--lg);background:var(--lg-bg)}
.pill.中型{color:var(--md);background:var(--md-bg)}
.pill.小型{color:var(--sm);background:var(--sm-bg)}
.tag{display:inline-block;margin-top:4px;font-family:var(--mono);font-size:10px;
  letter-spacing:.08em;color:var(--warn);border:1px solid var(--warn);
  border-radius:99px;padding:1px 7px}
td.addr{color:var(--ink-2);max-width:26ch;font-size:13.5px}
td.tel a,td.web a{text-decoration:none;border-bottom:1px solid var(--accent-soft)}
td.tel a{font-family:var(--mono);font-size:13.5px;white-space:nowrap}
td.web a{font-size:13px}
td.tel a:hover,td.web a:hover{border-bottom-color:var(--accent)}
.dash{color:var(--ink-3)}
td.sc{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:12.5px;
  white-space:nowrap;color:var(--ink-2);line-height:1.7}
td.sc b{color:var(--ink);font-weight:500}
td.rate{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap;font-size:13px}
td.rate small{color:var(--ink-3)}
.empty{padding:48px 16px;text-align:center;color:var(--ink-2)}
footer{margin-top:34px;padding-top:18px;border-top:1px solid var(--line);
  font-size:12.5px;color:var(--ink-3);line-height:1.75;max-width:80ch}
footer code{font-family:var(--mono);font-size:11.5px;background:var(--surface-2);
  padding:1px 5px;border-radius:3px;color:var(--ink-2)}
footer p{margin:0 0 10px}
@media (max-width:900px){
  .wrap{padding:22px 14px 60px}
  thead{display:none}
  table,tbody,tr,td{display:block;width:100%}
  tbody tr{padding:12px 12px 12px 0}
  td{padding:2px 12px;border:0}
  td.dist{text-align:left;border-left:4px solid var(--bc);padding:2px 12px 2px 10px}
  td.dist small{display:inline;margin-left:6px}
  tr.grouphead td{padding:8px 12px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<div class="wrap">
  <p class="eyebrow">Google Maps Places API ＋ 教育部短期補習班立案資料 · 2026-09-09</p>
  <h1>楊梅英語補習班名錄</h1>
  <p class="lede">以桃園市楊梅區永平路為圓心，半徑 20 公里內的英文／美語補習班，依直線距離分為四級。每筆含名稱、地址、電話、官網，並盡可能對上教育部立案資料，補上教室數、班舍面積、核准班級數與登記師資人數。</p>

  <dl class="origin">
    <div><dt>圓心</dt><dd>桃園市楊梅區永平路</dd></div>
    <div><dt>座標</dt><dd class="mono">24.920261, 121.178141</dd></div>
    <div><dt>半徑</dt><dd>20 km 直線距離</dd></div>
    <div><dt>筆數</dt><dd>__TOTAL__ 家</dd></div>
    <div><dt>對上立案</dt><dd>__NREG__ 家</dd></div>
    <div><dt>教室數中位數</dt><dd>__MEDROOM__ 間</dd></div>
    <div><dt>班舍面積中位數</dt><dd>__MEDAREA__ ㎡</dd></div>
    <div><dt>登記師資中位數</dt><dd>__MEDTEACH__ 人</dd></div>
  </dl>

  <p class="note"><b>沒有「實際學生人數」。</b>各補習班的在學人數不屬於公開資訊，Google Maps 與教育部立案系統都沒有這個欄位。表中的規模欄位是立案登記的<b>硬體與法定上限</b>：教室數、班舍總面積、核准班級數、每班核准人數、登記在案的教學人員數。「核定容量」是各核准科目的班級數 × 每班人數加總，同一批學生修多科會重複計算，僅能當上限參考，不是招生人數。</p>

  <p class="note"><b>覆蓋率：</b>Google Places 單次呼叫最多回 20 筆，掃描的 85 個網格中有 36 格觸頂，中壢、桃園、八德等密集區必有遺漏。__TOTAL__ 家中 __NREG__ 家對上立案資料（__PCT__%），其餘多為登記在「兒童課後照顧服務中心」名下、或 Google 地址與立案地址不一致者。順帶一提：同樣這 20 個行政區的立案外語類補習班共有 1,064 家，遠多於 Google 能看到的數量。</p>

  <ul class="bands" id="bands"></ul>

  <div class="controls">
    <div class="field"><label for="q">搜尋</label>
      <input type="search" id="q" placeholder="名稱、地址或路名…" autocomplete="off"></div>
    <div class="field"><label for="dist">行政區</label>
      <select id="dist"><option value="">全部</option>__DISTOPTS__</select></div>
    <div class="field"><label for="size">規模</label>
      <select id="size"><option value="">全部</option><option>大型</option><option>中型</option><option>小型</option></select></div>
    <div class="field"><label for="sort">排序</label>
      <select id="sort">
        <option value="d">距離（近→遠）</option>
        <option value="m2">班舍面積（大→小）</option>
        <option value="rm">教室數（多→少）</option>
        <option value="te">師資數（多→少）</option>
        <option value="r">評分（高→低）</option>
      </select></div>
    <label class="chk"><input type="checkbox" id="onlyreg">只看有立案資料</label>
    <span class="count" id="count"></span>
  </div>

  <div class="tablewrap">
    <table>
      <thead><tr>
        <th class="num">距離</th><th>名稱</th><th>地址</th><th>電話</th><th>官網</th>
        <th>規模</th><th>教室／面積／師資</th><th>評分</th>
      </tr></thead>
      <tbody id="tb"></tbody>
    </table>
  </div>

  <footer>
    <p><b>名單來源</b>：Google Maps Places API (New) <code>places:searchNearby</code>，六角網格覆蓋 20 公里圓域、每格半徑 2.8 公里，類型限定 <code>school</code> 與 <code>child_care_agency</code>，排除主類型為公立中小學與大學者。距離為 haversine 直線距離，非行車距離。</p>
    <p><b>規模來源</b>：教育部「直轄市及各縣市短期補習班資訊管理系統」立案資料。以地址（行政區＋路名＋巷弄號）比對為主、電話與名稱為輔。規模分級依實體條件認定：班舍總面積 ≥ 400 ㎡ 或教室 ≥ 8 間為大型，≥ 200 ㎡ 或 ≥ 5 間為中型，其餘為小型。</p>
    <p>立案名稱與招牌名稱常常不同——加盟品牌多以在地登記名稱立案，表中兩者並列。撥打前建議確認營業狀態，補習班異動頻繁。</p>
  </footer>
</div>

<script>
const BANDS=["0–5 km","5–10 km","10–15 km","15–20 km"];
const BC=["var(--b1)","var(--b2)","var(--b3)","var(--b4)"];
const COUNTS=__COUNTS__;
const DATA=__DATA__;
const state={band:null,q:"",dist:"",size:"",reg:false,sort:"d"};

const bandsEl=document.getElementById("bands");
function mk(i,label,n){
  const li=document.createElement("li");
  const b=document.createElement("button");
  b.className="band-btn";b.type="button";
  b.style.setProperty("--bc", i===null?"var(--accent)":BC[i]);
  b.setAttribute("aria-pressed", String(state.band===i));
  b.innerHTML='<span class="k">'+label+'</span><span class="v">'+n+'<small>家</small></span>';
  b.addEventListener("click",()=>{state.band = state.band===i ? null : i; render();});
  li.appendChild(b);bandsEl.appendChild(li);
}
mk(null,"全部",DATA.length);
BANDS.forEach((lb,i)=>mk(i,lb,COUNTS[i]));

const tb=document.getElementById("tb"), countEl=document.getElementById("count");
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const host=u=>{try{return new URL(u).hostname.replace(/^www\./,"")}catch(e){return "連結"}};

function render(){
  [...bandsEl.querySelectorAll(".band-btn")].forEach((b,idx)=>
    b.setAttribute("aria-pressed", String(state.band === (idx===0?null:idx-1))));
  const q=state.q.trim().toLowerCase();
  let rows=DATA.filter(r=>
    (state.band===null||r.b===state.band) &&
    (!state.dist||r.g===state.dist) &&
    (!state.size||r.sz===state.size) &&
    (!state.reg||r.rn) &&
    (!q||(r.n+" "+r.rn+" "+r.a).toLowerCase().includes(q)));
  const S=state.sort;
  if(S==="d") rows.sort((a,b)=>a.d-b.d);
  else if(S==="r") rows.sort((a,b)=>(b.r??-1)-(a.r??-1)||(b.c??0)-(a.c??0));
  else rows.sort((a,b)=>(b[S]??-1)-(a[S]??-1));

  countEl.textContent=rows.length+" / "+DATA.length+" 家";
  if(!rows.length){tb.innerHTML='<tr><td colspan="8" class="empty">沒有符合條件的補習班。放寬篩選條件再試一次。</td></tr>';return;}

  let html="",last=null;
  for(const r of rows){
    if(S==="d" && r.b!==last){
      last=r.b;
      html+='<tr class="grouphead" style="--bc:'+BC[r.b]+'"><td colspan="8">'
          +'<span><i></i>'+BANDS[r.b]+'　'+rows.filter(x=>x.b===r.b).length+' 家</span></td></tr>';
    }
    const sc=[];
    if(r.rm) sc.push('<b>'+r.rm+'</b> 室');
    if(r.m2) sc.push('<b>'+Math.round(r.m2)+'</b> ㎡');
    if(r.te) sc.push('<b>'+r.te+'</b> 師');
    const sc2=[];
    if(r.cl) sc2.push(r.cl+' 班');
    if(r.cen) sc2.push('英文科核定 '+r.cen+' 人');
    if(r.lic) sc2.push(r.lic+' 立案');
    html+='<tr>'
      +'<td class="dist" style="--bc:'+BC[r.b]+'">'+r.d.toFixed(2)+'<small>km</small></td>'
      +'<td><span class="nm">'+esc(r.n)+'</span>'
        +(r.rn&&r.rn!==r.n?'<span class="reg">'+esc(r.rn)+'</span>':'')
        +(r.x?'<span class="tag">已歇業／暫停</span>':'')+'</td>'
      +'<td class="addr">'+esc(r.a)+'</td>'
      +'<td class="tel">'+(r.p?'<a href="tel:'+esc(r.p.replace(/\s/g,""))+'">'+esc(r.p)+'</a>':'<span class="dash">—</span>')+'</td>'
      +'<td class="web">'+(r.w?'<a href="'+esc(r.w)+'" target="_blank" rel="noopener">'+esc(host(r.w))+'</a>':'<span class="dash">—</span>')+'</td>'
      +'<td>'+(r.sz?'<span class="pill '+r.sz+'">'+r.sz+'</span>':'<span class="dash">—</span>')+'</td>'
      +'<td class="sc">'+(sc.length?sc.join('　'):'<span class="dash">—</span>')
        +(sc2.length?'<br><span style="color:var(--ink-3)">'+sc2.join('　')+'</span>':'')+'</td>'
      +'<td class="rate">'+(r.r?'<b>'+r.r.toFixed(1)+'</b> <small>('+(r.c??0)+')</small>':'<span class="dash">—</span>')+'</td>'
      +'</tr>';
  }
  tb.innerHTML=html;
}
document.getElementById("q").addEventListener("input",e=>{state.q=e.target.value;render()});
document.getElementById("dist").addEventListener("change",e=>{state.dist=e.target.value;render()});
document.getElementById("size").addEventListener("change",e=>{state.size=e.target.value;render()});
document.getElementById("sort").addEventListener("change",e=>{state.sort=e.target.value;render()});
document.getElementById("onlyreg").addEventListener("change",e=>{state.reg=e.target.checked;render()});
render();
</script>
"""

opts = "".join(f'<option value="{d}">{d}（{dist_cnt[d]}）</option>' for d in districts)
HTML = (HTML
        .replace("__TOTAL__", str(len(rows)))
        .replace("__NREG__", str(n_reg))
        .replace("__PCT__", str(round(n_reg * 100 / len(rows))))
        .replace("__MEDROOM__", f"{st.median(crooms):.0f}")
        .replace("__MEDAREA__", f"{st.median(areas):.0f}")
        .replace("__MEDTEACH__", f"{st.median(teach):.0f}")
        .replace("__DISTOPTS__", opts)
        .replace("__COUNTS__", json.dumps([cnt[b] for b in BANDS]))
        .replace("__DATA__", json.dumps(data, ensure_ascii=False)))

open(f"{SP}/yangmei-english-schools.html", "w").write(HTML)
print(f"wrote {len(HTML)} bytes; {len(rows)} rows; {n_reg} with registry; {n_scale} with scale")
