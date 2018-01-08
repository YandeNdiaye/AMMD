""" Ajax calls for the exploration tree

"""
import json
from django.http.response import HttpResponse
from django.shortcuts import render
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK
from explore_tree.api.models import Navigation, MyParser, MaxDepth, Node
from explore_tree.api.navigation.operations import retrieve_navigation_filters, get_navigation_node_for_document
from mgi.models import XMLdata
from mgi.models import Template#
from utils.json_parser.processview import processview, processviewdocidlist, process_cross_query, doc_to_query, ids_docs_to_query, ids_docs_to_querys
from parser import query
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.core.cache import caches

from xml.dom import minidom #
from xml.dom.minidom import parse, parseString, Document #
import xml.etree.ElementTree as ET #
import xml.etree.cElementTree as ET#

from rest_framework.response import Response#
from rest_framework import status#
from utils.XSDParser.renderer import DefaultRenderer#
from utils.XSDParser.renderer.list import ListRenderer#
from utils.XSDParser.renderer.xml import XmlRenderer#
from curate.models import SchemaElement#
from cStringIO import StringIO#
from django.core.servers.basehttp import FileWrapper#

from mgi.models import find_content_by_id#
from lxml import etree#
from collections import OrderedDict, deque #
import collections
from bson.objectid import ObjectId#
from explore_tree.parser.renderer import get_projection#
from xml.etree.ElementTree import XMLParser, ElementTree, fromstring#
from itertools import izip, chain #
from copy import deepcopy#
from itertools import tee#

#from apscheduler.schedulers.blocking import BlockingScheduler

import dicttoxml
import random
#import sys
from threading import Thread
#import time


leaf_cache   = caches['leaf']
branch_cache = caches['branch']
link_cache   = caches['link']


AmTest_list=[]
AmTest_list1=[]

my_result_to_d = []

list_of_ordered_dict = ''
list_of_ordered_dict_cross_docs = ''
my_listof_ordereddicts_tab = []
my_listof_ordereddicts_cross_docs_tab = []
my_list_of_cross_results = []
query_and_results_tab = []
results_initial_doc = []
list_od_dwnld_files =[]
navigation_name_tab= []#''
my_tab = []
mytab = []

caching_docs = False
docs_already_cached = False
@cache_page(600 * 15)
def load_view(request):
    """

    :param request:
    :return:
    """

    # nav_id parameter is mandatory, if it doesn't exist we delete other parameters to raise and error
    if "nav_id" not in request.POST:
        request.POST = {}

    node_id=''
    doc_id =''
    ref_node_id=''


    if "node_id" in request.POST and "doc_id" in request.POST:
        node_id = request.POST['node_id']
        doc_id  = request.POST['doc_id']
        leaf    = None
        #c_id    = str(node_id) + '_' + str(doc_id)
        nod_name = Navigation.get_name(node_id)
        indexx = (nod_name).rfind("#")
        node_name = nod_name[indexx+1:]
        c_id    = str(node_name) + '_' + str(doc_id)
        mt=[]
        if ( c_id in leaf_cache ):
            #print "-----------GET FROM CACHE------------"
            leaf = leaf_cache.get(c_id)

        else:
            #print "-----------PROCESSING-----------"
            load_doc = load_leaf_view(request, doc_id)
            r = render(request, "explore_tree/components/view.html", load_doc)
            #leaf_cache.set(str(request.POST['node_id']) + '_' + doc_id, r)
            leaf_cache.set(c_id, r)#,30)
            leaf = r
            xmldata_objects = XMLdata.objects()
            tableau = []
            for x in xmldata_objects:
                for k, v in x.items():
                    if k == "_id" and v!= doc_id:
                        tableau.append(v)

            for t in tableau:
                try:
                    request2 = request
                    mutable = request2.POST._mutable
                    request2.POST._mutable = True
                    request2.POST['doc_id'] = str(t)
                    request2.POST._mutable = mutable

                    load_other_doc = load_leaf_view(request2,t)
                    r2 = render(request2, "explore_tree/components/view.html", load_other_doc)
                    leaf_cache.set(str(node_name) + '_' + str(t), r2)
                    mt.append(str(node_name) + '_' + str(t))
                except:
                    pass

        return leaf

    elif "node_id" in request.POST:
        node_id = request.POST['node_id']
        branch  = None

        if ( node_id in branch_cache ):
            branch = branch_cache.get(node_id)

        else:
            branch = __load_branch_view(request)
            branch_cache.set(node_id, branch)

        return  branch


    elif "ref_node_id" in request.POST and "doc_id" in request.POST:
        ref_node_id = request.POST['ref_node_id']
        doc_id      = request.POST['doc_id']
        c_id        = ref_node_id + '_' + doc_id
        link        = None

        if ( c_id in link_cache ):
            link = link_cache.get(c_id)
        else:
            link = __load_link_view(request)
            link_cache.set(c_id, link)
        return link

    else:
        error = {
            "message": "Request is malformed."
        }
        return HttpResponse(json.dumps(error), status=HTTP_400_BAD_REQUEST)


