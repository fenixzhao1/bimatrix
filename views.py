# -*- coding: utf-8 -*-
from __future__ import division
from . import models
from ._builtin import Page, WaitPage
from otree.common import Currency as c, currency_range
from .models import Constants

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


class Question(Page):

    form_model = models.Player
    form_fields = ['training_question_1']

    def vars_for_template(self):
        return {'num_q': 1}

    timeout_seconds = 100


class Feedback1(Page):

    template_name = 'bimatrix/Feedback.html'

    def vars_for_template(self):
        return {'num_q': 1,
                'question': 'Suppose Alice chose to defect and Bob chose to cooperate. How many points would Alice and Bob receive, respectively?',
                }


class DecisionWaitPage(WaitPage):
    body_text = 'Waiting for everyone to answer comprehension question'

    def after_all_players_arrive(self):
        self.session.vars['end_time'] = timezone.now() + timedelta(seconds=Constants.game_length)


class Decision(Page):

    timeout_seconds = Constants.game_length


class Results(Page):

    def vars_for_template(self):
        self.player.set_payoff()

        return {
            'decisions_over_time': self.player.decisions_over_time,
            'total_plus_base': self.player.payoff + Constants.base_points
        }



page_sequence = [
        Introduction,
        Question,
        Feedback1,
        DecisionWaitPage,
        Decision,
        Results
    ]
