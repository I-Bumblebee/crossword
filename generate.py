import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.domains:
            # Create a new set to store valid words
            valid_words = set()
            for word in self.domains[var]:
                # Check if word length matches variable length
                if len(word) == var.length:
                    valid_words.add(word)
            # Update domain with only valid words
            self.domains[var] = valid_words

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        
        # Get the overlap between variables x and y
        overlap = self.crossword.overlaps[x, y]
        
        # If there's no overlap, no revision needed
        if overlap is None:
            return False
        
        # Get the indices where the variables overlap
        i, j = overlap
        
        # Create a copy of the domain to avoid modifying during iteration
        words_to_remove = set()
        
        # Check each word in the domain of x
        for word_x in self.domains[x]:
            # Check if there's any word in y's domain that satisfies the constraint
            if not any(word_x[i] == word_y[j] for word_y in self.domains[y]):
                words_to_remove.add(word_x)
                revised = True
        
        # Remove words that don't satisfy the constraint
        self.domains[x] -= words_to_remove
        
        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # Initialize queue of arcs to process
        if arcs is None:
            queue = [(x, y) for x in self.crossword.variables for y in self.crossword.neighbors(x)]
        else:
            queue = list(arcs)
        
        # Process each arc in the queue
        while queue:
            x, y = queue.pop(0)
            
            # Try to revise the domain of x with respect to y
            if self.revise(x, y):
                # If domain of x is empty, problem is unsolvable
                if len(self.domains[x]) == 0:
                    return False
                
                # Add new arcs for all neighbors of x (except y)
                for z in self.crossword.neighbors(x) - {y}:
                    queue.append((z, x))
        
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        # Check if all variables have been assigned
        return all(var in assignment for var in self.crossword.variables)

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # Check if all values are distinct
        if len(set(assignment.values())) != len(assignment):
            return False
        
        # Check if all values have the correct length
        for var, word in assignment.items():
            if len(word) != var.length:
                return False
        
        # Check if there are no conflicts between neighboring variables
        for var1 in assignment:
            for var2 in assignment:
                if var1 != var2:
                    # Get the overlap between the variables
                    overlap = self.crossword.overlaps[var1, var2]
                    
                    # If there is an overlap, check for conflict
                    if overlap:
                        i, j = overlap
                        if assignment[var1][i] != assignment[var2][j]:
                            return False
        
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # Dictionary to count how many values each domain value rules out
        constraints = {}
        
        # Get unassigned neighbors
        unassigned_neighbors = [n for n in self.crossword.neighbors(var) if n not in assignment]
        
        # For each word in the domain of var
        for word in self.domains[var]:
            count = 0
            
            # Check against each unassigned neighbor
            for neighbor in unassigned_neighbors:
                # Get the overlap
                overlap = self.crossword.overlaps[var, neighbor]
                if overlap:
                    i, j = overlap
                    
                    # Count how many values in the neighbor's domain would be ruled out
                    for neighbor_word in self.domains[neighbor]:
                        if word[i] != neighbor_word[j]:
                            count += 1
                            
            constraints[word] = count
        
        # Sort domain values by the number of constraints they impose
        return sorted(self.domains[var], key=lambda word: constraints[word])

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # Find unassigned variables
        unassigned = [var for var in self.crossword.variables if var not in assignment]
        
        # If no unassigned variables, return None
        if not unassigned:
            return None
        
        # Sort by the minimum remaining value (MRV) heuristic
        # If tied, sort by degree heuristic (number of neighbors)
        return min(
            unassigned,
            key=lambda var: (
                len(self.domains[var]),             # MRV - prefer fewer remaining values
                -len(self.crossword.neighbors(var)) # Degree - prefer more neighbors (negative to sort in descending order)
            )
        )

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # Check if the assignment is complete
        if self.assignment_complete(assignment):
            return assignment
        
        # Select an unassigned variable
        var = self.select_unassigned_variable(assignment)
        
        # Try each value in the domain of the variable
        for value in self.order_domain_values(var, assignment):
            # Create a new assignment with the new value
            assignment[var] = value
            
            # Check if the assignment is consistent
            if self.consistent(assignment):
                # Recursively try to complete the assignment
                result = self.backtrack(assignment)
                if result is not None:
                    return result
            
            # If we reach here, the assignment didn't work, remove the value
            del assignment[var]
        
        # If no value works, return None (backtrack)
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
