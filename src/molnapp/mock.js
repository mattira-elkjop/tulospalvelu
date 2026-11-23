(function(){
  const store={}; const subs=[];
  const collOf=p=>p.split("/").slice(0,-1).join("/");
  const snapDoc=(path)=>{const id=path.split("/").pop();const d=store[path];return {id,exists:d!==undefined,data:()=>d,metadata:{fromCache:false}}};
  const docsIn=c=>Object.keys(store).filter(k=>collOf(k)===c).map(snapDoc);
  const notify=()=>subs.forEach(s=>s());
  const uid=()=>"id"+Math.random().toString(36).slice(2,9);
  const docRef=path=>({id:path.split("/").pop(),path,
    async get(){return snapDoc(path)},
    async set(d){store[path]=JSON.parse(JSON.stringify(d));notify()},
    async update(d){if(!store[path])throw {code:"invalid_argument",message:"nej"};Object.assign(store[path],d);notify()},
    async delete(){delete store[path];notify()}});
  const collRef=path=>({path,doc:id=>docRef(path+"/"+(id||uid())),
    async add(d){const r=docRef(path+"/"+uid());await r.set(d);return r},
    onSnapshot(next){const f=()=>{const docs=docsIn(path);next({docs,size:docs.length,empty:!docs.length,metadata:{fromCache:false}})};subs.push(f);setTimeout(f,0);return()=>{subs.splice(subs.indexOf(f),1)}}});
  window.__store=store;
  window.claude={use:async n=>n==="db"?{doc:docRef,collection:collRef}:n==="user"?{can:async()=>true,id:async()=>"u1",isOwner:async()=>true}:null};
  const P=[[5,"Spelare 5"],[6,"Spelare 6"],[7,"Spelare 7"],[10,"Spelare 10"],[11,"Spelare 11"],[13,"Spelare 13"],[19,"Spelare 19"],[20,"Spelare 20"],[21,"Spelare 21"],[22,"Spelare 22"],[24,"Spelare 24"],[30,"Spelare 30"],[41,"Spelare 41"],[43,"Spelare 43"],[49,"Spelare 49"],[90,"Spelare 90"],[91,"Spelare 91"],[92,"Spelare 92"]];
  store["seasons/s1"]={lag:"MIF",serie:"U13 Valkoinen, lohko 3b",sasong:"2026–2027",created:1};
  P.forEach(([n,m])=>store["seasons/s1/players/p"+n]={nr:n,name:m,pos:n>=90?"MV":"UP"});
  const G=[[11,6,7],[11,6,null],[10,41,5],[41,10,null],[20,43,null],[5,null,null],[19,11,6]];
  G.forEach(([s,a,b],i)=>store["seasons/s1/goals/g"+i]={scorer:"p"+s,a1:a?"p"+a:null,a2:b?"p"+b:null,date:"2026-11-15",opp:"Exempel IK",ts:i});
  store["seasons/s1/pens/u1"]={pid:"p20",min:2,date:"2026-11-15",opp:"Exempel IK",ts:9};
  store["seasons/s1/pens/u2"]={pid:"p43",min:10,date:"2026-11-15",opp:"Exempel IK",ts:10};
})();
