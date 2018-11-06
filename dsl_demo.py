from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Range, MatchAll, Term, Terms, Match, MatchPhrase, MultiMatch, QueryString, Bool, \
    FunctionScore
from elasticsearch_dsl.function import FieldValueFactor, Exp, RandomScore
import json
from pprint import pprint

client = Elasticsearch(['127.0.0.1:9300'])

search = (Search(using=client, index='resource')
          .query(MatchAll())
          .source(['title', 'available_from_date']).sort('-available_from_date'))

(search.aggs.bucket('organizations', 'terms', field='resource_organization')
 .metric('views_per_month_stats', 'stats', field='views_per_month'))

print('Search Body:')
pprint(search.to_dict())
print(json.dumps(search.to_dict()))

response = search.execute()
print(response)
for hit in response:
    print(hit.meta.score, hit.title)

for org in response.aggregations.organizations.buckets:
    print(org.key, org.doc_count, org.views_per_month_stats.to_dict())
