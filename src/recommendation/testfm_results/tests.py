__author__ = 'joaonrb'

from recommendation.model_factory import TensorCoFi, Popularity
import testfm
import pandas as pd
from pkg_resources import resource_filename


class TestModelsWithTestFM(object):

    @staticmethod
    def test_tensorcofi():
        df = pd.read_csv(resource_filename(testfm.__name__, "data/movielenshead.dat"),
                         sep="::", header=None, names=["user", "item", "rating", "date", "title"])

        items = pd.DataFrame({"item": df.item.unique()})
        items["i"] = items.index
        items = items.set_index("item")

        users = pd.DataFrame({"user": df.user.unique()})
        users["i"] = users.index
        users = users.set_index("user")

        #tell me what models we want to evaluate
        model = TensorCoFi(n_users=len(users), n_items=len(items))

        df["user"] = df["user"].map(lambda x: users["i"][x] + 1)
        df["item"] = df["item"].map(lambda x: items["i"][x] + 1)
        #training, testing = testfm.split.holdoutByRandom(df, 0.6)

        #models += [LinearRank([models[2], models[3]],  item_features_column=["rating"])]
        model.fit(df)
        TensorCoFi.load_to_cache()

        for user in users["i"]:
            rec = model.get_not_mapped_recommendation(user-1)
            for i in range(len(items)):
                assert model.get_score(user, i+1) == rec[i], "User %s item in position %d is not the same as " \
                                                             "(%f, %f)" % (user, i, model.get_score(user, i+1), rec[i])