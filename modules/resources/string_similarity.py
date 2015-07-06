# _touching() needs a keyboard model lookup table, which we build here

qwerty_US = (
    ( tuple('`1234567890-='),   tuple('~!@#$%^&*()_+')  ),
    ( tuple(' qwertyuiop[]\\'), tuple(' QWERTYUIOP{}|') ),
    ( tuple(" asdfghjkl;'"),    tuple(' ASDFGHJKL:"')   ),
    ( tuple(' zxcvbnm,./'),     tuple(' ZXCVBNM<>?')    ),
)

# lookup table to convert a character into a coordinate on a keyboard
keyboard = {}
x = y = 0
for row in qwerty_US:
    for unshifted, shifted in zip(row[0], row[1]):
        if unshifted != ' ':
            keyboard[unshifted] = (x, y, False)
        
        if shifted != ' ':
            keyboard[shifted]   = (x, y, True)
        
        x += 1
    y += 1
    x = 0

# ----------------------------------------------------------------
# here is vaguely how the similarity() function works

# boron -> cartoon

# note: this grid only uses a replacement cost of 1
#         c   a   r   t   o   o   n
#     |(0)|(1)|(2)|(3)|(4)|(5)|(6)|(7)
#  ---+---+---+---+---+---+---+---+---
#  (0)| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7
# b---+---+---+---+---+---+---+---+---
#  (1)| 1 | 1 | 2 | 3 | 4 | 5 | 6 | 7
# o---+---+---+---+---+---+---+---+---
#  (2)| 2 | 2 | 2 | 3 | 4 | 4 | 5 | 6
# r---+---+---+---+---+---+---+---+---
#  (3)| 3 | 3 | 3 | 2 | 3 | 4 | 5 | 6 
# o---+---+---+---+---+---+---+---+---
#  (4)| 4 | 4 | 4 | 3 | 4 | 3 | 4 | 5
# n---+---+---+---+---+---+---+---+---
#  (5)| 5 | 5 | 5 | 4 | 5 | 4 | 5 | 4 
#  ---+---+---+---+---+---+---+---+---

# boron   -> coron   b->c (0,0)->(1,1) replacement cost: 1
# coron   -> caron   o->a (1,1)->(2,2) replacement cost: 1
# caron   -> caron   r->r (2,2)->(3,3) no change   cost:
# caron   -> carton   ->t (3,3)->(3,4) addition    cost: 1
# carton  -> carton  o->o (3,4)->(4,5) no change   cost:
# carton  -> cartoon  ->o (4,5)->(4,6) addition    cost: 1
# cartoon -> cartoon n->n (4,6)->(5,7) no change   cost:
#                                                 total: 4

def similarity(a, b):
    len_a, len_b = len(a), len(b)
    # grid init values pre-fill top-most and left-most cells correctly
    grid = [[x+y for x in range(len_a + 1)] for y in range(len_b + 1)]
    
    for x in range(1, len_a + 1):
        for y in range(1, len_b + 1):
            
            delete_total  = grid[y][x - 1] + 1 # above
            add_total     = grid[y - 1][x] + 1 # left
            replace_total = (grid[y - 1][x - 1] +
                                _replace_cost(a[x - 1], b[y - 1])) # diagonal
            
            # pick the cheapest option
            grid[y][x] = min(delete_total, add_total, replace_total)
    
    # bottom-right square holds the cheapest route from a to b
    score = grid[-1][-1]
    
    # divide by the max possible score for a relative difference value
    return 1 - ( score / max(max(row) for row in grid) )

def _replace_cost(a, b):
    if a == b:
        return 0
    
    return (_touching(a, b) and 1 or 2)

# keys are touching their shifted value, but not their shifted neighbors
def _touching(a, b):
    # special case for the space bar
    if a == ' ' or b == ' ':
        adjacents = 'cvbnm'
        return (a.lower() in adjacents or b.lower() in adjacents)
    
    # anything missing from our keyboard model is not touching anything
    if a not in keyboard or b not in keyboard:
        return False
    
    a, b = keyboard[a], keyboard[b]
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    if dx > 1 or dy > 1:
        return False
    
    if a[2] == b[2]: # same shift value
        return True
    
    # different shift value, so it needs to be the intended key
    return (dx + dy == 0)
