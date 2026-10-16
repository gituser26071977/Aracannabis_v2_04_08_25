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
      <div class="row">
        <div>
          <label>Sintoma / observação</label>
          <input id="regSintoma" placeholder="Ex.: dor, sono, ansiedade...">
        </div>
        <div style="max-width:150px">
          <label>Intensidade (0–10)</label>
          <input id="regInt" type="number" min="0" max="10" value="5">
        </div>
      </div>
      <label>Detalhes (opcional)</label>
      <textarea id="regObs" rows="3" placeholder="Conte como está se sentindo..."></textarea>
      <button id="btnReg">Registrar</button>
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
  el("btnReg").disabled = true;
  try{
    await api("/patient-portal/me/registro",{method:"POST",body:JSON.stringify({
      sintoma: el("regSintoma").value, intensidade: parseInt(el("regInt").value||"0"),
      observacao: el("regObs").value
    })});
    msg("Registro enviado. Obrigado!","ok");
    el("regSintoma").value=""; el("regObs").value="";
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
}
</script>
</body>
</html>"""


@patient_page_bp.route("/paciente", methods=["GET"])
def patient_page():
    return Response(_PAGE, mimetype="text/html; charset=utf-8")
