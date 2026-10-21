import {search} from './rng.mjs';
self.onmessage=({data})=>{
 try{self.postMessage({results:search(data)});}
 catch(e){self.postMessage({error:e.message});}
};
