"use strict";

const main = document.getElementById("content");
const stateNames = {
  duplicate_rules: "Descartado · reglas duplicadas", walk_forward_completed: "Walk-forward guardado",
  run_completed: "Investigación completada", completed: "Completado", observation_recorded: "Respuesta registrada",
  pending_semantic_review: "Pendiente de revisión", needs_clarification: "Requiere aclaración",
  incomplete: "Registro incompleto", unreadable: "Archivo no legible", registered_inactive: "Registro inactivo",
  execution_completed: "Cálculo guardado", not_met: "Criterio no cumplido", met: "Criterio cumplido",
  inconclusive: "Inconcluso", not_supported_in_sample: "Hipótesis no respaldada en este histórico",
  supported_in_sample: "Hipótesis respaldada en este histórico"
};
Object.assign(stateNames,{blocked_by_translation:"Bloqueado por traducción pendiente",campaign_memory_saved:"Memoria guardada",evaluation_completed:"Evaluación guardada",frozen_not_evaluated:"Registro previo a la evaluación",memory_only:"Memoria histórica",offline_preview_only:"Vista previa sin ejecutar",pending_tool_mapping:"Pendiente de reglas precisas",proposal_completed:"Propuesta guardada",reserved_not_submitted:"Reserva sin envío registrado",session_prepared:"Sesión preparada",structured_session_prepared:"Sesión estructurada preparada"});
const names = {inicio:"Inicio", experimentos:"Experimentos", resultados:"Resultados", memoria:"Memoria del agente", consumo:"Consumo"};
let navigation = 0;
let activePage = "inicio";

function el(tag, text, cls) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = String(text);
  if (cls) node.className = cls;
  return node;
}
function add(parent, ...children) { children.filter(Boolean).forEach(child => parent.append(child)); return parent; }
function link(text, href, cls) { const node=el("a",text,cls); node.href=href; return node; }
function button(text, action, cls) { const node=el("button",text,cls);node.type="button";node.addEventListener("click",action);return node; }
function json(value) { return typeof value === "string" ? value : JSON.stringify(value, null, 2); }
function code(value) { return el("pre",value === undefined || value === null ? "No disponible en este registro." : json(value)); }
function fmt(value, digits=4) {
  if (value === undefined || value === null || value === "" || typeof value === "boolean" || !Number.isFinite(Number(value))) return "No disponible";
  return new Intl.NumberFormat("es-ES",{maximumFractionDigits:digits}).format(Number(value));
}
function at(value) { if (!value) return "Fecha no registrada"; const date=new Date(value);return Number.isNaN(date.getTime())?String(value):date.toLocaleString("es-ES"); }
function localDay(value) { if(!value)return "";const date=new Date(value);return Number.isNaN(date.getTime())?"":date.getFullYear()+"-"+String(date.getMonth()+1).padStart(2,"0")+"-"+String(date.getDate()).padStart(2,"0"); }
function badge(text, cls="") { return el("span",stateNames[text]||text,"badge "+cls); }
function notice(text, cls="") { return el("div",text,"notice "+cls); }
function section(title) { return add(el("section",null,"section"),el("h2",title)); }
function title(label, description) { add(main,el("p","TIRESIAS / LABORATORIO LOCAL","eyebrow"),el("h1",label),el("p",description,"intro")); }
function updated(value) { add(main,el("p","Consultado: "+at(value)+" · Las fechas de mercado se muestran en cada cuenta.","meta updated")); }
function disclosure(label, value) { const node=el("details");return add(node,el("summary",label),code(value)); }
function dl(items) { const node=el("dl"); for(const [label,value] of items) add(node,el("dt",label),el("dd",value ?? "No disponible"));return node; }
function source(file) {
  const node=el("li"); const anchor=link(file.path,"/sources/"+file.id);anchor.target="_blank";anchor.rel="noopener";
  add(node,anchor,el("small","Procedencia: "+file.source,"source-path"));
  if(file.expected_sha256) add(node,el("small","SHA-256 del inventario: "+file.expected_sha256,"source-path"));
  return node;
}
async function api(path) {
  const response=await fetch(path,{cache:"no-store"}); const value=await response.json();
  if(!response.ok) throw new Error(value.error||"No se pudo leer el registro.");
  return value;
}
function table(headers, rows) {
  const node=el("table"),head=el("thead"),tr=el("tr");headers.forEach(x=>add(tr,el("th",x)));add(head,tr);add(node,head);
  const body=el("tbody");rows.forEach(row=>{const tr=el("tr");row.forEach(cell=>add(tr,add(el("td"),cell instanceof Node?cell:el("span",cell))));add(body,tr);});
  return add(el("div",null,"table-wrap"),add(node,body));
}
function experimentCell(item) {
  return add(el("div"),link(item.title,"#"+activePage+"/"+item.id,"row-title"),el("span",item.kind,"meta"),el("div",item.path,"meta source-path"));
}
function experimentTable(items) {
  if(!items.length) return el("p","No hay registros que coincidan con estos filtros.","empty");
  return table(["EXPERIMENTO / FUENTE","PAR · ESTRATEGIA","FECHA REGISTRADA","ESTADO GUARDADO","PROCEDENCIA"],items.map(item=>[
    experimentCell(item),add(el("div"),el("div",item.pair||"No registrado"),el("small",item.strategy||"Ver ficha","meta")),
    at(item.date),badge(item.state,"warning"),badge(item.origin==="archive"?"Copia histórica":"Registro local",item.origin)
  ]));
}

