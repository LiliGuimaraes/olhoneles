# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2013 Gustavo Noronha Silva
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

from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

from montanha.api import __version__


admin.autodiscover()


urlpatterns = [
    # Admin
    path(r'^admin/', admin.site.urls),

    # # API
    # path(r'api/v0/',
    #     include('tastypie_swagger.urls', namespace='olhoneles-v0'),
    #     kwargs={
    #         'namespace': 'olhoneles-v0',
    #         'tastypie_api_module': 'montanha.api.urls.api',
    #         'version': __version__,
    #     }),
    # path(r'^api/', include('montanha.api.urls')),

    # Montanha
    path(r'^', include('montanha.urls',
                      namespace='montanha')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path(r'^__debug__/', include(debug_toolbar.urls)),
    ]

handler500 = 'montanha.views.error_500'
handler404 = 'montanha.views.error_404'
