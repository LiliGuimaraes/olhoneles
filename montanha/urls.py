# -*- coding: utf-8 -*-
#
# Copyright (©) 2013 Marcelo Jorge Vieira <metal@alucinados.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import path
from django.views.generic.base import RedirectView
from django.views.generic import TemplateView

from montanha.views import (
    query_all, query_biggest_suppliers, query_supplier_all,
    query_legislator_all, show_all, show_per_nature, show_per_legislator,
    show_per_party, show_per_supplier, show_supplier_overview,
    show_legislator_detail, show_supplier_detail, what_is_expenses,
    contact_us, show_index,
)
app_name = 'montanha'

urlpatterns = [
    # JSON queries
    path(r'^([^/]+)?/?q/all/?$', query_all, name='query-all'),
    path(r'^([^/]+)?/?q/biggest_suppliers/?$', query_biggest_suppliers, name='query-biggest-suppliers'),
    path(r'^([^/]+)?/?q/supplier_all/?$', query_supplier_all, name='query-supplier-all'),
    path(r'^([^/]+)?/?q/legislator_all/?$', query_legislator_all, name='query-legislator-all'),

    path(r'^([^/]+)?/?all/?([^/]+)?/$', show_all, name='show-all'),

    path(r'^([^/]+)?/?per-nature/?([^/]+)?/$', show_per_nature, name='per-nature'),
    path(r'^([^/]+)?/?per-legislator/?([^/]+)?/$', show_per_legislator, name='per-legislator'),
    path(r'^([^/]+)?/?per-party/?([^/]+)?/$', show_per_party, name='per-party'),
    path(r'^([^/]+)?/?per-supplier/?([^/]+)?/$', show_per_supplier, name='per-supplier'),

    path(r'^detail-supplier/(\d+)/?$', show_supplier_overview, name='show-supplier-overview'),

    path(r'^([^/]+)?/?detail-legislator/(\d+)/?$', show_legislator_detail, name='show-legislator-detail'),
    path(r'^([^/]+)?/?detail-supplier/(\d+)/?$', show_supplier_detail, name='show-supplier-detail'),

    # favicon
    path(
        r'^favicon.ico$',
        RedirectView.as_view(
            url=staticfiles_storage.url('favicon.ico'),
            permanent=True),
        name='favicon'
    ),

    # Robots.txt
    path(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt',
                                               content_type='text/plain')),

    # What is expenses?
    path(r'^o-que-e-verba-indenizatoria/?$', what_is_expenses, name='what-is-expenses'),

    # Contact us
    path(r'^fale-conosco/?$', contact_us, name='contact-us'),

    # Index
    path(r'^([^/]+)?/?$', show_index, name='index'),
]
