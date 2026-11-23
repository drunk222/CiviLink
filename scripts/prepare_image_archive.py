"""Build a valid preview RAR from fully downloaded leading ranges; never include partial entries."""
from pathlib import Path,PurePosixPath
import json,struct,zlib,shutil
ROOT=Path(__file__).resolve().parents[1];PARTS=ROOT/'data/archive-ranges';STEP=1048576
def vint(b,p):
    value=0;shift=0
    for _ in range(10):
        c=b[p];p+=1;value|=(c&127)<<shift
        if c<128:return value,p
        shift+=7
    raise ValueError('invalid vint')
def headers(stream,limit):
    position=8;entries=[]
    while position+7<limit:
        stream.seek(position);b=stream.read(4096);n,p=vint(b,4);end=p+n
        if end>len(b):break
        if zlib.crc32(b[4:end])&0xffffffff!=struct.unpack_from('<I',b,0)[0]:raise ValueError(f'Header CRC at {position}')
        typ,p=vint(b,p);flags,p=vint(b,p)
        extra,p=vint(b,p) if flags&1 else (0,p)
        data,p=vint(b,p) if flags&2 else (0,p)
        nextpos=position+end+data
        if nextpos>limit:break
        if typ==2:
            ff,p=vint(b,p);size,p=vint(b,p);attrs,p=vint(b,p)
            if ff&2:p+=4
            crc=None
            if ff&4:crc=struct.unpack_from('<I',b,p)[0];p+=4
            comp,p=vint(b,p);host,p=vint(b,p);ln,p=vint(b,p);name=b[p:p+ln].decode('utf-8')
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or ':' in name:raise ValueError('Unsafe archive path')
            entries.append(dict(path=name,bytes=size,crc32=f'{crc:08x}' if crc is not None else None))
        position=nextpos
    return position,entries
def main():
    parts=[]
    for i in range(1230):
        p=PARTS/f'{i:05d}.part';expected=min(STEP,1288822982-i*STEP)
        if not p.exists() or p.stat().st_size!=expected:break
        parts.append(p)
    target=ROOT/'data/image-prefix.rar'
    with target.open('wb') as out:
        for p in parts:
            with p.open('rb') as source:shutil.copyfileobj(source,out)
    with target.open('rb') as stream:end,entries=headers(stream,target.stat().st_size)
    with target.open('r+b') as out:out.truncate(end);out.seek(end);out.write((ROOT/'data/channel2_tail.bin').read_bytes()[-8:])
    (ROOT/'data/image-prefix-inventory.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Complete leading ranges',len(parts),'valid entries',len(entries),'RAR bytes',target.stat().st_size)
if __name__=='__main__':main()