async function home(token) {
  const data=await api("/api/home");if(token!==navigation)return;
  main.replaceChildren();title("Un espacio para investigar.","Explora qué se probó, revisa los resultados guardados y sigue su evidencia. Consultar el laboratorio no inicia investigaciones ni simulaciones.");
  const cards=el("div",null,"cards");
  [["Registros de experimentos",data.counts.experiments,"Incluye originales y copias históricas"],["Registros locales",data.counts.local,"Estado guardado, sin ejecución activa"],["Inventarios archivados",data.counts.archives,"Integridad comprobable desde las fichas"]].forEach(([label,num,caption])=>add(cards,add(el("div",null,"card"),el("div",label,"stat-label"),el("div",num,"stat-number"),el("div",caption,"stat-caption"))));
  add(main,cards,notice(data.limits));
  const grid=el("div",null,"grid"),recent=add(el("section",null,"card"),el("h2","Últimos registros")),list=el("ul",null,"list");
  data.recent.forEach(item=>add(list,add(el("li"),link(item.title,"#experimentos/"+item.id),el("small",(item.origin==="archive"?"Copia histórica":"Registro local")+" · "+(stateNames[item.state]||item.state)+" · "+at(item.date)))));
  add(recent,list);const guide=add(el("section",null,"card"),el("h2","De la idea a la evidencia"));
  add(guide,el("p","1. Encuentra una investigación por par, estrategia o fecha.","subtle"),el("p","2. Revisa sus controles, criterio y cuentas virtuales.","subtle"),el("p","3. Abre los archivos originales y su inventario.","subtle"),link("Explorar experimentos →","#experimentos","button primary"));add(main,add(grid,recent,guide));
  const reports=section("Informes del laboratorio"),reportList=el("ul",null,"list");data.reports.forEach(file=>add(reportList,source(file)));add(main,add(reports,disclosure("Cómo interpretar la verificación","La verificación comprueba integridad de archivos. No certifica rentabilidad, significado de una propuesta, autoría externa o vigencia de un permiso."),reportList));
  if(data.warnings.length)add(main,disclosure("Avisos de fuentes ("+data.warnings.length+")",data.warnings));updated(data.queried_at);
}

