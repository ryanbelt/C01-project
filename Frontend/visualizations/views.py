from django.shortcuts import render, redirect
from django.template import RequestContext, loader
from subprocess import Popen
from articles.models import *
from explorer.models import *
import sys, os
import json

path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../../', 'src'))
sys.path.append(path)
import visualizer

def article_hypertree(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    data = []
    context = {'data': data}
    return render(request, 'visualizations/article_hypertree.html', context)

def article_hypertree_js(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    data = visualizer.article_hypertree()

    data = json.dumps(data)
    context = {'data': data}
    return render(request, 'visualizations/article_hypertree_js.html', context)

def article_spacetree(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    data = []
    context = {'data': data}
    return render(request, 'visualizations/article_spacetree.html', context)

def article_spacetree_js(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    if request.method == 'POST':
        data, msites = visualizer.article_spacetree(request.POST.get('msite'))
    else:
        data, msites = visualizer.article_spacetree(None)

    data = json.dumps(data)

    context = {'data': data, 'msites': msites}
    return render(request, 'visualizations/article_spacetree_js.html', context)

def article_weightedtree(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    data = []
    context = {'data': data}
    return render(request, 'visualizations/article_weightedtree.html', context)

def article_weightedtree_js(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    if request.method == 'POST':
        data, msites = visualizer.article_weightedtree(request.POST.get('msite'))
    else:
        data, msites = visualizer.article_weightedtree(None)
    data = json.dumps(data)

    context = {'data': data, 'msites': msites}
    return render(request, 'visualizations/article_weightedtree_js.html', context)

def article_forcegraph(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    data = []
    context = {'data': data}
    return render(request, 'visualizations/article_forcegraph.html', context)

def article_forcegraph_js(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    if request.method == 'POST':
        data, msites = visualizer.article_forcegraph(request.POST.get('msite'))
    else:
        data, msites = visualizer.article_forcegraph(None)
    data = json.dumps(data)

    context = {'data': data, 'msites': msites}

    return render(request, 'visualizations/article_forcegraph_js.html', context)

def tweet_hypertree(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    data = []
    context = {'data': data}
    return render(request, 'visualizations/tweet_hypertree.html', context)

def tweet_hypertree_js(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    data = visualizer.tweet_hypertree()
    data = json.dumps(data)
    context = {'data': data}
    return render(request, 'visualizations/tweet_hypertree_js.html', context)

def tweet_spacetree(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    data = []
    context = {'data': data}
    return render(request, 'visualizations/tweet_spacetree.html', context)

def tweet_spacetree_js(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    if request.method == 'POST':
        data, taccounts = visualizer.tweet_spacetree(request.POST.get('taccount'))
    else:
        data, taccounts = visualizer.tweet_spacetree(None)

    data = json.dumps(data)

    context = {'data': data, 'taccounts': taccounts}
    return render(request, 'visualizations/tweet_spacetree_js.html', context)

def tweet_weightedtree(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    data = []
    context = {'data': data}
    return render(request, 'visualizations/tweet_weightedtree.html', context)

def tweet_weightedtree_js(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    if request.method == 'POST':
        data, taccounts = visualizer.tweet_weightedtree(request.POST.get('taccount'))
    else:
        data, taccounts = visualizer.tweet_weightedtree(None)

    data = json.dumps(data)

    context = {'data': data, 'taccounts': taccounts}
    return render(request, 'visualizations/tweet_weightedtree_js.html', context)

def tweet_forcegraph(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    data = []
    context = {'data': data}
    return render(request, 'visualizations/tweet_forcegraph.html', context)

def tweet_forcegraph_js(request):
    if not request.user.is_authenticated():
        return redirect('/admin/login/?next=%s' % request.path)

    if request.method == 'POST':
        data, taccounts = visualizer.tweet_forcegraph(request.POST.get('taccount'))
    else:
        data, taccounts = visualizer.tweet_forcegraph(None)

    data = json.dumps(data)

    context = {'data': data, 'taccounts': taccounts}
    return render(request, 'visualizations/tweet_forcegraph_js.html', context)