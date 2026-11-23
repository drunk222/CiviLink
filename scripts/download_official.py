"""Download the public competition archive in verified, resumable HTTP ranges."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import subprocess, time, hashlib, json, re

ROOT=Path(__file__).resolve().parents[1]
URL='https://chinavis.org/2024/document/channel2_data.rar'
TOTAL=1288822982
CHUNK=16*1024*1024
PARTS=ROOT/'data/official-parts'
PARTS.mkdir(parents=True,exist_ok=True)

def fetch(index):
    start=index*CHUNK;end=min(TOTAL-1,start+CHUNK-1)
    target=PARTS/f'{index:04d}.part'
    if target.exists() and target.stat().st_size==end-start+1:return index
    failures=0
    while failures<15:
        offset=target.stat().st_size if target.exists() else 0
        if offset==end-start+1:return index
        if offset>end-start+1:raise RuntimeError(f'Oversized part {index}')
        fragment=PARTS/f'{index:04d}.download';header=PARTS/f'{index:04d}.headers'
        result=subprocess.run(['curl.exe','--silent','--show-error','--http1.1','--tlsv1.2','--tls-max','1.2','--fail','--connect-timeout','15','--max-time','90','--range',f'{start+offset}-{end}','--dump-header',str(header),'--output',str(fragment),URL],capture_output=True)
        headers=header.read_text(errors='replace') if header.exists() else ''
        ranges=re.findall(r'Content-Range:\s*bytes (\d+)-(\d+)/(\d+)',headers,re.I)
        size=fragment.stat().st_size if fragment.exists() else 0
        if ranges and tuple(map(int,ranges[-1]))==(start+offset,end,TOTAL) and 0<size<=end-start+1-offset:
            with target.open('ab') as out,fragment.open('rb') as stream:
                while block:=stream.read(1024*1024):out.write(block)
            fragment.unlink();failures=0
        else:failures+=1;time.sleep(2)
    raise RuntimeError(f'Failed range {index}: {result.stderr.decode(errors="replace")[:150]}')

def main():
    count=(TOTAL+CHUNK-1)//CHUNK
    with ThreadPoolExecutor(max_workers=12) as pool:
        done=0;pending={pool.submit(fetch,i) for i in range(count)};began=time.monotonic()
        while pending:
            finished,pending=wait(pending,timeout=20,return_when=FIRST_COMPLETED)
            for future in finished:future.result();done+=1
            downloaded=sum(p.stat().st_size for p in PARTS.glob('*.part'))+sum(p.stat().st_size for p in PARTS.glob('*.download'))
            print(f'{downloaded/TOTAL:.1%} / {downloaded/1024**2:.1f} MiB; verified parts {done}/{count}; {time.monotonic()-began:.0f}s',flush=True)
    target=ROOT/'data/channel2_data.rar'
    sha=hashlib.sha256()
    with target.open('wb') as out:
        for i in range(count):
            with (PARTS/f'{i:04d}.part').open('rb') as part:
                while chunk:=part.read(1024*1024):out.write(chunk);sha.update(chunk)
    assert target.stat().st_size==TOTAL
    (ROOT/'data/official-download.json').write_text(json.dumps({'source':URL,'bytes':TOTAL,'sha256':sha.hexdigest(),'downloadedAt':'2026-11-08','verification':'HTTP ranges and total size verified; SHA256 calculated locally, no publisher checksum available.'},indent=2),encoding='utf-8')
    print(f'COMPLETE {TOTAL} bytes SHA256 {sha.hexdigest()}',flush=True)
if __name__=='__main__':main()