class Afficheur(Thread):

    def __init__(self,request,table,navigation_list,b):
        Thread.__init__(self)
        self.request = request
        self.table = table
        self.navigation_list = navigation_list
        self.bool = b
    def run(self):
        for t in self.table:
            for nav in self.navigation_list:
                request2 = self.request
                mutable = request2.POST._mutable
                request2.POST._mutable = True
                request2.POST['doc_id'] = str(t)
                request2.POST['node_id'] = nav.id
                request2.POST._mutable = mutable
                try:
                    load_other_doc = load_leaf_view(request2, request2.POST['doc_id'])
                    r = render(request2, "explore_tree/components/view.html", load_other_doc)
                    #c = str(request2.POST['node_id']) + '_' + str(request2.POST['doc_id'])
                    nod_name = Navigation.get_name(request2.POST['node_id'])
                    indexx = (nod_name).rfind("#")
                    node_name = nod_name[indexx+1:]
                    c = str(node_name) + '_' + str(request2.POST['doc_id'])

                    leaf_cache.set(c, r)
                    mytab.append(c)
                    if self.bool == "True":
                        break
                except:
                    pass

def run(request,table,nav,b):
    for t in table:
        request2 = request
        mutable = request2.POST._mutable
        request2.POST._mutable = True
        request2.POST['doc_id'] = str(t)
        request2.POST['node_id'] = nav.id#nav.id
        request2.POST._mutable = mutable
        try:
            load_other_doc = load_leaf_view(request2, request2.POST['doc_id'])
            r = render(request2, "explore_tree/components/view.html", load_other_doc)
            #c = str(request2.POST['node_id']) + '_' + str(request2.POST['doc_id'])
            nod_name = Navigation.get_name(request2.POST['node_id'])
            indexx = (nod_name).rfind("#")
            node_name = nod_name[indexx+1:]
            c = c = str(node_name) + '_' + str(request2.POST['doc_id'])
            leaf_cache.set(c, r)
            mytab.append(c)
            if b == "True":
                break
        except:
            pass

def appendAllChildrenToList(nodes, parent, getChildChildren):
    AmTest_list1 = []
    childrens = parent.children
    if (childrens != None):
        size_nodes = len(childrens)
        i = 0
        while (size_nodes!=0):
            node = Navigation.objects.get(pk=childrens[i])
            nodes.append(node)
            if (node.children!=None and node.name!="http://siam.nist.gov/Database-Navigation-Ontology#AMTests"):
                appendAllChildrenToList(nodes, node, getChildChildren)
            size_nodes -=1
            i +=1
            if (node.children!=None and node.name=="http://siam.nist.gov/Database-Navigation-Ontology#AMTests"):
                AmTest_list1.append(node)
                appendAllChildrenToList(AmTest_list1, node, getChildChildren)

    for nav_t in AmTest_list1:
        if len(nav_t.children) == 0 and ("projection_view" in nav_t.options) and len(nav_t.options)==3:
            AmTest_list.append(nav_t)
    navigation_table = []
    for nav_t in nodes:
        if len(nav_t.children) == 0 and ("projection_view" in nav_t.options) and len(nav_t.options)==3:
            navigation_table.append(nav_t)
    return navigation_table

def cache_docs(request):
    if caching_docs == False:#docs_already_cached == False:
        caching_docs = True
        leaf_cache.clear()
        cache_all_docs(request)
    else:
        print "-------DEJA EN TRAIN DE CACHE UN DOC-----------"
        HttpResponse(json.dumps({}), HTTP_208_OK)

def cache_all_docs(request):
    caching_docs = True
    docs_already_cached = True
    print "----------------------------------caching doc----------------------------------"
    debut = time.time()
    xmldata_objects = XMLdata.objects()
    tableau = []
    for x in xmldata_objects:
        for k, v in x.items():
            if k == "_id":
                tableau.append(v)

    size_tableau = len(tableau)
    tab1 = []
    tab2 = []

    if len(tableau)%2 == 0:
        tab1 = tableau[:(size_tableau/2)]
        tab2 = tableau[(size_tableau/2):]
    else:
        tab1 = tableau[:(size_tableau/2)-(1/2)]
        tab2 = tableau[(size_tableau/2)+(1/2):]
    nav_tab = []
    navigation = Navigation.objects.get(pk=request.POST['nav_id'])
    nav_tab.append(navigation)
    navigation_table = appendAllChildrenToList(nav_tab,navigation,"True")
    print "--------------------------------------------------------- PROCESSING : ---------------------------------------------------------"
    thread_1 = Afficheur(request,tab1,navigation_table,"True")
    thread_2 = Afficheur(request,tab2,navigation_table,"True")
    thread_1.start()
    thread_2.start()
    thread_1.join()
    thread_2.join()
    for n in AmTest_list:
        run(request,tableau,n,"False")
    fin = time.time()
    #print request.POST['nav_id']
    #print "---------------- DOCS --------------------"
    #print "SIZE DOCS"
    #print size_tableau
    #print "SIZEEEE DES Nav 1"
    #print len(navigation_table)
    #print "SIZEEEE DES Nav 2"
    #print len(AmTest_list)
    #print "----------------TIMING--------------------"
    #print(debut, fin)
    #print (fin-debut)
    #print "----------------CACHE list --------------------"
    #print mytab

    return HttpResponse(json.dumps({}), HTTP_200_OK)

