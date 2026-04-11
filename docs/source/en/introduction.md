# The Electoral Procedure

## Introduction and Motivation

Germany uses a form of proportional representation. The goal of proportional representation is to reflect the major forces in society approximately proportionally in parliament. This is intended to increase public acceptance of parliament and promote social stability. The drawback of this system is obvious: when there are many parties, it is relatively unlikely that any single party can win an outright majority on its own. This leads to the necessity of often unwanted coalitions, in which the partners block each other and none can truly keep their campaign promises. Alternatively, election gifts are distributed repeatedly — each coalition partner tries to satisfy its own clientele, and in the end the budget becomes impossible to finance.

The proposed electoral procedure suggests a compromise: limiting the reflection of the balance of power in society to the opposition. Through an iterative process, voting continues until a winning party is determined. Coalitions remain possible, but unlike before, they are no longer forced when no party achieves an outright majority in the first round. The procedure ensures that a winning party emerges that has been chosen by at least half of the voters — even if for many it was only a choice of "the lesser evil." This winning party (or coalition) is awarded a majority of seats. The remaining seats are then distributed proportionally among the opposition parties based on the result of the first round.

A German peculiarity is the "personalized proportional representation." The "second vote" (Zweitstimme) determines the proportional share of each party, while the "first vote" (Erststimme) allows voters to elect specific candidates into parliament, provided the party has sufficient second-vote coverage. Under the current system used for German federal elections, it can happen that individual constituencies have no representation in parliament, because the winning candidate's party has no remaining seat for the direct candidate after the second-vote apportionment. Under the previously used system this could not happen — but the Bundestag grew increasingly large as discrepancies between first- and second-vote results widened. This is why the old system was replaced by the current one.

The proposed procedure departs from the principle of the constituency winner as the mechanism for electing direct candidates. Instead, parties would be required to field three candidates per constituency. Voters may cast a "candidate vote" (Erststimme) for their preferred candidate in any party standing in their constituency, even if it is not their own party. Each voter has one candidate vote per party in their constituency. Based on a procedure that determines the **relative importance** of a constituency for a party using the distribution of party votes (Zweitstimmen) across constituencies, constituencies are assigned to parties for representation. The candidate with the most candidate votes from the representing party is elected to parliament.

This procedure guarantees that every constituency is represented in parliament and that the party vote result (Zweitstimmenergebnis) is preserved with an unchanged parliament size. It cannot guarantee that the representing person is always the candidate with the most candidate votes across all parties in a constituency — only that they are the candidate with the most candidate votes within the representing party in that constituency.

**Note**: The selection of parliamentary members from the three direct candidates per party based on their candidate vote result is not part of the simulation, as this is trivial and would only add unnecessary complexity. All votes in this simulation are party votes. What is non-trivial — and therefore part of the simulation — is the assignment of parties to constituencies based on the party vote distribution.

---

## Overview of Procedure Steps

The procedure consists of several steps. The simulation is designed so that an entire election can be configured upfront and run end-to-end in a single pass, or each step can be executed individually. Note that some steps depend not only on previous rounds but also on initial configuration parameters.

### 1. Global Configuration
First, the following must be defined:
- Which constituencies exist
- Which parties participate in the election
- How large the government majority should be
- Whether constituencies should be represented by the entire parliament or only by the government majority. **Note**: This determines the size of parliament. For details see [Global Configuration](global_configuration.md)

### 2. Iterative Proportional Representation with Guaranteed Winner
An iterative proportional vote is conducted that guarantees a winning party or coalition. For details see [Iterative Proportional Representation](iterative_proportional_election.md)

### 3. Evaluation
Once the electoral process is complete, the evaluation takes place. It consists of the following three phases:
- [Seat allocation](seat_allocation.md) 
- [Constituency count determination per party](constituency_count_determination.md)
- [Constituency assignment by relative importance](constituency_assignment.md)

`ElectionEvaluator.evaluate()` runs all three steps automatically in the correct order. The individual classes `SeatDistributor`, `ConstituencyCountDeterminer`, and `ConstituencyAssigner` can also be called independently if needed.

An interactive demonstration of all three steps with their configuration options is provided in the notebook [Election Evaluation](../../notebooks/en/election_evaluation.ipynb).
