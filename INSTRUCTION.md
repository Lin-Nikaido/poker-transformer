# Poker Transformer AI

## Objective

Build a poker AI using PyTorch and a Transformer policy model. The first
milestone is a reproducible workflow from self-play experience collection through
reinforcement learning, inference, and match evaluation. Learn from playing
against the AI's own policies and measure playing strength against fixed opponents.

## Working Specification

The Step 01 MVP specification has been agreed with the user:

- Game: six-max No-Limit Texas Hold'em with no ante. Seats are UTG, MP, CO,
  BTN, SB, and BB. Starting stacks are 100 BB; blinds are 0.5 BB and 1 BB.
- Learning method: reinforcement learning through self-play from the start.
  Train from game rewards without supervised action labels or expert
  demonstrations. External hand-history data is not a prerequisite.
- Actions: fold (`f`), check (`x`), bet (`b`), call (`c`), and raise (`r`).
  Bet and raise sizes are 0.2, 0.5, 0.8, 1.0, 1.5, or 2.0 pot. A bet or raise
  amount equal to 50% of the acting player's stack is treated as all-in. A
  legal-action mask restricts policy choices.
- Model inputs include a six-element stack vector ordered by UTG, MP, CO, BTN,
  SB, and BB. Each element is sourced from that player's game state and passed
  through a dedicated input node. At the start of a hand, the vector naturally
  equals `[100, 100, 100, 100, 100, 100]` BB because each player starts with
  100 BB; stack values follow the game state as play progresses.
- Episodes contain one hand. The terminal reward is each player's net chip
  profit divided by the initial BB, yielding zero-sum rewards. Use PPO.
- Training is divided into epochs. The opponent is the frozen model from the
  previous epoch; the first opponent is a fully random policy.
- Training uses the local machine CPU with a provisional cap of eight CPU hours.
- Interface: CLI for training, inference, and evaluation. Policy inputs include
  the player's own cards, public game state, and observable action history.
  Opponents' private cards and future events must never reach the policy.
- Evaluate separately from training against fixed random, rule-based, and
  frozen-policy opponents. Rotate seats and use at least 20,000 hands against
  the fixed rule-based opponent; target positive mean profit with a 95%
  confidence interval above zero, repeated across seeds.
- Defer distributed training, a web UI, and cloud deployment until the MVP has
  been evaluated.

## Approved Architecture Refinement (2026-10-08)

- Application uses functions only and owns no stateful classes or mutable globals.
- Core GameRunner seats BasePlayer objects and owns UUID v4 player/hand IDs,
  position rotation and hand lifecycle. BaseGameEngine executes one hand;
  PokerKitGameEngine adapts it.
- BasePlayer has HumanPlayer and ModelPlayer implementations. ModelPlayer holds
  `model: nn.Module` directly, with an injected observation encoder and its own
  sampling generator. No mandatory Policy wrapper owns the module.
- GameRunner.run_hand is shared by play and future rollout collection. Application
  play_usecase only calls that method and passes injected observers through.
- Future Core SelfPlayTrainer owns the learner and training counters;
  RolloutCollector gathers learner-local experience, and PPOUpdater updates the
  same learner.model instance. Frozen opponent weights are independent copies.
- Planned CLI names are `learn` and `play`. Complete play uses one human and five
  model players; a random baseline is a pre-training smoke test.
- The first hand preserves the explicit seat order. Later hands rotate and carry
  stacks. The six-player play session stops when a player has no chips. Training
  and evaluation create fresh 100 BB hands at their own episode boundary.
- See ARCH-013 for implemented contracts versus pending learning/CLI work.

## Implementation Session Workflow

- Read this file and the relevant project documents before starting work.
- Use the checklist below as the canonical implementation roadmap across sessions.
- Select the earliest incomplete step whose dependencies are complete.
- Follow AGENTS.md approval gates before significant implementation changes.
- For every step that changes code, finish verification, commit and push the
  changes, and create a pull request before starting the next step. Mark the
  step's implementation work complete only after its pull request is created.
- Mark a step complete only when its acceptance criteria and relevant checks pass.
- Update this file with completed work, evidence, remaining tasks, and blockers
  before ending an implementation session.