def __load_leaf_view(request):
    """ Load view for a leaf

    Parameters:
        -   request:

    Returns:
    """

    print "\n___LOAD_LEAF_VIEW___:"
    navigation_name2=request.POST["node_id"]
    print request.POST["node_id"]

    print request

    xml_document = XMLdata.get(request.POST["doc_id"])
    navigation_node = Navigation.objects.get(pk=request.POST["node_id"])



    # Display XML file if "projection_view" annotation is not configured
    if "projection_view" not in navigation_node.options:
        # TODO transform the XML into a data table
        return HttpResponse(json.dumps({}), HTTP_200_OK)

    projection_views = json.loads(navigation_node.options["projection_view"])

    view_data = {
        "header": xml_document.get("title"),
        "type": "leaf",
        "views": []
    }
    my_listof_ordereddicts_cross_docs2 =[]
    query_and_results2 = []
    my_listof_ordereddicts2 = []
    # Send the annotation to the processor and collect the data


    for projection_view in projection_views:
        result_data = {
            "title": projection_view["title"],
            "data": None
        }

        # FIXME better handling of x-
        if "query" in projection_view.keys():

            my_projections = []
            # Get the names of the brakets which need to be displayed
            for value in projection_view["data"]:
                my_projections.append(value.get('path'))

            result_data["data"] = process_cross_query(request.POST["nav_id"], request.POST["doc_id"],
                                                      projection_view["query"], projection_view["data"])
            # Set the documents which must be queried
            doc_query_proc = {
                "_id": ObjectId(request.POST["doc_id"])
            }

            truc = doc_to_query(1)
            co_dict = {}

            for id_doc in truc:
                other_doc_query = {
                    "_id" : ObjectId(id_doc)
                }
                for projection in my_projections:

                    proj_co = {
                        my_projections[my_projections.index(projection)] : 1
                    }

                    res_co = XMLdata.executeQueryFullResult(other_doc_query,proj_co)

                    try:
                        doc_projco = get_projection(res_co[0])
                        s = str(my_projections[my_projections.index(projection)])
                        y = s.split(".")
                        attribute = y[len(y)-1]
                        result_cross = doc_projco
                        my_list_of_cross_results.append((attribute,result_cross))
                        global list_of_ordered_dict_cross_docs
                        list_of_ordered_dict_cross_docs = res_co
                        my_listof_ordereddicts_cross_docs2.append(res_co)
                    except:
                        res_co = ''

        else:
            my_projections = []

            for value in projection_view["data"]:
                my_projections.append(value.get('path'))
            id_doc_to_query = {
                "_id": ObjectId(request.POST["doc_id"])
            }

            for projection in my_projections:
                proj_co = {
                    my_projections[my_projections.index(projection)] : 1
                }

                res_co = XMLdata.executeQueryFullResult(id_doc_to_query,proj_co)
                query_and_results2.append(projection)
                try:
                    doc_projco = get_projection(res_co[0])
                    global list_of_ordered_dict
                    list_of_ordered_dict = res_co
                    my_listof_ordereddicts2.append(res_co)
                    results_initial_doc.append(doc_projco)

                except:
                    res_co = ''

            result_data["data"] = processview(request.POST["nav_id"], request.POST["doc_id"], projection_view["data"])
            my_result_to_d.append(result_data["data"])

        view_data["views"].append(result_data)

    query_and_results_tab.append(query_and_results2)
    my_listof_ordereddicts_cross_docs_tab.append(my_listof_ordereddicts_cross_docs2)
    navigation_name_tab.append(navigation_name2)
    my_listof_ordereddicts_tab.append(my_listof_ordereddicts2)
    my_tab.append(request.POST["doc_id"])

    return render(request, "explore_tree/components/view.html", view_data)

