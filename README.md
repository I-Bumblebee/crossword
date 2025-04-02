## Solution Approach

The solution uses a combination of these algorithms and techniques:

1. **Constraint Satisfaction Problem (CSP) Framework**:
   - Variables: Each word slot in the crossword (horizontal or vertical)
   - Domain: Possible words that could fit in each slot
   - Constraints: Word length, letter overlaps, and all words must be unique

2. **Node Consistency**:
   - Ensures each word in a variable's domain has the correct length
   - Removes words that don't match the required length

3. **Arc Consistency (AC-3 Algorithm)**:
   - Ensures that for any two overlapping variables, every value in one variable's domain has a compatible value in the other's domain
   - Systematically checks and revises domains to maintain consistency between all pairs of variables

4. **Backtracking Search with Heuristics**:
   - Starts with an empty assignment and gradually assigns values to variables
   - Uses two key heuristics to improve efficiency:
     - **Minimum Remaining Values (MRV)**: Selects the variable with the fewest remaining options
     - **Degree Heuristic**: When tied on MRV, chooses the variable with the most constraints on other variables
     - **Least Constraining Value**: Orders domain values to try those that rule out the fewest options for neighbors

## Usage

```
python generate.py data/structure1.txt data/words1.txt output.png
```
