# Authors: Calvin Chen, Safin Shihab

import sys

# Used to store the values a cell cannot be
# and the indicies of the cells greater/less than it
class Cell:
    def __init__(self):
        self.greater = set()
        self.less = set()
        self.domainC = set()


# Parameters:
# gt - int (0-24) index of cell greater than
# lt - int (0-24) index of cell less than
# arrowCells list(Cell) - stores arrow-influenced constraints of each cell, 
# and domain complement based on arrow
# affected - set of all cell indicies that are constrained by arrows
# 
# Description:
# Stores constraint between two cells, and logs that 
# they have an arrow constraint
def addLink(gt, lt, arrowCells, affected):
    arrowCells[gt].less.add(lt)
    arrowCells[lt].greater.add(gt)
    affected.add(gt)
    affected.add(lt)


# Parameters:
# board- list(int): stores current assigned values of board state
# 
# Output:
# row_domainC - list(set): stores set of all values within each row
# column_domainC - list(set): stores set of all values within each column

# Description:
# Stores the values each row and column the initial board state
# contains in vector of sets
def initialize_rc_domainC(board):
    row_domainC = [set() for i in range(5)]
    column_domainC = [set() for i in range(5)]

    for i in range(5):
        for j in range(5):
            if board[5 * i + j] != 0:
                row_domainC[i].add(board[5 * i + j])
                column_domainC[j].add(board[5 * i + j])
    return row_domainC, column_domainC

# Parameters:
# board- list(int): stores current assigned values of board state
# row_arrows - list(char): stores arrows signifying horizontal constraints between neighboring cells
# col_arrows - list(char): stores arrows signifying vertical constraints between neighboring cells 

# Output:
# arrowCells list(Cell) - stores arrow-influenced constraints of each cell, 
# and domain complement based on arrow

