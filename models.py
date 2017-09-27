# -*- coding: utf-8 -*-
from __future__ import division

from django.contrib.contenttypes.models import ContentType
from otree.constants import BaseConstants
from otree.models import BasePlayer, BaseSubsession

from otree_redwood.models import Event, DecisionGroup

doc = """
This is a configurable bimatrix game.
"""


class Constants(BaseConstants):
    name_in_url = 'bimatrix'
    players_per_group = 2
    num_rounds = 12

    payoff_matrices = [
        [
            [800, 0], [0, 200],
            [0, 200], [200, 0],
        ],
        [
            [500, 100], [0, 200],
            [0, 200], [300, 0],
        ],
        [
            [300, 300], [0, 800],
            [800, 0], [100, 100],
        ],
        [
            [300, 400], [100, 0],
            [0, 100], [400, 300],
        ]
    ]

    base_points = 0

    # Amount of time the game stays on the decision page in seconds.
    period_length = 120


class Subsession(BaseSubsession):
    def before_session_starts(self):
        self.group_randomly()

    def payoff_matrix(self):
        roundno = self.round_number

        if roundno in [1, 2, 3]:
            return Constants.payoff_matrices[2]
        elif roundno in [4, 5, 6]:
            return Constants.payoff_matrices[3]
        elif roundno in [7, 8, 9]:
            return Constants.payoff_matrices[0]
        elif roundno in [10, 11, 12]:
            return Constants.payoff_matrices[1]
        else:
            print("invalid round number!")

    def pure_strategy(self):
        return self.round_number % 2 == 0


class Group(DecisionGroup):

    def num_subperiods(self):
        roundno = self.round_number

        if roundno in [1, 2, 3]:
            return None
        elif roundno in [4, 5, 6]:
            return 10
        elif roundno in [7, 8, 9]:
            return None
        elif roundno in [10, 11, 12]:
            return 10
        else:
            print("invalid round number!")

    def period_length(self):
        return Constants.period_length


class Player(BasePlayer):

    def initial_decision(self):
        return 0.5

    def other_player(self):
        return self.get_others_in_group()[0]

    def set_payoff(self):
        decisions = list(Event.objects.filter(
                channel='decisions',
                content_type=ContentType.objects.get_for_model(self.group),
                group_pk=self.group.pk).order_by("timestamp"))

        try:
            period_start = Event.objects.get(
                    channel='state',
                    content_type=ContentType.objects.get_for_model(self.group),
                    group_pk=self.group.pk,
                    value='period_start')
            period_end = Event.objects.get(
                    channel='state',
                    content_type=ContentType.objects.get_for_model(self.group),
                    group_pk=self.group.pk,
                    value='period_end')
        except Event.DoesNotExist:
            return float('nan')

        payoff_matrix = self.subsession.payoff_matrix()

        self.payoff = self.get_payoff(period_start, period_end, decisions, payoff_matrix)
        

    def get_payoff(self, period_start, period_end, decisions, payoff_matrix):
        period_duration = period_end.timestamp - period_start.timestamp

        payoff = 0

        Aa = payoff_matrix[0][self.id_in_group-1]
        Ab = payoff_matrix[1][self.id_in_group-1]
        Ba = payoff_matrix[2][self.id_in_group-1]
        Bb = payoff_matrix[3][self.id_in_group-1]

        if self.id_in_group == 1:
            row_player = self.participant
            q1, q2 = self.initial_decision(), self.other_player().initial_decision()
        else:
            row_player = self.other_player().participant
            q2, q1 = self.initial_decision(), self.other_player().initial_decision()

        q1, q2 = 0.5, 0.5
        for i, d in enumerate(decisions):
            if d.participant == row_player:
                q1 = d.value
            else:
                q2 = d.value
            flow_payoff = ((Aa * q1 * q2) +
                           (Ab * q1 * (1 - q2)) +
                           (Ba * (1 - q1) * q2) +
                           (Bb * (1 - q1) * (1 - q2)))

            if i + 1 < len(decisions):
                next_change_time = decisions[i + 1].timestamp
            else:
                next_change_time = period_end.timestamp
            payoff += (next_change_time - d.timestamp).total_seconds() * flow_payoff

        return payoff / period_duration.total_seconds()
