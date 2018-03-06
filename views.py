from ._builtin import Page, WaitPage

from datetime import timedelta
from operator import concat
from functools import reduce
from .models import parse_config

class Introduction(Page):

    def is_displayed(self):
        return self.round_number == 1


class DecisionWaitPage(WaitPage):
    body_text = 'Waiting for all players to be ready'

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()


class Decision(Page):

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()
    

class Results(Page):
    #timeout_seconds = 30

    def vars_for_template(self):
        self.player.set_payoff()
        my_avg_strategy = self.player.get_average_strategy()
        row_player = self.player.id_in_group == 1
        player_average_strategy = self.subsession.get_average_strategy(row_player)
        player_average_payoff = self.subsession.get_average_payoff(row_player)
        return {
            'my_avg_strategy': my_avg_strategy,
            'player_average_strategy': player_average_strategy,
            'player_average_payoff': player_average_payoff,
        }

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

def get_config_columns(group):
    payoffs = group.subsession.payoff_matrix()
    payoffs = reduce(concat, payoffs)
    num_subperiods = group.num_subperiods()
    pure_strategy = group.subsession.pure_strategy()
    config = parse_config(group.session.config['config_file'])
    role_shuffle = config[group.round_number - 1]['shuffle_role']
    return payoffs + [num_subperiods, pure_strategy, role_shuffle]

output_table_header = [
    'session_code',
    'subsession_id',
    'id_in_subsession',
    'tick',
    'p1_strategy',
    'p2_strategy',
    'p1_code',
    'p2_code',
    'payoff1Aa',
    'payoff2Aa',
    'payoff1Ab',
    'payoff2Ab',
    'payoff1Ba',
    'payoff2Ba',
    'payoff1Bb',
    'payoff2Bb',
    'num_subperiods',
    'pure_strategy',
    'role_shuffle',
]

def get_output_table(events):
    if not events:
        return [], []
    rows = []
    minT = min(e.timestamp for e in events if e.channel == 'state')
    maxT = max(e.timestamp for e in events if e.channel == 'state')
    p1, p2 = events[0].group.get_players()
    p1_code = p1.participant.code
    p2_code = p2.participant.code
    group = events[0].group
    config_columns = get_config_columns(group)
    # sets sampling frequency for continuous time output
    ticks_per_second = 2
    if group.num_subperiods() == 0:
        p1_decision = float('nan')
        p2_decision = float('nan')
        for tick in range((maxT - minT).seconds * ticks_per_second):
            currT = minT + timedelta(seconds=(tick / ticks_per_second))
            cur_decision_event = None
            while events[0].timestamp <= currT:
                e = events.pop(0)
                if e.channel == 'group_decisions':
                    cur_decision_event = e
            if cur_decision_event:
                p1_decision = cur_decision_event.value[p1_code]
                p2_decision = cur_decision_event.value[p2_code]
            rows.append([
                group.session.code,
                group.subsession_id,
                group.id_in_subsession,
                tick,
                p1_decision,
                p2_decision,
                p1_code,
                p2_code,
            ] + config_columns)
    else:
        tick = 0
        for event in events:
            if event.channel == 'group_decisions':
                rows.append([
                    group.session.code,
                    group.subsession_id,
                    group.id_in_subsession,
                    tick,
                    event.value[p1_code],
                    event.value[p2_code],
                    p1_code,
                    p2_code,
                ] + config_columns)
                tick += 1
    return output_table_header, rows

page_sequence = [
    Introduction,
    DecisionWaitPage,
    Decision,
    Results
]
