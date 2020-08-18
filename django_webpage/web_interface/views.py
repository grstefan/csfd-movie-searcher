from django.http import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotFound
from elasticsearch import Elasticsearch as ES


def get_average():
    es = ES()
    query = {"size": 0, "aggs": {"average_rating": {"avg": {"field": "rating"}}}}
    return es.search(index='csfd', doc_type='movie', body=query)["aggregations"]["average_rating"]["value"]


class Model(object):
    def __init__(self, i, herci):
        id = i['_id']
        self.url = 'https://www.csfd.cz/film/' + str(id)
        self.rating = i['_source']['rating']
        self.title = i['_source']['title']
        if not herci:
            try:
                self.reziser = ', '.join(i['_source']['creators']['Režie:'])
            except Exception as e:
                self.reziser = '\n'
        else:
            self.reziser = i['highlight']["creators.Hrají:"][0]
        self.plot = i['_source']['content'][0]['plot'][:150] + '...'


def index(request):
    return render(request, 'blank.html')


def herci(request, string, number, fuzzy, avg):
    if fuzzy == '1':
        mode = 'fuzzy'
    else:
        mode = 'match'

    if avg == '1':
        avega = get_average()
    else:
        avega = 0

    query = {"_source": ["title", "rating", "_score", "content.plot", "highlight"],
        "query": {"bool": {"must": [{mode: {"creators.Hrají:": string}}, {"range": {"rating": {"gte": avega, }}}]}},
        "highlight": {"fields": {"creators.Hrají:": {}}}, "sort": [{"rating": "desc", "_score": "desc"}], "size": 10,
        "from": int(number) * 10}
    es = ES()
    result_es = es.search(index='csfd', doc_type='movie', body=query)["hits"]

    pages = int(result_es['total']) // 10
    if pages > 10:
        pages = 10
    response = [x for x in result_es["hits"]]
    return render(request, 'search.html', {'movies': [Model(i, 1) for i in response], 'pages': [
        'search@strana-' + str(x) + '@' + string + '@herci@' + fuzzy + '@' + avg for x in range(pages + 1)]})


def hodnotenie(request, number, string, gte, lte):
    query = {"_source": ["title", "rating", "creators.Režie:", "_score", "content.plot"],
        "query": {"bool": {"must": [{"match": {"titles": string}}, {"range": {"rating": {"gte": gte, "lte": lte}}}]}},
        "size": 10, "from": int(number) * 10

    }
    es = ES()
    result_es = es.search(index='csfd', doc_type='movie', body=query)["hits"]
    pages = int(result_es['total']) // 10
    if pages > 10:
        pages = 10
    response = [x for x in result_es["hits"]]
    return render(request, 'search.html', {'movies': [Model(i, 0) for i in response], 'pages': [
        'search@strana-' + str(x) + '@' + string + '@hodnotenie@' + str(gte) + '@' + str(lte) for x in
        range(pages + 1)]})


def search(request, number, string, avg):
    if avg == '1':
        avega = get_average()
    else:
        avega = 0

    query = {"query": {"function_score": {
        "query": {"bool": {"must": [{"match": {"titles": string}}, {"range": {"rating": {"gte": avega}}}]}},
        "field_value_factor": {"field": "rating", "modifier": "log1p", "factor": 0.1

        }}}, "_source": ["title", "rating", "creators.Režie:", "_score", "content.plot"], "size": 10,
        "from": int(number) * 10}
    es = ES()
    result_es = es.search(index='csfd', doc_type='movie', body=query)["hits"]
    pages = int(result_es['total']) // 10
    if pages > 10:
        pages = 10
    response = [x for x in result_es["hits"]]
    return render(request, 'search.html', {'movies': [Model(i, 0) for i in response],
                                           'pages': ['search@strana-' + str(x) + '@' + string + '@' + avg for x in
                                                     range(pages + 1)]})


def autocomplete(request, string):
    if request.method == 'GET':
        es = ES()
        query = {"query": {"function_score": {"query": {"match_phrase_prefix": {"title": string}},
            "script_score": {"script": " doc['rating'].value / 2 * _score * Math.log(1 + 3* doc['no_ratings'].value )  "

            }}}, "_source": ["title", "_score"], "size": 8}
        response = [x['_source']['title'] for x in
                    es.search(index='csfd', doc_type='movie', body=query)["hits"]['hits']]
        return JsonResponse(response, safe=False)
    else:
        return HttpResponseNotFound('<h1>Page not found</h1>')