def load_leaf_view(request, docid):
    """ Load view for a leaf

    Parameters:
        -   request:

    Returns:
    """

    navigation_name2=request.POST["node_id"]

    xml_document = XMLdata.get(docid)
    navigation_node = Navigation.objects.get(pk=request.POST["node_id"])

    # Display XML file if "projection_view" annotation is not configured
    if "projection_view" not in navigation_node.options:
        # TODO transform the XML into a data table
        return HttpResponse(json.dumps({}), HTTP_200_OK)

    projection_views = json.loads(navigation_node.options["projection_view"])

    view_data = {
        "header": xml_document.get("title"),
        "type": "leaf",
        "views": []
    }
    my_listof_ordereddicts_cross_docs2 =[]
    query_and_results2 = []
    my_listof_ordereddicts2 = []

    # Send the annotation to the processor and collect the data
    for projection_view in projection_views:
        result_data = {
            "title": projection_view["title"],
            "data": None
        }

        # FIXME better handling of x-
        if "query" in projection_view.keys():

            my_projections = []
            # Get the names of the brakets which need to be displayed
            for value in projection_view["data"]:
                my_projections.append(value.get('path'))

            result_data["data"] = process_cross_query(request.POST["nav_id"], docid,
                                                      projection_view["query"], projection_view["data"])
            # Set the documents which must be queried
            doc_query_proc = {
                "_id": ObjectId(docid)
            }

            truc = doc_to_query(1)

            co_dict = {}

            for id_doc in truc:
                other_doc_query = {
                    "_id" : ObjectId(id_doc)
                }

                for projection in my_projections:

                    proj_co = {
                        my_projections[my_projections.index(projection)] : 1
                    }

                    res_co = XMLdata.executeQueryFullResult(other_doc_query,proj_co)

                    try:

                        doc_projco = get_projection(res_co[0])
                        s = str(my_projections[my_projections.index(projection)])
                        y = s.split(".")
                        attribute = y[len(y)-1]

                        result_cross = doc_projco
                        my_list_of_cross_results.append((attribute,result_cross))
                        global list_of_ordered_dict_cross_docs
                        list_of_ordered_dict_cross_docs = res_co
                        my_listof_ordereddicts_cross_docs2.append(res_co)
                    except:
                        res_co = ''

        else:
            my_projections = []
            for value in projection_view["data"]:
                my_projections.append(value.get('path'))
            id_doc_to_query = {
                "_id": ObjectId(docid)
            }

            for projection in my_projections:
                proj_co = {
                    my_projections[my_projections.index(projection)] : 1
                }

                res_co = XMLdata.executeQueryFullResult(id_doc_to_query,proj_co)
                query_and_results2.append(projection)
                try:
                    doc_projco = get_projection(res_co[0])
                    global list_of_ordered_dict
                    list_of_ordered_dict = res_co
                    my_listof_ordereddicts2.append(res_co)
                    results_initial_doc.append(doc_projco)

                except:
                    res_co = ''

            result_data["data"] = processview(request.POST["nav_id"], docid, projection_view["data"])
            my_result_to_d.append(result_data["data"])

        view_data["views"].append(result_data)

    query_and_results_tab.append(query_and_results2)
    my_listof_ordereddicts_cross_docs_tab.append(my_listof_ordereddicts_cross_docs2)
    navigation_name_tab.append(navigation_name2)
    my_listof_ordereddicts_tab.append(my_listof_ordereddicts2)
    my_tab.append(docid)

    return view_data

def __load_leaf_view_master(request):
    iddoc = request.POST["doc_id"]
    return render(request, "explore_tree/components/view.html", load_leaf_view(request,iddoc))

def __load_branch_view(request):
    """ Load view for a branch

    :param request:
    :return:
    """
    print "___LOAD_BRANCH_VIEW:"
    # Retrieve the view annotation
    navigation_node = Navigation.objects.get(pk=request.POST["node_id"])
    filters = retrieve_navigation_filters(navigation_node)


    # FIXME modified query part to execute query directly
    documents = []
    query_documents = query.execute_query(filters, '{"_id": 1}')

    for query_doc in query_documents:
        documents.append(query_doc["_id"])
    # Display XML file if "projection_view" annotation is not configured
    if "view" not in navigation_node.options:
        error = {
            "message": "'cql:view' annotation does not exist for this branch."
        }

        return HttpResponse(json.dumps(error), HTTP_400_BAD_REQUEST)

    branch_views = json.loads(navigation_node.options["view"])

    name = navigation_node.name.split('#')[1] if '#' in navigation_node.name else navigation_node.name
    view_data = {
        "header": name,
        "type": "branch",
        "views": []
    }

    for branch_view in branch_views:
        result_data = {
            "title": branch_view["title"],
            "data": processviewdocidlist(request.POST["nav_id"], documents, branch_view["data"])
        }

        view_data["views"].append(result_data)

    return render(request, "explore_tree/components/view.html", view_data)


