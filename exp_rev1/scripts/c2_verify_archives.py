"""C2: verify the downloaded nuScenes keyframe archives against the objects in the public
bucket. The bucket stores each archive as a multipart upload, whose ETag is the MD5 of the
concatenated MD5 digests of its parts, followed by the number of parts. The script
recomputes that value from the local file (part size 8 MiB) and compares it with the ETag
that the bucket returns, and it reads the gzip stream to its end (CRC check).

Usage: python c2_verify_archives.py F:/datasets/nuscenes_trainval_keyframes/archives [name ...]
Writes VERIFY.txt next to the archives folder. Reads only.
"""
import hashlib, sys, time, urllib.request, zlib
from pathlib import Path

BASE = "https://motional-nuscenes.s3.ap-northeast-1.amazonaws.com/public/v1.0/"
PART = 8 * 1024 * 1024


def main():
    d = Path(sys.argv[1]); names = sys.argv[2:] or sorted(p.name for p in d.glob("*.tgz"))
    lines = []; allok = True
    for name in names:
        req = urllib.request.Request(BASE + name, method="HEAD")
        with urllib.request.urlopen(req, timeout=60) as r:
            etag = r.headers["ETag"].strip('"'); size = int(r.headers["Content-Length"])
        t0 = time.time(); digs = []; n = 0; whole = hashlib.md5()
        z = zlib.decompressobj(16 + zlib.MAX_WBITS); gz_ok = True
        with open(d / name, "rb") as f:
            while True:
                b = f.read(PART)
                if not b:
                    break
                digs.append(hashlib.md5(b).digest()); whole.update(b); n += len(b)
                if gz_ok:
                    try:
                        z.decompress(b)
                    except zlib.error:
                        gz_ok = False
        local = hashlib.md5(b"".join(digs)).hexdigest() + f"-{len(digs)}"
        ok = (local == etag and n == size and gz_ok and z.eof)
        allok &= ok
        line = (f"{name}  size {n} ({'=' if n == size else '!='} bucket)  multipart ETag {local} ({'=' if local == etag else '!='} bucket {etag})  "
                f"gzip stream {'complete' if gz_ok and z.eof else 'BROKEN'}  md5 {whole.hexdigest()}  {'OK' if ok else 'FAILED'}  ({time.time()-t0:.0f} s)")
        print(line, flush=True); lines.append(line)
    with open(d.parent / "VERIFY.txt", "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n" + "\n".join(lines) + "\n")
    print("ALL ARCHIVES VERIFIED" if allok else "VERIFICATION FAILED")
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
