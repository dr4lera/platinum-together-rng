"""Local desktop UI; the only outbound action is an explicitly opened guide URL."""
import json
import sys
from reader import Reader
from rng import distance

GUIDE='https://dr4lera.github.io/platinum-together-rng/'

def run(smoke=False):
    import tkinter as tk
    from tkinter import ttk
    import webbrowser
    root=tk.Tk();root.title('PT RNG Monitor · Read only');root.geometry('780x660');root.minsize(680,600)
    if smoke:root.withdraw()
    root.configure(bg='#101b20')
    style=ttk.Style();style.theme_use('clam')
    style.configure('TFrame',background='#101b20');style.configure('TLabel',background='#101b20',foreground='#e9f4ee',font=('Segoe UI',11))
    style.configure('Title.TLabel',font=('Segoe UI',21,'bold'));style.configure('Seed.TLabel',font=('Consolas',29,'bold'),foreground='#d6f46b')
    style.configure('TButton',font=('Segoe UI',10),padding=8)
    frame=ttk.Frame(root,padding=24);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='PLATINUM TOGETHER',style='Title.TLabel').pack(anchor='w')
    ttk.Label(frame,text='RNG monitor  /  v1.0.0  /  Windows x64').pack(anchor='w',pady=(0,14))
    status=tk.StringVar(value='Open the game and load your save. Then connect.')
    ttk.Label(frame,textvariable=status,wraplength=710).pack(anchor='w')
    seed=tk.StringVar(value='--------');ttk.Label(frame,textvariable=seed,style='Seed.TLabel').pack(anchor='w',pady=10)
    info=tk.StringVar();ttk.Label(frame,textvariable=info,wraplength=710).pack(anchor='w')
    buttons=ttk.Frame(frame);buttons.pack(fill='x',pady=12)
    state={'reader':None,'snapshot':None,'target':None,'paused':False}
    def connect():
        if state['reader']:state['reader'].close()
        state.update(reader=None,snapshot=None,target=None)
        try:state['reader']=Reader();status.set('Connected. Read access only.');state['paused']=False
        except Exception as e:status.set(str(e));seed.set('--------');info.set('')
    def copy():
        if not state['snapshot']:status.set('Connect and load your save before copying.');return
        root.clipboard_clear();root.clipboard_append(json.dumps(state['snapshot'],indent=2));root.update()
        status.set('Snapshot copied. Paste it into the predictor on the guide page.')
    def target():
        try:
            value=json.loads(root.clipboard_get())
            if value.get('schema')!='pt-rng-target-v1':raise ValueError('Use “Track in monitor” beside a predictor result.')
            snap=state['snapshot']
            if not snap or value['tid']!=snap['tid'] or value['sid']!=snap['sid'] or value.get('sha256','')!=snap['sha256']:
                raise ValueError('Target belongs to different trainer IDs or a different build. Reimport your snapshot.')
            int(value['seed'],16);state['target']=value;status.set('Target loaded. Recheck remaining advances after opening or closing any menu.')
        except Exception as e:status.set(f'Target not loaded: {e}')
    ttk.Button(buttons,text='Connect / reconnect',command=connect).pack(side='left',padx=(0,8))
    ttk.Button(buttons,text='Copy snapshot',command=copy).pack(side='left',padx=(0,8))
    ttk.Button(buttons,text='Open guide + predictor',command=lambda:webbrowser.open(GUIDE)).pack(side='left')
    tracking=tk.StringVar(value='No target loaded.')
    ttk.Button(frame,text='Paste target from predictor',command=target).pack(anchor='w')
    ttk.Label(frame,textvariable=tracking,wraplength=710).pack(anchor='w',pady=10)
    ttk.Label(frame,text='GENERATED ROAMERS  ·  not predicted results').pack(anchor='w',pady=(12,4))
    tree=ttk.Treeview(frame,columns=('name','pid','shiny','map'),show='headings',height=6)
    for key,label,width in [('name','Pokémon',155),('pid','PID',130),('shiny','Status',180),('map','Map ID',90)]:
        tree.heading(key,text=label);tree.column(key,width=width,anchor='w')
    tree.pack(fill='x')
    ttk.Label(frame,text='No writes • No key presses • No save access • No uploads\nAfter Ctrl+R, click Connect again. Unknown builds are refused.',wraplength=710).pack(anchor='w',pady=14)
    def tick():
        r=state['reader']
        if r:
            try:
                s=r.snapshot();state['snapshot']=s;seed.set(s['seed'])
                lead=s['lead'];leadtext='Unknown lead (choose Synchronize manually)' if not lead else ('Synchronize ON' if lead['synchronize'] else 'Synchronize OFF')
                info.set(f"Build {s['version']}  ·  TID {s['tid']}  ·  SID {s['sid']}  ·  {leadtext}\n{s['calibration']}")
                for item in tree.get_children():tree.delete(item)
                for mon in s['roamers']:
                    if mon['name']=='Unused slot':continue
                    tree.insert('', 'end',values=(mon['name'],mon['pid'] if mon['active'] else '—',('SHINY' if mon['shiny'] else 'Not shiny') if mon['active'] else 'Inactive',mon['map'] if mon['active'] else '—'))
                t=state['target']
                if t:
                    n=distance(int(s['seed'],16),int(t['seed'],16))
                    tracking.set('AT TARGET — close menus, recheck seed, then interact.' if n==0 else
                      f'{n:,} advances remaining. Count actual advances, not assumed page turns.' if n<=1000000 else
                      'Target passed or RNG changed unexpectedly. Stop and calculate a fresh target.')
            except Exception as e:
                status.set(str(e));r.close();state.update(reader=None,snapshot=None);seed.set('--------');tracking.set('Disconnected; no live target tracking.')
        root.after(500,tick)
    def close():
        if state['reader']:state['reader'].close()
        root.destroy()
    root.protocol('WM_DELETE_WINDOW',close);tick()
    if smoke:root.after(100,close)
    root.mainloop()

if __name__=='__main__':
    if '--snapshot' in sys.argv:
        r=Reader()
        try:print(json.dumps(r.snapshot(),indent=2))
        finally:r.close()
    elif '--self-test' in sys.argv:
        assert distance(0,next_seed:=__import__('rng').next_seed(0))==1
        print('Read-only monitor self-test passed.')
    elif '--smoke-test' in sys.argv:
        run(smoke=True)
    else:run()
