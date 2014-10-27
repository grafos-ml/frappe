#we use SVG as png is somewhat gives strange results on mac

suml --svg --scruffy --sequence \
"[Client] request recommendation >[A/B testing],\
[A/B testing] forward request >[Module A],\
[Module A] returns topk recs >[Client], \
[Module A] logs the event  >[Logger]" \
> general-flow.svg


suml --svg --scruffy --sequence \
"[Outer Space] request recs >[Module A],\
[Module A]predict scores >[Predictor 1],\
[Predictor 1]returns scores>[Module A],\
[Module A]filter scores >[Filter 1],\
[Filter 1]returns filtered scores>[Module A],\
[Module A]filter scores >[Filter 2],\
[Filter 2]returns filtered scores>[Module A],\
[Module A]rerank recs >[Reranker 1],\
[Reranker 1]returns reranked list >[Module A],\
[Module A] returns topk recs >[Outer Space],\
[Module A] logs the event  >[Logger]" \
> module-flow.svg

suml --png --font-family Purisa --scruffy "[Module|+IdMap; +Predictors; +Aggregator; +Filters;+Rerankers;|\
+predictScores(user);+Filter(user,item);+Rerank(user,item);loadFromDB()]" > module-class.png