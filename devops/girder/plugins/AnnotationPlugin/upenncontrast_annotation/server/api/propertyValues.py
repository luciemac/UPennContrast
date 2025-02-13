from girder.api import access
from girder.api.describe import Description, autoDescribeRoute, describeRoute
from girder.constants import AccessType
from girder.api.rest import Resource, loadmodel
from ..models.annotation import Annotation as AnnotationModel
from ..models.propertyValues import AnnotationPropertyValues as PropertyValuesModel
from girder.exceptions import AccessException, RestException, ValidationException


class PropertyValues(Resource):
    def __init__(self):
        super().__init__()
        self.resourceName = 'annotation_property_values'
        self._annotationModel = AnnotationModel()
        self._annotationPropertyValuesModel = PropertyValuesModel()

        self.route('POST', (), self.add)
        self.route('GET', (), self.find)
        self.route('GET', ('histogram',), self.histogram)

    # TODO: anytime a dataset is mentioned, load the dataset and check for existence and that the user has access to it
    # TODO: creation date, update date, creatorId ?
    # TODO(performance): proper indexing
    # TODO(performance): use objectId whenever possible

    @access.user
    @describeRoute(Description("Save computed property values").param('body', 'Property values', paramType='body')
                   .param('annotationId', 'The ID of the annotation')
                   .param('datasetId', 'The ID of the dataset'))
    def add(self, params):
        currentUser = self.getCurrentUser()
        if not currentUser:
            raise AccessException('User not found', 'currentUser')
        return self._annotationPropertyValuesModel.appendValues(currentUser, self.getBodyJson(), params['annotationId'], params['datasetId'])

    @access.user
    @describeRoute(Description("Search for property values")
                   .responseClass('annotation')
                   .param('datasetId', 'Get all property values for this dataset', required=False)
                   .param('annotationId', 'Get all property values for this annotation', required=False)
                   # TODO: figure out how to implement this. But do we need it ?
                   .param('propertyId', 'Restrict results to this property', required=False)
                   .pagingParams(defaultSort='_id')
                   .errorResponse()
                   )
    def find(self, params):
        limit, offset, sort = self.getPagingParameters(params, 'lowerName')
        query = {}
        if 'datasetId' in params:
            query['datasetId'] = params['datasetId']
        if 'annotationId' in params:
            query['annotationId'] = params['annotationId']
        return self._annotationPropertyValuesModel.findWithPermissions(query, sort=sort, user=self.getCurrentUser(), level=AccessType.READ, limit=limit, offset=offset)

    @access.user
    @describeRoute(Description("Get a histogram for property values in the specified dataset")
    .param('propertyId', 'The id of the property')
    .param('datasetId', 'The id of the dataset')
    .param('buckets', 'The number of buckets', required=False)
    )
    def histogram(self, params):
        if 'buckets' in params:
            return self._annotationPropertyValuesModel.histogram(params['propertyId'], params['datasetId'], int(params['buckets']))
        else:
            return self._annotationPropertyValuesModel.histogram(params['propertyId'], params['datasetId'])
