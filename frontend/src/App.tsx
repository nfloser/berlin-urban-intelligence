import {useEffect,useState} from 'react';
import {request,type Health,type Observation} from './api';
import {CityMap} from './Map';
interface Source {id:string;provider:string;dataset:string;reference_url:string;licence:string|null}
interface SourceStatus {source_id:string;availability:string;freshness:string;error_code:string|null}
export default function App(){
 const [health,setHealth]=useState<Record<string,Health>>({});
 const [observations,setObservations]=useState<Observation[]>([]);
 const [sources,setSources]=useState<Source[]>([]);
 const [statuses,setStatuses]=useState<SourceStatus[]>([]);
 const [error,setError]=useState(''); const [loading,setLoading]=useState(true);
 const [filter,setFilter]=useState(''); const [delta,setDelta]=useState(3);
 const [result,setResult]=useState<unknown>(null);const [busy,setBusy]=useState(false);
 const [workflow,setWorkflow]=useState('urban_snapshot');
 async function refresh(){setLoading(true);setError('');try{
  const [h,o,s,t]=await Promise.all([request<Record<string,Health>>('agents/health'),request<Observation[]>('observations'),request<Source[]>('sources'),request<SourceStatus[]>('source-status')]);
  setHealth(h);setObservations(o);setSources(s);setStatuses(t);
 }catch(e){setError(e instanceof Error?e.message:'Could not load state.');}finally{setLoading(false);}}
 useEffect(()=>{void refresh();},[]);
 async function run(kind:'heat'|'workflow'){setBusy(true);setError('');try{setResult(await request(kind==='heat'?'assessments':'orchestrate',kind==='heat'?{scenario:{name:`Heat ${delta>=0?'+':''}${delta} °C`,kinds:['extreme_heat'],temperature_delta_c:delta}}:{workflow}));}catch(e){setError(e instanceof Error?e.message:'Analysis failed.');}finally{setBusy(false);}}
 return <main><header><a className="brand" href="/">BUI<span>BERLIN URBAN INTELLIGENCE</span></a><span className="research">RESEARCH PLATFORM · 0.1</span></header>
 <section className="intro"><div className="eyebrow">ONE CITY. CONNECTED DOMAINS.</div><h1>Understand the city.<br/><em>Keep the evidence visible.</em></h1><p>Environmental conditions, mobility and infrastructure — connected through traceable data and explicit scenarios.</p><button onClick={()=>void refresh()} disabled={loading}>{loading?'Loading state…':'Refresh view'}</button></section>
 {error&&<p role="alert" className="error">{error}</p>}
 <section className="health-grid" aria-label="Domain health">{Object.entries(health).map(([id,h])=><article key={id}><div className="eyebrow">{id.replaceAll('_',' ')}</div><strong className={h.status}>{h.status}</strong><small>Freshness: {h.freshness}</small><p>{h.detail}</p></article>)}</section>
 <CityMap/>
 <section className="panel"><div className="section-title"><div><div className="eyebrow">CANONICAL STATE</div><h2>Latest observations</h2></div><input aria-label="Filter observations" placeholder="Filter phenomenon…" value={filter} onChange={e=>setFilter(e.target.value)}/></div>
 {!loading&&observations.length===0?<p className="empty">No observations available. Acquire real source data to populate this view.</p>:<div className="table-scroll"><table><thead><tr><th>Phenomenon</th><th>Value</th><th>Time (UTC)</th><th>State / quality</th><th>Provenance</th></tr></thead><tbody>{observations.filter(o=>o.phenomenon.includes(filter)).map(o=><tr key={o.id}><td>{o.phenomenon}</td><td>{String(o.value)} {o.unit}</td><td>{new Date(o.observed_at).toISOString().replace('T',' ').slice(0,19)}</td><td>{o.state} / {o.quality}</td><td><a href={o.provenance.source_url} target="_blank" rel="noreferrer">{o.provenance.provider}</a><small>{o.provenance.quality_note}</small></td></tr>)}</tbody></table></div>}</section>
 <section className="panel"><div className="eyebrow">EXPLICIT WHAT-IF ANALYSIS</div><h2>Scenario laboratory</h2><p>Temperature perturbations use the latest measured baseline. Results remain hypothetical; missing inputs remain unavailable.</p><div className="controls"><label>Temperature change (°C)<input type="number" min={-20} max={20} step={0.5} value={delta} onChange={e=>setDelta(Number(e.target.value))}/></label><button disabled={busy||!Number.isFinite(delta)||Math.abs(delta)>20} onClick={()=>void run('heat')}>Assess heat scenario</button><label>Workflow<select value={workflow} onChange={e=>setWorkflow(e.target.value)}>{['urban_snapshot','heat_energy','mobility_exposure','mobility_resilience','heat_mobility_resilience'].map(w=><option key={w} value={w}>{w.replaceAll('_',' ')}</option>)}</select></label><button disabled={busy} onClick={()=>void run('workflow')}>Check workflow</button></div>{result!==null&&<pre aria-label="Analysis result">{JSON.stringify(result,null,2)}</pre>}</section>
 <section className="panel"><div className="eyebrow">DATA LINEAGE</div><h2>Sources & availability</h2><div className="sources">{sources.map(s=>{const t=statuses.find(t=>t.source_id===s.id);return <article key={s.id}><h3><a href={s.reference_url} target="_blank" rel="noreferrer">{s.dataset}</a></h3><p>{s.provider}</p><small>{s.licence||'Licence not specified'}</small><p>{t?.availability||'unknown'} · freshness {t?.freshness||'unknown'}</p>{t?.error_code&&<small>{t.error_code}</small>}</article>})}</div></section>
 <footer>Independent research platform. No composite urban score. <a href="/api/v1/graph">Download semantic state (Turtle)</a></footer></main>;
}
