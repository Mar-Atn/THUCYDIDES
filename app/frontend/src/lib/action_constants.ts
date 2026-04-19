/**
 * Shared action constants — labels, categories, positions, conditions.
 * Single source of truth for all action-related display data.
 * Used by TabRoles (role detail) and TabActions (action permission matrix).
 */

export const ACTION_LABELS: Record<string, string> = {
  // Military
  ground_attack: 'Ground Attack',
  air_strike: 'Air Strike',
  naval_combat: 'Naval Combat',
  naval_bombardment: 'Naval Bombardment',
  launch_missile_conventional: 'Missile Launch (conventional)',
  naval_blockade: 'Naval Blockade',
  move_units: 'Move Units',
  ground_move: 'Ground Movement',
  // Nuclear
  nuclear_test: 'Nuclear Test',
  nuclear_launch_initiate: 'Nuclear Launch',
  nuclear_authorize: 'Nuclear Authorize',
  nuclear_intercept: 'Nuclear Intercept',
  // Economic
  set_budget: 'Set Budget',
  set_tariffs: 'Set Tariffs',
  set_sanctions: 'Set Sanctions',
  set_opec: 'Set Oil Production',
  // Diplomatic
  declare_war: 'Declare War',
  propose_agreement: 'Propose Agreement',
  sign_agreement: 'Sign Agreement',
  propose_transaction: 'Propose Transaction',
  accept_transaction: 'Accept Transaction',
  basing_rights: 'Basing Rights',
  // Political
  arrest: 'Arrest',
  reassign_types: 'Reassign Powers',
  martial_law: 'Martial Law',
  change_leader: 'Change Leader',
  cast_vote: 'Cast Vote',
  // Covert
  intelligence: 'Intelligence',
  covert_operation: 'Covert Operation',
  assassination: 'Assassination',
  // Columbia Elections
  self_nominate: 'Self-Nominate',
  cast_election_vote: 'Cast Election Vote',
  // Communication
  public_statement: 'Public Statement',
  call_org_meeting: 'Call Org Meeting',
  publish_org_decision: 'Publish Org Decision',
  invite_to_meet: 'Invite to Meet',
  accept_meeting: 'Accept Meeting',
  // Legacy
  meet_freely: 'Meet Freely',
}

export const ACTION_CATEGORIES: Record<string, string[]> = {
  'Military': ['ground_attack', 'air_strike', 'naval_combat', 'naval_bombardment', 'launch_missile_conventional', 'naval_blockade', 'move_units', 'ground_move'],
  'Nuclear Chain': ['nuclear_test', 'nuclear_launch_initiate', 'nuclear_authorize', 'nuclear_intercept'],
  'Economic': ['set_budget', 'set_tariffs', 'set_sanctions', 'set_opec'],
  'Diplomatic': ['declare_war', 'propose_agreement', 'sign_agreement', 'propose_transaction', 'accept_transaction', 'basing_rights'],
  'Political': ['arrest', 'reassign_types', 'martial_law', 'change_leader', 'cast_vote'],
  'Covert & Intelligence': ['intelligence', 'covert_operation', 'assassination'],
  'Columbia Elections': ['self_nominate', 'cast_election_vote'],
  'Communication': ['public_statement', 'call_org_meeting', 'publish_org_decision', 'invite_to_meet', 'accept_meeting'],
}

/** Action type classification */
export const REACTIVE_ACTIONS = new Set([
  'nuclear_authorize', 'nuclear_intercept', 'accept_transaction',
  'sign_agreement', 'cast_vote', 'cast_election_vote', 'accept_meeting',
])

/** Position labels for display */
export const POSITION_LABELS: Record<string, string> = {
  head_of_state: 'Head of State',
  military: 'Military',
  economy: 'Economy',
  diplomat: 'Diplomat',
  security: 'Security',
  opposition: 'Opposition',
}

/** Which positions get each proactive action (for display in the UI) */
export const ACTION_POSITIONS: Record<string, string[]> = {
  // HoS + Military
  ground_attack: ['head_of_state', 'military'],
  air_strike: ['head_of_state', 'military'],
  naval_combat: ['head_of_state', 'military'],
  naval_bombardment: ['head_of_state', 'military'],
  launch_missile_conventional: ['head_of_state', 'military'],
  naval_blockade: ['head_of_state', 'military'],
  move_units: ['head_of_state', 'military'],
  ground_move: ['head_of_state', 'military'],
  // HoS only
  declare_war: ['head_of_state'],
  reassign_types: ['head_of_state'],
  nuclear_test: ['head_of_state'],
  nuclear_launch_initiate: ['head_of_state'],
  // HoS + Security
  arrest: ['head_of_state', 'security'],
  // HoS + Economy
  set_budget: ['head_of_state', 'economy'],
  set_tariffs: ['head_of_state', 'economy'],
  set_sanctions: ['head_of_state', 'economy'],
  set_opec: ['head_of_state', 'economy'],
  // HoS + Diplomat
  propose_agreement: ['head_of_state', 'diplomat'],
  propose_transaction: ['head_of_state', 'diplomat'],
  basing_rights: ['head_of_state', 'diplomat'],
  // Security + Military
  intelligence: ['security', 'military', 'diplomat', 'opposition'],
  covert_operation: ['security', 'military'],
  assassination: ['security', 'military'],
  // Dynamic
  martial_law: ['head_of_state'],
  // Universal
  public_statement: ['all'],
  invite_to_meet: ['all'],
  change_leader: ['all'],
  // Org-based
  call_org_meeting: ['org_members'],
  publish_org_decision: ['org_chairman'],
  // Columbia
  self_nominate: ['opposition'],
  // Reactive (shown for reference, not stored)
  nuclear_authorize: ['2 per country (priority)'],
  nuclear_intercept: ['head_of_state', 'military'],
  accept_transaction: ['head_of_state', 'diplomat'],
  sign_agreement: ['head_of_state', 'diplomat'],
  cast_vote: ['all'],
  cast_election_vote: ['all'],
  accept_meeting: ['all'],
}

/** Action conditions (dynamic) */
export const ACTION_CONDITIONS: Record<string, string> = {
  nuclear_test: 'nuclear_level >= 1',
  nuclear_launch_initiate: 'nuclear_confirmed = true',
  nuclear_intercept: 'Missile in flight + nuclear_level >= 2 + confirmed',
  nuclear_authorize: 'Nuclear launch pending in own country',
  set_opec: 'OPEC+ member country',
  martial_law: 'Eligible country + not yet declared',
  move_units: 'Phase B only (inter-round)',
  change_leader: 'Stability <= threshold (or HoS voluntary)',
  launch_missile_conventional: 'Country has deployed missiles',
  accept_transaction: 'Transaction proposed to country',
  sign_agreement: 'Agreement proposed to country',
  cast_vote: 'Leadership vote active in country',
  cast_election_vote: 'Election nomination open (Columbia)',
  self_nominate: 'Election round, moderator confirmed (Columbia)',
  accept_meeting: 'Meeting invitation received',
}
