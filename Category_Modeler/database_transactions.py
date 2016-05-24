from Category_Modeler.models import Trainingset, ChangeTrainingsetActivity, AuthUser, Classificationmodel, Classifier, LearningActivity 
from Category_Modeler.models import Confusionmatrix, ExplorationChain, ClassificationActivity, Concept, Legend, LegendConceptCombination, ComputationalIntension
from Category_Modeler.models import Extension, Category, HierarchicalRelationship, HorizontalRelationship, MeanVector, CovarianceMatrix, ChangeEvent, ChangeEventOperations
from Category_Modeler.models import AddTaxonomyOperation, AddConceptOperation, SetOfOccurences, CategoryInstantiationOperation, AddTaxonomyVersionOperation, AddExistingConceptToNewVersion
from Category_Modeler.models import AddConSplitFrmExistToNewVer
from datetime import datetime
import numpy
from django.db import transaction, connection

class UpdateDatabase:
    
    def __init__(self, request):
        self.authuser_instance = AuthUser.objects.get(id = int(request.session['_auth_user_id']))
        self.request = request
        if 'new_taxonomy_name' not in self.request.session:
            self.current_taxonomy = self.request.session['existing_taxonomy_name']
        else:
            self.current_taxonomy = self.request.session['new_taxonomy_name']
        self.change_event = self.__create_change_event()
    
    def __create_change_event(self):
        exp_chain = self.request.session['exploration_chain_id']
        change_event = ChangeEvent(exploration_chain_id = exp_chain, created_by= self.authuser_instance)
        change_event.save()
        return change_event
    
    def create_legend(self):
        if Legend.objects.all().exists():
            legendId = Legend.objects.latest("legend_id").legend_id +1
        else:
            legendId =0
        model_instance = Classificationmodel.objects.get(id = int(self.request.session['current_model_id']))
        legend = Legend(legend_id = legendId, legend_ver = 1, legend_name= self.current_taxonomy, date_expired = datetime(9999, 9, 12), description = self.request.session['new_taxonomy_description'], created_by = self.authuser_instance, model = model_instance, change_event_id = self.change_event)
        legend.save()
        self.request.session['legend_id'] = legend.legend_id
        self.request.session['legend_ver'] = legend.legend_ver
        self.__create_root_concept(legendId, 1)
    
    def create_new_legend_version(self):
        model_instance = Classificationmodel.objects.get(id = int(self.request.session['current_model_id']))
        version = int(self.request.session['existing_taxonomy_ver']) + 1
        legend_new_version = Legend(legend_id = self.request.session['existing_taxonomy_id'], legend_ver = version, legend_name= self.current_taxonomy, date_expired = datetime(9999, 9, 12), created_by = self.authuser_instance, model = model_instance, change_event_id = self.change_event)
        legend_new_version.save(force_insert=True)
        self.request.session['existing_taxonomy_ver'] = legend_new_version.legend_ver
        Legend.objects.filter(legend_id = self.request.session['existing_taxonomy_id'], legend_ver = self.request.session['existing_taxonomy_id']).update(date_expired = datetime.now())
        self.__create_root_concept(legend_new_version.legend_id, legend_new_version.legend_ver)
    
    def __create_root_concept(self, legendId, legendVer):
        details = "Root concept to legend " + self.current_taxonomy
        conceptName = "root_"+self.current_taxonomy.replace(" ", "_") + str(legendVer)
        root_concept = Concept(concept_name = conceptName, description = details, date_expired = datetime(9999, 9, 12), created_by = self.authuser_instance, change_event_id = self.change_event)
        root_concept.save(force_insert=True)
        self.request.session['root_concept'] = root_concept.concept_name
        connectToLegend = LegendConceptCombination(legend_id = legendId, legend_ver = legendVer, concept = root_concept, change_event_id = self.change_event)
        connectToLegend.save()
        if 'new_taxonomy_name' in self.request.session:
            createLegend = AddTaxonomyOperation(legend_id = legendId, legend_ver = legendVer, root_concept_id = root_concept, legend_root_concept_combination_id = connectToLegend)
            createLegend.save(force_insert=True)
            newOperationForChangeEvent = ChangeEventOperations(change_event_id = self.change_event, change_operation_id = createLegend.id, change_operation='Add_Taxonomy')
        elif 'existing_taxonomy_name' in self.request.session and 'create_new_taxonomy_version' in self.request.session:
            oldVer = int(legendVer)-1
            createLegendVersion = AddTaxonomyVersionOperation(legend_id = legendId, old_legend_ver = oldVer, new_legend_ver = legendVer, root_concept_id = root_concept, legend_root_concept_combination_id = connectToLegend)
            createLegendVersion.save(force_insert=True)
            newOperationForChangeEvent = ChangeEventOperations(change_event_id = self.change_event, change_operation_id = createLegendVersion.id, change_operation='Add_Taxonomy_Version')
        newOperationForChangeEvent.save(force_insert=True)
    
       
    def create_concept(self, conceptName, mean_vector, covariance_matrix, extension, producer_accuracy, user_accuracy, parentName="", details=""):
        current_concept = Concept(concept_name = conceptName, description = details, date_expired = datetime(9999, 9, 12), created_by = self.authuser_instance, change_event_id = self.change_event)
        current_concept.save(force_insert=True)
        
        connectToLegend = LegendConceptCombination(legend_id = self.request.session['legend_id'], legend_ver = self.request.session['legend_ver'], concept = current_concept, change_event_id = self.change_event)
        connectToLegend.save(force_insert=True)
        
        if parentName == "":
            parentName = self.request.session['root_concept']
        parent_concept_connection_to_legend = LegendConceptCombination.objects.get(concept__concept_name = parentName,  legend_id = self.request.session['legend_id'], legend_ver = self.request.session['legend_ver'])
        
        addRelationship = HierarchicalRelationship(relationship_name='parent-of', expired=False, concept1 =  parent_concept_connection_to_legend, concept2 = connectToLegend)
        addRelationship.save(force_insert=True)
        
        extension_id = self.create_extension(extension)
        cov_mat_id = self.create_covariance_matrix(covariance_matrix)
        vector_id = self.create_mean_vector(mean_vector)
        comp_int = self.create_computational_intension(vector_id, cov_mat_id, producer_accuracy, user_accuracy)
        CatInstop_instance = self.create_categories(connectToLegend, comp_int, extension_id)
        
        createConcept_op = AddConceptOperation(concept_id = current_concept, legend_concept_comb_id = connectToLegend, hierarchical_relationship_id= addRelationship, category_instantiation_op_id= CatInstop_instance)
        createConcept_op.save(force_insert=True)
        newOperationForChangeEvent = ChangeEventOperations(change_event_id = self.change_event, change_operation_id = createConcept_op.id, change_operation='Add_Concept')
        newOperationForChangeEvent.save(force_insert=True)
        
    def add_existing_concept_to_new_version_of_legend_with_updated_categories(self, conceptName, mean_vector, covariance_matrix, extension, producer_accuracy, user_accuracy, int_similarity, ext_similarity, int_relation, ext_relation, parentName=""):
        concept_instance = Concept.objects.get(concept_name = conceptName)
        
        customquery = CustomQueries()
        oldversion = self.request.session['existing_taxonomy_ver'] - 1
        old_category = customquery.get_category_details_of_a_concept_in_a_legend(self.request.session['existing_taxonomy_id'], oldversion, conceptName)
        
        connectToLegend = LegendConceptCombination(legend_id = self.request.session['existing_taxonomy_id'], legend_ver = self.request.session['existing_taxonomy_ver'], concept = concept_instance, change_event_id = self.change_event)
        connectToLegend.save(force_insert=True)
        
        if parentName == "":
            parentName = self.request.session['root_concept']
        parent_concept_connection_to_legend = LegendConceptCombination.objects.get(concept__concept_name = parentName,  legend_id = self.request.session['existing_taxonomy_id'], legend_ver = self.request.session['existing_taxonomy_ver'])
        
        addRelationship = HierarchicalRelationship(relationship_name='parent-of', expired=False, concept1 =  parent_concept_connection_to_legend, concept2 = connectToLegend)
        addRelationship.save(force_insert=True)
        
        extension_id = self.create_extension(extension)
        cov_mat_id = self.create_covariance_matrix(covariance_matrix)
        vector_id = self.create_mean_vector(mean_vector)
        comp_int = self.create_computational_intension(vector_id, cov_mat_id, producer_accuracy, user_accuracy)
        CatInstop_instance = self.create_categories(connectToLegend, comp_int, extension_id)
        
        addHorizontalRelationship = HorizontalRelationship(comp_intension_relationship_name = int_relation, extension_relationship_name= ext_relation, expired=False, category1_id = CatInstop_instance.category_id, category1_evol_ver = CatInstop_instance.category_evol_ver, category1_comp_ver=  CatInstop_instance.category_comp_ver, category2_id = old_category[0], category2_evol_ver = old_category[1], category2_comp_ver=  old_category[2],intensional_similarity = int_similarity, extensional_similarity = ext_similarity)
        addHorizontalRelationship.save(force_insert=True)
        
        new_op = AddExistingConceptToNewVersion(concept_id = concept_instance, legend_concept_comb_id = connectToLegend, hierarchical_relationship_id= addRelationship, horizontal_relationship_id= addHorizontalRelationship, category_instantiation_op_id= CatInstop_instance)
        new_op.save(force_insert=True)
        newOperationForChangeEvent = ChangeEventOperations(change_event_id = self.change_event, change_operation_id = new_op.id, change_operation='Add_Existing_Concept_To_New_Version_Of_Legend')
        newOperationForChangeEvent.save(force_insert=True)
        
    def add_concept_split_from_existing_concept_to_new_version_of_legend(self, conceptName, existingConcept, mean_vector, covariance_matrix, extension, producer_accuracy, user_accuracy, int_similarity, ext_containment, int_relation, ext_relation, parentName="", details=""):
        print conceptName, existingConcept, mean_vector,producer_accuracy, user_accuracy, int_similarity, ext_containment, int_relation, ext_relation
        current_concept = Concept(concept_name = conceptName, description = details, date_expired = datetime(9999, 9, 12), created_by = self.authuser_instance, change_event_id = self.change_event)
        current_concept.save(force_insert=True)
        
        customquery = CustomQueries()
        oldversion = self.request.session['existing_taxonomy_ver'] - 1
        existing_category_that_split = customquery.get_category_details_of_a_concept_in_a_legend(self.request.session['existing_taxonomy_id'], oldversion, existingConcept)
        
        connectToLegend = LegendConceptCombination(legend_id = self.request.session['existing_taxonomy_id'], legend_ver = self.request.session['existing_taxonomy_ver'], concept = current_concept, change_event_id = self.change_event)
        connectToLegend.save(force_insert=True)
        
        if parentName == "":
            parentName = self.request.session['root_concept']
        parent_concept_connection_to_legend = LegendConceptCombination.objects.get(concept__concept_name = parentName,  legend_id = self.request.session['existing_taxonomy_id'], legend_ver = self.request.session['existing_taxonomy_ver'])
        
        addRelationship = HierarchicalRelationship(relationship_name='parent-of', expired=False, concept1 =  parent_concept_connection_to_legend, concept2 = connectToLegend)
        addRelationship.save(force_insert=True)
        
        extension_id = self.create_extension(extension)
        cov_mat_id = self.create_covariance_matrix(covariance_matrix)
        vector_id = self.create_mean_vector(mean_vector)
        comp_int = self.create_computational_intension(vector_id, cov_mat_id, producer_accuracy, user_accuracy)
        CatInstop_instance = self.create_categories(connectToLegend, comp_int, extension_id)
        
        addHorizontalRelationship = HorizontalRelationship(comp_intension_relationship_name = int_relation, extension_relationship_name= ext_relation, expired=False, category1_id = CatInstop_instance.category_id, category1_evol_ver = CatInstop_instance.category_evol_ver, category1_comp_ver=  CatInstop_instance.category_comp_ver, category2_id = existing_category_that_split[0], category2_evol_ver = existing_category_that_split[1], category2_comp_ver=  existing_category_that_split[2],intensional_similarity = int_similarity, extensional_containment = ext_containment)
        addHorizontalRelationship.save(force_insert=True)
        
        new_op = AddConSplitFrmExistToNewVer(concept_id = current_concept, existing_split_concept_id = existing_category_that_split[0], legend_concept_comb_id = connectToLegend, hierarchical_relationship_id= addRelationship, horizontal_relationship_id= addHorizontalRelationship, category_instantiation_op_id= CatInstop_instance)
        new_op.save(force_insert=True)
        print self.change_event.id
        print new_op.id
        newOperationForChangeEvent = ChangeEventOperations(change_event_id = self.change_event, change_operation_id = new_op.id, change_operation='Add_Concept_Split_From_Existing_To_New_Version_Of_Legend')
        newOperationForChangeEvent.save(force_insert=True)

        
    def create_categories(self, legend_concept_comb_id, comp_int_id, ext_id):
        if Category.objects.all().exists():
            CId = Category.objects.latest("category_id").category_id + 1
        else:
            CId =0
        cat = Category(category_id = CId, category_evol_ver=1, category_comp_ver = 1, date_expired= datetime(9999, 9, 12), trainingset_id= self.request.session['current_training_file_id'], trainingset_ver=self.request.session['current_training_file_ver'], creator= self.authuser_instance, legend_concept_combination_id = legend_concept_comb_id, computational_intension_id= comp_int_id, extension_id= ext_id, change_event_id = self.change_event)
        
        cat.save(force_insert=True)
        
        CatInstop = CategoryInstantiationOperation(legend_concept_id = legend_concept_comb_id, comp_int_id = comp_int_id, ext_id = ext_id, category_id = cat.category_id, category_evol_ver = cat.category_evol_ver, category_comp_ver = cat.category_comp_ver)
        CatInstop.save(force_insert=True)
        
        return CatInstop
            
    
    def create_extension(self, extension):
        if SetOfOccurences.objects.all().exists():
            setofocc_id = SetOfOccurences.objects.latest("id").id + 1
        else:
            setofocc_id = 0
        
        soc = [SetOfOccurences(id = setofocc_id, x_coordinate = row[0], y_coordinate=row[1]) for row in extension]
        SetOfOccurences.objects.bulk_create(soc)
        
        cursor = connection.cursor()
        cursor.execute("select activity_instance from exploration_chain where id = %s and activity = 'classification' order by activity_instance \
                        desc limit 1", [self.request.session['exploration_chain_id']])
        activity_id = cursor.fetchone()[0]
        
        classification_activity_instance = ClassificationActivity.objects.get(id = activity_id)
        
        ext = Extension(set_of_occurences_id = setofocc_id, classification_activity_id = classification_activity_instance)
        ext.save(force_insert=True)
        return ext
        
    def create_mean_vector(self, mean_vector):
        
        if len(mean_vector)==3:
            meanVector = MeanVector(band1 = mean_vector[0], band2 = mean_vector[1], band3 = mean_vector[2])
        else:
            meanVector = MeanVector(band1 = mean_vector[0], band2 = mean_vector[1], band3 = mean_vector[2], band4 = mean_vector[3], band5 = mean_vector[4], band6 = mean_vector[5], band7 = mean_vector[6], band8 = mean_vector[7])
        meanVector.save(force_insert=True)
        return meanVector.id
    
    def create_covariance_matrix(self, covariance_matrix):
        if CovarianceMatrix.objects.all().exists():
            CM_id = CovarianceMatrix.objects.latest("covariance_matrix_id").covariance_matrix_id + 1
        else:
            CM_id =0
        row=0
        column=0
        
        cm =[]
        matrix = numpy.array(covariance_matrix)
        for eachRow in matrix:
            for eachCell in eachRow:
                cm.append(CovarianceMatrix(covariance_matrix_id = CM_id, matrix_row = row, matrix_column = column, cell_value = eachCell))
                column = column+1
            row = row +1
        CovarianceMatrix.objects.bulk_create(cm)
        return CM_id
    
    def create_computational_intension(self, meanvector_id, cov_mat_id, prodacc, useracc):
        cursor = connection.cursor()
        cursor.execute("select activity_instance from exploration_chain where id = %s and activity = 'learning' order by activity_instance \
                        desc limit 1", [self.request.session['exploration_chain_id']])
        activity_id = cursor.fetchone()[0]
        
        learning_activity_instance = LearningActivity.objects.get(id = activity_id)
        comp_int = ComputationalIntension(mean_vector_id = meanvector_id, covariance_matrix_id = cov_mat_id, learning_activity_id=learning_activity_instance, producer_accuracy = prodacc, user_accuracy = useracc)
        comp_int.save(force_insert=True)
        return comp_int