def __load_link_view(request):
    # retrieve document id
    # retrieve the projection content

    print "___LOAD_LINK_VIEW:"
    ref_node_id = request.POST["ref_node_id"]
    print request.POST["ref_node_id"]
    print  request.POST["doc_id"]
    print  request.POST["nav_id"]

    reference_node = get_navigation_node_for_document(ref_node_id, request.POST["doc_id"])

    print "---------------"

    navigation_name2 = request.POST["ref_node_id"]#
    xml_document = XMLdata.get(request.POST["doc_id"])#

    if "projection_view" in reference_node.options and reference_node.options["projection_view"] is not None:
        projection_views = json.loads(reference_node.options["projection_view"])

        view_data = {
            "header": xml_document.get("title"),
            "type": "leaf",
            "views": []
        }

        my_listof_ordereddicts_cross_docs2 =[]#
        query_and_results2 = []#
        my_listof_ordereddicts2 = []#

        # Send the annotation to the processor and collect the data
        for projection_view in projection_views:
            result_data = {
                "title": projection_view["title"],
                "data": None
            }

            # FIXME better handling of x-queries
            if "query" in projection_view.keys():
                my_projections = []#
                # Get the names of the brakets which need to be displayed
                for value in projection_view["data"]:#
                    my_projections.append(value.get('path'))#
                result_data["data"] = process_cross_query(request.POST["nav_id"], request.POST["doc_id"],
                                                          projection_view["query"], projection_view["data"])
                ##################################################
                # Set the documents which must be queried
                doc_query_proc = {
                    "_id": ObjectId(request.POST["doc_id"])
                }

                truc = doc_to_query(1)

                co_dict = {}

                for id_doc in truc:
                    other_doc_query = {
                        "_id" : ObjectId(id_doc)
                    }

                    for projection in my_projections:

                        proj_co = {
                            my_projections[my_projections.index(projection)] : 1
                        }

                        res_co = XMLdata.executeQueryFullResult(other_doc_query,proj_co)

                        try:

                            doc_projco = get_projection(res_co[0])
                            s = str(my_projections[my_projections.index(projection)])
                            y = s.split(".")
                            attribute = y[len(y)-1]

                            result_cross = doc_projco
                            my_list_of_cross_results.append((attribute,result_cross))
                            global list_of_ordered_dict_cross_docs
                            list_of_ordered_dict_cross_docs = res_co
                            my_listof_ordereddicts_cross_docs2.append(res_co)
                        except:
                            res_co = ''
                ##################################################
            else:
                ##################################################
                my_projections = []
                for value in projection_view["data"]:
                    my_projections.append(value.get('path'))
                id_doc_to_query = {
                    "_id": ObjectId(request.POST["doc_id"])
                }

                for projection in my_projections:
                    proj_co = {
                        my_projections[my_projections.index(projection)] : 1
                    }

                    res_co = XMLdata.executeQueryFullResult(id_doc_to_query,proj_co)
                    query_and_results2.append(projection)
                    try:
                        doc_projco = get_projection(res_co[0])
                        global list_of_ordered_dict
                        list_of_ordered_dict = res_co
                        my_listof_ordereddicts2.append(res_co)
                        results_initial_doc.append(doc_projco)

                    except:
                        res_co = ''
                ##################################################
                result_data["data"] = processview(request.POST["nav_id"], request.POST["doc_id"],
                                                  projection_view["data"])
                my_result_to_d.append(result_data["data"])##################

            view_data["views"].append(result_data)

        ##################################################
        query_and_results_tab.append(query_and_results2)
        my_listof_ordereddicts_cross_docs_tab.append(my_listof_ordereddicts_cross_docs2)
        navigation_name_tab.append(navigation_name2)
        my_listof_ordereddicts_tab.append(my_listof_ordereddicts2)
        my_tab.append(request.POST["doc_id"])
        ##################################################
        html_data = render(request, "explore_tree/components/view.html", view_data)
        doc_id = str(reference_node.pk) + "." + str(xml_document["_id"])

        return HttpResponse(json.dumps({"html": html_data.content, "doc_id": doc_id}), status=HTTP_200_OK)
    else:
        return HttpResponse(json.dumps({}), HTTP_200_OK)


def json2xml(json_obj, line_padding=""):
    result_list = list()
    json_obj_type = type(json_obj)

    if json_obj_type is list:
        for sub_elem in json_obj:
            result_list.append(json2xml(sub_elem, line_padding))
        return "\n".join(result_list)

    if json_obj_type is dict or isinstance(json_obj, OrderedDict):
        for tag_name in json_obj:
            sub_obj = json_obj[tag_name]
            result_list.append("%s<%s>" % (line_padding, tag_name))
            result_list.append(json2xml(sub_obj, "\t" + line_padding))
            result_list.append("%s</%s>" % (line_padding, tag_name))

        return "\n".join(result_list)

    return "%s%s" % (line_padding, json_obj)


