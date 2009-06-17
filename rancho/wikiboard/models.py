########################################################################
# Rancho - Open Source Group/Project Management Tool
#    Copyright (C) 2008 The Rancho Team
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the 
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
########################################################################

from django.db import models
from django.contrib.auth.models import User

from rancho.project.models import Project
from rancho import djangosearch    

import datetime

class WikiManager(models.Manager):
    
    def search(self, user, query, project = None):
        wikiboards = WikiEntry.index.search(query)
        if not user.is_superuser: #restrict to projects with perm
            perm = user.get_rows_with_permission(Project, PERMISSIONS_MESSAGE_VIEW)
            projs_ids = perm.values_list('object_id', flat=True)
            wikiboards = wikiboards.filter(wiki__project__in=projs_ids)    
        if project: #restrict to given project        
            wikiboards = wikiboards.filter(wiki__project=project)

        return wikiboards
     
class Wiki(models.Model):
    creator = models.ForeignKey(User)
    project = models.ForeignKey(Project)
    
    name = models.CharField(max_length=100)
    last_version = models.ForeignKey('WikiEntry', related_name='last_version', null=True)
    
    objects = WikiManager()
    
    def __unicode__(self):
        return self.name
    
    
class WikiEntry(models.Model):
    author = models.ForeignKey(User)
    wiki = models.ForeignKey(Wiki)
        
    content = models.TextField(blank=True)
    creation_date = models.DateTimeField(default = datetime.datetime.now())    
     
    index = djangosearch.ModelIndex(text=['content'])
    
    def get_version_number(self):
        versions = WikiEntry.objects.filter(wiki = self.wiki).order_by('creation_date').values_list('id', flat = True)
        return list(versions).index(self.id)
