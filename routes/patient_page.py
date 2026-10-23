"""Página do Paciente — HTML self-contained servido em /paciente.

Acesso por código (OTP) no WhatsApp; mostra resumo do quadro, exames (com gráfico
de tendência dos valores numéricos), medicações e um espaço para o paciente
registrar como está se sentindo. Usa só a API do próprio SIAP (mesma origem).
"""

from flask import Blueprint, Response

patient_page_bp = Blueprint("patient_page", __name__)

_PAGE = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Meu Portal — Área do Paciente</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root{--verde:#003030;--dourado:#B08030;--cinza:#667;--bg:#f4f6f6;--card:#fff;--borda:#e3e7e7}
  *{box-sizing:border-box}
  body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:var(--bg);color:#1b2323}
  header{background:var(--verde);color:#fff;padding:14px 18px;display:flex;align-items:center;gap:10px}
  header b{font-size:18px;letter-spacing:.3px}
  header span{color:#d9c79a;font-size:12px}
  .wrap{max-width:920px;margin:0 auto;padding:18px}
  .card{background:var(--card);border:1px solid var(--borda);border-radius:14px;padding:16px 18px;margin:14px 0;box-shadow:0 1px 3px rgba(0,0,0,.04)}
  h2{margin:0 0 10px;font-size:16px;color:var(--verde)}
  label{display:block;font-size:13px;color:var(--cinza);margin:10px 0 4px}
  input,textarea,select{width:100%;padding:11px 12px;border:1px solid var(--borda);border-radius:10px;font-size:15px}
  button{background:var(--verde);color:#fff;border:0;border-radius:10px;padding:12px 16px;font-size:15px;font-weight:600;cursor:pointer;margin-top:12px}
  button:disabled{opacity:.55;cursor:default}
  .row{display:flex;gap:12px;flex-wrap:wrap}
  .row>div{flex:1;min-width:140px}
  .muted{color:var(--cinza);font-size:13px}
  .pill{display:inline-block;background:#eef4f4;color:var(--verde);border-radius:999px;padding:3px 10px;font-size:12px;margin:2px 4px 2px 0}
  .item{border-top:1px solid var(--borda);padding:10px 0}
  .item:first-child{border-top:0}
  .item b{display:block;font-size:14px}
  .erro{background:#fdecec;color:#a11;border:1px solid #f3c9c9;border-radius:10px;padding:10px 12px;font-size:14px}
  .ok{background:#eafaf0;color:#17623b;border:1px solid #bfe8cf;border-radius:10px;padding:10px 12px;font-size:14px}
  .hide{display:none}
  canvas{max-height:260px}
  .chips{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 4px}
  .chip{border:1px solid var(--borda);background:#fff;color:var(--verde);border-radius:999px;padding:12px 16px;font-size:15px;font-weight:600;cursor:pointer;margin:0}
  .chip.on{background:var(--verde);color:#fff;border-color:var(--verde)}
  .regua{border:1px solid var(--borda);border-radius:12px;padding:10px 12px;margin:8px 0}
  .regua .top{display:flex;justify-content:space-between;align-items:center;font-size:14px}
  .regua input[type=range]{width:100%;height:34px}
  .face{color:var(--cinza);font-size:13px}
  button.ghost{background:#fff;color:var(--verde);border:1px solid var(--verde)}
  button.rec{background:#a11;border-color:#a11}

</style>
</head>
<body>
<header>
  <div style="width:34px;height:34px;border-radius:8px;background:var(--dourado);display:flex;align-items:center;justify-content:center;font-weight:800;color:#003030">V</div>
  <div><b>Meu Portal</b><br><span>Área do paciente · Instituto Vittalis</span></div>
</header>

<div class="wrap">
  <div id="msg"></div>

  <!-- LOGIN -->
  <div id="login" class="card">
    <h2>Acessar meu portal</h2>
    <p class="muted">Informe seu CPF e enviaremos um código de acesso no seu WhatsApp.</p>
    <label>CPF</label>
    <input id="cpf" inputmode="numeric" placeholder="000.000.000-00" autocomplete="off">
    <button id="btnPedir">Receber código no WhatsApp</button>
    <div id="passo2" class="hide">
      <label>Código recebido</label>
      <input id="codigo" inputmode="numeric" placeholder="000000" autocomplete="one-time-code">
      <button id="btnEntrar">Entrar</button>
    </div>
  </div>

  <!-- PORTAL -->
  <div id="portal" class="hide">
    <div class="card">
      <h2 id="saudacao">Olá</h2>
      <div id="resumo"></div>
    </div>

    <div class="card">
      <h2>Como estou hoje</h2>
      <p class="muted">Toque no que voce esta sentindo e ajuste de 0 a 10. Leva segundos.</p>
      <div id="chips" class="chips"></div>
      <div id="reguas"></div>
      <label>Quer contar mais? (opcional)</label>
      <textarea id="regObs" rows="2" placeholder="Como voce esta se sentindo..."></textarea>
      <div class="row" style="margin-top:10px">
        <div><button id="btnReg">Salvar</button></div>
        <div><button id="btnAudio" class="ghost" type="button">Falar em vez de escrever</button></div>
      </div>
      <div id="audioBox"></div>
      <div id="historicoCheckin" style="margin-top:14px"></div>
    </div>

    <div class="card">
      <h2>Exames e tendência</h2>
      <div id="graficoBox" class="hide"><canvas id="grafico"></canvas></div>
      <div id="exames"></div>
    </div>

    <div class="card">
      <h2>Minhas medicações</h2>
      <div id="medicacoes"></div>
    </div>

    <div class="card">
      <h2>Escalas de acompanhamento</h2>
      <p class="muted">Responda você mesmo(a). As respostas ficam disponíveis para o seu profissional de saúde.</p>
      <div id="rastreiosCatalogo"></div>
      <div id="rastreioArea" class="hide"></div>
      <div id="rastreioResultado"></div>
      <h2 style="margin-top:16px">Histórico</h2>
      <div id="rastreioHistorico"></div>
    </div>
  </div>
</div>

<script>
const API = "/api";
let token = null, cpfAtual = "";

function el(id){return document.getElementById(id)}
function show(id){el(id).classList.remove("hide")}
function hide(id){el(id).classList.add("hide")}
function msg(txt, tipo){const c=el("msg"); c.innerHTML = txt ? '<div class="'+(tipo||"ok")+'">'+txt+'</div>' : ""}

async function api(path, opts){
  opts = opts || {};
  opts.headers = Object.assign({"Content-Type":"application/json"}, opts.headers||{});
  if(token) opts.headers["Authorization"] = "Bearer "+token;
  const r = await fetch(API+path, opts);
  const txt = await r.text();
  let data; try{data = JSON.parse(txt)}catch(e){data={raw:txt}}
  if(!r.ok) throw new Error((data && (data.error||data.message)) || ("Erro "+r.status));
  return data;
}

el("btnPedir").onclick = async () => {
  cpfAtual = el("cpf").value;
  if(cpfAtual.replace(/\D/g,"").length!==11){ msg("Informe um CPF válido (11 dígitos).","erro"); return; }
  el("btnPedir").disabled = true; msg("");
  try{
    const d = await api("/patient-auth/otp/request",{method:"POST",body:JSON.stringify({cpf:cpfAtual})});
    msg(d.message||"Código enviado no WhatsApp.","ok"); show("passo2");
  }catch(e){ msg(e.message,"erro"); }
  el("btnPedir").disabled = false;
};

el("btnEntrar").onclick = async () => {
  el("btnEntrar").disabled = true; msg("");
  try{
    const d = await api("/patient-auth/otp/verify",{method:"POST",body:JSON.stringify({cpf:cpfAtual,codigo:el("codigo").value})});
    token = d.access_token; hide("login"); show("portal"); carregar();
  }catch(e){ msg(e.message,"erro"); }
  el("btnEntrar").disabled = false;
};

el("btnReg").onclick = async () => {
  const nomes = Object.keys(selSintomas);
  const obs = (el("regObs").value||"").trim();
  if(!nomes.length && !obs){ msg("Toque em um sintoma ou escreva algo.","erro"); return; }
  el("btnReg").disabled = true;
  try{
    const sintomas = nomes.map(n => ({nome:n, intensidade: selSintomas[n]}));
    const d = await api("/patient-portal/me/checkin",{method:"POST", body:JSON.stringify({sintomas:sintomas, observacao: obs||null})});
    msg(d.message || "Registrado. Obrigado!","ok");
    selSintomas = {}; el("regObs").value="";
    renderChips(); renderReguas(); carregarCheckin();
  }catch(e){ msg(e.message,"erro"); }
  el("btnReg").disabled = false;
};

function fmtBR(s){ if(!s) return ""; const d=new Date(s); return isNaN(d)?s:d.toLocaleDateString("pt-BR"); }

async function carregar(){
  try{
    const me = await api("/patient-portal/me");
    const p = me.paciente || me;
    el("saudacao").textContent = "Olá, " + ((p.nome||"").split(" ")[0] || "");
    const linhas = [];
    if(p.data_nascimento) linhas.push("Nascimento: "+fmtBR(p.data_nascimento));
    if(p.condicao_medica || p.diagnostico) linhas.push("<b>Quadro:</b> "+(p.condicao_medica||p.diagnostico));
    if(p.composicao) linhas.push("<b>Tratamento:</b> "+p.composicao);
    if(p.dosagem) linhas.push("<b>Dosagem:</b> "+p.dosagem);
    if(p.horarios) linhas.push("<b>Horários:</b> "+p.horarios);
    el("resumo").innerHTML = linhas.length? linhas.map(l=>"<div class='muted' style='margin:4px 0'>"+l+"</div>").join("") : "<p class='muted'>Sem resumo cadastrado ainda.</p>";
  }catch(e){ msg("Não foi possível carregar seus dados: "+e.message,"erro"); }

  // exames
  try{
    const d = await api("/patient-portal/me/exames");
    const ex = d.exames||[];
    if(!ex.length){ el("exames").innerHTML = "<p class='muted'>Nenhum exame registrado ainda.</p>"; }
    else{
      el("exames").innerHTML = ex.map(e=>{
        const nome = e.titulo || e.tipo_exame || "Exame";
        const val = (e.tipo_exame==="numerico" && e.valor!=null)? " — <b>"+e.valor+(e.unidade?(" "+e.unidade):"")+"</b>" : "";
        const desc = e.descricao? "<div class='muted' style='white-space:pre-wrap'>"+e.descricao+"</div>" : "";
        return "<div class='item'><b>"+nome+"</b><span class='muted'>"+(e.data_exame?fmtBR(e.data_exame)+" · ":"")+[e.tipo_exame] .filter(Boolean).join("")+"</span>"+val+desc+"</div>";
      }).join("");
      // gráfico: séries numéricas
      const num = ex.filter(e=>e.tipo_exame==="numerico" && e.valor!=null).sort((a,b)=>new Date(a.data_exame)-new Date(b.data_exame));
      if(num.length>=2){
        const titulos = [...new Set(num.map(e=>e.titulo))];
        const cores = ["#003030","#B08030","#2b7a78","#a11","#5b3fa1","#17623b"];
        const ds = titulos.map((t,i)=>({
          label:t, borderColor:cores[i%cores.length], backgroundColor:cores[i%cores.length],
          data: num.filter(e=>e.titulo===t).map(e=>({x:e.data_exame,y:e.valor})), tension:.25
        }));
        show("graficoBox");
        new Chart(el("grafico"),{type:"line",data:{datasets:ds},options:{
          responsive:true, parsing:false, scales:{x:{type:"time",time:{unit:"month"},title:{display:true,text:"Data"}},y:{title:{display:true,text:"Valor"}}},
          plugins:{legend:{position:"bottom"}}}});
      }
    }
  }catch(e){ el("exames").innerHTML = "<p class='muted'>Exames indisponíveis no momento.</p>"; }

  // medicações
  try{
    const d = await api("/patient-portal/me/prescricoes");
    const pr = d.prescricoes||[];
    el("medicacoes").innerHTML = pr.length? pr.map(x=>{
      const nome = x.medicamento || x.produto || x.descricao || "Prescrição";
      const pos = x.posologia? "<div class='muted'>"+x.posologia+"</div>":"";
      return "<div class='item'><b>"+nome+"</b>"+pos+"</div>";
    }).join("") : "<p class='muted'>Nenhuma medicação registrada ainda.</p>";
  }catch(e){ el("medicacoes").innerHTML = "<p class='muted'>Medicações indisponíveis no momento.</p>"; }

  carregarRastreios();
  carregarCatalogoCheckin();
  carregarCheckin();
}

let rastreioCatalogo = {}, rastreioAtual = null;

function nivelClasse(n){ return "pill"; }

async function carregarRastreios(){
  try{
    const d = await api("/patient-portal/me/rastreios");
    rastreioCatalogo = {};
    (d.catalogo||[]).forEach(c => { rastreioCatalogo[c.chave] = c; });
    const cat = d.catalogo || [];
    el("rastreiosCatalogo").innerHTML = cat.length ? cat.map(c => {
      const aviso = (c.publico === "responsavel")
        ? "<div class='muted' style='margin:4px 0'>"+ (c.aviso || "Este questionário deve ser respondido pelo pai/mãe/responsável, pensando na criança.") +" <span class='pill'>respondido pelo responsável</span></div>"
        : "";
      return "<div class='item'><b>"+c.nome+"</b>"+
      "<span class='muted'>"+c.descricao+" · "+c.n_itens+" itens</span>"+
      aviso+
      "<button data-tipo='"+c.chave+"' class='btnRastreio'>Responder agora</button></div>";
    }).join("") : "<p class='muted'>Nenhuma escala disponível no momento.</p>";
    document.querySelectorAll(".btnRastreio").forEach(b => {
      b.onclick = () => abrirRastreio(b.getAttribute("data-tipo"));
    });
    renderHistoricoRastreios(d.historico||[]);
  }catch(e){
    el("rastreiosCatalogo").innerHTML = "<p class='muted'>Escalas indisponíveis no momento.</p>";
  }
}

function renderHistoricoRastreios(hist){
  if(!hist.length){ el("rastreioHistorico").innerHTML = "<p class='muted'>Nenhum resultado registrado ainda.</p>"; return; }
  el("rastreioHistorico").innerHTML = hist.map(h => {
    const nivel = h.nivel_label || h.nivel || "";
    const pontos = (h.pontuacao_total === null || h.pontuacao_total === undefined)
      ? "Desatenção: <b>"+(h.pontos_desatencao ?? 0)+"</b>/9 · Hiperatividade: <b>"+(h.pontos_hiperatividade ?? 0)+"</b>/9"
      : "Pontuação: <b>"+h.pontuacao_total+"</b>/"+(h.pontuacao_maxima||"");
    return "<div class='item'><b>"+(h.nome||h.tipo)+"</b>"+
      "<span class='muted'>"+(h.data_realizacao?fmtBR(h.data_realizacao)+" · ":"")+
      pontos+"</span>"+
      "<div><span class='"+nivelClasse(h.nivel)+"'>"+nivel+"</span></div></div>";
  }).join("");
}

async function abrirRastreio(tipo){
  el("rastreioResultado").innerHTML = "";
  el("rastreioArea").innerHTML = "<p class='muted'>Carregando...</p>";
  show("rastreioArea");
  try{
    const d = await api("/patient-portal/me/rastreios/"+encodeURIComponent(tipo));
    rastreioAtual = { dados:d, respostas:{}, idx:0 };
    renderPerguntaRastreio();
  }catch(e){
    el("rastreioArea").innerHTML = "<div class='erro'>"+e.message+"</div>";
  }
}

function renderPerguntaRastreio(){
  const s = rastreioAtual;
  const pergunta = s.dados.perguntas[s.idx];
  const total = s.dados.perguntas.length;
  const opcoes = s.dados.opcoes.map(o =>
    "<label style='display:flex;justify-content:space-between;align-items:center;border:1px solid var(--borda);border-radius:10px;padding:10px 12px;margin:6px 0;cursor:pointer'>"+
    "<span>"+o.label+"</span><input type='radio' name='rastreioOpt' value='"+o.valor+"' "+
    (s.respostas[pergunta.campo]===o.valor?"checked":"")+"></label>"
  ).join("");
  const ultimo = s.idx === total-1;
  el("rastreioArea").innerHTML =
    "<div class='muted' style='margin-bottom:8px'>"+s.dados.nome+" · Item "+(s.idx+1)+" de "+total+"</div>"+
    "<div class='item'><b>"+pergunta.numero+". "+pergunta.texto+"</b></div>"+
    "<div class='muted' style='margin:6px 0 10px'>"+s.dados.instrucoes+"</div>"+
    "<div id='rastreioOpcoes'>"+opcoes+"</div>"+
    "<div class='row' style='margin-top:12px'>"+
    (s.idx>0?"<div><button id='btnRastreioVoltar' style='background:#667'>Voltar</button></div>":"")+
    "<div><button id='btnRastreioProx'>"+(ultimo?"Enviar respostas":"Próxima")+"</button></div>"+
    "<div><button id='btnRastreioCancelar' style='background:#667'>Cancelar</button></div>"+
    "</div>";

  document.querySelectorAll("input[name='rastreioOpt']").forEach(r => {
    r.onchange = () => { s.respostas[pergunta.campo] = parseInt(r.value); };
  });
  if(s.idx>0) el("btnRastreioVoltar").onclick = () => { s.idx--; renderPerguntaRastreio(); };
  el("btnRastreioCancelar").onclick = () => { rastreioAtual = null; hide("rastreioArea"); el("rastreioArea").innerHTML=""; };
  el("btnRastreioProx").onclick = () => {
    if(s.respostas[pergunta.campo]===undefined){ msg("Escolha uma opção para continuar.","erro"); return; }
    if(!ultimo){ s.idx++; renderPerguntaRastreio(); return; }
    enviarRastreio();
  };
}

async function enviarRastreio(){
  const s = rastreioAtual;
  if(!s) return;
  if(s.dados.perguntas.some(p => s.respostas[p.campo]===undefined)){ msg("Responda todos os itens.","erro"); return; }
  const btn = el("btnRastreioProx");
  if(btn) btn.disabled = true;
  try{
    const d = await api("/patient-portal/me/rastreios/"+encodeURIComponent(s.dados.chave),{
      method:"POST", body:JSON.stringify(s.respostas)
    });
    const r = d.resultado || {};
    const corpo = (r.pontos_desatencao !== undefined || r.pontos_hiperatividade !== undefined)
      ? "Desatenção: <b>"+(r.pontos_desatencao ?? 0)+"</b> de 9<br>"+
        "Hiperatividade/Impulsividade: <b>"+(r.pontos_hiperatividade ?? 0)+"</b> de 9<br>"+
        "Nível: <b>"+(r.nivel_label||r.nivel||"")+"</b>"
      : "Pontuação: <b>"+r.pontuacao_total+"</b>/"+(r.pontuacao_maxima||"")+"<br>"+
        "Nível: <b>"+(r.nivel_label||r.nivel||"")+"</b>";
    el("rastreioResultado").innerHTML =
      "<div class='ok' style='margin-top:12px'><b>Resultado — "+s.dados.nome+"</b><br>"+
      corpo+"</div>";
    rastreioAtual = null;
    hide("rastreioArea");
    el("rastreioArea").innerHTML = "";
    msg("Respostas enviadas. Obrigado!","ok");
    carregarRastreios();
  }catch(e){
    msg(e.message,"erro");
    if(btn) btn.disabled = false;
  }
}
/* ===== Check-in de 1 toque + observacao por audio ===== */
const SINTOMAS_PADRAO = ["Dor","Ansiedade","Insônia","Depressão"];
let catalogoSintomas = SINTOMAS_PADRAO.slice();
let selSintomas = {};
let mediaRec = null, audioChunks = [], audioTimer = null;

function faceEmoji(v){ if(v<=2) return "😌"; if(v<=4) return "🙂"; if(v<=6) return "😕"; if(v<=8) return "😣"; return "😖"; }

function renderChips(){
  const box = el("chips"); if(!box) return;
  box.innerHTML = catalogoSintomas.map(function(n){
    return "<button type='button' class='chip"+(selSintomas[n]!==undefined?" on":"")+"' data-s='"+n+"'>"+n+"</button>";
  }).join("");
  document.querySelectorAll(".chip").forEach(function(b){
    b.onclick = function(){
      const n = b.getAttribute("data-s");
      if(selSintomas[n]!==undefined){ delete selSintomas[n]; } else { selSintomas[n] = 5; }
      renderChips(); renderReguas();
    };
  });
}

function renderReguas(){
  const box = el("reguas"); if(!box) return;
  const nomes = Object.keys(selSintomas);
  box.innerHTML = nomes.map(function(n,i){
    return "<div class='regua'><div class='top'><b>"+n+"</b><span id='valr_"+i+"' class='face'>"+selSintomas[n]+" "+faceEmoji(selSintomas[n])+"</span></div>"+
           "<input type='range' min='0' max='10' step='1' value='"+selSintomas[n]+"' data-r='"+n+"' data-i='"+i+"'></div>";
  }).join("");
  document.querySelectorAll("#reguas input[type=range]").forEach(function(r){
    r.oninput = function(){
      const n = r.getAttribute("data-r"), i = r.getAttribute("data-i");
      selSintomas[n] = parseInt(r.value);
      const sp = el("valr_"+i); if(sp) sp.textContent = selSintomas[n]+" "+faceEmoji(selSintomas[n]);
    };
  });
}

async function carregarCatalogoCheckin(){
  try{
    const d = await api("/patient-portal/me/sintomas-catalogo");
    if(d && d.sintomas && d.sintomas.length) catalogoSintomas = d.sintomas;
  }catch(e){}
  renderChips(); renderReguas();
}

async function carregarCheckin(){
  try{
    const d = await api("/patient-portal/me/checkin/resumo");
    const streak = d.streak||0;
    const regs = d.registros||[];
    const topo = streak>0 ? "<div class='ok' style='margin-bottom:8px'>"+streak+" dia(s) seguido(s) de registro. Continue!</div>" : "";
    const itens = regs.slice(0,6).map(function(r){
      const q = r.sintoma ? ("<b>"+r.sintoma+"</b>"+(r.intensidade!=null?(" — "+r.intensidade+"/10"):"")) : "";
      const o = r.observacao ? ("<div class='muted'>"+String(r.observacao).replace(/</g,"&lt;")+"</div>") : "";
      return "<div class='item'>"+q+"<span class='muted'>"+(r.data?fmtBR(r.data)+" · ":"")+"</span>"+o+"</div>";
    }).join("");
    el("historicoCheckin").innerHTML = topo + (itens || "<p class='muted'>Sem registros ainda.</p>");
  }catch(e){ var h=el("historicoCheckin"); if(h) h.innerHTML=""; }
}

function audioMsg(txt,tipo){ var b=el("audioBox"); if(b) b.innerHTML = txt ? ("<div class='"+(tipo||"ok")+"'>"+txt+"</div>") : ""; }

el("btnAudio").onclick = async () => {
  if(mediaRec && mediaRec.state === "recording"){ mediaRec.stop(); return; }
  if(!navigator.mediaDevices || !window.MediaRecorder){ audioMsg("Seu navegador nao permite gravar audio aqui. Use o campo de texto.","erro"); return; }
  try{
    const stream = await navigator.mediaDevices.getUserMedia({audio:true});
    audioChunks = [];
    mediaRec = new MediaRecorder(stream);
    mediaRec.ondataavailable = function(e){ if(e.data && e.data.size) audioChunks.push(e.data); };
    mediaRec.onstop = function(){
      stream.getTracks().forEach(function(t){t.stop();});
      el("btnAudio").textContent = "Falar em vez de escrever";
      el("btnAudio").classList.remove("rec");
      clearTimeout(audioTimer);
      enviarAudio(new Blob(audioChunks, {type: mediaRec.mimeType || "audio/webm"}));
    };
    mediaRec.start(); audioChunks = [];
    el("btnAudio").textContent = "Parar e enviar";
    el("btnAudio").classList.add("rec");
    audioMsg("Gravando... fale como esta se sentindo.","ok");
    audioTimer = setTimeout(function(){ if(mediaRec && mediaRec.state==="recording"){ audioMsg("Limite de 60s atingido. Enviando...","ok"); mediaRec.stop(); } }, 60000);
  }catch(e){ audioMsg("Nao foi possivel acessar o microfone. Verifique a permissao do navegador.","erro"); }
};

async function enviarAudio(blob){
  audioMsg("Transcrevendo... aguarde.","ok");
  try{
    const fd = new FormData();
    fd.append("audio", blob, "observacao.webm");
    const r = await fetch(API+"/patient-portal/me/observacao-audio", {method:"POST", headers: token?{Authorization:"Bearer "+token}:{}, body: fd});
    const txt = await r.text(); let d; try{d=JSON.parse(txt)}catch(e){d={raw:txt}}
    if(!r.ok) throw new Error((d && d.error) || ("Erro "+r.status));
    const texto = (d.texto||"").trim();
    el("audioBox").innerHTML =
      "<label>Confirme o que entendi (pode editar):</label>"+
      "<textarea id='audioTxt' rows='3'>"+texto.replace(/</g,"&lt;")+"</textarea>"+
      "<div class='row'><div><button id='audioSalvar'>Salvar observacao</button></div>"+
      "<div><button id='audioDescartar' class='ghost' type='button'>Descartar</button></div></div>";
    el("audioSalvar").onclick = async () => {
      const t = el("audioTxt").value.trim();
      if(!t){ audioMsg("Nada para salvar.","erro"); return; }
      el("audioSalvar").disabled = true;
      try{
        await api("/patient-portal/me/registro",{method:"POST", body:JSON.stringify({observacao:t})});
        audioMsg("Observacao salva. Obrigado!","ok");
        carregarCheckin();
      }catch(e){ audioMsg(e.message,"erro"); el("audioSalvar").disabled=false; }
    };
    el("audioDescartar").onclick = function(){ audioMsg(""); };
  }catch(e){
    audioMsg(e.message + " Use o campo de texto como alternativa.","erro");
  }
}

</script>
</body>
</html>"""


@patient_page_bp.route("/paciente", methods=["GET"])
def patient_page():
    return Response(_PAGE, mimetype="text/html; charset=utf-8")
