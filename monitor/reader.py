"""Windows memory reader. Only QUERY_LIMITED_INFORMATION | VM_READ are requested.

No memory writes, injection, input automation, networking, or save-file access.
Unknown executable hashes fail closed. All addresses are ASLR-relative.
"""
import ctypes as C
from ctypes import wintypes as W
import hashlib
from pathlib import Path
import struct
import sys
from rng import next_seed, ivs, is_shiny

PROFILES = {
 '94b851a80c166329d62a410e2374d79b5e8dddfe2c5b4ae24b13a3e9f805c810':
    dict(version='0.1.12', rng=0x1329440, rng_fn=0x54eb7, field=0x16977c0,
         calibration='Encounter targets verified on this exact executable'),
 '863322cad34fef3b1073fb200de92b407e07eb1c53a1d0153fd0b3873fea4949':
    dict(version='0.1.13', rng=0x1329440, rng_fn=0x54f47, save=0x13381c0,
         calibration='Live memory layout verified; encounter targets need fresh in-game calibration'),
}
ORDER = [(0,1,2,3),(0,1,3,2),(0,2,1,3),(0,3,1,2),(0,2,3,1),(0,3,2,1),
 (1,0,2,3),(1,0,3,2),(2,0,1,3),(3,0,1,2),(2,0,3,1),(3,0,2,1),
 (1,2,0,3),(1,3,0,2),(2,1,0,3),(3,1,0,2),(2,3,0,1),(3,2,0,1),
 (1,2,3,0),(1,3,2,0),(2,1,3,0),(3,1,2,0),(2,3,1,0),(3,2,1,0)]

class ProcessEntry(C.Structure):
    _fields_ = [('size',W.DWORD),('usage',W.DWORD),('pid',W.DWORD),('heap',C.c_size_t),
      ('module',W.DWORD),('threads',W.DWORD),('parent',W.DWORD),('priority',W.LONG),
      ('flags',W.DWORD),('exe',W.WCHAR*260)]

class ModuleEntry(C.Structure):
    _fields_ = [('size',W.DWORD),('module',W.DWORD),('pid',W.DWORD),('global_uses',W.DWORD),
      ('process_uses',W.DWORD),('base',C.c_void_p),('image_size',W.DWORD),('handle',W.HMODULE),
      ('name',W.WCHAR*256),('path',W.WCHAR*260)]

def kernel():
    if sys.platform != 'win32' or C.sizeof(C.c_void_p) != 8:
        raise RuntimeError('Use 64-bit Windows and 64-bit Python, or the packaged Windows app.')
    k = C.WinDLL('kernel32', use_last_error=True)
    k.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD];k.CreateToolhelp32Snapshot.restype=W.HANDLE
    for n, typ in [('Process32FirstW',ProcessEntry),('Process32NextW',ProcessEntry),('Module32FirstW',ModuleEntry)]:
        getattr(k,n).argtypes=[W.HANDLE,C.POINTER(typ)];getattr(k,n).restype=W.BOOL
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.CloseHandle.argtypes=[W.HANDLE];k.CloseHandle.restype=W.BOOL
    k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
    k.ReadProcessMemory.restype=W.BOOL
    k.GetExitCodeProcess.argtypes=[W.HANDLE,C.POINTER(W.DWORD)];k.GetExitCodeProcess.restype=W.BOOL
    return k

def snapshot_handle(k, flags, pid):
    h=k.CreateToolhelp32Snapshot(flags,pid)
    if h == C.c_void_p(-1).value:
        raise C.WinError(C.get_last_error())
    return h