- Record approved specification changes here; do not silently replace assumptions.
- Keep unrelated user changes intact.
- Create GitHub Issues only after explicit user approval. Keep the roadmap here.

## Steps

- [x] **01. Define the MVP requirements and evaluation criteria.**
  Confirm the game, player count, stacks, betting rules, action representation,
  reward definition and scaling, RL algorithm, episode boundaries, opponent
  sampling, hardware, and measurable success criteria. Self-play reinforcement
  learning is confirmed and must remain the learning approach.
  Record the agreed specification in this file. Dependencies: none.

- [x] **02. Align the project structure and development environment.**
  Align documentation, package names, and configuration with `src/poker/`;
  remove stale project references where applicable. Add the required PyTorch
  dependencies and verify the CLI and quality checks. Define layer ownership
  for domain logic, model computation, orchestration, and external I/O, including
  the async I/O boundary. Dependencies: 01.

- [x] **03. Define typed poker states and actions.**
  Model cards, public observations, private hands, action history, chip amounts,
  each player's stack, and actions. Validate inputs and prevent
  hidden-information leakage.
  Dependencies: 01, 02.

- [x] **04. Select and integrate a game engine.**
  Evaluate reuse versus implementation and record the decision. Expose state
  transitions, legal actions, and terminal states through a consistent interface.
  Dependencies: 03.

- [x] **05. Verify the MVP game rules.**
  Test betting, raising, all-ins, hand ranking, payouts, and chip conservation
  under the agreed rules, including edge cases. Dependencies: 04.

- [ ] **06. Define the RL environment and reward contract.**
  Expose reset, player observations, legal actions, transitions, rewards, and
  termination. Define per-player terminal chip-profit rewards and their scaling
  subject to Step 01 approval. Test reward signs, zero-sum accounting, episode
  boundaries, and hidden-information isolation.
  Dependencies: 01, 04.

- [ ] **07. Implement self-play experience collection.**
  Collect player-specific observations, legal-action masks, actions, rewards,
  terminal flags, and policy versions. Preserve trajectory ordering and the
  quantities required by the chosen algorithm. Verify collection with simple
  policies first; connect the Transformer after Step 09. Separate training seeds
  and games from fixed evaluation runs. Dependencies: 03, 06.

- [ ] **08. Implement observation and history encoding.**
  At the training/model-input boundary, create a function that converts the full
  player observation and action history into embedding-ready model inputs.
  Include each seat's stack as a dedicated input in UTG, MP, CO, BTN, SB, BB
  order, sourced from the corresponding public player states; at hand start the
  values naturally equal 100 BB. Do not define a standalone domain `StackVector`
  type unless the encoder/model interface later demonstrates that it is needed.
  Share the encoder with inference. Define and test padding, masking, and
  history-length handling. Dependencies: 07.

- [ ] **09. Implement the minimal Transformer policy.**
  Produce action distributions, the agreed bet-size representation, and value
  estimates if required by the selected algorithm. Consume the full encoded
  observation, including the six seat-ordered stack inputs from Step 08. Verify
  tensor shapes, future-information masking, and legal-action masking.
  Dependencies: 05, 08.

- [ ] **10. Add interactive play CLI against a random policy.**
  Allow a person to play a hand from the CLI against an opponent that randomly
  selects from its legal actions. Use this as a pre-training gameplay smoke test
  after the game rules and policy interface are available. Keep the opponent
  behind a policy interface so a constructed or trained model can be selected
  later. Dependencies: 05, 09.

- [ ] **11. Implement RL updates, self-play opponents, and checkpoints.**
  Connect self-play collection to the Transformer and implement the selected
  algorithm's policy and value updates as applicable. Manage frozen historical
  opponents and their sampling alongside current-policy self-play. Verify a small
  collect-update cycle and algorithm-specific handling of policy versions.
  Support saving and resuming model, optimizer, RNG, training counters, and
  opponent-pool state. Record configuration, seeds, rewards, update metrics,
  and policy versions. Dependencies: 07, 09.

