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

    wait_for_all_groups = True

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()


class Decision(Page):

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()
    

class Results(Page):
    timeout_seconds = 30

    def vars_for_template(self):
        if not self.player.payoff:
            self.player.set_payoff()
        row_player = self.player.role() == 'row'
        return {
            'player_average_strategy': self.subsession.get_average_strategy(row_player),
            'player_average_payoff': self.subsession.get_average_payoff(row_player),
        }

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

def get_config_columns(group):
    config = parse_config(group.session.config['config_file'])[group.round_number - 1]
    payoffs = config['payoff_matrix']
    payoffs = reduce(concat, payoffs)

    return payoffs + [
        config['num_subperiods'],
        config['pure_strategy'],
        config['shuffle_role'],
        config['show_at_worst'],
        config['show_best_response'],
        config['rate_limit'],
        config['mean_matching'],
    ]

def get_output_table_header(groups):
    groups_per_silo = groups[0].session.config['groups_per_silo']
    max_num_players = groups_per_silo * 2
    header = [
        'session_code',
        'subsession_id',
        'id_in_subsession',
        'silo_num',
        'tick',
    ]

    for player_num in range(1, max_num_players + 1):
        header.append('p{}_code'.format(player_num))
        header.append('p{}_role'.format(player_num))
        header.append('p{}_strategy'.format(player_num))
        header.append('p{}_target'.format(player_num))
        # 'p1_strategy',
        # 'p2_strategy',
        # 'p1_target',
        # 'p2_target',
        # 'p1_avg',
        # 'p2_avg',
        # 'p1_code',
        # 'p2_code',
    header += [
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
        'show_at_worst',
        'show_best_response',
        'rate_limit',
        'mean_matching',
    ]
    return header

def get_output_table(events):
    if not events:
        return []
    rows = []
    minT = min(e.timestamp for e in events if e.channel == 'state')
    maxT = max(e.timestamp for e in events if e.channel == 'state')
    players = events[0].group.get_players()
    # p1_code = p1.participant.code
    # p2_code = p2.participant.code
    group = events[0].group
    groups_per_silo = group.session.config['groups_per_silo']
    max_num_players = groups_per_silo * 2
    config_columns = get_config_columns(group)
    # sets sampling frequency for continuous time output
    ticks_per_second = 2
    if group.num_subperiods() == 0:
        decisions = {p.participant.code: float('nan') for p in players}
        # p1_decision = float('nan')
        # p2_decision = float('nan')
        targets = {p.participant.code: float('nan') for p in players}
        # p1_target = float('nan')
        # p2_target = float('nan')
        for tick in range((maxT - minT).seconds * ticks_per_second):
            currT = minT + timedelta(seconds=(tick / ticks_per_second))
            cur_decision_event = None
            while events[0].timestamp <= currT:
                e = events.pop(0)
                if e.channel == 'group_decisions':
                    cur_decision_event = e
                elif e.channel == 'target':
                    targets[e.participant.code] = e.value
            if cur_decision_event:
                decisions.update(cur_decision_event.value)
            row = [
                group.session.code,
                group.subsession_id,
                group.id_in_subsession,
                group.silo_num,
                tick,
            ]
            for player_num in range(max_num_players):
                if player_num >= len(players):
                    row += ['', '', '']
                else:
                    pcode = players[player_num].participant.code
                    row += [
                        pcode,
                        players[player_num].role(),
                        decisions[pcode],
                        targets[pcode],
                    ]
            row += config_columns
            rows.append(row)
            # rows.append([
            #     group.session.code,
            #     group.subsession_id,
            #     group.id_in_subsession,
            #     group.silo_num,
            #     tick,
            #     p1_decision,
            #     p2_decision,
            #     p1_target,
            #     p2_target,
            #     row_avg,
            #     col_avg,
            #     p1_code,
            #     p2_code,
            # ] + config_columns)
    else:
        tick = 0
        targets = {p.participant.code: float('nan') for p in players}
        for event in events:
            if event.channel == 'target':
                targets[event.participant.code] = event.value
            elif event.channel == 'group_decisions':
                row = [
                    group.session.code,
                    group.subsession_id,
                    group.id_in_subsession,
                    group.silo_num,
                    tick,
                ]
                for player_num in range(max_num_players):
                    if player_num >= len(players):
                        row += ['', '', '']
                    else:
                        pcode = players[player_num].participant.code
                        row += [
                            pcode,
                            players[player_num].role(),
                            event.value[pcode],
                            targets[pcode],
                        ]
                row += config_columns
                rows.append(row)
                # rows.append([
                #     group.session.code,
                #     group.subsession_id,
                #     group.id_in_subsession,
                #     group.silo_num,
                #     tick,
                #     event.value[p1_code],
                #     event.value[p2_code],
                #     p1_target,
                #     p2_target,
                #     p1_avg,
                #     p2_avg,
                #     p1_code,
                #     p2_code,
                # ] + config_columns)
                tick += 1
    return rows

page_sequence = [
    Introduction,
    DecisionWaitPage,
    Decision,
    Results
]
