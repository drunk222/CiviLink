import http from 'node:http';
import {stat} from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.gif':'image/gif','.svg':'image/svg+xml','.md':'text/plain; charset=utf-8'};
const server=http.createServer(async(req,res)=>{
  try {
    const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const file=path.resolve(root,'.'+(pathname==='/'?'/index.html':pathname));
    const relative=path.relative(root,file);
    if(relative.startsWith('..')||path.isAbsolute(relative)||relative.split(path.sep).some(p=>p.startsWith('.'))){res.writeHead(403);res.end();return;}
    const info=await stat(file);if(!info.isFile())throw Error('missing');
    const etag=`W/"${info.size}-${info.mtimeMs.toString(16)}"`,cache=relative.startsWith('assets'+path.sep+'official'+path.sep)?'public, max-age=31536000, immutable':'no-cache';
    if(req.headers['if-none-match']===etag){res.writeHead(304,{'ETag':etag,'Cache-Control':cache});res.end();return;}
    res.writeHead(200,{'Content-Type':types[path.extname(file).toLowerCase()]||'application/octet-stream','Content-Length':info.size,'ETag':etag,'Cache-Control':cache,'X-Content-Type-Options':'nosniff'});
    if(req.method==='HEAD'){res.end();return;}
    createReadStream(file).on('error',()=>res.destroy()).pipe(res);
  } catch {res.writeHead(404);res.end('Not found');}
});
server.listen(Number(process.env.PORT)||5173,'127.0.0.1',()=>console.log(`万象同纹 Local: http://127.0.0.1:${server.address().port}`));
