const agents = [
  {name:"ORION", role:"Coordinador Central", glyph:"△", initials:"OR", color:"#00cfff"},
  {name:"ORION-ROBOTICS", role:"Robótica y Aprendizaje RL", glyph:"♟", initials:"RB", color:"#ff9d24"},
  {name:"ORION-SOFTWARE", role:"Ingeniería de Software", glyph:"</>", initials:"SW", color:"#00dca5"},
  {name:"ORION-SECURITY", role:"Seguridad Informática", glyph:"⬡", initials:"SE", color:"#ff526d"},
  {name:"ORION-LANGUAGES", role:"Idiomas y Traducción", glyph:"文", initials:"LA", color:"#d27bff"},
  {name:"ORION-MARKETING", role:"Mercado y Compras", glyph:"▥", initials:"MK", color:"#f4d52d"}
];
const agentList=document.querySelector("#agent-list");
const miniAgents=document.querySelector("#mini-agents");
let activeAgent=0;
let conversationCount=1;

function renderAgents(){
  agentList.innerHTML=agents.map((a,i)=>`<button class="agent-card ${i===activeAgent?'selected':''}" data-agent="${i}">
    <span class="agent-avatar" style="--accent:${a.color}">${a.initials}</span><span class="agent-glyph">${a.glyph}</span>
    <span class="agent-copy"><b>${a.name}</b><small>${a.role}</small></span><i class="dot"></i></button>`).join("");
  miniAgents.innerHTML=agents.map(a=>`<span class="mini-avatar" style="--accent:${a.color}" title="${a.name}">${a.initials}</span>`).join("");
}
function selectAgent(i){
  activeAgent=i; const a=agents[i];
  document.querySelector("#chat-agent-name").textContent=a.name;
  document.querySelector("#chat-agent-role").textContent=a.role;
  document.querySelector(".active-agent-mark").textContent=a.glyph;
  document.querySelectorAll(".assistant-message .message-meta b").forEach(x=>x.textContent=a.name);
  renderAgents();
}
renderAgents();
agentList.addEventListener("click",e=>{const b=e.target.closest("[data-agent]");if(b)selectAgent(Number(b.dataset.agent));});

function addMessage(text,who="user"){
  const messages=document.querySelector("#messages");
  const node=document.createElement("div"); node.className=`message ${who==="user"?"user-message":"assistant-message"}`;
  const safe=text.replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  if(who==="user") node.innerHTML=`<div class="message-content"><div class="message-meta"><b>● &nbsp;Tú</b><time>${new Date().toLocaleTimeString("es-AR",{hour:"2-digit",minute:"2-digit"})}</time></div>${safe}</div>`;
  else node.innerHTML=`<div class="message-avatar">${agents[activeAgent].glyph}</div><div class="message-content"><div class="message-meta"><b>${agents[activeAgent].name}</b><time>${new Date().toLocaleTimeString("es-AR",{hour:"2-digit",minute:"2-digit"})}</time></div><p>${safe}</p><p class="muted-response">Esta es una respuesta de demostración. La conexión con el agente se incorporará en la etapa de integración.</p></div>`;
  messages.appendChild(node); messages.scrollTop=messages.scrollHeight;
}
document.querySelector("#message-form").addEventListener("submit",e=>{
  e.preventDefault();const input=document.querySelector("#message-input");const value=input.value.trim();if(!value)return;
  addMessage(value,"user");input.value="";
  setTimeout(()=>addMessage(`He recibido tu mensaje. Soy ${agents[activeAgent].name} y estoy respondiendo en modo de prototipo.`,"assistant"),450);
});
document.querySelectorAll(".quick-action[data-prompt]").forEach(b=>b.addEventListener("click",()=>{document.querySelector("#message-input").value=b.dataset.prompt;document.querySelector("#message-input").focus();}));
document.querySelector("#mode-select").addEventListener("change",e=>{
  const value=e.target.value.replace("Modo ","");document.querySelector("#mode-label").textContent=value;
});
document.querySelector("#new-chat").addEventListener("click",()=>{
  conversationCount++;const list=document.querySelector("#conversation-list");const item=document.createElement("div");
  item.className="conversation-item active";item.textContent=`Nueva conversación ${conversationCount}`;item.innerHTML=`Nueva conversación ${conversationCount}<small>Ahora</small>`;
  list.querySelectorAll(".conversation-item").forEach(x=>x.classList.remove("active"));list.prepend(item);
  document.querySelector("#messages").innerHTML="";addMessage("Nueva conversación iniciada. ¿En qué puedo ayudarte?","assistant");
});
document.querySelectorAll(".nav-item").forEach(b=>b.addEventListener("click",()=>{
  document.querySelectorAll(".nav-item").forEach(x=>x.classList.remove("active"));b.classList.add("active");
  if(b.dataset.section!=="Conversación") addMessage(`La sección «${b.dataset.section}» está representada en la navegación. Su módulo funcional se desarrollará en una etapa posterior.`,"assistant");
}));
document.querySelector("#voice-button").addEventListener("click",()=>alert("Control de voz de demostración. La captura y reproducción de audio se integrarán posteriormente."));
document.querySelector("#more-actions").addEventListener("click",()=>addMessage("Acciones adicionales: adjuntos, historial, exportación y configuración se incorporarán progresivamente.","assistant"));
