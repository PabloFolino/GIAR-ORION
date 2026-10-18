# -*- coding: utf-8 -*-
"""G1-RAG-07: prueba ampliada de robustez del router, independiente de producción.
Ejecutar desde la raíz del proyecto:
    python Tests\\test_g1_rag07_router_robustness.py
No modifica main.py ni Agent/MultilingualKnowledgeRetriever.py.
"""
from __future__ import annotations
import argparse, csv, importlib.util, json, re, sys, time
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

# Casos ampliados. acceptable_routes permite consultas genuinamente híbridas/ambiguas.
CASES = [
("R07-01","Enumerá las seis articulaciones de la pierna izquierda con sus nombres exactos.",["identifier"],"identifier",["left_hip_pitch_joint","left_hip_roll_joint","left_hip_yaw_joint","left_knee_joint","left_ankle_pitch_joint","left_ankle_roll_joint"]),
("R07-02","¿Qué joints corresponden a la pierna izquierda del G1? Lista los identificadores.",["identifier"],"identifier",["left_hip_pitch_joint","left_hip_roll_joint","left_hip_yaw_joint","left_knee_joint","left_ankle_pitch_joint","left_ankle_roll_joint"]),
("R07-03","Dame waist_yaw_joint, waist_roll_joint y waist_pitch_joint en el orden del bloque actuator del MJCF.",["structured","identifier"],"hybrid",["waist_yaw_joint","waist_roll_joint","waist_pitch_joint"]),
("R07-04","¿Cuáles son las tres articulaciones de la cintura? No necesito el orden del XML.",["identifier"],"identifier",["waist_yaw_joint","waist_roll_joint","waist_pitch_joint"]),
("R07-05","¿Qué sensores IMU aparecen en el MJCF y qué mide cada uno?",["identifier","semantic"],"hybrid",["imu-torso-angular-velocity","imu-torso-linear-acceleration","imu-pelvis-angular-velocity","imu-pelvis-linear-acceleration"]),
("R07-06","Explicá la diferencia entre el sitio imu_in_torso y el sensor imu-torso-angular-velocity.",["identifier","semantic"],"hybrid",["imu_in_torso","imu-torso-angular-velocity"]),
("R07-07","¿Qué diferencia conceptual hay entre un site y un sensor en MJCF?",["semantic"],"semantic",["site","sensor"]),
("R07-08","Listá las siete articulaciones de la mano derecha con los nombres exactos.",["identifier"],"identifier",["right_hand_thumb_0_joint","right_hand_thumb_1_joint","right_hand_thumb_2_joint","right_hand_index_0_joint","right_hand_index_1_joint","right_hand_middle_0_joint","right_hand_middle_1_joint"]),
("R07-09","¿Cuántos actuadores hay y cuáles son, en el orden exacto en que aparecen en actuator?",["structured"],"structured",[]),
("R07-10","Extraé del XML la secuencia de actuadores, sin resumirla.",["structured"],"structured",[]),
("R07-11","¿Qué función cumple la recompensa durante el aprendizaje por refuerzo?",["semantic"],"semantic",["recompensa","aprendizaje"]),
("R07-12","Explicá la relación entre política del agente y función de valor en RL.",["semantic"],"semantic",["política","valor"]),
("R07-13","Buscá en el dossier el identificador right_hand_index_1_joint.",["identifier"],"identifier",["right_hand_index_1_joint"]),
("R07-14","¿Dónde está definido imu-pelvis-linear-acceleration y qué representa?",["identifier","semantic"],"hybrid",["imu-pelvis-linear-acceleration"]),
("R07-15","Quiero comprender cómo el agente decide una acción a partir de las observaciones, no los nombres de las articulaciones.",["semantic"],"semantic",["observaciones","acción"]),
("R07-16","¿Cuáles son los nombres exactos de los joints del brazo izquierdo?",["identifier"],"identifier",["left_shoulder_pitch_joint","left_shoulder_roll_joint","left_shoulder_yaw_joint","left_elbow_joint","left_wrist_roll_joint","left_wrist_pitch_joint","left_wrist_yaw_joint"]),
("R07-17","¿Qué orden tienen los actuadores de la cintura en el XML?",["structured","identifier"],"hybrid",["waist_yaw_joint","waist_roll_joint","waist_pitch_joint"]),
("R07-18","Compará la función de recompensa con la política de un agente SAC.",["semantic"],"semantic",["recompensa","política"]),
("R07-19","Buscá el nombre imu_in_pelvis y decime si es sensor o site.",["identifier","semantic"],"hybrid",["imu_in_pelvis"]),
("R07-20","Extrae todos los actuadores de g1_29dof_with_hand.xml y comprueba si son 43.",["structured"],"structured",[]),
]

def load_module(path):
    spec=importlib.util.spec_from_file_location("g1_rag07_retriever",path)
    if spec is None or spec.loader is None: raise RuntimeError(f"No se pudo cargar {path}")
    mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod); return mod

def route_query(query):
    q=query.casefold()
    structured=(r"\b\d+\s+actuadores\b",r"\borden exacto\b",r"\bbloque\s+actuator\b",r"\bextra[eé]\b.*\b(xml|mjcf|actuadores)\b",r"\bsecuencia\b.*\bactuadores\b",r"\borden\b.*\bactuadores\b",r"\bactuadores\b.*\bxml\b")
    if any(re.search(p,q) for p in structured): return "structured"
    identifiers=("_joint","_in_","imu-","identificador","nombres exactos","lista los identificadores","nombres de los joints","nombre exacto","articulaciones de la","articulaciones de","buscá en el dossier","busca en el dossier")
    if any(s in q for s in identifiers): return "identifier"
    return "semantic"

