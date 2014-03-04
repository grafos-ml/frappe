"""
Created on Dec 9, 2013

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

"""


from django.views.generic.base import View, TemplateResponseMixin
from django.shortcuts import render_to_response, RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ffos.models import FFOSUser

class Landing(View, TemplateResponseMixin):

    template_name = "landing.html"

    http_method_names = [
        'get',
        #'post',
        #'put',
        #'patch',
        #'delete',
        #'head',
        #'options',
        #'trace'
    ]

    #def get_context_data(self,request,**kwargs):
    #    context = RequestContext(request)
    #    context.update({'settings': settings})
    #    return context

    def get(self, request, page=1):
        """
        """
        page = int(page)
        p = page-1
        users_list = FFOSUser.objects.all()
        paginator = Paginator(users_list, 15)  # Show 15 users per page
        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            users = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            users = paginator.page(paginator.num_pages)
        mn, mx = 2-(paginator.num_pages-p) if p+3 > paginator.num_pages else 0, 2-p if p < 3 else 0
        mn, mx = p-(2+mn) if p-(2+mn) >= 0 else 0, p+3+mx
        page_list = paginator.page_range[mn:mx]
        context = RequestContext(request)
        context.update({"users": users, 'page_list': page_list})
        return render_to_response(self.template_name, context)


class Recommend(View, TemplateResponseMixin):

    template_name = "recommend.v2.html"

    http_method_names = [
        'get',
        #'post',
        #'put',
        #'patch',
        #'delete',
        #'head',
        #'options',
        #'trace'
    ]

    def get(self, request, user, **kwargs):
        """

        """
        context = RequestContext(request)
        context.update({"ffosuser": user})
        return render_to_response(self.template_name, context)