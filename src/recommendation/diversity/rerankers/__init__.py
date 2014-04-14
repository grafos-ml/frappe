__author__ = 'joaonrb'

from recommendation.diversity.rerankers.simple import SimpleDiversityReRanker
from recommendation.diversity.rerankers.binomial import BinomialDiversityReRanker


class DynamicDiversityReRanker(object):
    """
    Use Simple diversity or Binomial, dependent of the size of the recommendation
    """

    def __init__(self, alpha_constant=0.8, lambda_constant=1.):  # Set lambda lower to improve user tendencies
        """
        Constructor

        :param lambda_constant: Some weight. It has to be between 0 and 1. Default is 0.5.
        :type lambda_constant: float
        :return:
        """
        self.lambda_constant = lambda_constant
        self.alpha_constant = alpha_constant

    def __call__(self, user, recommendation, size, *args, **kwargs):
        """

        :param user: The user that want the recommendation
        :type user: FFOSUser
        :param recommendation: The recommendation to re-rank
        :type recommendation: list
        :param size: The size of the recommendation asked
        :type size: int
        :return: The re-ranked recommendation
        :rtype: list
        """
        try:
            if size <= 50:
                self.__class__ = BinomialDiversityReRanker
                return self(user, recommendation, size)
            self.__class__ = SimpleDiversityReRanker
            return self(user, recommendation, size)
        finally:
            self.__class__ = DynamicDiversityReRanker