class CustomQueries:
    
    def get_latest_versions_of_all_legends(self):
        cursor = connection.cursor()
        
        cursor.execute("select legend_id, max(legend_ver), legend_name from legend group by legend_id, legend_name")
        
        row = cursor.fetchall()
        return row



    def get_trainingset_name_for_current_version_of_legend(self, legendName):
        cursor = connection.cursor()
        
        cursor.execute("select t.trainingset_id, t.trainingset_ver, t.trainingset_name from trainingset t, category c, legend l, legend_concept_combination lcc \
                        where l.legend_name = %s and c.trainingset_id = t.trainingset_id and c.trainingset_ver = t.trainingset_ver and c.legend_concept_combination_id = lcc.id and \
                        lcc.id = (select lcc1.id from legend_concept_combination lcc1 where lcc1.legend_id = l.legend_id and lcc1.legend_ver= l.legend_ver order by lcc1.id DESC limit 1)", [legendName])
        
        row = cursor.fetchone()
        return row
        
    def get_trainingsample_id_and_ver_for_concept_in_reference_taxonomy(self, tid, ver, concept):
        cursor = connection.cursor()
        
        a = True
        while a:
            
            cursor.execute("select tsc.trainingsample_id, tsc.trainingsample_ver, tsc.samplefile_name from trainingsample_for_category tsc, trainingset_trainingsamples tts where tts.trainingsample_id = tsc.trainingsample_id \
                            and tts.trainingsample_ver = tsc.trainingsample_ver and tsc.concept_name = %s and tts.trainingset_id = %s and tts.trainingset_ver =%s", [concept, tid, ver])
            row = cursor.fetchone()
            if not row:
                ver = int(ver)-1
            else:
                a = False
        return row
            
            
        
    def get_model_name_and_accuracy_from_a_legend(self, lid, ver):
        cursor = connection.cursor()
        
        cursor.execute("select classificationmodel.model_type, classificationmodel.accuracy from classificationmodel, legend where \
                        legend.model_id = classificationmodel.id and legend.legend_id = %s and legend.legend_ver = %s", [lid, ver])
        
        row = cursor.fetchone()
        return row
        
    
    def get_concepts_list_for_a_legend(self, lid, ver):
        cursor = connection.cursor()
            
        cursor.execute("select concept.id, concept.concept_name from concept, legend_concept_combination where legend_concept_combination.legend_id = %s and \
                        legend_concept_combination.legend_ver = %s and legend_concept_combination.concept_id = concept.id and concept_name NOT LIKE 'root%%'", [lid, ver])
        
        row = cursor.fetchall()
        return row
    
    def get_concept_details(self, clid):
        cursor = connection.cursor()
            
        cursor.execute("select concept.id, concept.concept_name from concept, legend_concept_combination where legend_concept_combination.legend_id = %s and \
                        legend_concept_combination.legend_ver = %s and legend_concept_combination.concept_id = concept.id and concept_name NOT LIKE 'root%%'", [clid])
        
        row = cursor.fetchall()
        return row
        
    def get_accuracies_and_validation_method_of_a_category(self, lid, ver, concept):
        cursor = connection.cursor()
            
        cursor.execute("select ci.producer_accuracy, ci.user_accuracy, la.validation, cl.classifier_name from computational_intension ci, category ca, concept c, legend l, \
                        legend_concept_combination lcc, classificationmodel cm, learning_activity la, classifier cl where l.legend_id = %s and l.legend_ver = %s and \
                        c.concept_name= %s and c.id = lcc.concept_id and lcc.legend_id = l.legend_id and lcc.legend_ver=l.legend_ver and \
                        ca.legend_concept_combination_id = lcc.id and ca.computational_intension_id = ci.id and l.model_id = cm.id and \
                        l.model_id = la.model_id and cl.id = la.classifier_id", [lid, ver, concept])
        
        row = cursor.fetchall()
        return row
        
    def getExtension(self, concept_name, lid, ver):
        cursor = connection.cursor()
        
        cursor.execute("select soc.x_coordinate, soc.y_coordinate from concept c, legend l, legend_concept_combination lcc, set_of_occurences soc,\
                        category ca, extension e where lcc.concept_id = c.id and lcc.legend_id = %s and lcc.legend_ver = %s \
                        and c.concept_name = %s and ca.legend_concept_combination_id = lcc.id and  \
                        ca.extension_id = e.id and soc.id = e.set_of_occurences_id", [lid, ver, concept_name])
        
        row = cursor.fetchall()
        return row
        
    def getTrainingSampleForTrainingset(self, id, ver):
        cursor = connection.cursor()
        
        cursor.execute("select tsc.trainingsample_id, tsc.trainingsample_ver, tsc.samplefile_name from trainingset_trainingsamples tts, trainingsample_for_category tsc \
                        where tts.trainingsample_id = tsc.trainingsample_id and tts.trainingsample_ver = tsc.trainingsample_ver and tts.trainingset_id = %s and \
                        tts.trainingset_ver = %s", [id, ver])
        
        row = cursor.fetchall()
        return row
        
        
        
    def getTrainingSampleIdAndVersionForAGivenConceptInATrainingSet(self, id, ver, name):
        cursor = connection.cursor()
        
        cursor.execute("select tsc.trainingsample_id, tsc.trainingsample_ver from trainingset_trainingsamples tts, trainingsample_for_category tsc where \
                        tts.trainingsample_id = tsc.trainingsample_id and tts.trainingsample_ver = tsc.trainingsample_ver and tts.trainingset_id = %s and \
                        tts.trainingset_ver = %s and tsc.concept_name = %s", [id, ver, name])
        
        row = cursor.fetchall()
        return row
    
    
    def get_latest_version_of_a_trainingset(self, id):
        cursor = connection.cursor()
        
        cursor.execute("select trainingset_ver from trainingset where trainingset_id = %s  order by trainingset_ver desc limit 1", [id])
        
        row = cursor.fetchone()
        
        return row[0]
        
    def get_category_details_of_a_concept_in_a_legend(self, id, ver, concept):
        cursor = connection.cursor()
        
        cursor.execute("select ca.category_id, ca.category_evol_ver, ca.category_comp_ver from category ca, concept c, legend_concept_combination l where l.id = ca.legend_concept_combination_id and l.concept_id = c.id and l.legend_id = %s and l.legend_ver = %s and c.concept_name= %s", [id, ver, concept])
        
        row = cursor.fetchone()
        
        return row
    
    def getDetailsOfCreateTrainingSetActivity(self, ctaid):
        cursor = connection.cursor()
        
        cursor.execute("select trainingset_id, trainingset_ver, reference_trainingset_id, reference_trainingset_ver, operation, concept1, concept2, concept3, concept4 from \
                        create_trainingset_activity cta, create_trainingset_activity_operations ctao where cta.id = %s and cta.id = ctao.create_trainingset_activity_id", [ctaid])
        
        row = cursor.fetchall()
        return row        
        
    def getDetailsOfChangeTrainingSetActivity(self, ctaid):
        cursor = connection.cursor()
        
        cursor.execute("select oldtrainingset_id, oldtrainingset_ver, newtrainingset_ver, operation, concept1, concept2, concept3, concept4 from change_trainingset_activity cta, \
                        change_trainingset_activity_details ctad where cta.id = %s and cta.id = ctad.activity_id", [ctaid])
        
        row = cursor.fetchall()
        return row        
        
    def getDetailsOfTrainingActivity(self, taid):
        cursor = connection.cursor()
        
        cursor.execute("select classifier_name, validation_score, validation from learning_activity, classifier where learning_activity.id = %s and \
                        learning_activity.classifier_id = classifier.id", [taid])
        
        row = cursor.fetchone()
        
        return row         
        
        
        
        