"""
Util module for the re-ranker calculation
"""

__author__ = 'joaonrb'


def weighted_p(p_global, p_local, alpha):
    """
    Measure the frequency for the items for a specific user based on parameter alpha.

    :param p_global: Global probability
    :param p_local: Local probability
    :param alpha: The weight to push toward p_local. The bigger alpha the more influence p_local have
    """
    return (alpha * p_local) + ((1. - alpha) * p_global)


def normalize(value, mean_value, var):
    """
    Normalize value by approximate it to a Gauss(0, 1).

    :param value: Value to normalize
    :type value: float
    :param mean_value: The mean value of the "value's" population
    :type mean_value: float
    :param var: The variance of the "value's" population
    :type var: float
    :return: The normalized value
    :rtype: float
    """
    return (value - mean_value) / var