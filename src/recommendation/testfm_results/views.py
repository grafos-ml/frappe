#! -*- encoding: utf-8 -*-
"""
Api to test the models in cache wit test.fm
This is not a proper nose test because the values of this result are a bit subjective and require a bit sensitivity from
experts on the matter. A proper nose test will also be made but of course will be more susceptible to error.
"""
__author__ = "joaonrb"

from recommendation.api.views import JSONResponse
from rest_framework.views import APIView
import pandas as pd
import testfm
from testfm.evaluation.evaluator import Evaluator
from recommendation.models import Inventory, Item
from recommendation.model_factory import TensorCoFi, Popularity


class AnalyzeModels(APIView):
    """
    View to throw the test
    """
    http_method_names = [
        "get"
    ]

    def get(self, request, non_rel=100):
        """
        Test the models tensorcofi and popularity
        """
        users, items = zip(*Inventory.objects.all().values_list("user_id", "item_id"))
        df = pd.DataFrame({"user": users, "item": items})
        evaluator = Evaluator(use_multi_threading=False)
        #training, testing = testfm.split.holdoutByRandom(df, 0.2)
        tensor = TensorCoFi.get_model()
        pop = Popularity.get_model()
        items = pd.Series(list(range(1, len(Item.all_items())+1)))
        response = {
            tensor.get_name(): evaluator.evaluate_model(tensor, df, all_items=items, non_relevant_count=non_rel),
            pop.get_name(): evaluator.evaluate_model(pop, df, all_items=items, non_relevant_count=non_rel)
        }
        return JSONResponse(response)