def download_corrolated_xml(request):
    dejadwl = False
    index_i=''
    json_contents =""
    j=0

    for mydoc in my_tab:
        if mydoc == request.GET["doc_id"]:
            j = my_tab.index(mydoc)
            break

    query_and_results = query_and_results_tab[j]
    my_listof_ordereddicts_cross_docs = my_listof_ordereddicts_cross_docs_tab[j]
    #navigation_name = navigation_name_tab[j]
    navigation_id = navigation_name_tab[j]
    navigation_name = Navigation.get_name(navigation_id)
    indexx = (navigation_name).rfind("#")
    navigation_name = navigation_name[indexx+1:]
    my_listof_ordereddicts = my_listof_ordereddicts_tab[j]

    for i in list_od_dwnld_files:
        if i[0] == navigation_name and i[1] == request.GET["doc_id"]:
            dejadwl = True
            index_i = list_od_dwnld_files.index(i)
            break
    if dejadwl:
        #print "--------------DOC already dwld--------------"
        json_contents = list_od_dwnld_files[index_i][2]
    else:
        #print "--------------DOC never dwld-----------------"
        j1 = download_corrolated_xml_initial_file(query_and_results)
        j2 = download_corrolated_xml_others_files(my_listof_ordereddicts_cross_docs)

        doc_name = request.GET["file_name"]
        xml = my_tree = download_file(request)

        liste_of_txt = recuperaationtextes(my_listof_ordereddicts)

        nb = 0
        for child in xml.iter():
            car = False
            if child.text=="":
                pass
            else:
                nb +=1

        pare = 0
        for l in liste_of_txt:
            for child in xml.iter():
                car = False
                if child.text == l[1]:
                    car = True
                #if car==False:
                    ct = child.text
                    child.text = "MAMIIIIII"+ct
                    pare +=1
        par = 0
        for child in xml.iter():
            b=''
            if child.text:
                if (child.text)[0:9] == "MAMIIIIII":
                    ancien = (child.text)[9:]
                    child.text = ancien
                    par +=1
                else:
                    child.text=b
        bg = 0
        for child in xml.iter():
            car = False
            if child.text:
                if (child.text)[0:9]==b:
                    pass
                else:
                    bg +=1

        y= etree.tostring(xml, pretty_print=True)
        json_contents = "<xml>\n"+j2+y+"</xml>"
        list_od_dwnld_files.append((navigation_name,request.GET["doc_id"],json_contents))

    print "navigation_name"
    print navigation_id
    print navigation_name
    print request.GET["doc_id"]
    return HttpResponse(json_contents, HTTP_200_OK)


def download_corrolated_xml_initial_file(L):
    tree = aggregate_query(L)
    json_contents = print_xml_string(tree_to_xml_string(tree))
    return json_contents


def recuperaationtextes(L):
    listofcontents = []
    listoftexts = []
    listoftag_texts = []

    print "VOILA"
    for ordereddict in L:
        xml_data = (ordereddict[0]).items()[1][1]
        xml_dta = json.dumps(xml_data)
        xml_d = json.loads(xml_dta)
        json_content = json2xml(xml_d)
        jsoncontent = u''.join((json_content)).encode('utf-8')
        jsoncontent = str(jsoncontent)
        jsoncontent = jsoncontent.replace("\t","")
        jsoncontent = jsoncontent.replace("\n","")
        listofcontents.append(jsoncontent)

    for l in listofcontents:
        my_tree = generate_xml(l)
        for child in my_tree.getiterator():
            if child.getchildren():
                pass
            else:
                listoftag_texts.append((child.tag,child.text))

    return  listoftag_texts


def aggregate_query(L):
    queries = [query.split('.') for query in L]
    # Check that the first elements of each query are all identical and we initialize the root
    if not queries or [_[0] for _ in queries].count(queries[0][0]) == len(queries):
        root = Node(queries[0][0])
        for query in queries:
            current_node = root
            for element in query[1:]:
                child = current_node.get_child(element)
                if child is None:
                    new_node = Node(element)
                    current_node.add_child(new_node)
                    current_node = new_node
                else:
                    current_node = child
        return root
    else:
        print("No common root")


def tree_to_xml_string(tree):
    from itertools import tee, izip
    """Conversion of an Node-Tree to an XML String
    """
    def iter_2_by_2(iterable):
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        a, b = tee(iterable)
        next(b, None)
        return izip(a, b)

    def rec_xml_to_string(tree):
        current_node = tree
        left = "<{}>".format(current_node.data)
        right = "</{}>".format(current_node.data)
        if current_node.children:
            return "".join([left+rec_xml_to_string(child)+right for child in current_node.children])
        else:
            return left+""+right

    xml_string = rec_xml_to_string(tree)
    xml_str_split = xml_string.split('><')
    xml_str_split[0] = xml_str_split[0][1:]
    xml_str_split[-1] = xml_str_split[-1][:-1]
    remove_idx = [i for i, (a, b) in enumerate(iter_2_by_2(xml_str_split)) if (a.startswith('/') and a[1:] == b)]
    remove_idx_set = set(remove_idx) | set([x+1 for x in remove_idx])
    filtered_list = ["<{}>".format(x) for i, x in enumerate(xml_str_split) if (i not in remove_idx_set)]
    return '<?xml version="1.0"?>{}'.format(''.join(filtered_list))

def print_xml_string(xml_string):
    tab = ' ' * 2
    compteur = 0
    # First we split the tags
    s = xml_string.split('><')
    s[0] = s[0][1:]
    s[-1] = s[-1][:-1]
    str_split = ["<{}>".format(x) for x in s]
    for tag in str_split:
        if tag.startswith("</"):
            compteur -= 1
            print("{}{}".format(compteur*tab, tag))
        else:
            print("{}{}".format(compteur*tab, tag))
            compteur += 1

def generate_xml(content):
    tree = etree.fromstring(content)
    return tree


