"use strict";

async function simulationPage(token,key) {
  const overview=await api('/api/simulation');if(token!==navigation)return;
  main.replaceChildren();title('Simulación y TradingView','Prepara contratos y Pine, revisa eventos y consulta cuentas virtuales independientes. FASE 6 en desarrollo; todavía no hay una conexión externa verificada.');
  const content=el('div',null,'simulation');add(main,content);
  add(content,notice(overview.notice,'warn'));
  if(key)add(content,link('← Volver a simulación','#simulacion','breadcrumbs'));
  const status=el('div',null,'sim-status');status.setAttribute('role','status');status.setAttribute('aria-live','polite');add(content,status);
  async function action(value) {
    const response=await fetch('/api/simulation',{method:'POST',headers:{'Content-Type':'application/json','X-Tiresias-Action':overview.action_token},body:JSON.stringify(value)});
    const result=await response.json();if(!response.ok)throw Error(result.error||'No se pudo completar la acción.');return result;
  }
  function fail(error){if(token===navigation)status.replaceChildren(notice(error.message,'error'));}
  function panel(label){const node=add(el('section',null,'card'),el('h2',label));add(content,node);return node;}
  function field(parent,label,value,type='text',options=null) {
    const wrap=el('label',label),node=el(options?'select':'input');node.setAttribute('aria-label',label);
    if(options)options.forEach(value=>{const option=el('option',value);option.value=value;add(node,option);});else node.type=type;
    node.value=value;node.required=true;add(parent,add(wrap,node));return node;
  }
  function textarea(parent,label,value){const wrap=el('label',label),node=el('textarea');node.setAttribute('aria-label',label);node.value=typeof value==='string'?value:JSON.stringify(value,null,2);node.required=true;add(parent,add(wrap,node));return node;}
  function approval(parent,text){const label=el('label',null,'sim-approval'),input=el('input');input.type='checkbox';input.required=true;add(parent,add(label,input,el('span',text)));return input;}
  function submit(form,label,callback){const control=el('button',label,'primary');control.type='submit';add(form,control);form.addEventListener('submit',async event=>{event.preventDefault();control.disabled=true;status.replaceChildren();try{await callback();}catch(error){fail(error);}finally{control.disabled=false;}});return control;}
  function download(label,name,text){return button(label,()=>{const url=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'})),a=link(label,url);a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);});}
  function refresh(){if(token===navigation)void navigate();}
  function go(hash){if(token===navigation)location.hash=hash;}
  function confirmation(result){status.replaceChildren(notice('Acción guardada. El detalle conserva su resultado.'),disclosure('Resultado de la acción',result));}

  const researchStatus={simulated:'Prueba histórica calculada',insufficient_history:'Histórico insuficiente',blocked_internal_gaps:'Bloqueado por huecos dentro de las sesiones',blocked_coverage_gaps:'Bloqueado por cobertura incompleta del período'};
  function utcAt(value){return value?String(value).replace('T',' ').replace(/(?:\.000)?Z$/,' UTC'):'Sin fecha';}
  function calculator(parent,items,selected){
    const form=el('form'),grid=el('div',null,'sim-fields');add(parent,form);add(form,grid);
    const dataset=field(grid,'Histórico preparado',selected||items[0].id,'text',items.map(item=>item.id));dataset.parentElement.classList.add('wide');
    [...dataset.options].forEach((option,index)=>{const item=items[index];option.textContent=(item.provider||'Dukascopy')+' · '+(item.start_date||item.first_month)+' → '+(item.end_date_exclusive||item.last_month)+' · '+item.daily_sessions+' sesiones · '+item.id;});
    const capital=field(grid,'Capital hipotético (USD)','1000'),quantity=field(grid,'Cantidad fija (EUR)','1'),commission=field(grid,'Comisión proporcional supuesta','');
    commission.placeholder='Ejemplo: 0.001 equivale a 0.1 %';
    const readiness=el('div');add(form,readiness);
    function available(){const item=items.find(item=>item.id===dataset.value);const gaps=(item.internal_gap_count||0)+(item.coverage_gap_count||0);readiness.replaceChildren(notice(gaps?'Hay huecos en el período seleccionado. Se conserva el diagnóstico y se bloquean las métricas.':item.missing_sessions?'Hay '+item.daily_sessions+' sesiones; faltan '+item.missing_sessions+' para SMA 20/60. Puedes verificar los originales y guardar el diagnóstico.':'Hay suficiente longitud para calcular. Se verificarán los originales antes de ejecutar.',gaps||item.missing_sessions?'warn':''));}
    dataset.addEventListener('change',available);available();
    add(form,el('p','Indica una comisión supuesta con punto decimal. Cero permite un ensayo sin comisión y no confirma la tarifa del proveedor. El spread se incorpora mediante BID/ASK; no se modelan swaps ni deslizamiento.','subtle'));
    submit(form,'Verificar datos y calcular',async()=>{const result=await action({action:'simulate_dukascopy',dataset:dataset.value,capital:capital.value.trim(),quantity:quantity.value.trim(),commission_rate:commission.value.trim()});go('#simulacion/dukascopy-'+result.id);});
  }
  const executionStates={invalid_report:'Informe con filas inválidas',incompatible_configuration:'Configuración declarada incompatible',differences:'Diferencias detectadas',inconclusive_no_fills:'Sin ejecuciones para concluir',incomplete_evidence:'Faltan datos para concluir',matching_fields_unverified_origin:'Coinciden los campos revisados; origen sin verificar'};
  const executionFieldNames={quantity:'Cantidad',price:'Precio',fee:'Comisión',signal_at:'Hora de señal',executed_at:'Hora de ejecución'};
  function executionFacts(parent,value){
    const data=value.comparison;
    add(parent,notice(executionStates[data.status]||data.status,'warn'),dl([['Archivo aportado',value.file_name],['Productor declarado',value.declaration.producer],['Origen declarado',value.declaration.origin],['Ejecuciones Python',data.reference_rows],['Filas aportadas',data.external_rows],['Pares alineados',data.pairs.length],['Faltan respecto a Python',data.missing.length],['Sobran en el informe',data.extra.length],['Alineaciones ambiguas',data.ambiguous.length],['Filas inválidas',data.errors.length]]),
      notice('Este contraste no autentica el origen del informe ni demuestra equivalencia con otro motor. Los costes y campos ausentes siguen siendo desconocidos. No se importan operaciones a ninguna cuenta.','warn'));
    if(data.metadata_unknown.length)add(parent,notice('Metadatos sin comprobar: '+data.metadata_unknown.join(', '),'warn'));
    if(data.metadata_differences.length)add(parent,disclosure('Diferencias de configuración',data.metadata_differences));
    if(data.unknown_fields.length)add(parent,notice('Campos ausentes en las ejecuciones alineadas: '+data.unknown_fields.map(key=>executionFieldNames[key]||key).join(', '),'warn'));
    if(data.pairs.length){const rows=el('div');add(parent,el('p','Ejecuciones alineadas con diferencias: '+data.pairs.filter(pair=>pair.differences.length).length+'.','subtle'),rows);paginate(rows,data.pairs,items=>table(['PYTHON / FILA','ACCIÓN','FECHA PYTHON','FECHA INFORME','CANTIDAD · PYTHON / INFORME','PRECIO · PYTHON / INFORME','COSTE USD · PYTHON / INFORME','DIFERENCIAS'],items.map(pair=>[pair.reference.index+' / '+pair.external.line,pair.reference.side==='buy'?'Compra':'Venta',utcAt(pair.reference.executed_at),utcAt(pair.external.executed_at),pair.reference.quantity+' / '+pair.external.quantity,pair.reference.price+' / '+pair.external.price,pair.reference.fee+' / '+(pair.external.fee??'Desconocido'),pair.differences.length?pair.differences.map(item=>executionFieldNames[item.field]||item.field).join(', '):pair.unknown_fields.length?'Datos incompletos':'Sin diferencias en campos disponibles'])));}
    if(data.missing.length)add(parent,disclosure('Ejecuciones Python sin pareja',data.missing));if(data.extra.length)add(parent,disclosure('Filas del informe sin pareja',data.extra));if(data.ambiguous.length)add(parent,disclosure('Parejas ambiguas: no se eligen automáticamente',data.ambiguous));if(data.errors.length)add(parent,disclosure('Errores del informe: no se compara un subconjunto de filas',data.errors));
  }
  function executionForm(parent,selected=''){
    const runs=overview.dukascopy.runs.filter(item=>item.status==='simulated');
    if(!runs.length){add(parent,notice('Guarda antes una prueba BID/ASK con histórico suficiente. El contraste reutiliza ese resultado sin recalcularlo.'));return;}
    add(parent,el('p','Selecciona un resultado Python guardado y un CSV de ejecuciones aportado. Este lector genérico requiere declarar columnas, unidades y zona horaria; no es un adaptador certificado de JForex o TradingView.','subtle'));
    const form=el('form'),reference=field(form,'Resultado Python de referencia',selected,'text',['',...runs.map(item=>item.id)]);reference.options[0].textContent='Selecciona un resultado';const referenceInfo=el('div');add(form,referenceInfo);
    const upload=field(form,'Informe CSV de ejecuciones para contrastar','','file');upload.accept='.csv,text/csv';
    const mapping=textarea(form,'Mapa de columnas del informe y unidades base',overview.execution_mapping_template),metadata=textarea(form,'Origen y configuración del informe (desconocidos: null)',overview.execution_declaration_template),tolerances=textarea(form,'Tolerancias y ventana de alineación',overview.execution_policy_template),preview=el('div'),saveForm=el('form');saveForm.hidden=true;
    add(form,el('p','La cantidad normalizada se expresa en EUR y las comisiones en USD. Declara cualquier conversión de lotes mediante quantity_multiplier. Las fechas sin zona solo se admiten si declaras un formato UTC. No inventes identificadores, señales ni costes ausentes: usa null para sus columnas.','subtle'));
    let reviewed=null,version=0,revision=0;const check=approval(saveForm,'He revisado el resultado, origen declarado, mapa, unidades, tolerancias y diferencias. Apruebo guardar este contraste, sin operar cuentas.');
    const save=submit(saveForm,'Guardar contraste revisado',async()=>{if(!check.checked||!reviewed)throw Error('Revisa primero la vista previa actual.');const result=await action({...reviewed.request,action:'save_execution_comparison',approve_preview_sha256:reviewed.approval_sha256});go('#simulacion/execution-'+result.id);});
    function invalidate(){revision++;reviewed=null;saveForm.hidden=true;check.checked=false;preview.replaceChildren();}
    async function describeReference(){const own=++version;referenceInfo.replaceChildren();if(!reference.value)return;try{const value=await api('/api/simulation/dukascopy/'+encodeURIComponent(reference.value));if(own!==version||token!==navigation)return;add(referenceInfo,dl([['Estrategia Python',value.configuration.strategy.toUpperCase()+' '+value.configuration.fast+'/'+value.configuration.slow],['Período UTC',value.source.start_date+' → '+value.source.end_date_exclusive+' (fin excluido)'],['Cantidad fija EUR',value.configuration.quantity],['Comisión proporcional supuesta',value.configuration.assumed_commission_rate]]),disclosure('Configuración y huella de sesiones de Python',{configuration:value.configuration,start_date:value.source.start_date,end_date_exclusive:value.source.end_date_exclusive,sessions_sha256:value.sessions_sha256}));}catch(error){if(own===version)fail(error);}}
    reference.addEventListener('change',()=>{invalidate();void describeReference();});upload.addEventListener('change',invalidate);for(const node of [mapping,metadata,tolerances])node.addEventListener('input',invalidate);
    submit(form,'Mostrar contraste sin guardar',async()=>{invalidate();const own=revision,file=upload.files[0];if(!file||file.size>2*1024*1024)throw Error('Selecciona un informe CSV de hasta 2 MiB.');const controls={run:reference.value,mapping:JSON.parse(mapping.value),metadata:JSON.parse(metadata.value),tolerances:JSON.parse(tolerances.value)},bytes=new Uint8Array(await file.arrayBuffer());if(own!==revision)return;let binary='';for(let index=0;index<bytes.length;index+=8192)binary+=String.fromCharCode(...bytes.subarray(index,index+8192));const request={action:'preview_execution_comparison',...controls,name:file.name,csv_base64:btoa(binary)},value=await action(request);if(own!==revision||token!==navigation||!form.isConnected)return;reviewed={request,approval_sha256:value.approval_sha256};executionFacts(preview,value.preview);add(preview,disclosure('Vista previa completa y procedencia',value.preview));saveForm.hidden=false;save.disabled=false;});
    add(parent,form,preview,saveForm);if(selected)void describeReference();
  }
  if(key?.startsWith('execution-')){const identity=key.slice(10),value=await api('/api/simulation/execution-comparisons/'+encodeURIComponent(identity));if(token!==navigation)return;const box=panel('Contraste de ejecuciones guardado');executionFacts(box,value);add(box,download('Descargar contraste JSON','execution-comparison.json',JSON.stringify(value,null,2)),disclosure('Controles, huellas y originales normalizados',value));return;}
  const jforexIssueNames={native_cutoff_equity_not_observed:'Falta una observación nativa del patrimonio al corte',native_cutoff_snapshot_after_target:'La captura nativa es posterior al corte solicitado',account_api_values_may_lag:'Los valores de cuenta de la API son informativos y pueden tener retraso',per_fill_commission_unknown:'Comisión por ejecución desconocida',reported_amounts_have_limited_precision:'Los importes publicados tienen precisión limitada',commission_totals_differ:'Los totales de comisión no coinciden',swaps_after_strategy_cutoff:'El informe incluye swaps posteriores al corte',session_or_signal_differences:'Hay diferencias de sesiones o señales',execution_differences_or_unknown_fields:'Hay diferencias o datos ausentes en las ejecuciones',fills_after_strategy_cutoff:'Hay ejecuciones posteriores al corte'};
  function jforexFacts(parent,value){
    const native=value.native_report,cut=value.common_cutoff,fees=value.commissions,coverage=value.coverage;
    add(parent,notice('Conciliación parcial: quedan datos por comprobar.','warn'),dl([['Informe',value.file_name],['Corte común UTC',utcAt(value.cutoff)],['Resultado al final del informe USD',native.net_change_usd],['Patrimonio al final del informe USD',native.final_equity_usd],['Último tick del informe (UTC declarado)',native.last_tick_reported],['Resultado bruto al corte, reconstruido USD',cut.gross_pnl_from_fills_usd],['Posición al corte EUR',cut.open_quantity_eur],['Swaps al corte, derivados USD',cut.derived_swaps_before_cutoff_usd],['Swaps posteriores, derivados USD',cut.derived_swaps_after_cutoff_usd],['Comisiones: HTML / órdenes / eventos USD',fees.html_reported_usd+' / '+fees.orders_reported_sum_usd+' / '+fees.events_reported_sum_usd],['Patrimonio nativo observado al corte',cut.native_equity_observed?'Disponible con fecha en el detalle':'Desconocido'],['Patrimonio Python al corte USD',cut.python_equity_usd],['Comisiones supuestas Python USD',cut.python_assumed_commissions_usd],['Sesiones reconstruidas',coverage.daily_sessions],['Sesiones idénticas a la referencia',coverage.matches_reference_sessions?'Sí':'No'],['Horas admitidas / excluidas',coverage.eligible_h1+' / '+coverage.excluded_h1]]));
    if(cut.diagnostic_scenarios.length)add(parent,el('p','Reconstrucciones al mismo corte usando cada total de comisión publicado. No son observaciones del saldo nativo ni límites certificados.','subtle'),table(['TOTAL DE COMISIÓN USADO','COMISIÓN USD','PATRIMONIO RECONSTRUIDO USD','RESULTADO RECONSTRUIDO USD'],cut.diagnostic_scenarios.map(r=>[r.commission_source==='html_reported'?'HTML':'Agregados de órdenes',r.commission_usd,r.reconstructed_equity_usd,r.reconstructed_pnl_usd])));
    add(parent,notice(value.issues.map(key=>jforexIssueNames[key]||key).join('. '),'warn'),notice('El patrimonio final del informe y el de Python tienen cortes distintos. Los swaps ya incluidos en el precio ajustado de una posición no se vuelven a descontar de su P/L. Esta revisión no importa operaciones a cuentas.','warn'),disclosure('Ejecuciones, swaps y procedencia',value));
  }
  function jforexForm(parent){
    const runs=overview.dukascopy.runs.filter(item=>item.status==='simulated');if(!runs.length){add(parent,notice('Selecciona primero una referencia Python calculada.'));return;}
    add(parent,el('p','Carga un ZIP con report.html y los CSV/JSON de la estrategia Tiresias TEST H1, Bid y 4 ticks at OHLC. Se conservan los originales y los datos desconocidos. Las fechas del HTML deben estar en UTC y coincidir con las ejecuciones ISO.','subtle'));
    const form=el('form'),reference=field(form,'Referencia Python para conciliar JForex','','text',['',...runs.map(r=>r.id)]);reference.options[0].textContent='Selecciona un resultado';
    const upload=field(form,'Paquete nativo de JForex (.zip)','','file');upload.accept='.zip,application/zip';
    const preview=el('div'),saveForm=el('form');saveForm.hidden=true;let reviewed=null,revision=0;
    const check=approval(saveForm,'He revisado el corte, las reconstrucciones, los costes desconocidos y las diferencias. Apruebo conservar esta conciliación, sin operar cuentas.');
    submit(saveForm,'Guardar conciliación revisada',async()=>{if(!check.checked||!reviewed)throw Error('Revisa la vista previa actual.');const result=await action({...reviewed.request,action:'save_jforex_reconciliation',approve_preview_sha256:reviewed.approval_sha256});go('#simulacion/jforex-'+result.id);});
    function invalidate(){revision++;reviewed=null;saveForm.hidden=true;check.checked=false;preview.replaceChildren();}
    reference.addEventListener('change',invalidate);upload.addEventListener('change',invalidate);
    submit(form,'Revisar paquete JForex sin guardar',async()=>{invalidate();const own=revision,file=upload.files[0];if(!file||file.size>2*1024*1024)throw Error('Selecciona un ZIP de hasta 2 MiB.');const bytes=new Uint8Array(await file.arrayBuffer());if(own!==revision)return;let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));const request={action:'preview_jforex_reconciliation',run:reference.value,name:file.name,zip_base64:btoa(binary),html_timezone:'UTC'},value=await action(request);if(own!==revision||token!==navigation||!form.isConnected)return;reviewed={request,approval_sha256:value.approval_sha256};jforexFacts(preview,value.preview);saveForm.hidden=false;});
    add(parent,form,preview,saveForm);
  }
  if(key?.startsWith('jforex-')){const value=await api('/api/simulation/jforex-reconciliations/'+encodeURIComponent(key.slice(7)));if(token!==navigation)return;const box=panel('Conciliación nativa de JForex');jforexFacts(box,value);add(box,download('Descargar conciliación JSON','jforex-reconciliation.json',JSON.stringify(value,null,2)));return;}
  if(key?.startsWith('compare-executions-')){executionForm(panel('Contrastar un informe de operaciones'),key.slice(19));return;}
  if(key?.startsWith('history-')){
    const value=await api('/api/simulation/price-histories/'+encodeURIComponent(key.slice(8)));if(token!==navigation)return;
    const m=value.manifest,box=panel('Histórico de precios verificado');
    add(box,dl([['Proveedor',m.provider||'Dukascopy'],['Identidad',value.id],['Período solicitado UTC',m.start_date?m.start_date+' → '+m.end_date_exclusive+' (fin exclusivo)':m.first_month+' → '+m.last_month],
      ['Primera observación',m.first_observed_open_at?utcAt(m.first_observed_open_at):'Conservada en los originales'],['Última observación',m.last_observed_close_at?utcAt(m.last_observed_close_at):'Conservada en los originales'],
      ['Sesiones diarias',value.daily_sessions],['Velas H1 seleccionadas',m.selected_hours??'En los originales'],['Velas fuera del período',m.excluded_hours_outside_period??0]]));
    if(m.attribution)add(box,notice(m.attribution));
    if(value.internal_gaps.length||value.coverage_gaps.length)add(box,notice('Hay huecos en este período. El cálculo conservará el diagnóstico sin métricas de rentabilidad.','warn'),disclosure('Huecos observados',{internal:value.internal_gaps,coverage:value.coverage_gaps}));
    calculator(box,[{id:value.id,provider:m.provider,daily_sessions:value.daily_sessions,missing_sessions:value.missing_sessions,
      start_date:m.start_date,end_date_exclusive:m.end_date_exclusive,first_month:m.first_month,last_month:m.last_month,
      internal_gap_count:value.internal_gaps.length,coverage_gap_count:value.coverage_gaps.length}],value.id);
    add(box,disclosure('Procedencia y originales conservados',m));return;
  }
  if(key?.startsWith('dukascopy-')){
    const identity=key.slice(10),result=await api('/api/simulation/dukascopy/'+encodeURIComponent(identity));if(token!==navigation)return;
    const box=panel('Prueba con precios históricos · SMA '+result.configuration.fast+'/'+result.configuration.slow);
    add(box,notice(researchStatus[result.status]||result.status,result.status==='simulated'?'':'warn'),
      dl([['Mercado','EUR/USD · sesiones diarias UTC observadas'],['Proveedor',result.source.provider||'Dukascopy'],['Histórico local',result.source.directory.split(/[\\/]/).pop()],['Período UTC',result.source.start_date?result.source.start_date+' → '+result.source.end_date_exclusive+' (fin exclusivo)':'Conservado en el histórico'],['Sesiones disponibles',result.daily_sessions],['Sesiones mínimas',result.required_sessions],
          ['Capital hipotético',result.configuration.initial_capital+' USD'],['Cantidad fija',result.configuration.quantity+' EUR'],
          ['Comisión proporcional supuesta',result.configuration.assumed_commission_rate],['Originales','Contrastados al calcular; consulta de un resultado guardado']]),
      el('p','La señal usa cierres BID. Compra a ASK y vende a BID en la primera apertura observada de la siguiente sesión. Se conservan domingos y días parciales.','subtle'));
    if(result.missing_sessions)add(box,notice('Faltan '+result.missing_sessions+' sesiones observadas para evaluar este cruce. No se publican operaciones ni rentabilidad.','warn'));
    if(result.source.attribution)add(box,notice(result.source.attribution));
    if(result.source.all_final_transports_https===false)add(box,notice('Los archivos originales llegaron mediante una redirección HTTP. Sus huellas se han contrastado, pero el transporte final no autentica su origen.','warn'));
    if(result.source.all_final_transports_https===null)add(box,el('p','Originales aportados y contrastados por sus huellas; la identidad procede del catálogo o de la declaración de importación.','subtle'));
    add(box,el('p','El spread ya está incluido en los precios de compra y venta. La comisión es una hipótesis elegida para esta prueba; no se modelan deslizamiento, swaps ni liquidez.','subtle'));
    if(result.summary){
      const s=result.summary,metrics=panel('Resultado hipotético en este histórico');
      add(metrics,dl([['Patrimonio final',fmt(s.final_equity)+' USD'],['Variación',fmt(s.return_percent)+' %'],['Operaciones cerradas',s.closed_trades],
        ['Posición abierta',s.open_quantity+' EUR'],['Comisiones supuestas',fmt(s.assumed_commissions)+' USD'],
        ['Máxima caída observada',fmt(s.max_observed_drawdown_percent)+' %'],['Última valoración',utcAt(s.last_valuation_at)]]));
      if(result.equity_curve.length)add(metrics,chart(result.equity_curve.map(point=>({...point,date:point.at})),'equity','USD'));
    }
    const fills=panel('Operaciones hipotéticas');
    if(result.status==='simulated')add(fills,link('Contrastar estas ejecuciones con un informe aportado','#simulacion/compare-executions-'+identity,'button'));
    if(result.hypothetical_fills.length){const list=el('div');add(fills,list);paginate(list,result.hypothetical_fills,rows=>table(['SEÑAL UTC','EJECUCIÓN OBSERVADA UTC','LADO','UNIDADES EUR','PRECIO USD/EUR','COMISIÓN SUPUESTA USD'],rows.map(fill=>[
      utcAt(fill.signal_at),utcAt(fill.executed_at),fill.side==='buy'?'Compra · ASK':'Venta · BID',fill.quantity,fill.price,fill.assumed_commission])));}
    else add(fills,el('p',result.status==='simulated'?'No hay operaciones en esta prueba.':'No se han simulado operaciones con estos datos.','subtle'));
    if(result.pending_order)add(fills,notice('Queda una señal pendiente. No se inventa una ejecución posterior al último precio disponible.','warn'));
    if(result.rejected_orders.length)add(fills,disclosure('Órdenes rechazadas en el cálculo',result.rejected_orders));
    add(box,download('Descargar resultado JSON','dukascopy-'+identity+'.json',JSON.stringify(result,null,2)),disclosure('Procedencia y reglas',result.source),disclosure('Resultado completo',result));
    return;
  }

  if(key?.startsWith('benchmark-')){
    const identity=key.slice(10),value=await api('/api/simulation/market-benchmarks/'+encodeURIComponent(identity));if(token!==navigation)return;
    const result=value.result,s=value.summary,c=s.configuration,box=panel('Referencias y sensibilidad a comisiones · SMA 20/60');
    add(box,notice(s.status==='calculated'?'Escenarios calculados con la misma cantidad y los mismos datos.':researchStatus[s.status]||s.status,s.status==='calculated'?'':'warn'),
      dl([['Proveedor',s.source.provider||'Dukascopy'],['Período UTC · fin excluido',s.source.start_date?s.source.start_date+' → '+s.source.end_date_exclusive:'Conservado en el histórico'],
        ['Sesiones',s.daily_sessions],['Capital por escenario',c.initial_capital+' USD'],['Cantidad fija',c.quantity+' EUR']]),
      el('p','Referencia: comprar la cantidad fija en ASK en la primera apertura observada tras 61 sesiones completas y mantenerla valorada a BID. El efectivo USD no genera intereses. Cada escenario empieza de cero; el tiempo en mercado puede ser distinto.','subtle'),
      el('p','Comisiones supuestas por ejecución: 0 %, 0,05 %, 0,1 % y 0,2 %. El spread permanece incluido con comisión cero. No se fuerza una venta final ni se añade una comisión de salida que no ocurrió. No se modelan swaps o deslizamiento.','subtle'));
    if(s.source.attribution)add(box,el('p',s.source.attribution,'subtle'));
    if(s.status==='calculated'){
      add(box,el('h3','Patrimonio final por comisión supuesta'),table(['COMISIÓN POR EJECUCIÓN','SMA · USD','COMPRAR Y MANTENER · USD'],s.scenarios.map(item=>[
        fmt(Number(item.commission_rate)*100,3)+' %',fmt(item.sma.final_equity,8),fmt(item.buy_hold.final_equity,8)])),
        el('p','Referencia en efectivo sin intereses: '+fmt(s.cash_reference.final_equity,8)+' USD en todos los escenarios. Las diferencias no ajustan por el distinto tiempo de exposición.','subtle'));
      const details=panel('Detalle del escenario'),rate=field(details,'Comisión del escenario','0.001','text',s.scenarios.map(item=>item.commission_rate)),view=el('div');
      [...rate.options].forEach(option=>{option.textContent=fmt(Number(option.value)*100,3)+' % por ejecución';});add(details,view);
      function renderScenario(){
        const item=s.scenarios.find(item=>item.commission_rate===rate.value),full=result.scenarios.find(item=>item.commission_rate===rate.value);
        const metrics=[['Patrimonio final (USD)','final_equity'],['Variación (%)','return_percent'],['Máxima caída observada (%)','max_observed_drawdown_percent'],['Comisiones supuestas (USD)','assumed_commissions'],['Operaciones cerradas','closed_trades'],['Posición abierta (EUR)','open_quantity']];
        const matrix=table(['MÉTRICA','SMA 20/60','COMPRAR Y MANTENER'],metrics.map(([label,key])=>[label,fmt(item.sma[key],8),fmt(item.buy_hold[key],8)]));matrix.classList.add('sim-period-comparison');
        view.replaceChildren();add(view,el('p','Entrada de referencia: '+utcAt(item.reference_entry_at)+'. Ejecuciones SMA / referencia: '+item.sma_fills+' / '+item.hold_fills+'.','subtle'),matrix,
          dl([['SMA menos referencia',fmt(item.sma_minus_buy_hold_usd,8)+' USD'],['SMA menos efectivo',fmt(item.sma_minus_cash_usd,8)+' USD']]),
          el('p','Diferencia positiva significa mayor patrimonio final bajo estas hipótesis. No selecciona una estrategia o comisión ganadora ni demuestra robustez estadística.','subtle'));
        if(item.hold_rejections||item.sma_rejections)add(view,notice('Hay entradas rechazadas por saldo. La referencia puede permanecer en efectivo; revisa las operaciones antes de interpretar la diferencia.','warn'));
        add(view,disclosure('Operaciones y rechazos del escenario',{sma_fills:full.sma.hypothetical_fills,sma_rejections:full.sma.rejected_orders,reference_fills:full.buy_hold.hypothetical_fills,reference_rejections:full.buy_hold.rejected_orders}));
      }
      rate.addEventListener('change',renderScenario);renderScenario();
    }else add(box,el('p','Esta comparación requiere 62 sesiones y los controles de calidad existentes. No se publican métricas sobre datos bloqueados.','subtle'));
    add(box,download('Descargar referencias y costes JSON','benchmark-'+identity+'.json',JSON.stringify(result,null,2)),disclosure('Procedencia y reglas conservadas',s));return;
  }

  if(key?.startsWith('comparison-')){
    const value=await api('/api/simulation/market-comparisons/'+encodeURIComponent(key.slice(11)));if(token!==navigation)return;
    const box=panel('Comparación de períodos · SMA '+value.configuration.fast+'/'+value.configuration.slow);
    add(box,notice(value.status==='compared'?'Resultados guardados contrastados con sus copias de entrada.':'Comparación incompleta: hay un período sin métricas.','warn'),
      dl([['Proveedor',value.provider],['Capital inicial por período',value.configuration.initial_capital+' USD'],['Cantidad fija',value.configuration.quantity+' EUR'],['Comisión supuesta',value.configuration.assumed_commission_rate]]),
      el('p','Cada período empieza con su propio capital, sin posiciones ni medias heredadas. Los saldos no se suman. Esta comparación retrospectiva no demuestra validación prospectiva ni selecciona parámetros.','subtle'));
    const metrics=[['Resultado original',p=>link('Abrir prueba','#simulacion/dukascopy-'+p.run_id)],['Estado',p=>researchStatus[p.status]||p.status],['Sesiones',p=>p.daily_sessions],['Ejecuciones hipotéticas',p=>p.hypothetical_fills],
      ['Patrimonio final (USD)',p=>p.summary?fmt(p.summary.final_equity,8):'Sin métricas'],['Variación (%)',p=>p.summary?fmt(p.summary.return_percent,8):'Sin métricas'],
      ['Máxima caída observada (%)',p=>p.summary?fmt(p.summary.max_observed_drawdown_percent,8):'Sin métricas'],['Operaciones cerradas',p=>p.summary?p.summary.closed_trades:'Sin métricas'],
      ['Posición abierta (EUR)',p=>p.summary?p.summary.open_quantity:'Sin métricas']];
    const comparisonTable=table(['PERÍODO UTC · FIN EXCLUIDO',...value.periods.map(p=>p.start_date+' → '+p.end_date_exclusive)],metrics.map(([label,read])=>[label,...value.periods.map(read)]));
    comparisonTable.classList.add('sim-period-comparison');add(box,comparisonTable);
    for(const attribution of new Set(value.periods.map(p=>p.attribution).filter(Boolean)))add(box,el('p',attribution,'subtle'));
    add(box,el('p','Se conserva también el resultado de períodos bloqueados. Los huecos y la escasez de operaciones limitan las conclusiones. Consultar esta ficha no vuelve a calcular estrategias.','subtle'),
      download('Descargar comparación JSON','comparison.json',JSON.stringify(value,null,2)),disclosure('Entradas y reglas conservadas',value));return;
  }

  if(key?.startsWith('bundle-')){
    const identity=key.slice(7),bundle=await api('/api/simulation/bundles/'+encodeURIComponent(identity));if(token!==navigation)return;
    const c=bundle.contract,box=panel('Paquete '+c.strategy.kind.toUpperCase()+' '+c.strategy.fast+'/'+c.strategy.slow);
    add(box,dl([['Identidad',identity],['Mercado',c.market.ticker+' · '+c.market.timeframe],['Cuenta virtual',c.account.id+' · '+c.account.currency],['Período UTC',c.period.start+' → '+c.period.end],['Capital / cantidad',c.account.initial_capital+' / '+c.account.quantity],['Coste proporcional',c.account.cost_rate]]),
      notice('Pine generado y verificado localmente. Compilación, gráfico y resultados externos pendientes. Modificar Properties o el script invalida la equivalencia con este contrato.','warn'),
      add(el('div',null,'sim-actions'),download('Descargar Pine','tiresias-'+identity.slice(0,12)+'.pine',bundle.pine),download('Descargar contrato','contract.json',JSON.stringify(c,null,2)),download('Descargar mensaje de alerta','alert-message.json.txt',bundle.alert_message)),
      disclosure('Código Pine',bundle.pine),disclosure('Plantilla de alerta',bundle.alert_message),disclosure('Contrato y huellas',bundle.manifest));
    if(overview.accounts.some(account=>account.id===identity))add(box,link('Abrir cuenta virtual →','#simulacion/account-'+identity,'button primary'));
    else {
      const register=panel('Registrar la cuenta virtual'),form=el('form');add(register,form);
      add(form,el('p','El capital y estos límites quedan fijados al registrar. No se reemplazan por saldos importados.','subtle'));
      const risk=textarea(form,'Límites del simulador (JSON)',overview.risk_defaults);
      const check=approval(form,'He revisado el contrato, capital, cantidad, moneda, costes y límites de esta cuenta virtual.');
      submit(form,'Registrar esta cuenta virtual',async()=>{if(!check.checked)throw Error('Revisión requerida.');await action({action:'register',bundle:identity,risk:JSON.parse(risk.value),approve_virtual_account:true});go('#simulacion/account-'+identity);});
    }
    const csv=panel('Revisar e importar ejecuciones CSV'),form=el('form');add(csv,form);
    add(form,el('p','Selecciona el archivo original (UTF-8, hasta 2 MiB) y adapta el mapa a sus columnas reales. La plantilla es genérica; no acredita un formato TradingView. Las importaciones guardan eventos en el inbox y requieren procesamiento posterior.','subtle'));
    const upload=field(form,'Archivo CSV original','','file');upload.accept='.csv,text/csv';
    const mapping=textarea(form,'Mapa explícito de columnas, números, acciones y zona horaria',overview.mapping_template),result=el('div');
    let reviewed=null;const approvalForm=el('form');approvalForm.hidden=true;const check=approval(approvalForm,'He revisado las filas normalizadas, fechas, costes y errores de esta vista previa.');
    const accept=submit(approvalForm,'Guardar filas revisadas en el inbox',async()=>{if(!check.checked||!reviewed||reviewed.preview.errors.length)throw Error('Revisar una vista previa válida.');const saved=await action({...reviewed.request,action:'import_csv',approve_preview_sha256:reviewed.approval_sha256});confirmation(saved);approvalForm.hidden=true;});
    function invalidate(){reviewed=null;approvalForm.hidden=true;check.checked=false;result.replaceChildren();}
    upload.addEventListener('change',invalidate);mapping.addEventListener('input',invalidate);
    submit(form,'Validar y mostrar vista previa',async()=>{
      invalidate();const file=upload.files[0];if(!file||file.size>2*1024*1024)throw Error('Selecciona un CSV de hasta 2 MiB.');
      const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
      const request={action:'preview_csv',bundle:identity,csv_base64:btoa(binary),mapping:JSON.parse(mapping.value)},preview=await action(request);
      if(token!==navigation)return;reviewed={...preview,request};
      add(result,dl([['Original SHA-256',preview.preview.raw_sha256],['Filas válidas',preview.preview.rows.length],['Errores',preview.preview.errors.length]]),disclosure('Todas las filas normalizadas y errores',preview.preview));
      if(preview.preview.errors.length)add(result,notice('Hay errores. No se importará ninguna fila.','error'));
      else if(!overview.accounts.some(account=>account.id===identity))add(result,notice('Registra antes la cuenta virtual para importar desde esta pantalla.','warn'));
      else{approvalForm.hidden=false;accept.disabled=false;}
    });add(csv,result,approvalForm);
    return;
  }

  if(key?.startsWith('account-')){
    const identity=key.slice(8),data=await api('/api/simulation/accounts/'+encodeURIComponent(identity));if(token!==navigation)return;
    const c=data.contract,s=data.state,box=panel('Cuenta virtual '+c.account.id+' · '+c.account.currency);
    add(box,dl([['Mercado / estrategia',c.market.ticker+' · '+c.strategy.kind.toUpperCase()+' '+c.strategy.fast+'/'+c.strategy.slow],['Capital inicial',c.account.initial_capital+' '+c.account.currency],['Último estado',at(s.last_at)],['Precio / fecha',s.price===null?'Precio aún no aportado':s.price+' · '+at(s.price_at)],['Antigüedad',data.price_age_seconds===null?'Desconocida':fmt(data.price_age_seconds/3600,1)+' horas'],['Próxima secuencia',data.waiting_for_sequence??'Sin eventos pendientes']]),
      notice(data.source_notice,data.price_stale?'warn':''));
    const metrics=el('div',null,'metrics');[['Efectivo',s.cash],['Cantidad abierta',s.quantity],['Patrimonio virtual',s.equity],['Costes acumulados',s.fees]].forEach(([label,value])=>add(metrics,add(el('div',null,'card'),el('div',label,'stat-label'),el('div',fmt(value,8),'metric-value'))));add(box,metrics);
    if(data.price_stale)add(box,notice('Precio ausente u obsoleto. El patrimonio no es una valoración actual verificada.','warn'));
    if(s.risk_paused)add(box,notice('Nuevas entradas pausadas por riesgo o discrepancia: '+(s.last_reason||'límite de drawdown')+'. Las salidas siguen sujetas a saldo y posición.','warn'));
    if(!data.engine_compatible)add(box,notice('El motor cambió desde el registro. Esta cuenta conserva su historial para consulta; procesar y valorar permanecen bloqueados hasta revisar una migración o preparar otra cuenta.','warn'));
    if(data.problem_count){
      add(box,notice('Esta cuenta tiene '+data.problem_count+' recepciones con conflicto o error. Revísalas antes de procesar; sus originales no sustituyen los eventos canónicos.','warn'),
        table(['RECEPCIÓN','ESTADO','EJECUCIÓN','MOTIVO'],data.problem_receipts.map(receipt=>[link(receipt.id.slice(0,12),'#simulacion/receipt-'+receipt.id),receipt.state,receipt.execution??'No normalizada',receipt.reason??'Conflicto de identidad o secuencia'])));
    }
    const bundleLink=overview.bundles.some(bundle=>bundle.id===identity)?link('Ver contrato y Pine','#simulacion/bundle-'+identity,'button'):button('Preparar Pine de este contrato',async()=>{try{await action({action:'prepare_bundle',contract:c});go('#simulacion/bundle-'+identity);}catch(error){fail(error);}});
    add(box,add(el('div',null,'sim-actions'),button('Actualizar estado',refresh),bundleLink),disclosure('Estado exacto y controles',data));
    const history=panel('Historial contable de eventos · últimos 200');
    if(data.events.length)add(history,table(['SECUENCIA','EJECUCIÓN','ESTADO','MOTIVO'],data.events.slice(-200).map(event=>[event.sequence,event.execution,event.state,event.reason??'Sin rechazo'])));
    else add(history,el('p','Todavía no hay eventos normalizados.','subtle'));
    const pending=panel('Eventos pendientes de revisar · '+data.pending_count);
    if(data.pending_events.length){
      add(pending,table(['SECUENCIA','ACCIÓN','CANTIDAD','PRECIO','COSTE','SEÑAL / EJECUCIÓN'],data.pending_events.map(event=>[event.sequence,event.side==='buy'?'Compra':'Venta',event.quantity,event.price,event.fee??'Estimación según contrato',at(event.signal_at)+' / '+at(event.executed_at)])));
      const form=el('form');add(pending,form);approval(form,'He revisado este estado y los eventos pendientes. Autorizo contabilizar hasta 100 eventos simulados en secuencia, sujetos a saldo y riesgo.');
      const processButton=submit(form,'Procesar eventos revisados',async()=>{await action({action:'process',account:identity,chain_sha256:data.chain_sha256,review_sha256:data.review_sha256,approve_processing:true});refresh();});processButton.disabled=!data.engine_compatible;
      add(pending,el('p','Si falta una secuencia, el procesamiento espera. Si cambia la cuenta o el inbox, tendrás que recargar y revisar de nuevo.','subtle'));
    }else add(pending,el('p','No hay eventos pendientes. Abrir esta pantalla no crea operaciones.','subtle'));
    const marks=panel('Aportar una valoración virtual'),markForm=el('form'),fields=el('div',null,'sim-fields');add(marks,markForm);add(markForm,fields);
    const price=field(fields,'Precio aportado (decimal con punto)','','text'),when=field(fields,'Fecha ISO con zona horaria',new Date().toISOString());
    approval(markForm,'Identifico este precio como aportado manualmente y autorizo actualizar la valoración virtual, sin comprar ni vender.');const markId=crypto.randomUUID();
    const markButton=submit(markForm,'Registrar valoración',async()=>{await action({action:'mark',account:identity,price:price.value,at:when.value,mark_id:markId,chain_sha256:data.chain_sha256,approve_valuation:true});refresh();});markButton.disabled=!data.engine_compatible;
    const reconcile=panel('Conciliar con un estado externo aportado'),reconcileForm=el('form');add(reconcile,reconcileForm);
    add(reconcileForm,el('p','Compara moneda, fecha, efectivo, cantidad y patrimonio. null conserva un dato desconocido. Esta consulta no sustituye el capital local.','subtle'));
    const external=textarea(reconcileForm,'Estado externo (JSON)',{as_of:s.last_at||new Date().toISOString(),currency:c.account.currency,cash:null,quantity:null,equity:null});
    submit(reconcileForm,'Comparar sin modificar la cuenta',async()=>{confirmation(await action({action:'reconcile',account:identity,external:JSON.parse(external.value)}));});
    return;
  }

  if(key?.startsWith('receipt-')){
    const receipt=await api('/api/simulation/receipts/'+encodeURIComponent(key.slice(8)));if(token!==navigation)return;
    const box=panel('Original del evento recibido');add(box,dl([['Estado',receipt.state],['Motivo',receipt.reason??'Sin error de normalización'],['SHA-256 original',receipt.hash],['Transporte',receipt.transport],['Recibido',at(receipt.received)]]),disclosure('Procedencia conservada',receipt.source),code(receipt.raw));
    if(receipt.account)add(box,link('Abrir cuenta asociada','#simulacion/account-'+receipt.account,'button'));return;
  }
  if(key)throw Error('Ficha de simulación desconocida.');

  const research=panel('Históricos EUR/USD y prueba con spread'),data=overview.dukascopy;
  add(research,el('p','SMA 20/60 sobre sesiones diarias UTC de EUR/USD. El cálculo conserva el resultado y no modifica cuentas virtuales. Esta pantalla utiliza los históricos locales ya preparados.','subtle'));
  if(data.datasets.length){
    calculator(research,data.datasets);
  }else add(research,el('p','Todavía no hay históricos locales preparados. Al preparar uno, aparecerá aquí.','subtle'));
  if(data.runs.length)add(research,el('h3','Resultados guardados'),table(['RESULTADO','PERÍODO UTC · FIN EXCLUIDO','SESIONES','PATRIMONIO HIPOTÉTICO'],data.runs.map(run=>[
    link(researchStatus[run.status]||run.status,'#simulacion/dukascopy-'+run.id),run.start_date?run.start_date+' → '+run.end_date_exclusive:'En el histórico',run.daily_sessions,run.summary?fmt(run.summary.final_equity)+' USD':'Sin métricas: revisar datos'])));
  const periodRuns=data.runs.filter(run=>run.start_date&&run.end_date_exclusive);
  if(periodRuns.length>1){
    const compare=el('form'),grid=el('div',null,'sim-fields');add(research,el('h3','Comparar períodos independientes'),compare);add(compare,grid);
    const left=field(grid,'Primer resultado guardado',periodRuns[0].id,'text',periodRuns.map(run=>run.id)),right=field(grid,'Segundo resultado guardado',periodRuns[1].id,'text',periodRuns.map(run=>run.id));
    for(const control of [left,right])[...control.options].forEach((option,index)=>{const run=periodRuns[index];option.textContent=run.start_date+' → '+run.end_date_exclusive+' · '+(researchStatus[run.status]||run.status)+' · '+run.id.slice(0,8);});
    add(compare,el('p','Requiere períodos sin solapamiento, misma configuración, proveedor y versión del motor. Compara resultados guardados; no ejecuta otra estrategia ni combina saldos.','subtle'));
    submit(compare,'Guardar comparación de períodos',async()=>{const result=await action({action:'compare_price_periods',left:left.value,right:right.value});go('#simulacion/comparison-'+result.id);});
  }
  if(data.comparisons?.length)add(research,el('h3','Comparaciones guardadas'),table(['PERÍODOS UTC · FIN EXCLUIDO','ESTADO'],data.comparisons.map(value=>[
    link(value.periods.map(p=>p.start_date+' → '+p.end_date_exclusive).join(' / '),'#simulacion/comparison-'+value.id),value.status==='compared'?'Comparación disponible':'Hay períodos sin métricas'])));
  if(data.warnings.length)add(research,disclosure('Avisos de históricos',data.warnings));

  const references=panel('Comparar con referencias y comisiones');
  add(references,el('p','Calcula SMA 20/60, comprar y mantener, y efectivo sin intereses sobre el mismo histórico. Usa cuatro comisiones supuestas fijas: 0 %, 0,05 %, 0,1 % y 0,2 % por ejecución. No selecciona parámetros ni modifica cuentas.','subtle'));
  if(data.datasets.length){
    const form=el('form'),grid=el('div',null,'sim-fields');add(references,form);add(form,grid);
    const dataset=field(grid,'Histórico para referencias',data.datasets[0].id,'text',data.datasets.map(item=>item.id));dataset.parentElement.classList.add('wide');
    [...dataset.options].forEach((option,index)=>{const item=data.datasets[index];option.textContent=(item.provider||'Dukascopy')+' · '+(item.start_date||item.first_month)+' → '+(item.end_date_exclusive||item.last_month)+' · '+item.daily_sessions+' sesiones · '+item.id;});
    const capital=field(grid,'Capital de cada escenario (USD)','1000'),quantity=field(grid,'Cantidad de cada escenario (EUR)','1');
    add(form,el('p','Se requieren 62 sesiones para observar una apertura tras el calentamiento. Los huecos conservan su bloqueo. La compra de referencia usa ASK, mantiene la cantidad fija y termina valorada a BID.','subtle'));
    submit(form,'Calcular referencias y costes',async()=>{const result=await action({action:'benchmark_price_history',dataset:dataset.value,capital:capital.value.trim(),quantity:quantity.value.trim()});go('#simulacion/benchmark-'+result.id);});
  }
  if(data.benchmarks?.length)add(references,el('h3','Ensayos guardados'),table(['PERÍODO UTC · FIN EXCLUIDO','SESIONES','ESTADO'],data.benchmarks.map(item=>[
    link(item.start_date?item.start_date+' → '+item.end_date_exclusive:item.id.slice(0,12),'#simulacion/benchmark-'+item.id),item.daily_sessions,item.status==='calculated'?'Referencias calculadas':researchStatus[item.status]||item.status])));

  const importer=panel('Importar precios históricos'),importForm=el('form'),importGrid=el('div',null,'sim-fields');add(importer,importForm);add(importForm,importGrid);
  const closedYear=new Date().getUTCFullYear()-1;
  const format=field(importGrid,'Formato de precios','dukascopy_csv','text',['dukascopy_csv','evtradelabs_h1_json_gzip']);
  format.options[0].textContent='CSV Dukascopy · BID y ASK';format.options[1].textContent='EV Trading Labs · JSON gzip anual H1';
  const start=field(importGrid,'Inicio UTC incluido',closedYear+'-01-01','date'),end=field(importGrid,'Fin UTC excluido',(closedYear+1)+'-01-01','date');
  const bid=field(importGrid,'CSV BID en orden por nombre','','file'),ask=field(importGrid,'CSV ASK en orden por nombre','','file'),annual=field(importGrid,'Archivo anual H1 (.json.gz)','','file'),year=field(importGrid,'Año declarado del archivo',closedYear,'number');
  bid.multiple=true;ask.multiple=true;bid.accept=ask.accept='.csv,text/csv';annual.accept='.gz,application/gzip';
  function sourceFormat(){const ev=format.value==='evtradelabs_h1_json_gzip';for(const node of [annual,year]){node.disabled=!ev;node.required=ev;node.parentElement.hidden=!ev;}for(const node of [bid,ask]){node.disabled=ev;node.required=!ev;node.parentElement.hidden=ev;}}
  format.addEventListener('change',sourceFormat);sourceFormat();
  add(importForm,el('p','Solo EUR/USD H1 en UTC. Máximo 2 MiB en total. Los CSV de cada lado se ordenan por nombre; deben coincidir en fechas y no solaparse. Se guardan los originales y el período elegido; importar no ejecuta la estrategia.','subtle'),
    el('p','EV Trading Labs publica archivos anuales H1 con BID y ASK y declara agregación de Dukascopy. Su atribución se conserva en los resultados. No mezcles estos precios con CSV de ejecuciones.','subtle'));
  submit(importForm,'Conservar y verificar precios',async()=>{
    const ev=format.value==='evtradelabs_h1_json_gzip',chosen=ev?[{file:annual.files[0],side:'BOTH'}]:[
      ...Array.from(bid.files).sort((a,b)=>a.name.localeCompare(b.name)).map(file=>({file,side:'BID'})),
      ...Array.from(ask.files).sort((a,b)=>a.name.localeCompare(b.name)).map(file=>({file,side:'ASK'}))];
    if(!chosen.length||chosen.some(item=>!item.file)||chosen.reduce((total,item)=>total+item.file.size,0)>2*1024*1024)throw Error('Selecciona los archivos de precios, hasta 2 MiB en total.');
    const files=[];for(const item of chosen){const bytes=new Uint8Array(await item.file.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));files.push({name:item.file.name,side:item.side,content_base64:btoa(binary)});}
    const result=await action({action:'import_price_history',format:format.value,year:ev?Number(year.value):null,start_date:start.value,end_date:end.value,files});go('#simulacion/history-'+result.id);
  });

  const executions=panel('Contrastar informes de operaciones');
  const jforex=panel('Conciliar costes y valoración de JForex');
  if(overview.jforex_reconciliations?.reconciliations.length)add(jforex,table(['INFORME','CORTE UTC','RESULTADO DEL INFORME USD'],overview.jforex_reconciliations.reconciliations.map(r=>[link(r.file_name,'#simulacion/jforex-'+r.id),utcAt(r.cutoff),r.native_report_pnl_usd])));
  if(overview.jforex_reconciliations?.warnings.length)add(jforex,disclosure('Avisos de conciliación',overview.jforex_reconciliations.warnings));
  jforexForm(jforex);
  if(overview.execution_comparisons.comparisons.length)add(executions,table(['INFORME','ESTADO','ORIGEN DECLARADO'],overview.execution_comparisons.comparisons.map(item=>[link(item.file_name,'#simulacion/execution-'+item.id),executionStates[item.status]||item.status,item.origin])));
  if(overview.execution_comparisons.warnings.length)add(executions,disclosure('Avisos de contrastes',overview.execution_comparisons.warnings));
  executionForm(executions);
  const accounts=panel('Cuentas virtuales independientes');
  if(!overview.accounts.length)add(accounts,el('p','Todavía no hay cuentas registradas. Prepara y revisa primero un contrato.','subtle'));
  else add(accounts,table(['CUENTA / CONTRATO','CREADA','TIPO'],overview.accounts.map(account=>{const bundle=overview.bundles.find(bundle=>bundle.id===account.id);return[link(bundle?bundle.account.id+' · '+bundle.market.pair:account.id.slice(0,16),'#simulacion/account-'+account.id),at(account.created),'Virtual · sin saldo de bróker'];})));
  const bundles=panel('Paquetes de estrategia');
  if(!overview.bundles.length)add(bundles,el('p','No hay paquetes Pine preparados.','subtle'));
  else add(bundles,table(['ESTRATEGIA','PROVEEDOR / SÍMBOLO','CUENTA','VERIFICACIÓN'],overview.bundles.map(bundle=>[link(bundle.strategy.kind.toUpperCase()+' '+bundle.strategy.fast+'/'+bundle.strategy.slow,'#simulacion/bundle-'+bundle.id),bundle.market.ticker,bundle.account.id,'Compilación externa pendiente'])));
  if(overview.warnings.length)add(bundles,disclosure('Avisos de paquetes',overview.warnings));
  const prepare=panel('Preparar un contrato y su Pine'),form=el('form'),grid=el('div',null,'sim-fields');add(prepare,form);add(form,grid);
  const template=overview.contract_template,controls={};
  controls.strategy=field(grid,'Tipo de media',template.strategy.kind,'text',['sma','ema']);controls.fast=field(grid,'Ventana rápida',template.strategy.fast,'number');controls.slow=field(grid,'Ventana lenta',template.strategy.slow,'number');
  controls.pair=field(grid,'Par',template.market.pair,'text',overview.supported_pairs);controls.ticker=field(grid,'Proveedor y símbolo exactos',template.market.ticker);controls.account=field(grid,'Nombre de cuenta virtual',template.account.id);
  controls.start=field(grid,'Inicio UTC (ISO con zona)',template.period.start);controls.end=field(grid,'Fin UTC (ISO con zona)',template.period.end);controls.capital=field(grid,'Capital inicial en moneda cotizada',template.account.initial_capital);
  controls.quantity=field(grid,'Cantidad fija en unidades base',template.account.quantity);controls.cost=field(grid,'Coste proporcional por ejecución',template.account.cost_rate);
  add(form,el('p','Solo largos, D1 estándar, sin apalancamiento, ejecución en apertura de la vela siguiente. El coste 0.001 equivale a 0.1 %. La cuenta usa la moneda cotizada del par; el valor por punto del gráfico debe ser 1.','subtle'));
  submit(form,'Preparar contrato y Pine',async()=>{
    const c=structuredClone(template);c.strategy={kind:controls.strategy.value,fast:Number(controls.fast.value),slow:Number(controls.slow.value)};
    c.market.pair=controls.pair.value;c.market.ticker=controls.ticker.value.trim();c.market.quote_currency=c.market.pair.split('/')[1];c.period={start:controls.start.value.trim(),end:controls.end.value.trim()};
    c.account={id:controls.account.value.trim(),currency:c.market.quote_currency,initial_capital:controls.capital.value.trim(),quantity:controls.quantity.value.trim(),cost_rate:controls.cost.value.trim()};
    const result=await action({action:'prepare_bundle',contract:c});go('#simulacion/bundle-'+result.id);
  });
  const inbox=panel('Guardar un evento JSON aportado'),receiveForm=el('form');add(inbox,receiveForm);
  const raw=textarea(receiveForm,'Original JSON del evento','');raw.placeholder='Pega un evento tiresias_simulated_fill_v1 o tiresias_pine_fill_v1 de un contrato registrado.';
  approval(receiveForm,'He revisado la procedencia de este evento simulado. Guardarlo en el inbox no autoriza contabilizarlo.');
  submit(receiveForm,'Conservar evento en el inbox',async()=>{const result=await action({action:'receive',raw:raw.value,approve_inbox:true});go('#simulacion/receipt-'+result.receipt);});
  const receipts=panel('Últimas recepciones · hasta 200');
  if(overview.receipts.length)add(receipts,table(['RECIBIDO','ESTADO','TRANSPORTE','EJECUCIÓN'],overview.receipts.map(receipt=>[link(at(receipt.received),'#simulacion/receipt-'+receipt.id),receipt.state,receipt.transport,receipt.execution??'Sin ejecución normalizada'])));
  else add(receipts,el('p','El inbox está vacío. No hay un receptor externo conectado.','subtle'));
}
