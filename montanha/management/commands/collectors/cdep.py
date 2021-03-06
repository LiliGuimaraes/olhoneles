# -*- coding: utf-8 -*-
#
# Copyright (©) 2010-2013 Estêvão Samuel Procópio
# Copyright (©) 2010-2013 Gustavo Noronha Silva
# Copyright (©) 2014 Lúcio Flávio Corrêa
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

import os
import requests
import threading
from datetime import date, datetime
from zipfile import ZipFile
from Queue import Queue, Empty
from django.db import reset_queries, connection
from email.utils import formatdate as http_date
from lxml.etree import iterparse

from basecollector import BaseCollector
from montanha.models import (
    Institution, Legislature, Legislator,
    AlternativeLegislatorName, ExpenseNature, PoliticalParty,
)


OBJECT_LIST_MAXIMUM_COUNTER = 1000


def db_thread(cdep):
    cursor = connection.cursor()
    query = u'INSERT INTO `montanha_archivedexpense` '
    query += u'(`original_id`, `number`, `nature_id`, `date`, `value`, `expensed`, `mandate_id`, `supplier_id`, `collection_run_id`) '
    query += u'VALUES (NULL, %(number)s, %(nature)s, %(date)s, NULL, %(expensed)s, %(mandate)s, %(supplier)s, %(collection_run)s)'

    data_to_insert = []
    force_insert = False
    while True:
        # If empty, we want to force inserting what we already have and
        # let the queue know we are done.
        try:
            data = cdep.db_queue.get(timeout=2)
            cdep.debug(u"New expense found: %s" % unicode(data))
            data_to_insert.append(data)
        except Empty:
            force_insert = True

        if force_insert or len(data_to_insert) == OBJECT_LIST_MAXIMUM_COUNTER:
            # To help with debug mode using up memory for query logs.
            reset_queries()
            force_insert = False

            if cdep.db_queue.qsize() or data_to_insert:
                cdep.info('Queue size: {} rows to insert: {}'.format(cdep.db_queue.qsize(), len(data_to_insert)))

            cursor.executemany(query, data_to_insert)
            for d in data_to_insert:
                cdep.db_queue.task_done()
            data_to_insert[:] = []


def cleanup_element(elem):
    elem.clear()
    while elem.getprevious() is not None:
        del elem.getparent()[0]