def download_corrolated_xml_others_files(L):

    xml_files = []
    doc_ids = []
    json_contents = ''
    json_to_render=''
    docid_and_trees = []
    for ordereddict in L:
        xml_data = (ordereddict[0]).items()[1][1]
        xml_dta = json.dumps(xml_data)
        xml_d = json.loads(xml_dta)

        json_content = json2xml(xml_d)
        my_xml_string = str(json_content)
        my_tree = get_tree(my_xml_string)

        doc_ids.append((ordereddict[0]).items()[0][1])
        xml_files.append(json_content)
        docid_and_trees.append(((ordereddict[0]).items()[0][1],my_tree))


        json_contents = json_contents + '\n' + json_content

    if len(docid_and_trees)>1:

        for li in docid_and_trees:
            i = docid_and_trees.index(li)
            for lii in docid_and_trees[i+1:]:
                ii = docid_and_trees.index(lii)
                var_p = 0
                for child1, child2 in izip(li,lii):
                    if child1 == child2:
                        var_p +=1
                if var_p == len(li) & len(li) == len(lii):
                        del docid_and_trees[ii]
        print docid_and_trees

        table_id=[]
        my_ordered_xml_list = []

        for t1 in docid_and_trees:

            y=[]
            i = docid_and_trees.index(t1)
            deja_parcouru = False
            for tab in table_id:
                if tab == t1[0]:
                    deja_parcouru = True
            if deja_parcouru == False:
                table_id.append(t1[0])
                for t2 in docid_and_trees[i+1:]:
                    if t1[0] == t2[0]:
                        if y!=[]:
                            x = union_tree(t1[1],t2[1],verbose=False)
                            y = union_tree(y,x,verbose=False)
                        else:#Write for the first time
                            y = union_tree(t1[1],t2[1],verbose=False)

            if y:
                my_ordered_xml_list.append((t1[0],y))

        string_xml=''
        jsson = ''

        if my_ordered_xml_list==[]:
            json_to_render = json_contents

        for xml in my_ordered_xml_list:

            s = LTree_to_xml_string(xml[1])
            string_xml += s

            uni = unicode(s, 'utf-8')
            tree = ET.XML(uni)
            tree2 = etree.fromstring(s)
            xmlbase = etree.Element("xml")
            xmlb = etree.Element("data")
            xml_r = None
            firsttime = True
            dek = False
            pu_var = True
            i=1
            for child in tree2.getiterator():
                if pu_var:
                    xml = etree.SubElement(xmlb,child.tag)
                    i=1
                    pu_var = False
                else:
                    if i==1:
                        xml_r = etree.SubElement(xml,child.tag)
                        i=0
                    else:
                        print "2:"
                        for a in l:
                            if a.tag == child.tag:
                                dek = True
                        if dek:
                            xml_r = etree.SubElement(xml_r,child.tag)
                        else:

                            xmlpere = child.findall("..")
                            xml_r.addnext(child)
                        dek = False
                l = child.getchildren()
            fill_xml(xmlb, my_list_of_cross_results)
            json_to_render += etree.tostring(xmlb, pretty_print=True)
    else:
        json_to_render = json_contents
    print "JSON TO RENDER"
    print json_to_render

    return json_to_render


def fill_xml(xml, my_list_of_tag_text_initialdoc):
    i=0
    for child in xml.iter():
        if child.getchildren():
            print('')
        else:
            child.text = my_list_of_tag_text_initialdoc[i][1]
            i +=1
    return xml

def get_tree(xml_string):
    parser = XMLParser(target=MyParser())
    parser.feed(xml_string)
    tree = parser.close()
    return tree



def pairwise(iterable):
    """"s -> (s0,s1), (s2,s3), (s4, s5), ..."
    """
    it = iter(iterable)
    return izip(it, it)


def get_union(tree1, tree2):
    if len(tree1) == len(tree2) and tree1[::2] == tree2[::2]:
        for (tag1, tail1), (tag2, tail2) in zip(pairwise(tree1), pairwise(tree2)):
            return [tag1, get_union(tail1, tail2)]
    else:
        return list(chain(tree1, tree2))

