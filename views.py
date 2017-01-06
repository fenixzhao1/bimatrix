# -*- coding: utf-8 -*-
from __future__ import division
from . import models
from ._builtin import Page, WaitPage
from otree.common import Currency as c, currency_range
from otree.firebase.events import start_emitter
from .models import Constants
from .models import Decision as DecisionModel

from django.utils import timezone
from datetime import timedelta

def vars_for_all_templates(self):
    if (self.player.id_in_group == 1):
        return {
            "my_A_A_payoff": Constants.p1_A_p2_A_amount,
            "my_A_B_payoff": Constants.p1_A_p2_B_amount,
            "my_B_A_payoff": Constants.p1_B_p2_A_amount,
            "my_B_B_payoff": Constants.p1_B_p2_B_amount,
            "other_A_A_payoff": Constants.p2_A_p1_A_amount,
            "other_A_B_payoff": Constants.p2_A_p1_B_amount,
            "other_B_A_payoff": Constants.p2_B_p1_A_amount,
            "other_B_B_payoff": Constants.p2_B_p1_B_amount,
            "total_q": 1
        }
    else:
        return {
            "my_A_A_payoff": Constants.p2_A_p1_A_amount,
            "my_A_B_payoff": Constants.p2_A_p1_B_amount,
            "my_B_A_payoff": Constants.p2_B_p1_A_amount,
            "my_B_B_payoff": Constants.p2_B_p1_B_amount,
            "other_A_A_payoff": Constants.p1_A_p2_A_amount,
            "other_A_B_payoff": Constants.p1_A_p2_B_amount,
            "other_B_A_payoff": Constants.p1_B_p2_A_amount,
            "other_B_B_payoff": Constants.p1_B_p2_B_amount,
            "total_1": 1
        }


class Introduction(Page):
    timeout_seconds = 100


class DecisionWaitPage(WaitPage):
    body_text = 'Waiting for all players to be ready'

    def after_all_players_arrive(self):
        # calculate start and end times for the period
        start_time = timezone.now()
        end_time = start_time + timedelta(seconds=Constants.period_length)

        self.session.vars['start_time_{}'.format(self.group.id_in_subsession)] = start_time
        self.session.vars['end_time_{}'.format(self.group.id_in_subsession)] = end_time

        # insert dummy decisions into database
        # put a decision of -1 for each player at the start and end of the period
        for player in self.group.get_players():
            start_decision, end_decision = DecisionModel(), DecisionModel()

            for d in start_decision, end_decision:
                d.component = "otree-server"
                d.session = self.session.code
                d.subsession = self.subsession.name()
                d.round = self.round_number
                d.group = self.group.id_in_subsession
                d.page = "Decision"
                d.app = "bimatrix"
                d.participant = player.participant
                d.decision = -1

            start_decision.timestamp = start_time
            end_decision.timestamp = end_time

            start_decision.save()
            end_decision.save()


class Decision(Page):
    timeout_seconds = Constants.period_length


class Results(Page):

    def vars_for_template(self):
        self.player.set_payoff()

        return {
            'decisions_over_time': self.player.decisions_over_time,
            'total_plus_base': self.player.payoff + Constants.base_points
        }



page_sequence = [
        Introduction,
        DecisionWaitPage,
        Decision,
        Results
    ]