async function explorer(token, page) {
  const data=await api("/api/experiments");if(token!==navigation)return;
  main.replaceChildren();title(names[page],page==="memoria"?"Propuestas, revisiones, errores y descartes conservados. El contenido del modelo se muestra como texto original, separado de las conclusiones de Python.":page==="resultados"?"Cuentas virtuales y resultados históricos guardados. Abre una ficha para consultar las curvas y operaciones disponibles.":"Encuentra una investigación y revisa su hipótesis, controles, resultados y procedencia.");
  const form=el("form",null,"filters");const controls={};
  function field(label,key,options) {
    const wrap=el("label",label,"field"),node=el(options?"select":"input");node.name=key;node.setAttribute("aria-label",label);
    if(options){add(node,el("option","Todos"));options.forEach(value=>{const option=el("option",key==="state"?(stateNames[value]||value):key==="origin"?(value==="local"?"Registro local":"Copia histórica"):value);option.value=value;add(node,option);});}
    else node.type=key==="date"?"date":"search";
    if(options)node.firstChild.value="";controls[key]=node;add(form,add(wrap,node));
  }
  field("Par","pair",[...new Set(data.items.map(x=>x.pair).filter(Boolean))].sort());
  field("Estrategia","strategy");field("Fecha registrada","date");field("Estado guardado","state",[...new Set(data.items.map(x=>x.state))].sort());field("Procedencia","origin",["local","archive"]);field("Buscar","q");
  const submit=el("button","Filtrar","primary");submit.type="submit";add(form,submit,button("Limpiar",()=>{form.reset();render();}));
  const container=el("div"),counter=el("p",null,"meta");
  function render() {
    const items=data.items.filter(item=>{
      if(page==="resultados"&&!item.has_results)return false;
      return Object.entries(controls).every(([key,node])=>{
        const value=node.value.toLowerCase();if(!value)return true;
        if(key==="q")return json(item).toLowerCase().includes(value);
        if(key==="date")return localDay(item.date)===value;
        if(key==="strategy")return String(item.strategy||"").toLowerCase().includes(value);
        return String(item[key]||"").toLowerCase()===value;
      });
    });counter.textContent=items.length+(items.length===1?" registro":" registros")+" · Los originales y sus copias aparecen identificados por separado.";container.replaceChildren(experimentTable(items));
  }
  form.addEventListener("submit",event=>{event.preventDefault();render();});add(main,form,counter,container);
  if(data.warnings.length)add(main,disclosure("Avisos del catálogo",data.warnings));render();updated(data.queried_at);
}