def union_tree(tree1, tree2, verbose = False):

    if verbose:
        def verboseprint(*args):
            for arg in args:
                end = " "
                print(arg, end)
            print()
    else:
        verboseprint = lambda *a: None

    tree = deepcopy(tree1)
    stack_tree = deque([tree])
    stack_tree1 = deque([tree1])
    stack_tree2 = deque([tree2])
    while stack_tree1:
        verboseprint("stack tree1 = {}".format([x[0] for x in stack_tree1]))

        current_node_tag_t, current_node_childs_t = stack_tree.pop()
        current_node_tag_t1, current_node_childs_t1 = stack_tree1.pop()
        current_node_tag_t2, current_node_childs_t2 = stack_tree2.pop()
        verboseprint("tag courant t1 = {}".format(current_node_tag_t1))
        verboseprint("tag courant t2 = {}".format(current_node_tag_t2))

        current_node_childs_t1_pairwised = list(pairwise(current_node_childs_t1))
        current_node_childs_t2_pairwised = list(pairwise(current_node_childs_t2))
        current_node_childs_tags_t1 = [x[0] for x in current_node_childs_t1_pairwised]
        current_node_childs_tags_t2 = [x[0] for x in current_node_childs_t2_pairwised]
        verboseprint("current_node_childs_tags_t1 = {}".format(current_node_childs_tags_t1))
        verboseprint("current_node_childs_tags_t2 = {}".format(current_node_childs_tags_t2))

        # It is necessary to stack the common nodes for the continuation of the course and to add the non common node

        # compare the tags between each tree
        childs_t1_dict = {tag:val for tag, val in current_node_childs_t1_pairwised}
        childs_t2_dict = {tag:val for tag, val in current_node_childs_t2_pairwised}
        tag_set_1, tag_set_2 = set(current_node_childs_t1[::2]), set(current_node_childs_t2[::2])
        interection_tag = tag_set_1 & tag_set_2
        difference_tag = tag_set_2 - tag_set_1
        verboseprint("Intersection tag = {}".format(interection_tag))
        verboseprint("Difference tag = {}".format(difference_tag))

        # We make sure of the order of the ensembles
        intersection_tag_ordered = [_ for _ in current_node_childs_tags_t1 if _ in interection_tag]
        difference_tag_ordered   = [_ for _ in current_node_childs_tags_t2 if _ in difference_tag]
        verboseprint("difference_tag_ordered = {}".format(difference_tag_ordered))
        #retrieve subtrees of each sub ensemble
        common_childs = list(chain.from_iterable([(tag, childs_t1_dict[tag]) for tag in intersection_tag_ordered]))
        uncommon_childs = list(chain.from_iterable([(tag, childs_t2_dict[tag]) for tag in difference_tag_ordered]))
        verboseprint("common_childs_list = {}".format(common_childs))
        verboseprint("uncommon_childs_list = {}".format(uncommon_childs))

        # Stack for the rest of the way, there are always common nodes
        if common_childs:
            stack_tree.extend(list(pairwise(current_node_childs_t))[::-1])
            stack_tree1.extend(list(pairwise(current_node_childs_t1))[::-1])
            stack_tree2.extend(list(pairwise(current_node_childs_t2))[::-1])

        # Gather nodes not common to both trees
        #if current_node_tag_t1 == current_node_tag_t2:
        current_node_childs_t.extend(uncommon_childs)

#         verboseprint("tree = {}".format(tree))
        verboseprint()
    return tree

def iter_2_by_2(iterable):
    #"s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

def LTree_to_xml_string(tree):
    """Conversion of an L-Tree to an XML String
    """
    def rec_xml_to_string(tree):
        current_node_tag, current_node_childs = tree
        left = "<{}>".format(current_node_tag)
        right = "</{}>".format(current_node_tag)
    #     print(current_node_tag, [x for x in current_node_childs[::2]])
        if current_node_childs:
            return "".join([left+rec_xml_to_string(child)+right for child in pairwise(current_node_childs)])
        else:
            return left+""+right

    xml_string = rec_xml_to_string(tree)
    xml_str_split = xml_string.split('><')
    xml_str_split[0] = xml_str_split[0][1:]
    xml_str_split[-1] = xml_str_split[-1][:-1]
    remove_idx = [i for i, (a, b) in enumerate(iter_2_by_2(xml_str_split)) if (a.startswith('/') and a[1:] == b)]
    remove_idx_set = set(remove_idx) | set([x+1 for x in remove_idx])
    filtered_list = ["<{}>".format(x) for i, x in enumerate(xml_str_split) if (i not in remove_idx_set)]
    return ''.join(filtered_list)

def print_xml_string(xml_string):
    tab = ' ' * 2
    compteur = 0
    # First we split the tags
    s = xml_string.split('><')
    s[0] = s[0][1:]
    s[-1] = s[-1][:-1]
    str_split = ["<{}>".format(x) for x in s]
    tim = ""
    for tag in str_split:
        if tag.startswith("</"):
            compteur -= 1
            a = "{}{}".format(compteur*tab, tag)
            #print("{}{}".format(compteur*tab, tag))
            tim +="\n" + a
            print a
        else:
            b = "{}{}".format(compteur*tab, tag)
            #print("{}{}".format(compteur*tab, tag))
            tim +="\n" + b
            print b
            compteur += 1
    return tim

def download_file(request):
    xml_data = XMLdata.get(request.GET["doc_id"])
    xml_dta = json.dumps(xml_data.items()[3][1],sort_keys=False)
    xml_d = json.loads(xml_dta, object_pairs_hook=OrderedDict) # Convert the ordered dict in dict
    j = json.dumps(xml_d)
    jk = json.loads(j)
    print jk
    #dicttoxml.set_debug(False)
    xml_object = dicttoxml.dicttoxml(jk, custom_root='data',attr_type=False)#, root=True)

    return etree.fromstring(xml_object)
def download_xml(request):
    xml_data = XMLdata.get(request.GET["doc_id"])
    xml_dta = json.dumps(xml_data.items()[3][1],sort_keys=False)
    xml_d = json.loads(xml_dta, object_pairs_hook=OrderedDict) # Convert the ordered dict in dict

    json_content = json2xml(xml_d)

    return HttpResponse(json_content, HTTP_200_OK)