class CamaraDosDeputados(BaseCollector):
    db_queue = Queue(maxsize=5000)

    def __init__(self, collection_runs, debug_enabled=False):
        super(CamaraDosDeputados, self).__init__(collection_runs, debug_enabled)

        institution, _ = Institution.objects.get_or_create(siglum='CDEP', name=u'Câmara dos Deputados Federais')
        self.legislature, _ = Legislature.objects.get_or_create(institution=institution,
                                                                date_start=datetime(2015, 1, 1),
                                                                date_end=datetime(2018, 12, 31))

    def retrieve_legislators(self):
        uri = 'http://www.camara.gov.br/SitCamaraWS/Deputados.asmx/ObterDeputados'
        return BaseCollector.retrieve_uri(self, uri)

    def try_name_disambiguation(self, name):
        if name.title() == 'Sergio Souza':
            return Legislator.objects.get(id=293), False

        return None, False

    def update_legislators(self):
        xml = self.retrieve_legislators()

        for l in xml.findAll('deputado'):
            alternative_name = None
            name = l.find('nomeparlamentar')
            if not name:
                name = l.find('nome')
            else:
                alternative_name = l.find('nome').text.title().strip()

            name = name.text.title().strip()

            self.debug(u"Looking for legislator: %s" % unicode(name))
            legislator, created = Legislator.objects.get_or_create(name=name)

            if created:
                self.debug(u"New legislator: %s" % unicode(legislator))
            else:
                self.debug(u"Found existing legislator: %s" % unicode(legislator))

            if alternative_name:
                try:
                    legislator.alternative_names.get(name=alternative_name)
                except AlternativeLegislatorName.DoesNotExist:
                    alternative_name, _ = AlternativeLegislatorName.objects.get_or_create(name=alternative_name)
                    legislator.alternative_name = alternative_name

            legislator.email = l.find('email').text
            legislator.save()

            party_name = self.normalize_party_name(l.find('partido').text)
            party, _ = PoliticalParty.objects.get_or_create(siglum=party_name)

            state = l.find('uf').text

            original_id = l.find('ideCadastro')

            self.mandate_for_legislator(legislator, party, state=state, original_id=original_id)

    def update_data(self):
        if os.path.exists('cdep-collection-run'):
            crid = int(open('cdep-collection-run').read())
            self.remove_collection_run(crid)
            os.unlink('cdep-collection-run')

        self.collection_run = self.create_collection_run(self.legislature)

        data_path = os.path.join(os.getcwd(), 'data', 'cdep')
        if not os.path.isdir(data_path):
            os.makedirs(data_path)
            self.debug(u"Creating directory %s" % data_path)

        files_to_download = ['AnoAtual.zip']
        previous_years = date.today().year - self.legislature.date_start.year

        if previous_years:
            files_to_download.append('AnoAnterior.zip')

        if previous_years > 1:
            files_to_download.append('AnosAnteriores.zip')

        files_to_process = list()
        for file_name in files_to_download:
            xml_file_name = file_name.replace('zip', 'xml')
            full_xml_path = os.path.join(data_path, xml_file_name)
            files_to_process.append(os.path.join(data_path, full_xml_path))

            full_path = os.path.join(data_path, file_name)

            headers = dict()
            if os.path.exists(full_path):
                headers['If-Modified-Since'] = http_date(os.path.getmtime(full_path), usegmt=True)

            uri = 'http://www.camara.gov.br/cotas/' + file_name
            self.debug(u"Preparing to download %s…" % (uri))
            r = requests.get(uri, headers=headers, stream=True)

            if r.status_code == requests.codes.not_modified:
                self.debug(u"File %s not updated since last download, skipping…" % file_name)
                continue

            with open(full_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self.debug(u"Unzipping %s…" % (file_name))
            zf = ZipFile(full_path, 'r')
            zf.extract(xml_file_name, data_path)

        with open('cdep-collection-run', 'w') as fh:
            fh.write('%d' % (self.collection_run.id))

        for i in range(2):
            db_worker = threading.Thread(name='db-worker-{}'.format(i), target=db_thread, args=(self,))
            db_worker.daemon = True
            db_worker.start()

        legislators = {}
        parties = {}
        natures = {}
        for file_name in reversed(files_to_process):
            self.debug(u"Processing %s…" % file_name)

            context = iterparse(file_name, events=("start", "end"))

            # turn it into an iterator
            context = iter(context)

            for event, elem in context:
                if event != "end" or elem.tag != "DESPESA":
                    continue

                # Some entries lack numLegislatura, so we fallback to numAno.
                legislature_year = elem.find('nuLegislatura').text
                if legislature_year is not None:
                    legislature_year = int(legislature_year)
                else:
                    legislature_year = int(elem.find('numAno').text)
                    if legislature_year < self.legislature.date_start.year or \
                       legislature_year > self.legislature.date_end.year:
                        legislature_year = None
                    else:
                        legislature_year = self.legislature.date_start.year

                if legislature_year != self.legislature.date_start.year:
                    self.debug(u"Ignoring entry because it's out of the target legislature…")
                    cleanup_element(elem)
                    continue

                name = elem.find('txNomeParlamentar').text.title().strip()

                nature_name = elem.find('txtDescricao').text.title().strip()

                supplier_name = elem.find('txtBeneficiario')
                if supplier_name is not None:
                    supplier_name = supplier_name.text.title().strip()
                else:
                    supplier_name = u'Sem nome'

                supplier_identifier = elem.find('txtCNPJCPF')
                if supplier_identifier is not None and supplier_identifier.text is not None:
                    supplier_identifier = supplier_identifier.text

                if not supplier_identifier:
                    supplier_identifier = u'Sem CNPJ/CPF (%s)' % supplier_name

                supplier = self.get_or_create_supplier(supplier_identifier, supplier_name)

                docnumber = elem.find('txtNumero').text
                if docnumber:
                    docnumber = docnumber.strip()
                else:
                    docnumber = ''

                expense_date = elem.find('datEmissao')
                if expense_date and expense_date.text is not None:
                    expense_date = date(*((int(x.lstrip('0')) for x in expense_date.text[:10].split('-'))))
                else:
                    expense_year = int(elem.find('numAno').text)
                    expense_month = int(elem.find('numMes').text)
                    expense_date = date(expense_year, expense_month, 1)

                expensed = float(elem.find('vlrLiquido').text)

                # memory cache
                nature = natures.get(nature_name)
                if not nature:
                    nature, _ = ExpenseNature.objects.get_or_create(name=nature_name)
                    natures[nature_name] = nature

                # memory cache
                party_siglum = elem.find('sgPartido').text
                party = parties.get(party_siglum)
                if not party and party_siglum is not None:
                    party_siglum = self.normalize_party_name(party_siglum)
                    party, _ = PoliticalParty.objects.get_or_create(siglum=party_siglum)
                    parties[party_siglum] = party

                state = elem.find('sgUF').text.strip()

                if elem.find('ideCadastro') is None:
                    original_id = elem.find('idecadastro').text.strip()
                else:
                    original_id = elem.find('ideCadastro').text.strip()

                # memory cache
                legislator = legislators.get(name)
                if not legislator:
                    try:
                        legislator = Legislator.objects.get(name__iexact=name)
                    except Legislator.DoesNotExist:
                        # Some legislators do are not listed in the other WS because they are not
                        # in exercise.
                        self.debug(u"Found legislator who's not in exercise: %s" % name)
                        legislator = Legislator(name=name)
                        legislator.save()
                    legislators[name] = legislator

                mandate = self.mandate_for_legislator(legislator, party,
                                                      state=state, original_id=original_id)

                # Model objects should not cross thread boundaries
                self.db_queue.put(
                    dict(
                        number=docnumber,
                        nature=nature.id,
                        date=expense_date,
                        expensed=expensed,
                        mandate=mandate.id,
                        supplier=supplier.id,
                        collection_run=self.collection_run.id,
                    )
                )

                cleanup_element(elem)

        os.unlink('cdep-collection-run')