async function detail(token,key) {
  const data=await api("/api/experiments/"+encodeURIComponent(key));if(token!==navigation)return;
  main.replaceChildren();add(main,add(el("div",null,"breadcrumbs"),link("← "+names[activePage],"#"+activePage)));
  title(data.title,(data.pair||"Par no registrado")+" · "+data.kind+" · "+(data.origin==="archive"?"Copia histórica archivada":"Registro local"));
  add(main,badge(data.state,"warning"),notice(data.integrity.label+(data.integrity.reason?". "+data.integrity.reason:"")+". Alcance: integridad de archivos; sin certificación semántica o de rentabilidad.",data.integrity.state==="unverifiable"||data.integrity.state==="changed"?"warn":""),el("p",data.recorded_state_notice,"meta"));
  data.warnings.forEach(message=>add(main,notice(message,"warn")));
  const grid=el("div",null,"grid"),hyp=add(el("section",null,"card"),el("h2","Qué se propuso"));
  add(hyp,el("h3","Hipótesis · texto registrado"),el("p",data.hypothesis||"No se guardó una hipótesis en este formato.","subtle"),el("h3","Criterio registrado"),code(data.criterion),disclosure("Propuesta y parámetros originales",data.proposal));
  if(data.rules)add(hyp,disclosure("Reglas declarativas registradas",data.rules));
  const controls=add(el("section",null,"card"),el("h2","Controles y periodo"));
  add(controls,dl([["Par",data.policy.pair],["Capital inicial",fmt(data.policy.initial_capital)],["Coste por ejecución",data.policy.cost_rate===undefined?null:"Tasa fraccionaria: "+data.policy.cost_rate],["Tamaño",data.policy.allocation_fraction===null?"Una unidad base":data.policy.allocation_fraction===undefined?null:"Fracción del efectivo: "+data.policy.allocation_fraction],["Periodo histórico",data.data.first_date&&data.data.last_date?data.data.first_date+" → "+data.data.last_date:"Por tramo, en cada cuenta"],["Fecha registrada",at(data.date)]]),disclosure("Controles y fuente completos",{policy:data.policy,data:data.data}));add(main,add(grid,hyp,controls));
  if(data.accounts.length) {
    const results=section("Resultados y capital virtual"),accountLabel=el("label","Cuenta independiente","field"),select=el("select");select.setAttribute("aria-label","Cuenta independiente");
    data.accounts.forEach(account=>{const option=el("option",account.label+" · "+(account.currency||"moneda no registrada"));option.value=account.id;add(select,option);});
    const accountView=el("div");add(results,add(el("div",null,"account-toolbar"),add(accountLabel,select)),accountView);add(main,results);
    let request=0;
    async function showAccount(){const current=++request;accountView.replaceChildren(el("p","Leyendo la cuenta guardada…","loading"));try{const account=await api("/api/experiments/"+key+"/accounts/"+select.value);if(token!==navigation||current!==request)return;renderAccount(accountView,account);}catch(error){if(current===request)accountView.replaceChildren(notice(error.message,"error"));}}
    select.addEventListener("change",showAccount);await showAccount();if(token!==navigation)return;
    if(data.accounts.length>1) add(main,comparison(data,key));
  } else add(main,notice("Este registro no contiene cuentas calculadas admitidas. No se reconstruyen ni ejecutan simulaciones para completar la pantalla.","warn"));
  if(data.assessment)add(main,add(section(data.assessment_origin==="python"?"Conclusión guardada de Python":data.assessment_origin==="model"?"Conclusión del modelo contrastada por Python":"Conclusión guardada · ver atribución en el registro"),code(data.assessment)));
  if(data.current_ledger)add(main,add(section("Registro contable vigente · consulta de solo lectura"),notice("Las reservas contables no conceden permiso para ejecutar una campaña. Este estado es independiente del registro histórico del experimento."),disclosure("Estado actual de SQLite",data.current_ledger)));
  const memory=section("Memoria del agente"),models=add(el("div",null,"card"),el("h3","Respuesta original del modelo"));
  if(!data.model.length)add(models,el("p","No hay una respuesta original en los archivos admitidos de esta ficha. Consulta las fuentes enlazadas.","subtle"));
  data.model.forEach((item,i)=>add(models,disclosure("Respuesta "+(i+1)+" · "+(item.stage||"contenido guardado"),item.content)));
  add(memory,models);
  if(data.python.length)add(memory,add(el("div",null,"card section"),el("h3","Descripción o revisión mecánica de Python"),...data.python.map(value=>code(value))));
  add(memory,disclosure("Eventos, estados y errores registrados",data.events),disclosure("Errores y rechazos",data.errors),disclosure("Registro completo (texto)",data.record));add(main,memory);
  const usage=section("Consumo de esta fuente");renderUsage(usage,data.usage);add(main,usage);
  const evidence=section("Informes y evidencia original"),files=el("ul",null,"list");const seen=new Set();[...data.files,...data.evidence,...(data.manifest?[data.manifest]:[])].forEach(file=>{if(!seen.has(file.id)){seen.add(file.id);add(files,source(file));}});add(main,add(evidence,files),notice(data.limits));updated(data.queried_at);
}