class Reader:
    def __init__(self):
        self.k=kernel();self.handle=None
        snap=snapshot_handle(self.k,2,0);p=ProcessEntry();p.size=C.sizeof(p);pids=[]
        try:
            ok=self.k.Process32FirstW(snap,C.byref(p))
            while ok:
                if p.exe.lower()=='platinum.exe':pids.append(p.pid)
                ok=self.k.Process32NextW(snap,C.byref(p))
        finally:self.k.CloseHandle(snap)
        if len(pids)!=1:
            raise RuntimeError('Open exactly one Platinum Together game, then click Connect.')
        self.pid=pids[0];snap=snapshot_handle(self.k,0x18,self.pid)
        try:
            m=ModuleEntry();m.size=C.sizeof(m)
            if not self.k.Module32FirstW(snap,C.byref(m)):raise C.WinError(C.get_last_error())
            self.base=m.base;path=Path(m.path)
        finally:self.k.CloseHandle(snap)
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest not in PROFILES:
            raise RuntimeError(f'Unsupported executable SHA-256: {digest}. No game data was read. Check the website for a new profile.')
        self.profile=PROFILES[digest];self.digest=digest
        self.handle=self.k.OpenProcess(0x1010,False,self.pid)
        if not self.handle:raise C.WinError(C.get_last_error())
        try:
            if self.read(self.base+self.profile['rng_fn'],4)!=bytes.fromhex('554889e5') or self.read(self.base+self.profile['rng_fn']+10,6)!=bytes.fromhex('69c06d4ec641'):
                raise RuntimeError('Loaded game code does not match its profile. Reconnect after restarting the game.')
        except Exception:
            self.close();raise

    def close(self):
        if self.handle:self.k.CloseHandle(self.handle);self.handle=None

    def read(self, address, size):
        if not self.handle:raise RuntimeError('Not connected')
        code=W.DWORD()
        if not self.k.GetExitCodeProcess(self.handle,C.byref(code)) or code.value!=259:
            raise RuntimeError('Game exited or reset. Click Connect again.')
        buf=C.create_string_buffer(size);got=C.c_size_t()
        if not self.k.ReadProcessMemory(self.handle,address,buf,size,C.byref(got)) or got.value!=size:
            raise RuntimeError('Game data unavailable. Load your save and reconnect.')
        return buf.raw

    def ptr(self,a):return struct.unpack('<Q',self.read(a,8))[0]
    def u32(self,a):return struct.unpack('<I',self.read(a,4))[0]
    def seed(self):return self.u32(self.base+self.profile['rng'])

    def part(self,save,ident):
        tag,size,offset,_,_=struct.unpack('<IIIHH',self.read(save+0x20024+16*ident,16))
        if tag!=ident or not 0<size<0x20000 or offset+size>0x20000:
            raise RuntimeError('Save layout validation failed. No snapshot exported.')
        return save+0x14+offset

    def lead(self, party):
        if self.u32(party)!=6 or not 1<=self.u32(party+4)<=6:return None
        raw=self.read(party+8,236)
        if raw!=self.read(party+8,236):return None
        pid,_,checksum=struct.unpack_from('<IHH',raw);seed=checksum;plain=bytearray()
        for at in range(8,136,2):
            seed=next_seed(seed);plain+=struct.pack('<H',struct.unpack_from('<H',raw,at)[0]^(seed>>16))
        if sum(struct.unpack('<64H',plain))&65535!=checksum:return None
        a=32*ORDER[((pid>>13)&31)%24][0]
        return dict(species=struct.unpack_from('<H',plain,a)[0],ability=plain[a+13],nature=pid%25,
                    synchronize=plain[a+13]==28)

    def snapshot(self):
        profile=self.profile
        save=self.ptr(self.base+profile['save']) if 'save' in profile else self.ptr(self.ptr(self.base+profile['field'])+0x18)
        trainer=self.u32(self.part(save,1)+0x14);tid,sid=trainer&65535,trainer>>16
        spe=self.part(save,25);vf=self.part(save,4)
        raw=self.read(spe+0xc8,134)
        indexes=list(self.read(spe+0x148,6));recent=struct.unpack_from('<ii',raw)
        if any(i>=29 for i in indexes):raise RuntimeError('Roamer layout validation failed.')
        roamers=[]
        for slot,name in enumerate(('Mesprit','Cresselia','Unused slot','Moltres','Zapdos','Articuno')):
            route,iv,pid,sp,hp,level,status,active=struct.unpack('<IIIHHBBB',self.read(spe+0xd0+20*slot,19))
            if active not in (0,1):raise RuntimeError('Invalid roamer state.')
            roamers.append(dict(slot=slot,name=name,active=bool(active),species=sp,pid=f'{pid:08X}',
                 shiny=bool(active and is_shiny(pid,tid,sid)),ivs=ivs(iv),map=route,level=level))
        activated=bool(self.read(vf+0x240+0x99//8,1)[0]&(1<<(0x99%8)))
        states=[struct.unpack('<H',self.read(vf+2*(i-0x4000),2))[0] for i in (0x405e,0x405f,0x4060)]
        if any(x>3 for x in states):raise RuntimeError('Bird-state validation failed.')
        slots=[3,4,5] if not activated else [3+i for i,x in enumerate(states) if x==3]
        return dict(schema='pt-rng-snapshot-v1',version=profile['version'],sha256=self.digest,seed=f'{self.seed():08X}',
          tid=tid,sid=sid,lead=self.lead(self.part(save,2)),route_indexes=indexes,previous_map=recent[1],
          bird_release_slots=slots,birds_activated=activated,bird_states=states,roamers=roamers,
          calibration=profile['calibration'])
