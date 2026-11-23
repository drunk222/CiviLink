"""Prepare/assemble small HTTP ranges. curl runs directly, outside this script."""
from pathlib import Path
import re,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1];TOTAL=1288822982;STEP=1024*1024;OLDSTEP=16*STEP
PARTS=ROOT/'data/archive-ranges';PARTS.mkdir(exist_ok=True)
URL='https://chinavis.org/2024/document/channel2_data.rar'
def harvest():
    old=ROOT/'data/official-parts'
    for part in old.glob('*.part'):
        i=int(part.stem);frag=part.with_suffix('.download');hdr=part.with_suffix('.headers')
        if frag.exists() and hdr.exists():
            ranges=re.findall(r'Content-Range:\s*bytes (\d+)-(\d+)/(\d+)',hdr.read_text(errors='replace'),re.I)
            if ranges and int(ranges[-1][0])==i*OLDSTEP+part.stat().st_size and frag.stat().st_size<=OLDSTEP-part.stat().st_size:
                with part.open('ab') as f:f.write(frag.read_bytes())
                frag.unlink()
        with part.open('rb') as f:
            j=0
            while block:=f.read(STEP):
                start=i*OLDSTEP+j*STEP;expected=min(STEP,TOTAL-start)
                if len(block)==expected:
                    out=PARTS/f'{start//STEP:05d}.part'
                    if not out.exists():out.write_bytes(block)
                j+=1
def prepare():
    target=ROOT/'data/channel2_data.rar';report_path=ROOT/'data/official-download.json'
    if target.exists() and target.stat().st_size==TOTAL and report_path.exists():
        expected=json.loads(report_path.read_text(encoding='utf-8'))['sha256'];digest=hashlib.sha256()
        with target.open('rb') as stream:
            while block:=stream.read(STEP):digest.update(block)
        if digest.hexdigest()==expected:
            print('Complete archive already present and SHA256 unchanged; download skipped.');return
    harvest();cfg=[];done=0
    for i,start in enumerate(range(0,TOTAL,STEP)):
        end=min(TOTAL-1,start+STEP-1);out=PARTS/f'{i:05d}.part';header=PARTS/f'{i:05d}.headers'
        valid=out.exists() and out.stat().st_size==end-start+1
        if valid:done+=1;continue
        if cfg:cfg.append('next')
        cfg.extend(['url = "'+URL+'"',f'range = "{start}-{end}"',f'output = "{out.as_posix()}"',f'dump-header = "{header.as_posix()}"','http1.1','tlsv1.2','tls-max = "1.2"','fail','connect-timeout = 15','max-time = 60','retry = 3','retry-all-errors','retry-delay = 1','silent','show-error'])
    (ROOT/'data/archive-download.cfg').write_text('\n'.join(cfg),encoding='utf-8')
    batches=ROOT/'data/archive-batches';batches.mkdir(exist_ok=True)
    transfers='\n'.join(cfg).split('\nnext\n') if cfg else []
    batchnames=[]
    for n in range(0,len(transfers),64):
        name=f'batch-{n//64:03d}.cfg';(batches/name).write_text('\nnext\n'.join(transfers[n:n+64]),encoding='utf-8');batchnames.append(name)
    (ROOT/'data/archive-batch-list.json').write_text(json.dumps(batchnames),encoding='utf-8')
    print('Ready',done,'/',(TOTAL+STEP-1)//STEP,'ranges, remaining',sum(1 for x in cfg if x.startswith('url')))
def assemble():
    expected=(TOTAL+STEP-1)//STEP;missing=[];digest=hashlib.sha256()
    for i in range(expected):
        p=PARTS/f'{i:05d}.part'
        if not p.exists() or p.stat().st_size!=min(STEP,TOTAL-i*STEP):missing.append(i)
        hdr=p.with_suffix('.headers')
        if hdr.exists():
            found=re.findall(r'Content-Range:\s*bytes (\d+)-(\d+)/(\d+)',hdr.read_text(errors='replace'),re.I)
            if not found or tuple(map(int,found[-1]))!=(i*STEP,min(TOTAL-1,(i+1)*STEP-1),TOTAL):missing.append(i)
    if missing:raise RuntimeError(f'{len(set(missing))} incomplete/invalid ranges: {missing[:20]}')
    target=ROOT/'data/channel2_data.rar'
    with target.open('wb') as out:
        for i in range(expected):
            b=(PARTS/f'{i:05d}.part').read_bytes();out.write(b);digest.update(b)
    assert target.stat().st_size==TOTAL
    report=dict(source=URL,bytes=TOTAL,sha256=digest.hexdigest(),rangeValidation=True,publisherChecksumAvailable=False)
    (ROOT/'data/official-download.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
if __name__=='__main__':assemble() if len(sys.argv)>1 and sys.argv[1]=='assemble' else prepare()
