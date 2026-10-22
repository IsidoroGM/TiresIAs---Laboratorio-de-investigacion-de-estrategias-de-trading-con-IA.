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

  const researchStatus={simulated:'Prueba histórica calculada',insufficient_history:'Histórico insuficiente',blocked_internal_gaps:'Bloqueado por huecos dentro de las sesiones'};
  function utcAt(value){return value?String(value).replace('T',' ').replace(/(?:\.000)?Z$/,' UTC'):'Sin fecha';}
  if(key?.startsWith('dukascopy-')){
    const identity=key.slice(10),result=await api('/api/simulation/dukascopy/'+encodeURIComponent(identity));if(token!==navigation)return;
    const box=panel('Prueba con precios Dukascopy · SMA '+result.configuration.fast+'/'+result.configuration.slow);
    add(box,notice(researchStatus[result.status]||result.status,result.status==='simulated'?'':'warn'),
      dl([['Mercado','EUR/USD · sesiones diarias UTC observadas'],['Histórico local',result.source.directory.split(/[\\/]/).pop()],['Sesiones disponibles',result.daily_sessions],['Sesiones mínimas',result.required_sessions],
          ['Capital hipotético',result.configuration.initial_capital+' USD'],['Cantidad fija',result.configuration.quantity+' EUR'],
          ['Comisión proporcional supuesta',result.configuration.assumed_commission_rate],['Originales','Contrastados al calcular; consulta de un resultado guardado']]),
      el('p','La señal usa cierres BID. Compra a ASK y vende a BID en la primera apertura observada de la siguiente sesión. Se conservan domingos y días parciales.','subtle'));
    if(result.missing_sessions)add(box,notice('Faltan '+result.missing_sessions+' sesiones observadas para evaluar este cruce. No se publican operaciones ni rentabilidad.','warn'));
    if(!result.source.all_final_transports_https)add(box,notice('Los archivos originales llegaron mediante una redirección HTTP. Sus huellas se han contrastado, pero el transporte final no autentica su origen.','warn'));
    add(box,el('p','El spread ya está incluido en los precios de compra y venta. La comisión es una hipótesis elegida para esta prueba; no se modelan deslizamiento, swaps ni liquidez.','subtle'));
    if(result.summary){
      const s=result.summary,metrics=panel('Resultado hipotético en este histórico');
      add(metrics,dl([['Patrimonio final',fmt(s.final_equity)+' USD'],['Variación',fmt(s.return_percent)+' %'],['Operaciones cerradas',s.closed_trades],
        ['Posición abierta',s.open_quantity+' EUR'],['Comisiones supuestas',fmt(s.assumed_commissions)+' USD'],
        ['Máxima caída observada',fmt(s.max_observed_drawdown_percent)+' %'],['Última valoración',utcAt(s.last_valuation_at)]]));
      if(result.equity_curve.length)add(metrics,chart(result.equity_curve.map(point=>({...point,date:point.at})),'equity','USD'));
    }
    const fills=panel('Operaciones hipotéticas');
    if(result.hypothetical_fills.length){const list=el('div');add(fills,list);paginate(list,result.hypothetical_fills,rows=>table(['SEÑAL UTC','EJECUCIÓN OBSERVADA UTC','LADO','UNIDADES EUR','PRECIO USD/EUR','COMISIÓN SUPUESTA USD'],rows.map(fill=>[
      utcAt(fill.signal_at),utcAt(fill.executed_at),fill.side==='buy'?'Compra · ASK':'Venta · BID',fill.quantity,fill.price,fill.assumed_commission])));}
    else add(fills,el('p',result.status==='simulated'?'No hay operaciones en esta prueba.':'No se han simulado operaciones con estos datos.','subtle'));
    if(result.pending_order)add(fills,notice('Queda una señal pendiente. No se inventa una ejecución posterior al último precio disponible.','warn'));
    if(result.rejected_orders.length)add(fills,disclosure('Órdenes rechazadas en el cálculo',result.rejected_orders));
    add(box,download('Descargar resultado JSON','dukascopy-'+identity+'.json',JSON.stringify(result,null,2)),disclosure('Procedencia y reglas',result.source),disclosure('Resultado completo',result));
    return;
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

  const research=panel('Precios Dukascopy y prueba con spread'),data=overview.dukascopy;
  add(research,el('p','SMA 20/60 sobre sesiones diarias UTC de EUR/USD. El cálculo conserva el resultado y no modifica cuentas virtuales. Esta pantalla utiliza los históricos locales ya preparados.','subtle'));
  if(data.datasets.length){
    const form=el('form'),grid=el('div',null,'sim-fields');add(research,form);add(form,grid);
    const dataset=field(grid,'Histórico preparado',data.datasets[0].id,'text',data.datasets.map(item=>item.id));
    [...dataset.options].forEach((option,index)=>{const item=data.datasets[index];option.textContent=item.first_month+' → '+item.last_month+' · '+item.daily_sessions+' sesiones · '+item.id;});
    const capital=field(grid,'Capital hipotético (USD)','1000'),quantity=field(grid,'Cantidad fija (EUR)','1'),commission=field(grid,'Comisión proporcional supuesta','');
    commission.placeholder='Ejemplo: 0.001 equivale a 0.1 %';
    const readiness=el('div');add(form,readiness);
    function available(){const item=data.datasets.find(item=>item.id===dataset.value);readiness.replaceChildren(notice(item.missing_sessions?'Hay '+item.daily_sessions+' sesiones; faltan '+item.missing_sessions+' para SMA 20/60. Puedes verificar los originales y guardar el diagnóstico.':'Hay suficiente longitud para calcular. Se verificarán los originales antes de ejecutar.',item.missing_sessions?'warn':''));}
    dataset.addEventListener('change',available);available();
    add(form,el('p','Indica una comisión supuesta con punto decimal. Cero permite un ensayo sin comisión y no confirma la tarifa del proveedor. El spread se incorpora mediante BID/ASK; no se modelan swaps ni deslizamiento.','subtle'));
    submit(form,'Verificar datos y calcular',async()=>{const result=await action({action:'simulate_dukascopy',dataset:dataset.value,capital:capital.value.trim(),quantity:quantity.value.trim(),commission_rate:commission.value.trim()});go('#simulacion/dukascopy-'+result.id);});
  }else add(research,el('p','Todavía no hay históricos locales preparados. Al preparar uno, aparecerá aquí.','subtle'));
  if(data.runs.length)add(research,el('h3','Resultados guardados'),table(['RESULTADO','SESIONES','PATRIMONIO HIPOTÉTICO'],data.runs.map(run=>[
    link(researchStatus[run.status]||run.status,'#simulacion/dukascopy-'+run.id),run.daily_sessions,run.summary?fmt(run.summary.final_equity)+' USD':'Sin métricas: faltan datos'])));
  if(data.warnings.length)add(research,disclosure('Avisos de históricos',data.warnings));

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