- [ ] **12. Implement inference and CLI commands.**
  Load a checkpoint and return legal actions from observations. Share
  preprocessing between training and inference. Expose the agreed training,
  inference, and evaluation entry points. Dependencies: 11.

- [ ] **13. Implement baseline players and match evaluation.**
  Compare against fixed random, simple rule-based, and frozen historical policies.
  Rotate seats and record trial counts, chip-profit metrics, and uncertainty.
  Keep evaluation outside learning updates; self-play rewards alone do not
  demonstrate improved strength. Dependencies: 05, 12.

- [ ] **14. Verify and report the complete MVP.**
  Reproduce self-play collection, RL updates, checkpoint resumption, inference,
  and match evaluation.
  Document results, limitations, and evidence-based improvement candidates.
  Run the required quality checks. Dependencies: 13.

## Current Progress

- Completed: repository and documentation review; roadmap approved by the user.
- Confirmed learning decision: reinforcement learning entirely through self-play;
  supervised training is not part of the plan.
- Step 01 specification recorded from user decisions:
  - Game: six-max No-Limit Texas Hold'em with no ante. Seat names in order are
    UTG, MP, CO, BTN, SB, and BB.
  - Starting stacks are 100 BB per player. Small blind is 0.5 BB and big blind
    is 1 BB.
  - The model receives a six-element stack vector sourced from game state and
    ordered UTG, MP, CO, BTN, SB, BB. At hand start it naturally contains 100 BB
    for each seat and follows the players' stacks during play.
  - Action notation uses fold (`f`), check (`x`), bet (`b`), call (`c`), and
    raise (`r`). Bet and raise sizes are 0.2, 0.5, 0.8, 1.0, 1.5, or 2.0 pot.
    A bet or raise amount equal to 50% of the acting player's stack is treated
    as all-in. A legal-action mask restricts policy choices.
  - Learning is divided into epochs. The opponent is the frozen model from the
    previous epoch; the initial opponent is a fully random policy.
  - Training uses the local machine CPU. The provisional compute cap is eight
    CPU hours, pending a throughput check.
  - Confirmed defaults: terminal net chip profit divided by initial BB as
    reward, one hand per episode, PPO, evaluation against fixed random,
    rule-based, and frozen-policy opponents, and a target of positive mean
    profit with a 95% confidence interval above zero over at least 20,000
    hands against the fixed rule-based opponent, repeated across seeds.