# Description: Store constraints between cells imposed by arrows and  the complement of each cell's 
# domain from said constraints
def initialize_arrow_domain(board, row_arrows, col_arrows):
    arrowCells = [Cell() for x in board]
    affected = set()

    # Stores the constraint from each arrow in row_arrows and col_arrows
    # in their corresponding cell of arrowCells
    for i in range(len(row_arrows)):
        row_idx = 5 * (i // 4) + i % 4
        col_idx = i
        if row_arrows[i] == '<':
            addLink(row_idx + 1, row_idx, arrowCells, affected)
        elif row_arrows[i] == '>':
            addLink(row_idx, row_idx + 1, arrowCells, affected)
        if col_arrows[i] == '^':
            addLink(col_idx + 5, col_idx, arrowCells, affected)
        elif col_arrows[i] == 'v':
            addLink(col_idx, col_idx + 5, arrowCells, affected)
    
    # For all elements affected by arrows, we want to find the values 
    # that the arrows don't allow for each empty affected cell to be
    # When one cell is greater than another, it can not be 1 or then 
    # the value of the other cell must be 0.  Similarly, when a cell is 
    # smaller, it can not be 5.
    for elem in affected:
        if board[elem] != 0:
            for cell in arrowCells[elem].greater:
                for i in range(board[elem] + 1):
                    arrowCells[cell].domainC.add(i)
            for cell in arrowCells[elem].less:
                for i in range(board[elem], 6):
                    arrowCells[cell].domainC.add(i)
        elif len(arrowCells[elem].less) > 0:
            arrowCells[elem].domainC.add(1)
            for cell in arrowCells[elem].less:
                arrowCells[cell].domainC.add(5)

    # When there are chains of arrows where x > y > z, the domains of these 
    # cells decreases as the chains grow longer.  The current state of each cell's domain
    # limits the domain at most by two, but these chains can further restrict the domains
    # to even a single value. The cells are filled in until there exists no more discrepancies.
    # Since the domain has a max size of 5, the while loop can increment a total of 4 + 1 times (+1 being the last check)
    changed = True
    while changed:
        li = [i.domainC for i in arrowCells]
        changed = False
        for elem in affected:
            if board[elem] == 0:
                upper = 0
                lower = 6
                for cell in arrowCells[elem].greater:
                    i = 5
                    while i > 0 and i in arrowCells[cell].domainC:
                        i -= 1
                    lower = min(lower, i)
                for cell in arrowCells[elem].less:
                    i = 1
                    while i < 6 and i in arrowCells[cell].domainC:
                        i += 1
                    upper = max(upper, i)

                if lower not in arrowCells[elem].domainC and lower != 6:
                    changed = True
                    for i in range(lower, 6):
                        arrowCells[elem].domainC.add(i)
                if upper not in arrowCells[elem].domainC and upper != 0:
                    changed = True
                    for i in range(1, upper + 1):
                        arrowCells[elem].domainC.add(i)

    return arrowCells

# Parameters:
# index - int (0-24): cell's index whose degree is being calculated
# board- list(int): stores current assigned values of board state
# arrowCells list(Cell) - stores arrow-influenced constraints of each cell, 
# and domain complement based on arrow

# Output:
# int: number of empty cells whose domain is affected by cell at index

# Description:
# Finds the number of empty cells whose domain is affected by cell at index
def degree(index, board, arrowCells):
    influenced = set()
    row_start = 5 * (index // 5)
    column_start = index % 5
    for i in range(5):
        if board[row_start + i] != 0:
            influenced.add(row_start + i)
        if board[column_start + 5 * i] != 0:
            influenced.add(column_start + 5 * i)
    
    if index in influenced:
        influenced.remove(index)
    
    findLessCells(index, arrowCells, influenced)
    findGreaterCells(index, arrowCells, influenced)
    return len(influenced)

# Parameters:
# board- list(int): stores current assigned values of board state
# row_domain- list(set): stores values each row cotains
# col_domain - list(set): stores values each column contains
# arrowCells list(Cell) - stores arrow-influenced constraints of each cell, 
# and domain complement based on arrow

# Output:
# max_idx- int (0-24): index of selected Cell
# max_domain- set: set of all possible values board[max_index] can BaseException

def selectVar(board, row_domain, col_domain, arrowCells):
    max_idx = None
    max_domainC = {}
    max_degree = 0

    for i in range(len(board)):
        if board[i] == 0:
            curr_domain = row_domain[i // 5].union(col_domain[i % 5]).union(arrowCells[i].domainC)
            if len(curr_domain) == 5:
                return None, {}
            curr_degree = degree(i, board, arrowCells) 
            if len(curr_domain) > len(max_domainC) or (
                    curr_degree == len(max_domainC) and curr_degree > max_degree):
                max_idx = i
                max_domainC = curr_domain
    universal = {1, 2, 3, 4, 5}
    max_domain = universal.difference(max_domainC)
    return max_idx, max_domain

# Parameters:
# index- int(0-24): cell's index whose arrow constraints will be added to affected
# arrowCells list(Cell) - stores arrow-influenced constraints of each cell, 
# and domain complement based on arrow
# affected - set(int): set to add all indicies of cells less than index into

# Description: Recursively explore through the arrow constraints to add the indicies of all
# adjacent cells with greater than cell at index into affected set
def findGreaterCells(index, arrowCells, affected):
    affected.add(index)
    for elem in arrowCells[index].greater:
        if elem not in affected:
            findGreaterCells(elem, arrowCells, affected)

# Parameters:
# index- int(0-24): cell's index whose arrow constraints will be added to affected
# arrowCells list(Cell) - stores arrow-influenced constraints of each cell, 
# and domain complement based on arrow
# affected - set(int): set to add all indicies of cells less than index into

# Description: Recursively explore through the arrow constraints to add the indicies of all
# adjacent cells with greater than cell at index into affected set
def findLessCells(index, arrowCells, affected):
    affected.add(index)
    for elem in arrowCells[index].less:
        if elem not in affected:
            findGreaterCells(elem, arrowCells, affected)

# Parameters:
# changed_idx- int(0-24): index of recently assigned board cell
# board- list(int): stores current assigned values of board state
# arrowCells list(Cell) - stores arrow-influenced constraints of each cell, 
# and domain complement based on arrow

# Output: 
# changes_dict- dict: stores all changes made in update, to allow for easier resetting of 
# board[changed_idx] if needed

# Description: 
# updates the domains held in arrowCells based on the assignment at board[changed_idx], and stores
# all changes made
def updateArrowDomains(changed_idx, board, arrowCells):
    def updateCells(index, arrowCells, changes):
        upper = 1
        lower = 5
        while lower > 0 and lower in arrowCells[index].domainC:
            lower -= 1

        while upper < 6 and upper in arrowCells[index].domainC:
            upper += 1

        for elem in arrowCells[index].greater:
            curr_len = len(arrowCells[elem].domainC)
            for i in range(1, upper + 1):
                if i not in arrowCells[elem].domainC:
                    changes[elem].add(i)
                    arrowCells[elem].domainC.add(i)
            if len(arrowCells[elem].domainC) != curr_len:
                updateCells(elem, arrowCells, changes)
        for elem in arrowCells[index].less:
            curr_len = len(arrowCells[elem].domainC)
            for i in range(lower, 6):
                if i not in arrowCells[elem].domainC:
                    arrowCells[elem].domainC.add(i)
                    changes[elem].add(i)
            if len(arrowCells[elem].domainC) != curr_len:
                updateCells(elem, arrowCells, changes)

    changes = [set() for x in range(len(board))]

    for elem in arrowCells[changed_idx].greater:
        curr_len = len(arrowCells[elem].domainC)
        for i in range(1, board[changed_idx] + 1):
            if i not in arrowCells[elem].domainC:
                arrowCells[elem].domainC.add(i)
                changes[elem].add(i)
        if len(arrowCells[elem].domainC) != curr_len:
            updateCells(elem, arrowCells, changes)

    for elem in arrowCells[changed_idx].less:
        curr_len = len(arrowCells[elem].domainC)
        for i in range(board[changed_idx], 6):
            if i not in arrowCells[elem].domainC:
                arrowCells[elem].domainC.add(i)
                changes[elem].add(i)
        if len(arrowCells[elem].domainC) != curr_len:
            updateCells(elem, arrowCells, changes)

    changes_dict = {}
    for elem in range(len(changes)):
        if len(changes[elem]) > 0:
            changes_dict[elem] = tuple(changes[elem])

    return changes_dict

# Parameters:
# board- list(int): stores current assigned values of board state
# row_domain- list(set): stores values each row cotains
# col_domain - list(set): stores values each column contains
# arrowCells list(Cell) - stores arrow-influenced constraints of each cell, 
# and domain complement based on arrow

# Output:
# bool: returns success of full-board assignment

# Description:
# Recursive function for filling out futoshiki board based on known constraints
def backtrack(board, row_domain, col_domain, arrowCells):
    idx, domain = selectVar(board, row_domain, col_domain, arrowCells)
    if idx is None:
        return all([x != 0 for x in board])
    for elem in domain:
        board[idx] = elem
        row_domain[idx // 5].add(elem)
        col_domain[idx % 5].add(elem)
        changed = updateArrowDomains(idx, board, arrowCells)
        success = backtrack(board, row_domain, col_domain, arrowCells)
        if success:
            return True
        else:
            row_domain[idx // 5].remove(elem)
            col_domain[idx % 5].remove(elem)
            for key in changed:
                for val in changed[key]:
                    arrowCells[key].domainC.remove(val)

    board[idx] = 0
    return False

# for debugging
def printArrows(x):
    li = [i.domainC for i in x]

    for i in range(5):
        for j in range(5):
            print(li[5 * i + j], end=' ')
        print()
    print("___________________________________________________")

# for debugging
def printBoard(x):
    for i in range(5):
        for j in range(5):
            print(x[5 * i + j], end=' ')
        print()
    print("___________________________________________________")

# parse file function
def readFile(file_name):
    count = 0
    board = []
    row_arrows = []
    col_arrows = []
    try:
        with open(file_name, 'r') as file_obj:
            for item in file_obj.readlines():
                data = item.split()
                if data:
                    if count == 0:
                        board += ((int(i) for i in data))
                    elif count == 1:
                        row_arrows += ((int(i) if i.isdigit() else i for i in data))
                    elif count == 2:
                        col_arrows += ((int(i) if i.isdigit() else i for i in data))
                else:
                    count += 1
        return board, row_arrows, col_arrows
    except FileNotFoundError:
        return []

# output completed board function
def outputFile(file, board):
    try:
        with open(file, 'w') as f:
            for i in range(5):
                for j in range(5):
                    f.write(str(board[5 * i + j]))
                    f.write(' ')
                f.write('\n')
    except FileNotFoundError:
        return []


def main():
    board, row_arrows, col_arrows = readFile(sys.argv[1])
    row_domainC, column_domainC = initialize_rc_domainC(board)
    arrowCells = initialize_arrow_domain(board, row_arrows, col_arrows)

    backtrack(board, row_domainC, column_domainC, arrowCells)
    # printBoard(board)
    outputFile(sys.argv[2], board)

main()