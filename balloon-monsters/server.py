"""Local-only gallery and explicitly requested Desktop PNG export."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import base64, json, os, re, secrets, tempfile, threading, time, urllib.parse
ROOT=Path(__file__).resolve().parent
DIST=ROOT/'dist'
DATA=ROOT/'.local'
PHOTOS=DATA/'photos'
DESKTOP=Path.home()/'Desktop'
LOCK=threading.Lock()
CATALOG={v['id'] for v in json.loads((DIST/'catalog.json').read_text())}
ORIGINS={'http://127.0.0.1:4173','http://localhost:4173'}
def allocate(maker_id,catalog=None,path=None):
 catalog=list(catalog or CATALOG);path=path or DATA/'assignments.json'
 with LOCK:
  path.parent.mkdir(parents=True,exist_ok=True)
  try:state=json.loads(path.read_text())
  except (FileNotFoundError,json.JSONDecodeError):state={'makers':{},'remaining':[],'cycle':0}
  if maker_id in state['makers']:return state['makers'][maker_id]
  remaining=[x for x in state['remaining'] if x in catalog]
  if not remaining:
   remaining=catalog[:];secrets.SystemRandom().shuffle(remaining);state['cycle']+=1
   if len(remaining)>1 and remaining[-1]==state.get('last'):remaining[0],remaining[-1]=remaining[-1],remaining[0]
  cid=remaining.pop();state['last']=cid;state['remaining']=remaining;state['makers'][maker_id]=cid
  temp=path.with_suffix('.tmp');temp.write_text(json.dumps(state));os.replace(temp,path)
  return cid
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(DIST),**k)
 def json_response(self,data,status=200):
  raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  path=urllib.parse.urlparse(self.path).path
  if path=='/api/gallery':
   with LOCK:
    try:items=json.loads((DATA/'gallery.json').read_text())
    except (FileNotFoundError,json.JSONDecodeError):items=[]
   return self.json_response({'items':items,'desktopSave':True})
  if path.startswith('/api/photos/'):
   name=path.rsplit('/',1)[-1]
   if not re.fullmatch(r'[a-f0-9]{24}\.png',name):return self.send_error(404)
   try:raw=(PHOTOS/name).read_bytes()
   except FileNotFoundError:return self.send_error(404)
   self.send_response(200);self.send_header('Content-Type','image/png');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
  return super().do_GET()
 def do_POST(self):
  if self.path not in ('/api/snapshot','/api/assignment'):return self.send_error(404)
  if self.headers.get('Origin') not in ORIGINS:return self.json_response({'error':'Untrusted origin.'},403)
  if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send_error(415)
  try:
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<8000000:return self.json_response({'error':'Invalid image size.'},413)
   data=json.loads(self.rfile.read(length))
   if self.path=='/api/assignment':
    mid=str(data.get('makerId',''))
    if not re.fullmatch(r'[a-zA-Z0-9-]{16,80}',mid):return self.json_response({'error':'Invalid maker.'},400)
    return self.json_response({'characterId':allocate(mid),'designs':len(CATALOG)})
   name=str(data.get('name','')).strip();cid=data.get('characterId')
   if not 1<=len(name)<=40 or cid not in CATALOG:return self.json_response({'error':'Enter a name (1–40 characters).'},400)
   value=data['image']
   if not value.startswith('data:image/png;base64,'):raise ValueError()
   raw=base64.b64decode(value.split(',',1)[1],validate=True)
   if not raw.startswith(b'\x89PNG\r\n\x1a\n') or len(raw)>5500000:raise ValueError()
   ident=secrets.token_hex(12);safe=re.sub(r'[^\w-]+','-',name,flags=re.UNICODE).strip('-')[:45] or 'Maker'
   filename=f'Monster-{safe}-{time.strftime("%Y%m%d-%H%M%S")}-{ident[:4]}.png'
   if not DESKTOP.is_dir():return self.json_response({'error':'Desktop folder is unavailable.'},500)
   # Names and paths are server-owned. The client cannot supply a destination.
   with LOCK:
    PHOTOS.mkdir(parents=True,exist_ok=True)
    dest=DESKTOP/filename
    with open(dest,'xb') as f:f.write(raw)
    (PHOTOS/(ident+'.png')).write_bytes(raw)
    try:items=json.loads((DATA/'gallery.json').read_text())
    except (FileNotFoundError,json.JSONDecodeError):items=[]
    item={'id':ident,'name':name,'characterId':cid,'image':'/api/photos/'+ident+'.png','createdAt':int(time.time()*1000)}
    items.insert(0,item)
    temp=DATA/'gallery.tmp';temp.write_text(json.dumps(items,ensure_ascii=False));os.replace(temp,DATA/'gallery.json')
   return self.json_response({'saved':True,'destination':'Desktop','filename':filename,'item':item})
  except (ValueError,KeyError,TypeError,json.JSONDecodeError):return self.json_response({'error':'Invalid snapshot.'},400)
  except OSError:return self.json_response({'error':'Could not write to Desktop. Use Download PNG instead.'},500)
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',4173),Handler).serve_forever()