- Implementation steps completed: 01, 02, 03, 04, and 05. Step 05 is in draft
  PR [#3](https://github.com/Lin-Nikaido/poker-transformer/pull/3) from
  `feat/step-05-mvp-game-rules`.
- Next step: 06, define the RL environment and reward contract.
- Step 05 action-size interpretation: `BasePlayer.select_action` resolves each
  pot fraction against the total pot after calling, then adds the actor's
  current street bet and call amount. Size-based targets are clamped to legal
  bounds. A target at least half of the actor's remaining stack is converted
  to the maximum legal target, making the action all-in. Explicit target
  amounts are preserved unless the all-in threshold applies. The engine only
  validates and applies the resolved target amount.
- Step 02 completed: aligned README, architecture guidance, contributing
  instructions, and rulesync overview with the current `src/poker/` package.
  Added the `poker` CLI entry point and configured the PyTorch CPU wheel index.
  Defined ownership for domain/model logic, application orchestration, CLI,
  infrastructure, and the async I/O boundary.
- Step 02 verification: installed Python 3.12.11 and synchronized the locked
  environment. `poker --help`, `uv lock --check`, Ruff format check, Ruff lint,
  and all unit tests passed. The unit suite currently contains one test. Pytest
  settings are centralized in `pyproject.toml`; `pytest.ini` was removed.
  Importing PyTorch reported that optional NumPy support is unavailable; the
  CPU build loaded as `2.14.1+cpu`, and CUDA availability was false.
- Step 03 completed: added typed cards, actions, per-street grouped action
  history, public game state, player observations, private hands, and player
  stacks. `PublicPlayerState` contains public fields; `PlayerState` extends it
  with the private hand, and `get_public_state()`
  returns the public base type. `TableState` revalidates player subclasses
  so private hand fields cannot pass through. Player observations contain
  public state and only the observing player's private hand. All Pydantic
  models use camelCase aliases, allow population by field name, and are
  mutable for game-state updates. `CardRank.DEUCE` names rank two. Stack input
  encoding is deferred to Step 08 and will encode the full observation rather
  than a standalone `StackVector` domain object.
- Step 03 verification: all unit tests passed (3 total), Ruff format and lint
  passed, `uv lock --check` and layer import checks passed. The commit hooks ran
  Archgate successfully (36 rules passed) and found no secrets.
- Step 04 completed: selected PokerKit 0.7.6, an MIT-licensed engine that
  supports No-Limit Texas Hold'em with six players. Added a core game-engine
  port and a PokerKit adapter in `infrastructure/game_engine/`. The adapter
  creates hands with 100 BB stacks, no ante, 0.5/1 BB blinds, exposes the actor,
  legal action kinds and bet/raise bounds, applies actions, and reports terminal
  state. Recorded the selection and layer ownership in ARCH-012. Full player
  observations and transformer-facing policy outputs remain for later steps.
- Step 04 verification: all 21 unit tests passed; Ruff format and lint passed;
  `uv lock --check` resolved 48 packages; `git diff --check` passed; Archgate
  passed all 36 rules.
- Step 05 implementation: `BasePlayer.select_action` converts each `BetSize`
  into a legal target using the pot after calling. Targets at least half of the
  actor's remaining stack become all-in. Explicit target amounts remain exact
  below that threshold. The PokerKit adapter validates and applies resolved
  amounts. Deterministic tests cover all six sizes, 0.8 POT as a 3 BB preflop
  raise, half-stack and larger all-in triggers, uncontested and showdown
  payouts, main/side pots, hand ranking, and chip conservation.
- Step 05 verification: all 18 game-engine tests and all 34 unit tests passed;
  Ruff format and lint passed; Archgate passed all 40 rules; `git diff --check`
  passed. Archgate required running the cached CLI through `npx` because it was
  not on PATH.

- Step 05 architecture refinement: split Core GameRunner from the single-hand engine,
  added stable UUID v4 player/hand IDs, HumanPlayer and direct-module ModelPlayer,
  isolated player observations and applied-action history, GameRunner.run_hand,
  and function-only play_usecase. Recorded the ownership decision in ARCH-013.
  PPO, terminal RL rewards, the full encoder/model, checkpoints and interactive CLI
  remain pending; the mock-input human-plus-five-model integration is implemented.

- Latest Step 05 refactor (`4602460`): `BasePlayer.select_action` now validates
  the request, calls the subclass `_select_action_impl`, and resolves bet/raise
  sizes in its private `_resolve_bet_amount` method. `PublicPlayerState.street_bet`
  distinguishes current-street bets from cumulative `committed` chips. The
  PokerKit engine rejects unresolved `BetSize` inputs and applies explicit
  targets without sizing policy. Model policy traces retain the sampled action
  index after target resolution. ADR-012, ADR-013, `docs/ARCHITECTURE.md`, and
  `.rulesync/rules/architecture.md` record this ownership.

## Session Handoff

Update these fields at the end of each implementation session:

- Active step: 06 (Steps 01-05 complete; Step 05 and its architecture refinement
  are on the existing PR #3 branch).
- Work completed this session: caught up on `4602460` and documented the bet-size
  ownership change and current verification state. The earlier GameRunner/player
  architecture and its ADRs remain in place.
- Verification evidence: before `4602460`, 67 unit tests and 2 integration tests,
  Ruff format/lint, and Archgate (41 rules) passed. The latest refactor has not
  been verified in this session. `tests/unittests/core/players/test_base_player.py`
  and `tests/integration/test_player_bet_sizing.py` are currently untracked.
- Remaining work: define and verify the RL environment and terminal reward
  contract in Step 06, then create its pull request before starting Step 07.
- Blockers: publication status is recorded after local verification; do not update
  branch contents through a GitHub API instead of pushing a local commit.
- Next action: review and track the two new sizing tests, verify the latest
  BasePlayer/engine refactor, then define the RL environment and terminal reward
  contract in Step 06.

