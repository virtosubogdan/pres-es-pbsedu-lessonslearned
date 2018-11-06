### ElasticSearch:
#### Lessons Learned on PBS LearningMedia

Notes:
Examples in notes may depend on using the project

---

- Usage on PBS LearningMedia
- Lessons learned
    - Setup
    - Queries
    - Scoring
    - Aggregations
    - Suggestions
    - Things to know

---

#### Use case
- search
    - full text, scoring, simple aggregations
    - autocomplete
    - more like this
- no use for statistics or advanced data types


Notes:
Advantages/Disadvantages
Best search in town.
Easy to use, setup and learn. Does one thing very well.
Super fast, but don't overload it.
Super smart, but does not fix human error.

---

#### Scope

- Using ES 5.6
- Data
    - 5 indexes, 2 nested indexes
    - ~30 fields per index
    - 200k documents without duplicates, care about 60k
- Infrastructure
    - docker container locally, 1 node, 1-2GB
    - AWS managed clusters (ok, but no auto-scale)

Notes:
http://lvh.me:9300/collection example index
http://lvh.me:9300/collection/collection/_search for example document
http://lvh.me:9300/collection/_stats
http://lvh.me:9300/_nodes
http://lvh.me:9300/_cluster/health
http://lvh.me:9300/status

Careful about what AWS manages and what it does not.
https://aws.amazon.com/premiumsupport/knowledge-center/elasticsearch-status-red/


---


#### Dependencies
- elasticsearch-py
- elasticsearch-dsl-py, DSL wrapper


```python
client = Elasticsearch()
(Search(using=client, index='resource')
       .filter(Range(available_from_date={'lte': 'now/d'}))
       .query('match', title='math')
       .source(['title']))
```

Notes:
https://github.com/elastic/elasticsearch-py
https://github.com/elastic/elasticsearch-dsl-py
Low level packages exist for other languages.

----

Same as:
```json
{
  "query": {
    "bool": {
      "filter": [
        {
          "range": {
            "available_from_date": {
              "lte": "now/d"
            }
          }
        }
      ],
      "must": [
        {
          "match": {
            "title": "math"
          }
        }
      ]
    }
  },
  "_source": [
    "title"
  ]
}
```

---

### Setup: Mappings and clean data

- field by field
    - data type (text/keyword, object/nested)
    - indexed or not
    - analyzer (filter, tokenizer)
    - denormalize first
- consider DB <=> ES: models, use cases

Notes:
https://www.elastic.co/guide/en/elasticsearch/reference/5.6/mapping.html#mapping-type
https://www.elastic.co/guide/en/elasticsearch/reference/5.6/analysis.html
Consider:
- search use cases functionality without hitting the DB or not
- what should be done in ES and what in DB
- what you can no longer do in DB

---

### Queries

- term (=, range, exists)
- full text (match, match_phrase, multi_match, query_string)
- compound (bool, scoring)

Notes:
https://www.elastic.co/guide/en/elasticsearch/reference/6.4/full-text-queries.html

----

Filtering
```python
(Search(using=client, index='resource')
     .filter(Range(available_from_date={'lte': 'now/d'}))
     .filter(Term(media_type='Video'))
     .filter(Terms(language=['English', 'Spanish']))
     .query('match_all')
     .source(['language',
              'media_type',
              'available_from_date']))

```

----

Full text search
```python
(Search(using=client, index='resource')
          .source(['title', 'long_description']))
.query(Match(title='Daniel Tiger'))

.query(MatchPhrase(title='Daniel Tiger'))

.query(MultiMatch(query='Daniel Tiger',
                  fields=['title', 'long_description']))

.query(MultiMatch(query='Daniel Tiger', type='phrase',
                  fields=['title', 'long_description']))

.query(QueryString(
       query='title:Daniel and long_description:Tiger'))
```

Notes:
Match - sum of terms
MatchPhrase - combined weight, use slop for how close the word should be
MultiMatch - best match - max(sum(t1 in f1, t2 in f2), sum(t1 in f2, t2 in f2))
           - phase - max(phrase(t1), phrase(t2))
           - most_fields - sum(sum(t1 in f1, t2 in f2), sum(t1 in f2, t2 in f2))
QueryString - advanced, allows fieds, boolean operators
----

