"""Build a portable monitor with PyInstaller; never reads game or save files."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parent

def main():
    if sys.platform!='win32':raise SystemExit('Build this Windows app on Windows x64.')
    import tkinter
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed',
        '--name','PT-RNG-Monitor','--paths',str(ROOT/'monitor'),
        '--distpath',str(ROOT/'dist'),'--workpath',str(ROOT/'build'),'--specpath',str(ROOT/'build'),
        str(ROOT/'monitor/main.py')],check=True,cwd=ROOT)
    out=ROOT/'artifacts';out.mkdir(exist_ok=True)
    bundle=out/'PT-RNG-Monitor-Windows';bundle.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'dist/PT-RNG-Monitor.exe',bundle/'PT-RNG-Monitor.exe')
    for name in ('README.md','LICENSE','CHANGELOG.md'):shutil.copy2(ROOT/name,bundle/name)
    shutil.copytree(ROOT/'monitor',bundle/'source',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    lic=bundle/'third-party-licenses';lic.mkdir(exist_ok=True)
    python_license=Path(sys.base_prefix)/'LICENSE.txt'
    if not python_license.exists():raise RuntimeError('Missing CPython license')
    shutil.copy2(python_license,lic/'CPython.txt')
    tk=Path(tkinter.Tcl().eval('set tcl_library')).parent/'tk8.6/license.terms'
    if not tk.exists():raise RuntimeError('Missing Tk license')
    shutil.copy2(tk,lic/'Tk.txt')
    dist=importlib.metadata.distribution('pyinstaller')
    copying=next((dist.locate_file(f) for f in dist.files if str(f).endswith('COPYING.txt')),None)
    if not copying:raise RuntimeError('Missing PyInstaller license')
    shutil.copy2(copying,lic/'PyInstaller.txt')
    shutil.copy2(ROOT/'third-party/Tcl.txt',lic/'Tcl.txt')
    exe=bundle/'PT-RNG-Monitor.exe'
    manifest={'version':'1.0.0','file':exe.name,'sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
      'python':sys.version.split()[0],'pyinstaller':importlib.metadata.version('pyinstaller'),'platform':'Windows x64'}
    (bundle/'build-info.json').write_text(json.dumps(manifest,indent=2))
    archive=out/'PT-RNG-Monitor-Windows.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(bundle.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(bundle))
    source=out/'PT-RNG-Lab-Source.zip'
    allowed=['README.md','LICENSE','CHANGELOG.md','requirements-build.txt','package.py','monitor','docs','tests','third-party','.github']
    with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
        for name in allowed:
            p=ROOT/name
            for f in ([p] if p.is_file() else sorted(p.rglob('*'))):
                if f.is_file() and '__pycache__' not in f.parts:z.write(f,f.relative_to(ROOT))
    checksum=out/'SHA256SUMS.txt'
    checksum.write_text('\n'.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}' for p in (archive,source))+'\n')
    print(json.dumps({'zip':str(archive),'bytes':archive.stat().st_size,'exe_sha256':manifest['sha256']}))

if __name__=='__main__':main()
