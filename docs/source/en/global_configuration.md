# Election Configuration

## Explanation of the Main Procedure Parameters
The election procedure depends on several parameters, of which the following three are the most important:
- Number of constituencies
- Constituency representation: **Entire Parliament** or **Government Majority**
- Government majority

These three parameters determine the size of the parliament.

Each constituency should have a representative in parliament. From the perspective of a constituency, it can make a difference whether its representative sits in the government faction or not. One could therefore require that each constituency has a representative in the government faction. However, since we also want to grant all parties the right to bring as many of their own candidates into parliament as the voters have directly elected, this results in large parliaments.

Number of constituencies * 2 = Number of government seats = ceil(Government majority in % / 100 * Number of parliament seats) <br>
Parliament seats ≈ int(200 * Number of constituencies / Government majority in %)

With 299 constituencies and a government majority of 55%, this would result in int(200 ∗ 299 / 55) = 1087 parliament seats.

If the requirement for representation through the government majority is waived, the parliament size is simply determined by 2 * Number of constituencies. With 299 constituencies, this would result in 598 parliament seats.

Even with the old election procedure with overhang and compensatory mandates, not every constituency had a representative in the government faction, and nobody was bothered by it.
How much complete representation of all constituencies in the government faction is worth to society is a societal discussion that cannot be anticipated here. In the simulation, constituency representation is therefore configurable so that both cases can be tested.

Parameter name: **ElectionConfig.constituency_representation** <br>
Possible values:
 - **ENTIRE_PARLIAMENT** (Entire Parliament)
 - **GOVERNING_MAJORITY** (Government Majority)

When a yes/no question, such as "Which of two parties should govern?" is decided by voters with only small percentage differences, the result is more likely due to chance than voter intent. There are always people who make their decision only in the voting booth, and had the election been just one day later or earlier, they might have decided differently. Brexit with 51.9% for "Leave" and 48.1% for "Remain" was actually such a decision where both groups were essentially equal in size. They could have just as well drawn lots.

To avoid such stochastic effects, it makes sense to introduce a "minimum winner margin" to win a voting round. This margin can be specified in percentage of votes or in mandates, or can also be expressed as a qualified majority.
In the simulation, there is the **SuperMajorityMargin** class to express a margin either in seats or in percent.

A winner margin makes sense at two points in the procedure:
 - As the possibly granted parliament majority. So that the government retains its majority even if someone is sick, it should have, for example, 10 seats more than half of the parliament seats. Or it should have so many more seats that it has around 5% more votes than the rest of parliament. The parameter to set the "parliament margin" and thus indirectly the parliament majority is **ElectionConfig.parliament_majority_margin**.
 - As the winner threshold of a single voting round. To win a round, a contestant must exceed 50% by a small minimum margin. This is configurable via **ElectionConfig.ballot_majority_margin** (default: 2%, i.e. a contestant needs at least 52%).

## Global Configuration in the Simulation
In the simulation, the [`ElectionConfig`](../../src/ipres/election_config.py) class holds all parameters that are valid for the entire election. These are in detail:

| Parameter                   | Brief Description                                                                                                                                                           |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| constituencies_config       | Table of constituencies                                                                                                                                                     |
| participating_parties       | Participating parties                                                                                                                                                       |
| parliament_majority_margin  | "Parliament margin" in seats or percent. How many parliament seats or vote percent the government should have more than the opposition. See explanation above.               |
| ballot_majority_margin      | Minimum margin above 50% a contestant must reach in a single voting round. Default: 2% (i.e. 52%). See explanation above.                                                  |
| draw_lots_strategy          | Default method for resolving ties. Can be overridden in individual voting rounds. Default value: RANDOM (random)                                                            |
| seed                        | Seed value for the random generator. Default: None (seed value is chosen randomly.)                                                                                         |
| constituency_representation | Constituency representation. Possible values: ENTIRE_PARLIAMENT, GOVERNING_MAJORITY. See explanation in the previous chapter. Default: ENTIRE_PARLIAMENT                   |
| language                    | Output language for tables and charts. Possible values: `Language.DE` (German, default), `Language.EN` (English). Affects column headers, captions, chart titles, and number formatting. |
| seat_distribution_method    | Default method for proportional seat distribution used by `SeatDistributor` and `ElectionEvaluator`. Possible values: `SAINTE_LAGUE`, `D_HONDT`, `HARE_NIEMEYER`. Default: `SAINTE_LAGUE`. Can be overridden in the individual evaluator classes. |
| quota_correction_strategy   | Default strategy for quota correction when parties have an odd seat count, used by `ConstituencyCountDeterminer` and `ElectionEvaluator`. Possible values: `FAVOR_LARGE_PARTIES`, `FAVOR_SMALL_PARTIES`, `PROPORTIONAL`, `PROPORTIONAL_REVERSED`, `RANDOM`, `NEGOTIATED`. Default: `FAVOR_LARGE_PARTIES`. Can be overridden in the individual evaluator classes. |
| constituency_allocation_method | Default algorithm for constituency assignment used by `ConstituencyAssigner` and `ElectionEvaluator`. Possible values: `OPTIMAL`, `GREEDY`, `STABLE_MATCHING`. Default: `OPTIMAL`. Can be overridden in the individual evaluator classes. |
The notebook
[notebooks/en/global_configuration.ipynb](notebooks/en/global_configuration.ipynb) demonstrates the configuration options of the [`ElectionConfig`](../../src/ipres/election_config.py) class.