def exact_terms(text,terms):
    return [t for t in terms if re.search(r"(?<![A-Za-z0-9_])"+re.escape(t)+r"(?![A-Za-z0-9_])",text,re.I)]
def save_csv(path,rows):
    if rows:
        with path.open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--knowledge-dir",type=Path,default=Path("Knowledge")); p.add_argument("--dossier",type=Path,default=Path("Knowledge/Unitree/G1/Unitree_G1_Dossier_Tecnico_GIAR_ORION.md")); p.add_argument("--xml",type=Path,default=Path("Knowledge/Unitree/G1/g1_29dof_with_hand.xml")); p.add_argument("--top-k",type=int,default=5); p.add_argument("--device",default=None); a=p.parse_args()
    rp=Path("Agent/MultilingualKnowledgeRetriever.py")
    for x in (rp,a.knowledge_dir,a.dossier,a.xml):
        if not x.exists(): print(f"ERROR: no se encuentra {x.resolve()}"); return 2
    if a.top_k<1: print("ERROR: --top-k debe ser >= 1"); return 2
    mod=load_module(rp); kw={"knowledge_dir":a.knowledge_dir,"mode":"e5"}
    if a.device: kw["device"]=a.device
    print("Inicializando E5..."); t=time.perf_counter(); retr=mod.MultilingualKnowledgeRetriever(**kw); init=time.perf_counter()-t
    rel=str(a.dossier.resolve().relative_to(a.knowledge_dir.resolve())).replace("\\","/")
    chunks=[c for c in retr.chunks if c.source.replace("\\","/")==rel]
    if not chunks: print(f"ERROR: dossier no indexado: {rel}"); return 2
    root=ET.parse(a.xml).getroot(); block=root.find("actuator")
    if block is None: print("ERROR: falta bloque actuator"); return 2
    actuators=[e.attrib["joint"] for e in list(block) if "joint" in e.attrib]
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); out=Path("Tests")/f"results_g1_rag07_{stamp}"; out.mkdir(parents=True,exist_ok=True)
    rows=[]; details=[]
    for cid,q,acceptable,kind,terms in CASES:
        pred=route_query(q); method=pred
        if pred=="structured":
            retrieved=[{"source":str(a.xml),"text":"\n".join(actuators),"score":1.0}]
            terms=terms or actuators
        elif pred=="identifier":
            matches=[]
            for i,c in enumerate(chunks):
                found=exact_terms(c.text,terms)
                if found: matches.append({"source":c.source,"text":c.text,"score":len(found),"_found":found,"_i":i})
            matches.sort(key=lambda z:(-len(z["_found"]),z["_i"])); retrieved=matches[:a.top_k]
        else: retrieved=retr.search(q,top_k=a.top_k)
        joined="\n".join(str(z.get("text","")) for z in retrieved); found=exact_terms(joined,terms) if terms else []
        order=""
        if pred=="structured": order=int([x.strip() for x in joined.splitlines() if x.strip()]==actuators)
        row={"case_id":cid,"query":q,"case_kind":kind,"acceptable_routes":";".join(acceptable),"predicted_route":pred,"route_acceptable":int(pred in acceptable),"method_used":method,"expected_term_count":len(terms),"found_term_count":len(found),"literal_coverage":round(len(found)/len(terms),4) if terms else "","all_terms_found":int(bool(terms) and len(found)==len(terms)) if terms else "","order_matches_mjcf":order,"retrieved_chunks":len(retrieved),"found_terms":";".join(found),"missing_terms":";".join(t for t in terms if t not in joined),"human_relevance_review":"PENDIENTE"}
        rows.append(row)
        print(f"{cid}: {pred}; aceptable={pred in acceptable}; cobertura={len(found)}/{len(terms) if terms else 'N/A'}"+(f"; orden={order}" if order!="" else ""))
        for rank,item in enumerate(retrieved,1): details.append({"case_id":cid,"predicted_route":pred,"rank":rank,"source":item.get("source",""),"score":item.get("score",""),"expected_terms_found":";".join(exact_terms(str(item.get("text","")),terms)) if terms else "","text":item.get("text","")})
    # métricas por ruta predicha: útiles como diagnóstico, no sustituyen revisión humana
    total=len(rows); ok=sum(r["route_acceptable"] for r in rows)
    by_route={}
    for route in ("identifier","semantic","structured"):
        subset=[r for r in rows if r["predicted_route"]==route]
        by_route[route]={"n":len(subset),"acceptable_n":sum(x["route_acceptable"] for x in subset),"acceptability_rate":round(sum(x["route_acceptable"] for x in subset)/len(subset),4) if subset else None}
    meta={"experiment":"G1-RAG-07","timestamp":stamp,"cases":total,"route_acceptable":ok,"route_acceptability_rate":round(ok/total,4),"by_predicted_route":by_route,"top_k":a.top_k,"e5_model":mod.E5_MODEL_NAME,"device":str(retr.device),"total_chunks":len(retr.chunks),"dossier_chunks":len(chunks),"mjcf_actuators":len(actuators),"initialization_seconds":round(init,3),"limitations":["Las rutas aceptables pueden ser múltiples para consultas híbridas.","La cobertura literal mide presencia de términos, no calidad semántica.","La relevancia de fragmentos requiere revisión humana; human_relevance_review queda PENDIENTE.","Conjunto pequeño y diseñado manualmente: no demuestra generalización."]}
    save_csv(out/"resumen.csv",rows); save_csv(out/"detalle.csv",details); (out/"metadatos.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"\nAceptabilidad de ruta: {ok}/{total} ({ok/total:.1%})")
    print("No interpretar como calidad semántica final. Revisar detalle.csv y completar human_relevance_review.")
    print(f"Resultados: {out.resolve()}"); return 0
if __name__=="__main__": raise SystemExit(main())
