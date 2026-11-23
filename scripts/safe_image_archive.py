"""Repackage original compressed image entries under Windows-safe hash filenames.
Image payloads and their CRCs remain unchanged; original filenames are retained in an index.
"""
from pathlib import Path
import sys,json,zlib,struct,hashlib
from prepare_image_archive import vint
ROOT=Path(__file__).resolve().parents[1]
def encode(value):
    out=bytearray()
    while value>=128:out.append((value&127)|128);value>>=7
    out.append(value);return bytes(out)
def main():
    source=ROOT/(sys.argv[1] if len(sys.argv)>1 else 'data/channel2_data.rar' if (ROOT/'data/channel2_data.rar').exists() else 'data/image-prefix.rar');target=ROOT/'data/official-safe-images.rar';entries=[]
    with source.open('rb') as stream,target.open('wb') as out:
        assert stream.read(8)==b'Rar!\x1a\x07\x01\x00';out.write(b'Rar!\x1a\x07\x01\x00');position=8;limit=source.stat().st_size
        while position+7<=limit:
            stream.seek(position);b=stream.read(4096);size,p=vint(b,4);content_start=p;end=p+size
            if end>len(b):raise ValueError('Large unsupported header')
            assert zlib.crc32(b[4:end])&0xffffffff==struct.unpack_from('<I',b,0)[0],position
            typ,p=vint(b,p);flags,p=vint(b,p)
            extra,p=vint(b,p) if flags&1 else (0,p)
            packed,p=vint(b,p) if flags&2 else (0,p)
            if typ==1:out.write(b[:end])
            if typ==2:
                ff,p=vint(b,p);unpacked,p=vint(b,p);attrs,p=vint(b,p)
                if ff&2:p+=4
                crc=None
                if ff&4:crc=struct.unpack_from('<I',b,p)[0];p+=4
                comp,p=vint(b,p);host,p=vint(b,p);name_start=p;length,p=vint(b,p);name=b[p:p+length].decode('utf-8');name_end=p+length;ext=Path(name).suffix.lower()
                if ext in ['.jpg','.jpeg','.png','.gif','.webp','.bmp','.tif','.tiff']:
                    key=hashlib.sha256(name.encode()).hexdigest()[:20];safe=f'images/{key}{ext}';encoded=safe.encode();content=b[content_start:name_start]+encode(len(encoded))+encoded+b[name_end:end];headsize=encode(len(content));out.write(struct.pack('<I',zlib.crc32(headsize+content)&0xffffffff)+headsize+content)
                    stream.seek(position+end);remaining=packed
                    while remaining:
                        block=stream.read(min(1048576,remaining))
                        if not block:raise ValueError('Truncated packed data')
                        out.write(block);remaining-=len(block)
                    entries.append(dict(originalName=name,key=key,file='assets/official/'+safe,bytes=unpacked,crc32=f'{crc:08x}' if crc is not None else None))
            if typ==5:break
            position+=end+packed
        out.write((ROOT/'data/channel2_tail.bin').read_bytes()[-8:])
    (ROOT/'data/image-files.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8');print('Repacked unchanged image entries',len(entries))
if __name__=='__main__':main()