function metric(label,value,unit="") {return add(el("div",null,"card"),el("div",label,"stat-label"),el("div",fmt(value)+(value===undefined||value===null?"":" "+unit),"metric-value"));}
function renderAccount(container,account) {
  container.replaceChildren();const s=account.summary,currency=account.currency||"moneda no registrada";
  add(container,el("p",account.label+" · "+currency+" · "+(account.data.first_date||"Fecha inicial no disponible")+" → "+(account.data.last_date||"Fecha final no disponible"),"meta"));
  add(container,add(el("div",null,"metrics"),metric("Capital final",s.final_equity,currency),metric("Rentabilidad acumulada",s.return_percent,"%"),metric("Drawdown máximo",s.max_drawdown_percent,"%"),metric("Operaciones cerradas",s.closed_trades)));
  add(container,dl([["Estrategia",s.strategy],["Costes incurridos",fmt(s.total_costs)+" "+currency],["Posición abierta al final",s.has_open_position===true?"Sí":s.has_open_position===false?"No":"No disponible"],["Entradas rechazadas",s.rejected_entries],["Procedencia",account.integrity.label]]));
  add(container,disclosure("Parámetros de esta cuenta",account.parameters));
  account.warnings.forEach(value=>add(container,notice(value,"warn")));
  if(!account.backtest){add(container,notice("Este formato conserva el resumen, pero no dispone de una curva y operaciones detalladas verificables. No se recalcula el resultado.","warn"));return;}
  const points=account.backtest.equity_curve;
  add(container,add(el("div",null,"card section"),el("h3","Curva de capital · "+currency),chart(points,"equity",currency),el("p",points.length+" observaciones históricas guardadas · Efectivo más posición valorada a la referencia de cada fecha.","meta")));
  add(container,add(el("div",null,"card section"),el("h3","Drawdown guardado · %"),chart(points,"drawdown_percent","%",true)));
  const trades=section("Operaciones cerradas"),list=el("div");add(trades,list);add(container,trades);
  paginate(list,account.backtest.closed_trades,rows=>table(["ENTRADA (SEÑAL → EJECUCIÓN)","SALIDA (SEÑAL → EJECUCIÓN)","CANTIDAD BASE","PRECIOS","COSTES · "+currency,"RESULTADO NETO · "+currency],rows.map(trade=>[trade.position.entry_signal_date+" → "+trade.position.entry_date,trade.exit_signal_date+" → "+trade.exit_date,fmt(trade.position.quantity,6),fmt(trade.position.entry_price,6)+" → "+fmt(trade.exit_price,6),fmt(trade.position.entry_cost,6)+" / "+fmt(trade.exit_cost,6),fmt(trade.pnl,6)])));
  add(container,disclosure("Posición abierta guardada",account.backtest.open_position),disclosure("Efectivo y valoración en la última fecha guardada",points[points.length-1]));
  if(account.file)add(container,add(el("ul",null,"list"),source(account.file)));
}

function chart(points,field,unit,down=false) {
  const ns="http://www.w3.org/2000/svg";const svg=document.createElementNS(ns,"svg");svg.setAttribute("viewBox","0 0 880 260");svg.classList.add("chart");svg.setAttribute("role","img");svg.setAttribute("aria-label",(down?"Drawdown":"Capital")+" histórico de "+points[0].date+" a "+points[points.length-1].date+" en "+unit);
  const values=points.map(p=>Number(p[field])),low=Math.min(...values),high=Math.max(...values),range=high-low||1;
  const start=new Date(points[0].date).getTime(),end=new Date(points[points.length-1].date).getTime(),duration=end-start||1;
  function node(tag,attrs,text){const n=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,String(v)));if(text!==undefined)n.textContent=text;svg.append(n);return n;}
  [0,.5,1].forEach(f=>{const y=22+f*190;node("line",{x1:85,y1:y,x2:855,y2:y,stroke:"#e0e7dc"});node("text",{x:75,y:y+4,"text-anchor":"end"},fmt(high-f*(high-low),2)+" "+unit);});
  const path=points.map((p,i)=>(i?"L":"M")+(85+(new Date(p.date).getTime()-start)/duration*770).toFixed(2)+","+(22+(high-values[i])/range*190).toFixed(2)).join(" ");
  node("path",{d:path,class:"chart-line"+(down?" drawdown-line":"")});node("text",{x:85,y:243},points[0].date);node("text",{x:855,y:243,"text-anchor":"end"},points[points.length-1].date);
  return svg;
}

