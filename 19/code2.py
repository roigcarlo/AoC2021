import re
import sys
import time
import itertools

class pair_dist_hash:
    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.d = e_distance(a, b)

    def __eq__(self, other):
        return self.d == other.d

    def __lt__(self, other):
        return self.d < other.d 

def e_distance(a,b):
    return (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2

def m_distance(a,b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2])

def calculate_euclidean_pairs(scanners):
    scanner_pairs = {}
    for s in scanners:
        scanner_pairs[s] = {}
        for pair in itertools.combinations(scanners[s],2):
            pair_d_h = pair_dist_hash(pair[0],pair[1])
            scanner_pairs[s][pair_d_h.d] = pair_d_h

    return scanner_pairs

def find_rot(match_pairs):
    for rot in itertools.permutations([0, 1, 2]):
        for i in [-1,1]:
            for j in [-1,1]:
                for k in [-1,1]:
                    dir = [i,j,k]
                    diff_scan_a_p_1 = [ match_pairs[0].a[c] - match_pairs[0].b[c] for c in range(3)]
                    diff_scan_b_p_1 = [ match_pairs[1].a[rot[c]]*dir[c] - match_pairs[1].b[rot[c]]*dir[c] for c in range(3)]
                    if diff_scan_a_p_1 == diff_scan_b_p_1:
                        return (dir, rot, [match_pairs[0].a[c] - match_pairs[1].a[rot[c]]*dir[c] for c in range(3)])
    return None

def find_chain(scanner_id, scanners_frame):
    for i in range(scanner_id+1):
        visited = [i]
        not_visited = list(range(scanner_id+1))
        not_visited.remove(i)
        for pair in scanners_frame:
            for pair in scanners_frame:
                if pair[0] in visited and pair[1] not in visited:
                    visited.append(pair[1])
                    not_visited.remove(pair[1])
                if pair[1] in visited and pair[0] not in visited:
                    visited.append(pair[0])
                    not_visited.remove(pair[0])
        if len(not_visited) == 0:
            return visited
        print(i, visited, not_visited)

ta = time.perf_counter()
with open(sys.argv[1]) as data:
    scanners = {}
    scanner_id = None

    # Read
    for l in data:
        if "scanner" in l:
            m = re.search(r'\d+', l)
            scanner_id = int(m.group(0))
            scanners[scanner_id] = []
        elif l.strip() != '':
            coords = list(map(int,l.strip().split(',')))
            scanners[scanner_id].append(coords)

    # Fingerprint the maps
    scanners_fp = calculate_euclidean_pairs(scanners)

    # Select a sudo probe (sudo means that it has the correct frame):
    sudo_frame = None

    # Define a list of pairs of scanners that need to be checked
    scanner_pairs_to_check = []

    # Define a list of scanners transforms that are in sudo mode
    scanners_frame = {}

    # See which maps have at least 12 beacons in common
    for pair in itertools.combinations(list(range(scanner_id+1)),2):
        set_0 = set([scanners_fp[pair[0]][b].d for b in scanners_fp[pair[0]]])
        set_1 = set([scanners_fp[pair[1]][b].d for b in scanners_fp[pair[1]]])
        m = set_0.intersection(set_1)

        # This is because if at least 12 beacons are in common then
        # N*(N-1)/2 fingerprints will be shared
        if len(m) >= 66:
            scanner_pairs_to_check.append((pair[0], pair[1]))

    # Find the translations
    for pair in scanner_pairs_to_check:
        match_pairs = []
        match_pairs_t = []
        straight_pair = {}
        straight_pair_t = {} 
        straight_pair_data = {}
        straight_pair_data_t = {} 

        # Find a pair of matching points
        for d in scanners_fp[pair[0]]:
            if d in scanners_fp[pair[1]]:
                a, b = scanners_fp[pair[0]][d], scanners_fp[pair[1]][d]
                match_pairs = [a, b]
                match_pairs_t = [b, a]
                rot = find_rot(match_pairs)
                ret = find_rot(match_pairs_t)
                key_rot = (rot[2][0],rot[2][1],rot[2][2])
                key_ret = (ret[2][0],ret[2][1],ret[2][2])
                if rot is not None:
                    if key_rot not in straight_pair:
                        straight_pair[key_rot] = 0
                    straight_pair[key_rot] += 1
                    straight_pair_data[key_rot] = rot
                if ret is not None:
                    if key_ret not in straight_pair_t:
                        straight_pair_t[key_ret] = 0
                    straight_pair_t[key_ret] += 1
                    straight_pair_data_t[key_ret] = ret
                if straight_pair[key_rot] > 1 and straight_pair_t[key_ret] > 1:
                    break
        
        forward_match = max(straight_pair, key=straight_pair.get)
        backward_match = max(straight_pair_t, key=straight_pair_t.get)
        scanners_frame[pair] = straight_pair_data[forward_match]
        scanners_frame[(pair[1],pair[0])] = straight_pair_data_t[backward_match]

    # Find a chain that allows to move from one frame to all the others:
    chain = find_chain(scanner_id, scanners_frame)

    sudo_frame = chain[0]

    non_converted_scanners = list(range(scanner_id+1))
    yes_converted_scanners = []
    next_chain = {chain[0]:chain[0]}
    for i in chain:
        for pair in scanners_frame:
            if pair not in yes_converted_scanners and pair[0] in next_chain.keys() and pair[0] == i and pair[1] not in next_chain.keys():
                t = next_chain[pair[0]]
                d = scanners_frame[pair]
                next_chain[pair[1]] = pair[0]
                yes_converted_scanners.append(pair)

    points_manhattan = [[0,0,0]]

    # Calculate the relative location from any frame
    for s in chain[1:]:
        cf = s
        rot = scanners_frame[(next_chain[cf],cf)][0]
        dir = scanners_frame[(next_chain[cf],cf)][1]
        trn = scanners_frame[(next_chain[cf],cf)][2]
        cf  = next_chain[cf]
        while cf != sudo_frame:
            trn = [trn[scanners_frame[(next_chain[cf],cf)][1][c]] * scanners_frame[(next_chain[cf],cf)][0][c] + scanners_frame[(next_chain[cf],cf)][2][c] for c in range(3)]
            rot = [rot[scanners_frame[(next_chain[cf],cf)][1][c]] * scanners_frame[(next_chain[cf],cf)][0][c] for c in range(3)]
            dir = [dir[scanners_frame[(next_chain[cf],cf)][1][c]] for c in range(3)]
            cf = next_chain[cf]
        points_manhattan.append(trn)

    max = 0
    for pair in itertools.combinations(points_manhattan,2):
        new = m_distance(pair[0], pair[1])
        if new > max: max = new

tb = time.perf_counter()
print(f"Kowalsky I wanna sleep...: {max} {(tb-ta):0.2f}")