Compound/Should
```python
(Search(using=client, index='resource').query(Bool(
    minimum_should_match=1,
    should=[Term(media_type='Video'),
            Term(media_type='Image')],
    must=MatchPhrase(title='Daniel Tiger'),
    filter=[Range(available_from_date={'lte': 'now/d'})]))
```

---
#### Scoring

- boosts (fields, boosting query)
- scoring functions queries
- rescoring
- sort

Notes:
https://www.elastic.co/guide/en/elasticsearch/reference/6.4/search-request-rescore.html

----

Scoring functions
```python
(Search()
.query(Match(title='Daniel Tiger'))
.query(
    FunctionScore(
        functions=FieldValueFactor(
            field='views_per_month',
            factor=0.2,
            weight=0.2)
        )
    )
)

```

Notes:
Sorting
```python
(Search(using=client, index='resource')
        .query(MatchAll())
        .source(['available_from_date']).sort('-available_from_date'))
```

---

#### Aggregations

- Metrics
- Matrix
- Pipeline
- Bucket/Nested (filters, terms, nested)

Notes:
https://www.elastic.co/guide/en/elasticsearch/reference/6.4/search-aggregations.html

---
#### Suggestions

- edge n-grams
- suggesters (term, phrase, completion)
- more like this

Notes:
https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-edgengram-tokenizer.html
https://www.elastic.co/guide/en/elasticsearch/reference/5.6/search-suggesters.html
https://www.elastic.co/guide/en/elasticsearch/reference/6.4/search-suggesters-phrase.html

----
More like this:
```json
GET resource/_search
{
  "query": {
    "more_like_this": {
      "fields": ["long_description", "media_type", "grades"],
      "like": {
        "_id": 117570
        },
      "min_term_freq" : 1
    }
  },
  "_source": [
    "long_description",
    "media_type",
    "grades"
  ]
}
```


---

#### Things to know

- Plugins
    - X-Pack, yelp/elastalert
- dfs_query_then_fetch for relevance
- multi search
- reindex
- highlights for large documents
- refresh index/document for tests
- explain (search but also individual document)

Notes:
https://www.elastic.co/blog/understanding-query-then-fetch-vs-dfs-query-then-fetch

----

#### Highlighting
```json
{
    "query" : {
        "match": { "long_description": "tiger" }
    },
    "highlight" : {
        "fields" : {
            "long_description" : {"fragment_size": 30}
        }
    }
}
```

Notes:
https://www.elastic.co/guide/en/elasticsearch/reference/6.4/search-request-highlighting.html

----

#### Reindex
```json
POST _reindex
{
  "source": {
    "index": "twitter"
  },
  "dest": {
    "index": "new_twitter"
  }
}
```

Notes:
https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-reindex.html

---

### ES Docker

```yaml
  elasticseaarch:
    environment:
      - cluster.routing.allocation.disk.threshold_enabled=false
      - xpack.security.enabled=false
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - ./.docker-data/es-data:/usr/share/elasticsearch/data
    ulimits:
      memlock:
        soft: -1
        hard: -1
    healthcheck:
      test: "curl http://localhost:9200/"
```

Notes:
No shard reallocation on local single node wanted.
https://www.elastic.co/guide/en/elasticsearch/reference/current/disk-allocator.html
XPack not available on trials or basic licences.
https://www.elastic.co/guide/en/elasticsearch/reference/current/security-settings.html
We want to use little memory on local, but to make sure it is not swapped (es memory lock + system memlock)
https://www.elastic.co/guide/en/elasticsearch/reference/master/setup-configuration-memory.html#bootstrap-memory_lock
Mount volume so data is not lost on rebuild.
More info:
https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html


---

### Kibana

```yaml
  kibana:
    image: docker.elastic.co/kibana/kibana:5.6.5
    environment:
      SERVER_NAME: kibana
      ELASTICSEARCH_URL: http://elasticsearch:9200
      LOGGING_QUIET: "true"
    ports:
      - "5601:5601"
```

Notes:
https://www.elastic.co/guide/en/kibana/current/docker.html

---

#### Resources

- https://www.elastic.co/guide/index.html
- https://github.com/dzharii/awesome-elasticsearch
- https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html
- [ES Release Notes](https://www.elastic.co/guide/en/elasticsearch/reference/current/es-release-notes.html)


---

#### Thank you

-  made with [reveal-md]