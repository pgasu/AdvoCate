from django.conf.urls import patterns, url
from Category_Modeler.views import index, saveexistingtaxonomydetails, savenewtaxonomydetails, trainingsampleprocessing, supervised, createChangeEventForNewTaxonomy, applyChangeOperations
from Category_Modeler.views import signaturefile, visualizer, loginrequired, logout_view, auth_view, register_view, changeRecognizer, createChangeEventForNewTaxonomyVersion
from Category_Modeler.views import compareexistingtaxonomies, getconceptdetails, edittrainingset, applyeditoperations, changethresholdlimits
urlpatterns = patterns('',
        url(r'^$', index),
        url(r'^home/$', index),
        url(r'^saveexistingtaxonomydetails/$', saveexistingtaxonomydetails),
        url(r'^savenewtaxonomydetails/$', savenewtaxonomydetails),
        url(r'^compareexistingtaxonomies/$', compareexistingtaxonomies),        
        url(r'^trainingsample/$', trainingsampleprocessing),
        url(r'^edittrainingset/$', edittrainingset),
        url(r'^applyeditoperations/$', applyeditoperations),        
        url(r'^signaturefile/$', signaturefile),  
        url(r'^changethresholdlimits/$', changethresholdlimits),        
        url(r'^supervised/$', supervised),
        url(r'^changerecognition/', changeRecognizer),
        url(r'^createChangeEventForNewTaxonomy/', createChangeEventForNewTaxonomy),
        url(r'^createChangeEventForNewTaxonomyVersion/', createChangeEventForNewTaxonomyVersion),
        url(r'^applyChangeOperations/', applyChangeOperations),
        url(r'^visualizer/', visualizer),
        url(r'^getconceptdetails/', getconceptdetails),        
        url(r'^accounts/loginrequired/', loginrequired),
        url(r'^accounts/logout/', logout_view),
        url(r'^accounts/auth/', auth_view),
        url(r'^accounts/register/', register_view)
        
        

        
        
    )

