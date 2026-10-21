"""Independent deterministic RNG arithmetic. No process or file access."""
MULT, ADD, MASK = 0x41C64E6D, 0x6073, 0xFFFFFFFF
ROUTES = [342,343,344,345,346,347,349,350,353,354,356,362,363,365,366,367,371,373,380,382,383,385,388,391,467,392,395,200,204]

def next_seed(seed):
    return (seed * MULT + ADD) & MASK

def distance(seed, target):
    a, c, count, bit = MULT, ADD, 0, 1
    for _ in range(32):
        if (seed & bit) != (target & bit):
            seed = (seed * a + c) & MASK
            count |= bit
        c = c * (a + 1) & MASK
        a = a * a & MASK
        bit <<= 1
    return count

def is_shiny(pid, tid, sid):
    return (tid ^ sid ^ (pid & 65535) ^ (pid >> 16)) < 8

def ivs(word):
    return [(word >> i) & 31 for i in (0, 5, 10, 20, 25, 15)]

def method1(seed, offset=4):
    for _ in range(offset):
        seed = next_seed(seed)
    seed = next_seed(seed); low = seed >> 16
    seed = next_seed(seed); pid = low | ((seed >> 16) << 16)
    seed = next_seed(seed); x = seed >> 16
    seed = next_seed(seed); y = seed >> 16
    return dict(pid=f'{pid:08X}', nature=pid % 25, ivs=ivs((x & 32767) | ((y & 32767) << 15)), end_seed=seed)

def method_j(seed, sync=-1):
    def draw():
        nonlocal seed
        seed = next_seed(seed)
        return seed >> 16
    nature = sync if sync >= 0 and draw() // 32768 == 0 else draw() // 2622
    for _ in range(20000):
        pid = draw() | (draw() << 16)
        if pid % 25 == nature:
            break
    else:
        raise ValueError('PID loop exceeded safety bound')
    x, y = draw(), draw()
    return dict(pid=f'{pid:08X}', nature=nature, ivs=ivs((x & 32767) | ((y & 32767) << 15)), end_seed=seed)

def birds(seed, tid, sid, slots=(3,4,5), route_indexes=(0,0,0,0,0,0), previous_map=-1):
    out = []
    for slot in slots:
        p = method1(seed, 0); seed = p.pop('end_seed')
        while True:
            seed = next_seed(seed); route = (seed >> 16) // 2260
            if route != route_indexes[slot] and ROUTES[route] != previous_map:
                break
        p.update(name={3:'Moltres',4:'Zapdos',5:'Articuno'}[slot], route_index=route,
                 shiny=is_shiny(int(p['pid'],16),tid,sid))
        out.append(p)
    return out
