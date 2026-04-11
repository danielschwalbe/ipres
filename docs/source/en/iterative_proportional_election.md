# Iterative Proportional Representation with Guaranteed Winner
## Procedure Description

The core of the procedure is an iterative voting process that ensures a party or coalition with a clear governing majority always emerges at the end — without requiring a forced coalition.
In contrast to classical majority voting systems, which also produce winners through non-linearity, the votes of the losers are not lost until the last iteration. Even those whose party has been eliminated are allowed to vote again on the reduced party list and, if necessary, give their vote to another party still in the race according to the "lesser evil" principle.

### Step 1: First Proportional Election

A normal proportional election is conducted. The parties are ranked by their percentage vote share.

- **Is there a winner?** A party or a voluntarily formed coalition reaches an absolute majority (a pre-defined percentage slightly above 50 %, so that the government remains capable of acting even when individual members are absent) → **Procedure finished.**
- **No winner?** → Continue with step 2.

### Step 2: Reduction and New Round

The vote shares are cumulated starting with the strongest party until **two thirds** of all votes are reached or exceeded. Only the parties included in this sum take part in the next round. All voters — including those whose party has been eliminated — may vote again.

The procedure returns to step 1.

### Special Case: Only Two Parties Remaining

- **First round with two parties:** Round is repeated.
- **Second inconclusive round:** A random procedure decides (e.g. minimal percentage differences or drawing of lots).

### Termination

The procedure is guaranteed to terminate because the number of competing parties is reduced in each iteration until finally only two remain.

### Example (three rounds)

| Party | Round 1 | Round 2 | Round 3 |
|-------|---------|---------|---------|
| A     | 28 %    | 35 %    | 52 % ✓  |
| B     | 25 %    | 33 %    | 48 %    |
| C     | 20 %    | 32 %    | –       |
| D     | 15 %    | –       | –       |
| E     | 12 %    | –       | –       |

*After round 1:* A+B+C sum to 73 % ≥ 2/3 → D and E are eliminated.
*After round 2:* A+B sum to 68 % ≥ 2/3 → C is eliminated.
*Round 3:* A reaches 52 % → **A wins.**

## Execution in the Simulation

In the simulation, an election is started by creating an {class}`~ipres.election.Election` object. The constructor expects an {class}`~ipres.election_config.ElectionConfig` object with the global procedure configuration created in the first step.

The procedure is started using the {meth}`Election.run() <ipres.election.Election.run>` or the {meth}`Election.start() <ipres.election.Election.start>` method. The {meth}`Election.run() <ipres.election.Election.run>` method executes the entire procedure, while the {meth}`Election.start() <ipres.election.Election.start>` method only executes the first round and returns a reference to the executed round. This allows interactive intervention in the voting process, for example to form coalitions or to test the effect of individual parameters.

**Automatic run**:

```python
election = Election(electionConfig=config)
final_round = election.run()
print(final_round.getWinner().name)
```

A round is represented by an instance of the {class}`~ipres.election_round.ElectionRound` class. The {class}`~ipres.election_round.ElectionRound` class knows whether another round is required or not. If so, it returns the input for the next round. This can optionally be overridden manually to specifically test certain use cases.

A voting round is executed by calling {meth}`ElectionRound.run() <ipres.election_round.ElectionRound.run>`. ({meth}`Election.start() <ipres.election.Election.start>` also calls {meth}`ElectionRound.run() <ipres.election_round.ElectionRound.run>` internally.) The class method {meth}`ElectionRound.run() <ipres.election_round.ElectionRound.run>` takes an {class}`~ipres.election_round.ElectionRoundInput` object as a parameter and returns an {class}`~ipres.election_round.ElectionRound` object with the result of the executed voting round. Depending on whether it was a real election round or a drawing of lots, the result is an instance of {class}`~ipres.ballot.Ballot` or {class}`~ipres.draw_of_lots.DrawOfLots`. Both classes are subclasses of {class}`~ipres.election_round.ElectionRound`.

The procedure is only complete when there is a winner. In this case, {meth}`ElectionRound.hasNext() <ipres.election_round.ElectionRound.hasNext>` returns `False` and {meth}`ElectionRound.hasWinner() <ipres.election_round.ElectionRound.hasWinner>` is `True`.
Only then can the election be evaluated.

By forming coalitions, a round that ended without a winner can retrospectively receive a winner. Coalitions are created by calling {meth}`Ballot.formCoalition() <ipres.ballot.Ballot.formCoalition>`. Note that coalitions can only be formed after a voting round and, once formed, must remain together until the end of the procedure — this ensures that the number of participants is reduced in each round.

For details on `Contestant` and coalition formation see the notebook [Contestant](../../notebooks/en/contestant.ipynb).

**Manual run with coalition formation:**

```python
election = Election(electionConfig=config)
round1 = election.start()

if not round1.hasWinner():
    round1.formCoalition("A+B", ["A", "B"])

while not election.hasWinner():
    election.runNextIteration()

print(election.getWinner().name)
```

### Vote Injection

By default, the simulation generates votes randomly based on probabilities and turnout from the configuration. For tests, demonstrations, or the analysis of specific scenarios, votes can also be provided as fixed values.

For the first round, {meth}`Election.start() <ipres.election.Election.start>` accepts an optional `votes` parameter:

```python
round1 = election.start(votes={'A': 28, 'B': 25, 'C': 20, 'D': 15, 'E': 12})
```

For subsequent rounds, the method {meth}`ElectionRoundInput.with_votes() <ipres.election_round.ElectionRoundInput.with_votes>` is available on the input returned by {meth}`ElectionRound.getNextRoundInput() <ipres.election_round.ElectionRound.getNextRoundInput>`:

```python
round2 = election.runNextIteration(
    iterationInput=round1.getNextRoundInput().with_votes({'A': 35, 'B': 33, 'C': 32})
)
```

`getNextRoundInput()` returns the prepared input for the next round — carrying over all settings (remaining contestants, threshold, strategy, etc.) but without votes. `with_votes()` adds the desired vote counts and returns a new copy of the input with the specified votes.

For multiple constituencies, pass a nested dict:

```python
round1.getNextRoundInput().with_votes({
    'C1': {'A': 35, 'B': 33, 'C': 32},
    'C2': {'A': 40, 'B': 30, 'C': 30},
})
```
### Relevant Configuration Parameters

#### `ballot_majority_margin` — Ballot threshold

`ballot_majority_margin` controls at what vote share a single round produces a winner (default: 2% above 50% = 52%). It is independent of `parliament_majority_margin`. The margin can be specified in percent (`MarginUnit.PERCENT`) or in seats (`MarginUnit.SEATS`).

#### `DrawLotsStrategy` — Lot strategy

When two parties fail to produce a winner in two consecutive rounds, the third round is decided by lot:

- **`DrawLotsStrategy.RANDOM`** *(default)*: uniform random draw.
- **`DrawLotsStrategy.MARGINAL_LEAD`**: The marginal vote difference is treated as a random outcome — the party that happened to receive slightly more votes wins.