function paginate(container,items,render) {
  let page=0;const size=15;
  function show(){container.replaceChildren();if(!items.length){add(container,el("p","No hay operaciones cerradas guardadas.","empty"));return;}add(container,render(items.slice(page*size,(page+1)*size)));const prev=button("Anterior",()=>{page--;show();}),next=button("Siguiente",()=>{page++;show();});prev.disabled=page===0;next.disabled=(page+1)*size>=items.length;add(container,add(el("div",null,"pager"),prev,el("span",(page*size+1)+"–"+Math.min((page+1)*size,items.length)+" de "+items.length),next));}show();
}
function comparison(data,key) {
  const node=section("Comparar cuentas compatibles"),form=el("div",null,"compare"),view=el("div");
  const selects=["Primera cuenta","Segunda cuenta"].map((label,index)=>{const select=el("select");select.setAttribute("aria-label",label);data.accounts.forEach(a=>{const option=el("option",a.label);option.value=a.id;add(select,option);});select.selectedIndex=index;add(form,add(el("label",label,"field"),select));return select;});
  add(form,button("Comprobar compatibilidad",async()=>{view.replaceChildren(el("p","Contrastando fuentes y controles…","loading"));try{const response=await api("/api/compare?left="+key+":"+selects[0].value+"&right="+key+":"+selects[1].value);view.replaceChildren(notice(response.compatible?"Cuentas compatibles para esta comparación descriptiva.":"Comparación bloqueada. Diferencias o datos desconocidos: "+response.differences.join(", "),response.compatible?"":"warn"),el("p",response.notice,"subtle"),disclosure("Estrategias y parámetros diferentes",response.strategy_differences));if(response.compatible)add(view,table(["CUENTA","CAPITAL FINAL","RENTABILIDAD %","DRAWDOWN %"],response.accounts.map(a=>[a.label,fmt(a.summary.final_equity)+" "+a.currency,fmt(a.summary.return_percent),fmt(a.summary.max_drawdown_percent)])));}catch(error){view.replaceChildren(notice(error.message,"error"));}},"primary"));return add(node,form,view);
}

function renderUsage(node,usage) {
  add(node,el("h3","Consumo nuevo registrado en esta fuente"));
  add(node,table(["CONSULTAS REGISTRADAS","TOKENS DE ENTRADA","TOKENS DE SALIDA","COSTE API USD"],[[fmt(usage.new.model_requests,0),fmt(usage.new.input_tokens,0),fmt(usage.new.output_tokens,0),fmt(usage.new.api_cost_usd,6)]]),el("p",usage.scope,"subtle"));
  if(usage.inherited&&usage.inherited.length)add(node,disclosure("Consumo heredado · separado del nuevo",usage.inherited));
  if(usage.known_subtotals)add(node,disclosure("Subtotales conocidos (no sustituyen valores desconocidos)",usage.known_subtotals));
}
async function consumption(token) {
  const data=await api("/api/consumption");if(token!==navigation)return;
  main.replaceChildren();title("Consumo","Consulta el uso guardado por fuente. Las copias se identifican y el consumo heredado permanece separado del nuevo.");add(main,notice(data.notice));
  data.items.forEach(item=>{const card=add(el("section",null,"card section"),link(item.title||item.path,"#consumo/"+item.id,"row-title"),el("p",item.path,"meta"));if(item.issue)add(card,notice(item.issue,"warn"));renderUsage(card,{...item,scope:item.scope||"Fuente incompleta: consumo no disponible."});add(main,card);});updated(data.queried_at);
}

async function navigate() {
  const token=++navigation;const [page,key]=location.hash.slice(1).split("/");activePage=Object.hasOwn(names,page)?page:"inicio";
  document.querySelectorAll("[data-nav]").forEach(a=>{a.classList.toggle("active",a.dataset.nav===activePage);if(a.dataset.nav===activePage)a.setAttribute("aria-current","page");else a.removeAttribute("aria-current");});
  document.title=names[activePage]+" · TiresIAs";main.replaceChildren(el("p","Leyendo los registros del laboratorio…","loading"));
  try { if(key)await detail(token,key);else if(activePage==="inicio")await home(token);else if(activePage==="consumo")await consumption(token);else await explorer(token,activePage); }
  catch(error){if(token===navigation)main.replaceChildren(el("h1","No se pudo completar la consulta"),notice(error.message,"error"),button("Volver a intentar",navigate));}
}
window.addEventListener("hashchange",navigate);navigate();
document.querySelector(".skip").addEventListener("click",event=>{event.preventDefault();main.focus();});
