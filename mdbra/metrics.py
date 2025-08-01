from ranx import Qrels, Run, evaluate
from mdbra import Query
import warnings
from pprint import pprint

def GeneratorConfusionMatrix(label_set, prediction_set):
    confusion_matrix_prediction_actual = {}
    for key in label_set:
        labeled_keys = {}
        try:
            labels = label_set[key]
            predictions = prediction_set[key]
            confusion_matrix_elements = {}

            for g in labels:
                elem = confusion_matrix_elements.get(g,[0,0])
                elem[0] = labels[g]
                confusion_matrix_elements[g] = elem
            for p in predictions:
                elem = confusion_matrix_elements.get(p,[0,0])
                elem[1] = predictions[p]
                confusion_matrix_elements[p] = elem

            for elem_k in confusion_matrix_elements:
                elem = confusion_matrix_elements[elem_k]
                d = confusion_matrix_prediction_actual.get(elem[1],{})
                confusion_matrix_prediction_actual[elem[1]] = d
                v= d.get(elem[0],0)+1
                confusion_matrix_prediction_actual[elem[1]][elem[0]] = v

        except KeyError as e:
            warnings.warn(f"No predictions for {key}")

        return confusion_matrix_prediction_actual

async def CalculateMetrics(metrics:list[str] = ['mrr@10','ndcg@10'],query_filters:dict={},label_sets=None):
    queries = await Query.find(query_filters).to_list()
    q_pred = {}
    labels_per_set = {}
    false_negatives_per_label_set = {}

    for q in queries:
        q_pred[q.key] = q.predictions
        for label_set in q.labels:
            label_set_name = label_set.label_set.name
            false_negatives_per_label_set[label_set_name] = label_set.false_negatives_labeled

            o = labels_per_set.get(label_set_name,{})
            o[q.key] = label_set.relevant_docs
            labels_per_set[label_set_name] = o

    return_value = {}

    if label_sets is None:
        metrics_copy = metrics.copy()
        for m in metrics:

            if m.find('ndcg') ==0:
                for label_set_name in false_negatives_per_label_set:
                    if not false_negatives_per_label_set[label_set_name]:
                        warnings.warn(f"NDCG is requested on a non-comprehensize labeling set: {label_set_name}")

        run = Run(q_pred)
        for label_set_key in labels_per_set:
            for m in metrics_copy:
                if m == 'confusion_matrix':
                    rv = return_value.get(label_set_key,{})
                    rv['confusion_matrix']=GeneratorConfusionMatrix(q_pred,labels_per_set[label_set_key])
                    return_value[label_set_key]=rv
                    metric_copy.remove(m)

            qrels = Qrels(labels_per_set[label_set_key])
            return_value[label_set_key]=evaluate(qrels, run, metrics)



    else:
        for pair in label_sets:
            metric_copy = metrics.copy()
            for m in metric_copy:
                if m.find('ndcg') ==0:
                    if not false_negatives_per_label_set[pair[1]]:
                        warnings.warn(f"NDCG is requested on a non-comprehensize labeling set: {pair[1]}")

                if m == 'confusion_matrix':
                    rv = return_value.get(pair,{})
                    rv['confusion_matrix']=GeneratorConfusionMatrix(labels_per_set[pair[0]],labels_per_set[pair[1]])
                    return_value[pair]=rv
                    metric_copy.remove(m)
            qrels = Qrels(labels_per_set[pair[1]])
            rv = return_value.get(pair,{})
            return_value[pair] = rv
            results = evaluate(qrels, labels_per_set[pair[0]], metric_copy)
            if len(metric_copy)==1:
                r={}
                r[metric_copy[0]] = results
                results = r

            rv.update(results)
            return_value[pair] = rv

    return return_value

def DocIDValDictionaryToSortedList(dictionary,reverse=True):
    doc_tuples = []
    for k in dictionary:
        doc_tuples.append((k,dictionary[k]))
    doc_tuples.sort(reverse=reverse,key=lambda x: x[1])
    return doc_tuples


async def PrecisionVersusRank(query_filters={},label_rank:int=10):
    queries = await Query.find(query_filters).to_list()

    label_set_orders = {}
    label_set_counts = {}
    label_set_misses = {}
    for q in queries:
        doc_to_rank = {}
        for i,p in enumerate(q.predictions):
            doc_to_rank[p] = i
        prediction_length = len(list(doc_to_rank))
        for ls in q.labels:

            counts = {}
            rank_list = label_set_orders.get(ls.label_set.name,[0]*prediction_length)
            label_set_counts[ls.label_set.name] = label_set_counts.get(ls.label_set.name,0)+1

            doc_tuples = DocIDValDictionaryToSortedList(ls.relevant_docs)

            for i,l in enumerate(doc_tuples[:label_rank]):
                r = doc_to_rank.get(l[0],prediction_length+1)
                counts[l[0]] = counts.get(l[0],0)+1
                if r < prediction_length:
                    rank_list[r]+=1
                else:
                    label_set_misses[ls.label_set.name]=label_set_misses.get(ls.label_set.name,0)+1
            label_set_orders[ls.label_set.name] = rank_list

    for l in label_set_counts:
        n = label_set_counts[l]
        a = label_set_orders[l]
        r = len(a)
        p = [0]*r
        running_sum = 0.0
        for i,v in enumerate(a):
            running_sum+=v/(n*label_rank)
            p[i] = running_sum
        label_set_orders[l] = p

    return label_set_orders



